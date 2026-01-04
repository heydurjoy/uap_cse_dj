from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Max
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse
from datetime import datetime
from .models import Club, ClubPosition, ClubPost, SEMESTER_CHOICES, CLUB_POST_TYPE_CHOICES


def check_club_access(user):
    """Check if user has manage_club_settings permission and is Faculty, Officer, or Power User"""
    if not user.is_authenticated:
        return False
    # Check permission
    if not user.has_permission('manage_club_settings'):
        return False
    # Allow if user is Faculty, Officer, or a Power User (power users can have any permission)
    user_type = user.user_type
    return user_type and (user_type in ['faculty', 'officer'] or user.is_power_user)


def check_club_convener_access(user, club):
    """Check if user is the convener of the given club"""
    if not user.is_authenticated:
        return False
    if not club or not club.convener:
        return False
    # Check if user has faculty profile and is the convener
    if hasattr(user, 'faculty_profile') and user.faculty_profile:
        return user.faculty_profile.pk == club.convener.pk
    return False


def check_club_president_access(user, club):
    """Check if user is the president of the given club"""
    if not user.is_authenticated:
        return False
    if not club or not club.president:
        return False
    # Check if user has club_member profile and is the president
    if hasattr(user, 'club_member_profile') and user.club_member_profile:
        return user.club_member_profile.pk == club.president.pk
    return False


def check_club_management_access(user, club=None):
    """Check if user can manage clubs (level 4+ Faculty/Officer OR convener OR president of the club)"""
    if not user.is_authenticated:
        return False
    # Level 4+ Faculty/Officers can manage all clubs
    if check_club_access(user):
        return True
    # Conveners can manage their own clubs
    if club and check_club_convener_access(user, club):
        return True
    # Presidents can manage their own clubs
    if club and check_club_president_access(user, club):
        return True
    return False


@login_required
def manage_clubs(request):
    """
    Manage clubs view.
    Level 4+ Faculty/Officers can manage all clubs.
    Conveners can manage their own clubs.
    """
    # Check if user has access
    if check_club_access(request.user):
        # Level 4+ Faculty/Officers see all clubs
        clubs = Club.objects.all().select_related('convener', 'president')
    elif hasattr(request.user, 'faculty_profile') and request.user.faculty_profile:
        # Conveners see only their clubs
        clubs = Club.objects.filter(convener=request.user.faculty_profile).select_related('convener', 'president')
    else:
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('people:user_profile')
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        clubs = clubs.filter(
            Q(name__icontains=search_query) |
            Q(moto__icontains=search_query) |
            Q(description__icontains=search_query)
        )
    
    # Order by serial number, then name
    clubs = clubs.order_by('sl', 'name')
    
    # Check if user can create/delete clubs (only Faculty/Officers with manage_club_settings permission)
    can_create_delete = check_club_access(request.user)
    
    context = {
        'clubs': clubs,
        'search_query': search_query,
        'can_create_delete': can_create_delete,
    }
    
    return render(request, 'clubs/manage_clubs.html', context)


def club_detail(request, pk):
    """View club details - Public access, no authentication required"""
    club = get_object_or_404(Club, pk=pk)
    
    # Get positions for this club, ordered by year, semester, and serial number
    # Get the most recent year/semester positions
    from people.models import Faculty
    positions = ClubPosition.objects.filter(club=club).select_related('faculty', 'club_member').order_by('-academic_year', 'semester', 'sl')
    
    # Get the most recent year and semester
    if positions.exists():
        latest_position = positions.first()
        latest_year = latest_position.academic_year
        latest_semester = latest_position.semester
        
        # Filter positions for the latest year/semester
        latest_positions = positions.filter(
            academic_year=latest_year,
            semester=latest_semester
        ).order_by('sl')
    else:
        latest_positions = ClubPosition.objects.none()
    
    # Organize members: convener first, then faculties, then club members
    organized_members = []
    
    # 1. Add convener if exists
    if club.convener:
        organized_members.append({
            'type': 'convener',
            'faculty': club.convener,
            'club_member': None,
            'position_title': 'Convener',
            'name': club.convener.name,
            'profile_pic': club.convener.profile_pic if club.convener.profile_pic else None,
            'designation': club.convener.designation if club.convener.designation else None,
        })
    
    # 2. Add faculties in positions
    faculty_positions = latest_positions.filter(faculty__isnull=False).select_related('faculty')
    for position in faculty_positions:
        organized_members.append({
            'type': 'faculty',
            'faculty': position.faculty,
            'club_member': None,
            'position_title': position.position_title,
            'name': position.faculty.name,
            'profile_pic': position.faculty.profile_pic if position.faculty.profile_pic else None,
            'designation': position.faculty.designation if position.faculty.designation else None,
        })
    
    # 3. Add club members in positions (ordered by serial number)
    member_positions = latest_positions.filter(club_member__isnull=False).select_related('club_member', 'club_member__base_user')
    member_pks_in_positions = set()  # Track which members are already in positions
    for position in member_positions:
        member_pk = position.club_member.pk
        member_pks_in_positions.add(member_pk)
        organized_members.append({
            'type': 'club_member',
            'faculty': None,
            'club_member': position.club_member,
            'club_member_pk': member_pk,
            'position_title': position.position_title,
            'name': position.club_member.name,
            'profile_pic': position.club_member.profile_pic if position.club_member.profile_pic else None,
            'student_id': position.club_member.student_id if position.club_member.student_id else None,
            'is_president': club.president and club.president.pk == member_pk,
        })
    
    # 4. Add president if they exist and are not already in the list (not in a position)
    if club.president and club.president.pk not in member_pks_in_positions:
        organized_members.append({
            'type': 'club_member',
            'faculty': None,
            'club_member': club.president,
            'club_member_pk': club.president.pk,
            'position_title': 'President',
            'name': club.president.name,
            'profile_pic': club.president.profile_pic if club.president.profile_pic else None,
            'student_id': club.president.student_id if club.president.student_id else None,
            'is_president': True,
        })
    
    # Get pinned posts for this club
    pinned_posts = ClubPost.objects.filter(
        club=club,
        is_pinned=True
    ).select_related('posted_by', 'last_edited_by').order_by('-created_at')
    
    # Get all posts for this club (for newsfeed)
    all_posts = ClubPost.objects.filter(
        club=club
    ).select_related('posted_by', 'last_edited_by').order_by('-is_pinned', '-created_at')
    
    context = {
        'club': club,
        'organized_members': organized_members,
        'pinned_posts': pinned_posts,
        'all_posts': all_posts,
        'CLUB_POST_TYPE_CHOICES': CLUB_POST_TYPE_CHOICES,
    }
    
    return render(request, 'clubs/club_detail.html', context)


@login_required
def create_club(request):
    """
    Create a new club.
    Only level 4+ Faculty or Officers can create clubs.
    """
    if not check_club_access(request.user):
        messages.error(request, 'You do not have permission to create clubs.')
        return redirect('people:user_profile')
    
    if request.method == 'POST':
        try:
            club = Club()
            club.name = request.POST.get('name', '').strip()
            club.short_name = request.POST.get('short_name', '').strip() or None
            # Automatically set serial number (next available number)
            max_sl = Club.objects.aggregate(max_sl=Max('sl'))['max_sl']
            club.sl = (max_sl + 1) if max_sl else 1
            club.moto = request.POST.get('moto', '').strip() or None
            club.description = request.POST.get('description', '') or None
            
            # Handle ForeignKey fields
            convener_id = request.POST.get('convener', '')
            if convener_id:
                try:
                    from people.models import Faculty
                    club.convener = Faculty.objects.get(pk=convener_id)
                except (Faculty.DoesNotExist, ValueError):
                    club.convener = None
            else:
                club.convener = None
            
            president_id = request.POST.get('president', '')
            if president_id:
                try:
                    from people.models import ClubMember
                    club.president = ClubMember.objects.get(pk=president_id)
                except (ClubMember.DoesNotExist, ValueError):
                    club.president = None
            else:
                club.president = None
            
            # Handle URL fields
            club.website_url = request.POST.get('website_url', '').strip() or None
            club.facebook_url = request.POST.get('facebook_url', '').strip() or None
            club.instagram_url = request.POST.get('instagram_url', '').strip() or None
            club.youtube_url = request.POST.get('youtube_url', '').strip() or None
            
            # Handle image uploads
            if 'logo' in request.FILES:
                club.logo = request.FILES['logo']
            if 'cover_photo' in request.FILES:
                club.cover_photo = request.FILES['cover_photo']
            
            club.full_clean()  # This will trigger model validation
            club.save()
            
            messages.success(request, 'Club created successfully!')
            return redirect('clubs:manage_clubs')
        except Exception as e:
            messages.error(request, f'Error creating club: {str(e)}')
            # Get form data for repopulation
            from people.models import Faculty, ClubMember
            context = {
                'faculties': Faculty.objects.all().order_by('name'),
                'club_members': ClubMember.objects.all().order_by('name'),
                'club_data': request.POST,
            }
            return render(request, 'clubs/create_club.html', context)
    
    # Get form data for GET request
    from people.models import Faculty, ClubMember
    context = {
        'faculties': Faculty.objects.all().order_by('name'),
        'club_members': ClubMember.objects.all().order_by('name'),
    }
    return render(request, 'clubs/create_club.html', context)


@login_required
def edit_club(request, pk):
    """
    Edit an existing club.
    Level 4+ Faculty/Officers or conveners can edit clubs.
    """
    club = get_object_or_404(Club, pk=pk)
    
    if not check_club_management_access(request.user, club):
        messages.error(request, 'You do not have permission to edit this club.')
        return redirect('people:user_profile')
    
    if request.method == 'POST':
        try:
            club.name = request.POST.get('name', '').strip()
            club.short_name = request.POST.get('short_name', '').strip() or None
            # Serial number is automatically set on creation, preserve existing value when editing
            # (sl is not shown in form, so it won't be in POST data)
            club.moto = request.POST.get('moto', '').strip() or None
            club.description = request.POST.get('description', '') or None
            
            # Handle ForeignKey fields
            convener_id = request.POST.get('convener', '')
            if convener_id:
                try:
                    from people.models import Faculty
                    club.convener = Faculty.objects.get(pk=convener_id)
                except (Faculty.DoesNotExist, ValueError):
                    club.convener = None
            else:
                club.convener = None
            
            president_id = request.POST.get('president', '')
            if president_id:
                try:
                    from people.models import ClubMember
                    club.president = ClubMember.objects.get(pk=president_id)
                except (ClubMember.DoesNotExist, ValueError):
                    club.president = None
            else:
                club.president = None
            
            # Handle URL fields
            club.website_url = request.POST.get('website_url', '').strip() or None
            club.facebook_url = request.POST.get('facebook_url', '').strip() or None
            club.instagram_url = request.POST.get('instagram_url', '').strip() or None
            club.youtube_url = request.POST.get('youtube_url', '').strip() or None
            
            # Handle image uploads (only if new file is provided)
            if 'logo' in request.FILES:
                club.logo = request.FILES['logo']
            if 'cover_photo' in request.FILES:
                club.cover_photo = request.FILES['cover_photo']
            
            # Handle cropping fields
            if 'logo_cropping' in request.POST:
                club.logo_cropping = request.POST.get('logo_cropping', '')
            if 'cover_photo_cropping' in request.POST:
                club.cover_photo_cropping = request.POST.get('cover_photo_cropping', '')
            
            club.full_clean()  # This will trigger model validation
            club.save()
            
            messages.success(request, 'Club updated successfully!')
            return redirect('clubs:manage_clubs')
        except Exception as e:
            messages.error(request, f'Error updating club: {str(e)}')
    
    # Get form data for GET request
    from people.models import Faculty, ClubMember
    context = {
        'club': club,
        'faculties': Faculty.objects.all().order_by('name'),
        'club_members': ClubMember.objects.all().order_by('name'),
    }
    return render(request, 'clubs/edit_club.html', context)


@login_required
def delete_club(request, pk):
    """
    Delete a club.
    Level 4+ Faculty/Officers or conveners can delete clubs.
    """
    club = get_object_or_404(Club, pk=pk)
    
    if not check_club_management_access(request.user, club):
        messages.error(request, 'You do not have permission to delete this club.')
        return redirect('people:user_profile')
    
    if request.method == 'POST':
        club_name = club.name
        club.delete()
        messages.success(request, f'Club "{club_name}" deleted successfully!')
        return redirect('clubs:manage_clubs')
    
    context = {
        'club': club,
    }
    return render(request, 'clubs/delete_club.html', context)


@login_required
@require_http_methods(["POST"])
def delete_clubs(request):
    """
    Delete multiple clubs at once.
    Level 4+ Faculty/Officers or conveners can delete clubs.
    """
    club_ids = request.POST.getlist('club_ids[]')
    
    if not club_ids:
        return JsonResponse({
            'success': False,
            'message': 'No clubs selected for deletion.'
        })
    
    # Filter clubs based on access
    if check_club_access(request.user):
        # Level 4+ can delete any club
        clubs_to_delete = Club.objects.filter(pk__in=club_ids)
    else:
        # Conveners can only delete their own clubs
        if hasattr(request.user, 'faculty_profile') and request.user.faculty_profile:
            clubs_to_delete = Club.objects.filter(
                pk__in=club_ids,
                convener=request.user.faculty_profile
            )
        else:
            return JsonResponse({
                'success': False,
                'message': 'You do not have permission to delete clubs.'
            }, status=403)
    
    try:
        clubs = clubs_to_delete
        deleted_count = clubs.count()
        club_names = [club.name for club in clubs]
        clubs.delete()
        
        return JsonResponse({
            'success': True,
            'message': f'Successfully deleted {deleted_count} club(s).',
            'deleted_clubs': club_names
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error deleting clubs: {str(e)}'
        }, status=500)


# ==============================================================================
# CLUB POSITION MANAGEMENT VIEWS
# ==============================================================================

@login_required
def manage_club_positions(request, pk):
    """
    Manage positions for a specific club.
    Only conveners or level 4+ Faculty/Officers can manage positions.
    """
    club = get_object_or_404(Club, pk=pk)
    
    if not check_club_management_access(request.user, club):
        messages.error(request, 'You do not have permission to manage positions for this club.')
        return redirect('people:user_profile')
    
    # Get current year and calculate max year (current + 5)
    current_year = datetime.now().year
    max_year = current_year + 5
    
    # Get positions for this club, ordered by year, semester, and serial number
    positions = ClubPosition.objects.filter(club=club).select_related('faculty', 'club_member').order_by('-academic_year', 'semester', 'sl', 'position_title')
    
    # Filter by year and semester if provided
    year_filter = request.GET.get('year', '')
    semester_filter = request.GET.get('semester', '')
    
    if year_filter:
        try:
            positions = positions.filter(academic_year=int(year_filter))
        except ValueError:
            pass
    
    if semester_filter:
        positions = positions.filter(semester=semester_filter)
    
    # Get all faculties and club members for dropdowns
    from people.models import Faculty, ClubMember
    faculties = Faculty.objects.all().order_by('name')
    club_members = ClubMember.objects.all().order_by('name')
    
    # Generate year choices (2000 to current + 5)
    year_choices = list(range(2000, max_year + 1))
    year_choices.reverse()  # Most recent first
    
    context = {
        'club': club,
        'positions': positions,
        'faculties': faculties,
        'club_members': club_members,
        'SEMESTER_CHOICES': SEMESTER_CHOICES,
        'year_choices': year_choices,
        'current_year': current_year,
        'max_year': max_year,
        'year_filter': year_filter,
        'semester_filter': semester_filter,
    }
    
    return render(request, 'clubs/manage_positions.html', context)


@login_required
def add_club_position(request, pk):
    """
    Add a new position to a club for a specific semester.
    """
    club = get_object_or_404(Club, pk=pk)
    
    if not check_club_management_access(request.user, club):
        messages.error(request, 'You do not have permission to add positions to this club.')
        return redirect('people:user_profile')
    
    if request.method == 'POST':
        try:
            position_title = request.POST.get('position_title', '').strip()
            academic_year = int(request.POST.get('academic_year'))
            semester = request.POST.get('semester')
            faculty_id = request.POST.get('faculty', '')
            club_member_id = request.POST.get('club_member', '')
            new_member_email = request.POST.get('new_member_email', '').strip().lower()
            
            if not all([position_title, academic_year, semester]):
                messages.error(request, 'Position title, year, and semester are required.')
                return redirect('clubs:manage_positions', pk=club.pk)
            
            if not faculty_id and not club_member_id and not new_member_email:
                messages.error(request, 'Either faculty or club member must be selected.')
                return redirect('clubs:manage_positions', pk=club.pk)
            
            if faculty_id and (club_member_id or new_member_email):
                messages.error(request, 'Cannot select both faculty and club member.')
                return redirect('clubs:manage_positions', pk=club.pk)
            
            if club_member_id and new_member_email:
                messages.error(request, 'Cannot select existing member and add new email at the same time.')
                return redirect('clubs:manage_positions', pk=club.pk)
            
            # Handle new member email
            if new_member_email:
                from people.models import BaseUser, ClubMember, AllowedEmail
                from django.contrib.auth.hashers import make_password
                import random
                import string
                
                # Check if BaseUser with this email already exists
                existing_user = BaseUser.objects.filter(email=new_member_email).first()
                
                if existing_user:
                    # Check if they already have a ClubMember profile
                    if hasattr(existing_user, 'club_member_profile'):
                        messages.warning(request, f'A club member with email {new_member_email} already exists. They should reset their password to access their account instead of signing up.')
                        return redirect('clubs:manage_positions', pk=club.pk)
                    else:
                        messages.error(request, f'A user with email {new_member_email} already exists but is not a club member. Please select an existing club member or use a different email.')
                        return redirect('clubs:manage_positions', pk=club.pk)
                
                # Check if AllowedEmail already exists
                # If it exists for a different club, we can't use it (email is unique)
                existing_allowed_email = AllowedEmail.objects.filter(email=new_member_email).first()
                if existing_allowed_email:
                    if existing_allowed_email.club and existing_allowed_email.club != club:
                        messages.error(request, f'Email {new_member_email} is already associated with another club ({existing_allowed_email.club.name}). Each email can only be associated with one club.')
                        return redirect('clubs:manage_positions', pk=club.pk)
                    # If it exists but not linked to a club, link it to this club
                    allowed_email = existing_allowed_email
                    if not allowed_email.club:
                        allowed_email.club = club
                        allowed_email.save()
                else:
                    # Create new AllowedEmail linked to this club
                    allowed_email = AllowedEmail.objects.create(
                        email=new_member_email,
                        user_type='club_member',
                        is_power_user=False,
                        is_active=True,
                        is_blocked=False,
                        created_by=request.user,
                        club=club,  # Link to this club
                    )
                
                # Generate a dummy username from email
                username_base = new_member_email.split('@')[0]
                username = username_base
                counter = 1
                while BaseUser.objects.filter(username=username).exists():
                    username = f"{username_base}{counter}"
                    counter += 1
                
                # Generate a random password (user will reset it later)
                dummy_password = ''.join(random.choices(string.ascii_letters + string.digits, k=16))
                hashed_password = make_password(dummy_password)
                
                # Create BaseUser with dummy info
                base_user = BaseUser.objects.create(
                    username=username,
                    email=new_member_email,
                    password=hashed_password,
                    user_type='club_member',
                    is_power_user=False,
                    allowed_email=allowed_email,
                    is_active=True,
                    is_staff=False,
                    is_superuser=False,
                )
                
                # Create ClubMember with dummy info (just email, name will be set later)
                club_member = ClubMember.objects.create(
                    base_user=base_user,
                    name=new_member_email.split('@')[0].title(),  # Use email prefix as temporary name
                    student_id=None,  # Will be set later when they sign up
                )
                
                club_member_id = club_member.pk
                messages.info(request, f'Dummy club member created for {new_member_email}. They can sign up later to complete their profile and access their account.')
            
            # Get the next serial number for this club, year, and semester
            existing_positions = ClubPosition.objects.filter(
                club=club,
                academic_year=academic_year,
                semester=semester
            )
            max_sl = existing_positions.aggregate(Max('sl'))['sl__max'] or 0
            next_sl = max_sl + 1
            
            # Create position
            position = ClubPosition(
                club=club,
                position_title=position_title,
                academic_year=academic_year,
                semester=semester,
                sl=next_sl
            )
            
            if faculty_id:
                from people.models import Faculty
                position.faculty = Faculty.objects.get(pk=faculty_id)
            elif club_member_id:
                from people.models import ClubMember
                position.club_member = ClubMember.objects.get(pk=club_member_id)
            
            position.full_clean()
            position.save()
            
            messages.success(request, f'Position "{position_title}" added successfully!')
            return redirect('clubs:manage_positions', pk=club.pk)
            
        except ValidationError as e:
            messages.error(request, f'Validation error: {str(e)}')
        except Exception as e:
            messages.error(request, f'Error adding position: {str(e)}')
    
    return redirect('clubs:manage_positions', pk=club.pk)


@login_required
def edit_club_position(request, pk, position_pk):
    """
    Edit a club position.
    """
    club = get_object_or_404(Club, pk=pk)
    position = get_object_or_404(ClubPosition, pk=position_pk, club=club)
    
    if not check_club_management_access(request.user, club):
        messages.error(request, 'You do not have permission to edit positions for this club.')
        return redirect('people:user_profile')
    
    # Get current year and calculate max year (current + 5)
    current_year = datetime.now().year
    max_year = current_year + 5
    year_choices = list(range(2000, max_year + 1))
    year_choices.reverse()  # Most recent first
    
    # Get all faculties and club members for dropdowns
    from people.models import Faculty, ClubMember
    faculties = Faculty.objects.all().order_by('name')
    club_members = ClubMember.objects.all().order_by('name')
    
    if request.method == 'POST':
        try:
            position_title = request.POST.get('position_title', '').strip()
            academic_year = int(request.POST.get('academic_year'))
            semester = request.POST.get('semester')
            faculty_id = request.POST.get('faculty', '')
            club_member_id = request.POST.get('club_member', '')
            
            if not all([position_title, academic_year, semester]):
                messages.error(request, 'Position title, year, and semester are required.')
                context = {
                    'club': club,
                    'position': position,
                    'faculties': faculties,
                    'club_members': club_members,
                    'SEMESTER_CHOICES': SEMESTER_CHOICES,
                    'year_choices': year_choices,
                    'current_year': current_year,
                }
                return render(request, 'clubs/edit_position.html', context)
            
            if not faculty_id and not club_member_id:
                messages.error(request, 'Either faculty or club member must be selected.')
                context = {
                    'club': club,
                    'position': position,
                    'faculties': faculties,
                    'club_members': club_members,
                    'SEMESTER_CHOICES': SEMESTER_CHOICES,
                    'year_choices': year_choices,
                    'current_year': current_year,
                }
                return render(request, 'clubs/edit_position.html', context)
            
            if faculty_id and club_member_id:
                messages.error(request, 'Cannot select both faculty and club member.')
                context = {
                    'club': club,
                    'position': position,
                    'faculties': faculties,
                    'club_members': club_members,
                    'SEMESTER_CHOICES': SEMESTER_CHOICES,
                    'year_choices': year_choices,
                    'current_year': current_year,
                }
                return render(request, 'clubs/edit_position.html', context)
            
            # Update position
            position.position_title = position_title
            position.academic_year = academic_year
            position.semester = semester
            position.faculty = None
            position.club_member = None
            
            if faculty_id:
                position.faculty = Faculty.objects.get(pk=faculty_id)
            elif club_member_id:
                position.club_member = ClubMember.objects.get(pk=club_member_id)
            
            position.full_clean()
            position.save()
            
            messages.success(request, f'Position "{position_title}" updated successfully!')
            return redirect('clubs:manage_positions', pk=club.pk)
            
        except ValidationError as e:
            messages.error(request, f'Validation error: {str(e)}')
        except Exception as e:
            messages.error(request, f'Error updating position: {str(e)}')
    
    context = {
        'club': club,
        'position': position,
        'faculties': faculties,
        'club_members': club_members,
        'SEMESTER_CHOICES': SEMESTER_CHOICES,
        'year_choices': year_choices,
        'current_year': current_year,
    }
    return render(request, 'clubs/edit_position.html', context)


@login_required
def delete_club_position(request, pk, position_pk):
    """
    Delete a club position.
    Note: This only removes the position. The member's AllowedEmail and ClubMember profile
    remain intact, so they can still be in other clubs or be re-added to this club later.
    """
    club = get_object_or_404(Club, pk=pk)
    position = get_object_or_404(ClubPosition, pk=position_pk, club=club)
    
    if not check_club_management_access(request.user, club):
        messages.error(request, 'You do not have permission to delete positions from this club.')
        return redirect('people:user_profile')
    
    if request.method == 'POST':
        position_title = position.position_title
        # Get member info before deletion (for informational message)
        member_info = None
        if position.club_member:
            member_info = position.club_member.name or position.club_member.base_user.email if hasattr(position.club_member, 'base_user') else 'Unknown'
        
        # Delete the position (this does NOT delete the ClubMember or AllowedEmail)
        position.delete()
        
        if member_info:
            messages.success(request, f'Position "{position_title}" for {member_info} deleted successfully! The member\'s account and allowed email remain intact.')
        else:
            messages.success(request, f'Position "{position_title}" deleted successfully!')
        return redirect('clubs:manage_positions', pk=club.pk)
    
    context = {
        'club': club,
        'position': position,
    }
    return render(request, 'clubs/delete_position.html', context)


@login_required
@require_http_methods(["POST"])
def update_position_order(request, pk):
    """
    Update the order (serial numbers) of positions via drag and drop.
    Expects JSON: {"position_ids": [1, 2, 3, ...], "academic_year": 2024, "semester": "Fall"}
    """
    club = get_object_or_404(Club, pk=pk)
    
    if not check_club_management_access(request.user, club):
        return JsonResponse({
            'success': False,
            'message': 'You do not have permission to update positions for this club.'
        }, status=403)
    
    try:
        import json
        data = json.loads(request.body)
        position_ids = data.get('position_ids', [])
        academic_year = data.get('academic_year')
        semester = data.get('semester')
        
        if not position_ids or not academic_year or not semester:
            return JsonResponse({
                'success': False,
                'message': 'Missing required data: position_ids, academic_year, or semester.'
            }, status=400)
        
        # Verify all positions belong to this club and match the year/semester
        positions = ClubPosition.objects.filter(
            pk__in=position_ids,
            club=club,
            academic_year=academic_year,
            semester=semester
        )
        
        if positions.count() != len(position_ids):
            return JsonResponse({
                'success': False,
                'message': 'Some positions do not belong to this club or do not match the year/semester.'
            }, status=400)
        
        # Update serial numbers based on the order provided
        for index, position_id in enumerate(position_ids, start=1):
            ClubPosition.objects.filter(pk=position_id).update(sl=index)
        
        return JsonResponse({
            'success': True,
            'message': 'Position order updated successfully!'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': 'Invalid JSON data.'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error updating order: {str(e)}'
        }, status=500)


# ==============================================================================
# CLUB POST MANAGEMENT VIEWS
# ==============================================================================

def check_club_post_access(user, club):
    """Check if user can manage posts for a club (must be convener, president, or club member in a position)"""
    if not user.is_authenticated:
        return False
    
    # Check if user is convener (faculty)
    if hasattr(user, 'faculty_profile') and user.faculty_profile:
        if club.convener and club.convener.pk == user.faculty_profile.pk:
            return True
    
    # Check if user is club member
    if hasattr(user, 'club_member_profile') and user.club_member_profile:
        club_member = user.club_member_profile
        
        # Check if member is president
        if club.president and club.president.pk == club_member.pk:
            return True
        
        # Check if member is in any position for this club
        if ClubPosition.objects.filter(club=club, club_member=club_member).exists():
            return True
    
    return False


@login_required
def manage_club_posts(request, pk):
    """
    Manage posts for a specific club.
    Only club members (president or in positions) can manage posts.
    """
    club = get_object_or_404(Club, pk=pk)
    
    if not check_club_post_access(request.user, club):
        messages.error(request, 'You do not have permission to manage posts for this club.')
        return redirect('people:user_profile')
    
    # Get posts for this club
    posts = ClubPost.objects.filter(club=club).select_related('posted_by', 'last_edited_by')
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        posts = posts.filter(
            Q(short_title__icontains=search_query) |
            Q(long_title__icontains=search_query) |
            Q(tags__icontains=search_query) |
            Q(description__icontains=search_query)
        )
    
    # Filter by post type
    post_type_filter = request.GET.get('type', '')
    if post_type_filter:
        posts = posts.filter(post_type=post_type_filter)
    
    # Sort functionality
    sort_by = request.GET.get('sort', 'pinned')
    if sort_by == 'oldest':
        posts = posts.order_by('created_at')
    elif sort_by == 'newest':
        posts = posts.order_by('-created_at')
    elif sort_by == 'type':
        posts = posts.order_by('post_type', '-created_at')
    elif sort_by == 'title':
        posts = posts.order_by('short_title')
    elif sort_by == 'title_desc':
        posts = posts.order_by('-short_title')
    elif sort_by == 'pinned':
        # Pinned first, then by date
        posts = posts.order_by('-is_pinned', '-created_at')
    else:
        # Default: pinned first, then by date
        posts = posts.order_by('-is_pinned', '-created_at')
    
    context = {
        'club': club,
        'posts': posts,
        'search_query': search_query,
        'post_type_filter': post_type_filter,
        'sort_by': sort_by,
        'CLUB_POST_TYPE_CHOICES': CLUB_POST_TYPE_CHOICES,
    }
    
    return render(request, 'clubs/manage_posts.html', context)


@login_required
def create_club_post(request, pk):
    """
    Create a new post for a club.
    """
    club = get_object_or_404(Club, pk=pk)
    
    if not check_club_post_access(request.user, club):
        messages.error(request, 'You do not have permission to create posts for this club.')
        return redirect('people:user_profile')
    
    if request.method == 'POST':
        try:
            post_type = request.POST.get('post_type', 'event')
            short_title = request.POST.get('short_title', '').strip()
            long_title = request.POST.get('long_title', '').strip()
            tags = request.POST.get('tags', '').strip()
            description = request.POST.get('description', '').strip()
            is_pinned = request.POST.get('is_pinned') == 'on'
            
            # Optional date/time fields
            start_date_time_str = request.POST.get('start_date_time', '').strip()
            end_date_time_str = request.POST.get('end_date_time', '').strip()
            
            start_date_time = None
            end_date_time = None
            
            if start_date_time_str:
                try:
                    from django.utils.dateparse import parse_datetime
                    start_date_time = parse_datetime(start_date_time_str)
                except (ValueError, TypeError):
                    messages.error(request, 'Invalid start date/time format.')
                    return render(request, 'clubs/create_post.html', {
                        'club': club,
                        'CLUB_POST_TYPE_CHOICES': CLUB_POST_TYPE_CHOICES,
                        'form_data': request.POST,
                    })
            
            if end_date_time_str:
                try:
                    from django.utils.dateparse import parse_datetime
                    end_date_time = parse_datetime(end_date_time_str)
                except (ValueError, TypeError):
                    messages.error(request, 'Invalid end date/time format.')
                    return render(request, 'clubs/create_post.html', {
                        'club': club,
                        'CLUB_POST_TYPE_CHOICES': CLUB_POST_TYPE_CHOICES,
                        'form_data': request.POST,
                    })
            
            if not short_title or not long_title or not description:
                messages.error(request, 'Short title, long title, and description are required.')
                return render(request, 'clubs/create_post.html', {
                    'club': club,
                    'CLUB_POST_TYPE_CHOICES': CLUB_POST_TYPE_CHOICES,
                    'form_data': request.POST,
                })
            
            # Check pinned posts limit (max 3 per club)
            if is_pinned:
                pinned_count = ClubPost.objects.filter(club=club, is_pinned=True).count()
                if pinned_count >= 3:
                    messages.error(request, 'Maximum 3 pinned posts allowed per club. Please unpin another post first.')
                    return render(request, 'clubs/create_post.html', {
                        'club': club,
                        'CLUB_POST_TYPE_CHOICES': CLUB_POST_TYPE_CHOICES,
                        'form_data': request.POST,
                    })
            
            post = ClubPost.objects.create(
                club=club,
                post_type=post_type,
                short_title=short_title,
                long_title=long_title,
                tags=tags if tags else None,
                description=description,
                start_date_time=start_date_time,
                end_date_time=end_date_time,
                posted_by=request.user,
                is_pinned=is_pinned
            )
            
            messages.success(request, 'Post created successfully!')
            return redirect('clubs:manage_posts', pk=club.pk)
            
        except Exception as e:
            messages.error(request, f'Error creating post: {str(e)}')
            context = {
                'club': club,
                'form_data': request.POST,
            }
            return render(request, 'clubs/create_post.html', context)
    
    context = {
        'club': club,
        'CLUB_POST_TYPE_CHOICES': CLUB_POST_TYPE_CHOICES,
    }
    return render(request, 'clubs/create_post.html', context)


@login_required
def edit_club_post(request, pk, post_pk):
    """
    Edit an existing club post.
    """
    club = get_object_or_404(Club, pk=pk)
    post = get_object_or_404(ClubPost, pk=post_pk, club=club)
    
    if not check_club_post_access(request.user, club):
        messages.error(request, 'You do not have permission to edit posts for this club.')
        return redirect('people:user_profile')
    
    if request.method == 'POST':
        try:
            post.post_type = request.POST.get('post_type', 'event')
            post.short_title = request.POST.get('short_title', '').strip()
            post.long_title = request.POST.get('long_title', '').strip()
            post.tags = request.POST.get('tags', '').strip() or None
            post.description = request.POST.get('description', '').strip()
            is_pinned = request.POST.get('is_pinned') == 'on'
            
            # Optional date/time fields
            start_date_time_str = request.POST.get('start_date_time', '').strip()
            end_date_time_str = request.POST.get('end_date_time', '').strip()
            
            if start_date_time_str:
                try:
                    from django.utils.dateparse import parse_datetime
                    post.start_date_time = parse_datetime(start_date_time_str)
                except (ValueError, TypeError):
                    messages.error(request, 'Invalid start date/time format.')
                    context = {
                        'club': club,
                        'post': post,
                        'CLUB_POST_TYPE_CHOICES': CLUB_POST_TYPE_CHOICES,
                        'form_data': request.POST,
                    }
                    return render(request, 'clubs/edit_post.html', context)
            else:
                post.start_date_time = None
            
            if end_date_time_str:
                try:
                    from django.utils.dateparse import parse_datetime
                    post.end_date_time = parse_datetime(end_date_time_str)
                except (ValueError, TypeError):
                    messages.error(request, 'Invalid end date/time format.')
                    context = {
                        'club': club,
                        'post': post,
                        'CLUB_POST_TYPE_CHOICES': CLUB_POST_TYPE_CHOICES,
                        'form_data': request.POST,
                    }
                    return render(request, 'clubs/edit_post.html', context)
            else:
                post.end_date_time = None
            
            if not post.short_title or not post.long_title or not post.description:
                messages.error(request, 'Short title, long title, and description are required.')
                context = {
                    'club': club,
                    'post': post,
                    'CLUB_POST_TYPE_CHOICES': CLUB_POST_TYPE_CHOICES,
                    'form_data': request.POST,
                }
                return render(request, 'clubs/edit_post.html', context)
            
            # Check pinned posts limit (max 3 per club)
            if is_pinned and not post.is_pinned:
                pinned_count = ClubPost.objects.filter(club=club, is_pinned=True).count()
                if pinned_count >= 3:
                    messages.error(request, 'Maximum 3 pinned posts allowed per club. Please unpin another post first.')
                    context = {
                        'club': club,
                        'post': post,
                        'CLUB_POST_TYPE_CHOICES': CLUB_POST_TYPE_CHOICES,
                        'form_data': request.POST,
                    }
                    return render(request, 'clubs/edit_post.html', context)
            
            # Set last edited by
            post.last_edited_by = request.user
            post.is_pinned = is_pinned
            post.save()
            
            messages.success(request, 'Post updated successfully!')
            return redirect('clubs:manage_posts', pk=club.pk)
            
        except Exception as e:
            messages.error(request, f'Error updating post: {str(e)}')
    
    context = {
        'club': club,
        'post': post,
        'CLUB_POST_TYPE_CHOICES': CLUB_POST_TYPE_CHOICES,
    }
    return render(request, 'clubs/edit_post.html', context)


@login_required
def delete_club_post(request, pk, post_pk):
    """
    Delete a club post.
    """
    club = get_object_or_404(Club, pk=pk)
    post = get_object_or_404(ClubPost, pk=post_pk, club=club)
    
    if not check_club_post_access(request.user, club):
        messages.error(request, 'You do not have permission to delete posts for this club.')
        return redirect('people:user_profile')
    
    if request.method == 'POST':
        post_title = post.short_title or post.long_title or 'Post'
        post.delete()
        messages.success(request, f'Post "{post_title}" deleted successfully!')
        return redirect('clubs:manage_posts', pk=club.pk)
    
    context = {
        'club': club,
        'post': post,
    }
    return render(request, 'clubs/delete_post.html', context)


# ==============================================================================
# ALLOWED EMAIL MANAGEMENT FOR CLUB MEMBERS
# ==============================================================================

@login_required
def manage_club_allowed_emails(request, pk):
    """
    Manage allowed emails for club members.
    Conveners and presidents can manage allowed emails for their clubs.
    """
    club = get_object_or_404(Club, pk=pk)
    
    if not check_club_management_access(request.user, club):
        messages.error(request, 'You do not have permission to manage allowed emails for this club.')
        return redirect('people:user_profile')
    
    # Get allowed emails for this specific club
    from people.models import AllowedEmail
    allowed_emails = AllowedEmail.objects.filter(
        user_type='club_member',
        is_power_user=False,
        club=club  # Filter by club instead of created_by
    ).order_by('-created_at')
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        allowed_emails = allowed_emails.filter(email__icontains=search_query)
    
    context = {
        'club': club,
        'allowed_emails': allowed_emails,
        'search_query': search_query,
        'user': request.user,  # Pass user to template for permission checks
    }
    
    return render(request, 'clubs/manage_allowed_emails.html', context)


@login_required
def create_club_allowed_email(request, pk):
    """
    Create allowed email for club members.
    Conveners and presidents can create these, and they are restricted to club_member type and level 1.
    """
    club = get_object_or_404(Club, pk=pk)
    
    if not check_club_management_access(request.user, club):
        messages.error(request, 'You do not have permission to create allowed emails for this club.')
        return redirect('people:user_profile')
    
    if request.method == 'POST':
        try:
            email = request.POST.get('email', '').strip().lower()
            
            if not email:
                messages.error(request, 'Email is required.')
                return render(request, 'clubs/create_allowed_email.html', {
                    'club': club,
                    'form_data': request.POST,
                })
            
            from people.models import AllowedEmail
            
            # Check if email already exists
            existing_email = AllowedEmail.objects.filter(email=email, user_type='club_member').first()
            
            if existing_email:
                # Email already exists - check if it's for this club or another club
                if existing_email.club == club:
                    # Email already exists for this club - just send invitation
                    allowed_email = existing_email
                    email_already_exists = True
                else:
                    # Email exists for a different club - update it to this club and send invitation
                    # Note: Since email is unique, we update the club association
                    existing_email.club = club
                    existing_email.created_by = request.user  # Update creator
                    existing_email.save()
                    allowed_email = existing_email
                    email_already_exists = True
            else:
                # Email doesn't exist - create new allowed email
                allowed_email = AllowedEmail.objects.create(
                    email=email,
                    user_type='club_member',
                    is_power_user=False,
                    is_active=True,
                    is_blocked=False,
                    created_by=request.user,  # Track who created this email
                    club=club,  # Link to this specific club
                )
                email_already_exists = False
            
            # Send invitation email using Brevo API (like password reset)
            email_sent = False
            email_error = None
            
            # Get inviter name (convener or president)
            inviter_name = 'Club Administrator'
            if request.user.user_type == 'faculty' and hasattr(request.user, 'faculty_profile'):
                inviter_name = request.user.faculty_profile.name or inviter_name
            elif request.user.user_type == 'officer' and hasattr(request.user, 'officer_profile'):
                inviter_name = request.user.officer_profile.name or inviter_name
            elif request.user.user_type == 'club_member' and hasattr(request.user, 'club_member_profile'):
                inviter_name = request.user.club_member_profile.name or inviter_name
            
            # Build signup URL using helper function from uap_cse_dj.views
            from uap_cse_dj.views import get_frontend_domain
            DOMAIN = get_frontend_domain(request)
            signup_url = f"{DOMAIN}{reverse('signup')}"
            
            # Email content
            subject = f'Invitation to Join {club.name} - CSE UAP'
            html_content = f'''
                <p>Hello,</p>
                <p>You have been invited by {inviter_name} to join <strong>{club.name}</strong> as a club member at the Department of Computer Science and Engineering (CSE), University of Asia Pacific (UAP).</p>
                <p>To complete your registration, please follow these steps:</p>
                <ol>
                    <li>Visit the signup page: <a href="{signup_url}">{signup_url}</a></li>
                    <li>Enter your email address: <strong>{email}</strong></li>
                    <li>Fill in your full name and create a password (minimum 8 characters)</li>
                    <li>Click "Sign Up" to create your account</li>
                </ol>
                <p>Once you sign up, you will be able to:</p>
                <ul>
                    <li>Access club information and announcements</li>
                    <li>Participate in club activities</li>
                    <li>Connect with other club members</li>
                </ul>
                <p>If you have any questions or need assistance, please contact the club administrator or the CSE department.</p>
                <p>Best regards,<br>CSE UAP Team</p>
            '''
            text_content = f'''Hello,

You have been invited by {inviter_name} to join {club.name} as a club member at the Department of Computer Science and Engineering (CSE), University of Asia Pacific (UAP).

To complete your registration, please follow these steps:

1. Visit the signup page: {signup_url}
2. Enter your email address: {email}
3. Fill in your full name and create a password (minimum 8 characters)
4. Click "Sign Up" to create your account

Once you sign up, you will be able to:
- Access club information and announcements
- Participate in club activities
- Connect with other club members

If you have any questions or need assistance, please contact the club administrator or the CSE department.

Best regards,
CSE UAP Team'''
            
            BREVO_API_KEY = os.getenv('BREVO_API_KEY', '')
            EMAIL_FROM = os.getenv('EMAIL_FROM', 'noreply@uap-cse.edu')
            
            # Send email via Brevo API
            if BREVO_API_KEY:
                try:
                    import requests
                    import logging
                    logger = logging.getLogger(__name__)
                    
                    brevo_url = 'https://api.brevo.com/v3/smtp/email'
                    headers = {
                        'accept': 'application/json',
                        'api-key': BREVO_API_KEY,
                        'content-type': 'application/json'
                    }
                    payload = {
                        'sender': {'name': 'CSE UAP', 'email': EMAIL_FROM},
                        'to': [{'email': email}],
                        'subject': subject,
                        'htmlContent': html_content,
                        'textContent': text_content
                    }
                    logger.info(f"Attempting to send club invitation email to {email} via Brevo API")
                    response = requests.post(brevo_url, json=payload, headers=headers, timeout=10)
                    response.raise_for_status()
                    email_sent = True
                    logger.info(f"✅ Club invitation email sent successfully to {email} via Brevo API")
                except requests.exceptions.RequestException as e:
                    email_error = f"Brevo API error: {str(e)}"
                    if hasattr(e, 'response') and e.response is not None:
                        try:
                            error_detail = e.response.json()
                            email_error = f"Brevo API error: {error_detail}"
                            logger.error(f"Brevo API response: {error_detail}")
                        except:
                            email_error = f"Brevo API error: {e.response.status_code} - {e.response.text}"
                    logger.exception(f"❌ Failed to send via Brevo API: {email_error}")
                    # Fallback to SMTP
                    try:
                        EMAIL_HOST = os.getenv('EMAIL_HOST')
                        EMAIL_PORT = os.getenv('EMAIL_PORT', '587')
                        EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER')
                        EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD')
                        
                        if EMAIL_HOST and EMAIL_HOST_USER and EMAIL_HOST_PASSWORD:
                            logger.info(f"Attempting SMTP fallback for {email}")
                            from django.core.mail import get_connection
                            connection = get_connection(
                                host=EMAIL_HOST,
                                port=int(EMAIL_PORT),
                                username=EMAIL_HOST_USER,
                                password=EMAIL_HOST_PASSWORD,
                                use_tls=True,
                                fail_silently=False
                            )
                            send_mail(
                                subject=subject,
                                message=text_content,
                                from_email=EMAIL_FROM,
                                recipient_list=[email],
                                connection=connection
                            )
                            email_sent = True
                            logger.info(f"✅ Club invitation email sent successfully to {email} via SMTP fallback")
                        else:
                            logger.warning("SMTP credentials not configured, cannot use SMTP fallback")
                            email_error = "SMTP credentials not configured"
                    except Exception as smtp_err:
                        email_error = f"SMTP fallback failed: {str(smtp_err)}"
                        logger.exception(f"❌ SMTP fallback also failed: {email_error}")
                except Exception as e:
                    email_error = f"Unexpected error: {str(e)}"
                    logger.exception(f"❌ Unexpected error sending email: {email_error}")
            else:
                # Try SMTP if BREVO_API_KEY is not set
                try:
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.warning("⚠️ BREVO_API_KEY not set, attempting SMTP fallback")
                    
                    EMAIL_HOST = os.getenv('EMAIL_HOST')
                    EMAIL_PORT = os.getenv('EMAIL_PORT', '587')
                    EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER')
                    EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD')
                    
                    if EMAIL_HOST and EMAIL_HOST_USER and EMAIL_HOST_PASSWORD:
                        from django.core.mail import get_connection
                        connection = get_connection(
                            host=EMAIL_HOST,
                            port=int(EMAIL_PORT),
                            username=EMAIL_HOST_USER,
                            password=EMAIL_HOST_PASSWORD,
                            use_tls=True,
                            fail_silently=False
                        )
                        send_mail(
                            subject=subject,
                            message=text_content,
                            from_email=EMAIL_FROM,
                            recipient_list=[email],
                            connection=connection
                        )
                        email_sent = True
                        logger.info(f"✅ Club invitation email sent successfully to {email} via SMTP")
                    else:
                        email_error = "Email credentials not configured (BREVO_API_KEY and SMTP credentials missing)"
                        logger.warning(f"⚠️ {email_error}")
                except Exception as e:
                    email_error = f"SMTP error: {str(e)}"
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.exception(f"❌ Failed to send email: {email_error}")
            
            # Show appropriate message based on email sending result
            if email_already_exists:
                if email_sent:
                    messages.success(request, f'Invitation email sent to "{email}"! The email is already in the allowed list for this club.')
                else:
                    messages.warning(request, f'Email "{email}" is already in the allowed list, but failed to send invitation email. Error: {email_error}.')
            else:
                if email_sent:
                    messages.success(request, f'Allowed email "{email}" created successfully and invitation email sent! The user can now sign up as a club member.')
                else:
                    messages.warning(request, f'Allowed email "{email}" created successfully, but failed to send invitation email. Error: {email_error}. The user can still sign up using their email address.')
            
            return redirect('clubs:manage_allowed_emails', pk=club.pk)
            
        except Exception as e:
            messages.error(request, f'Error creating allowed email: {str(e)}')
            return render(request, 'clubs/create_allowed_email.html', {
                'club': club,
                'form_data': request.POST,
            })
    
    context = {
        'club': club,
    }
    return render(request, 'clubs/create_allowed_email.html', context)


@login_required
def delete_club_allowed_email(request, pk, email_pk):
    """
    Delete an allowed email. Only club managers (convener or president) can delete emails for their club.
    Note: This only removes the email from this club's allowed list. If the member is in other clubs,
    their AllowedEmail will remain (though since email is unique, this is a limitation).
    """
    club = get_object_or_404(Club, pk=pk)
    
    if not check_club_management_access(request.user, club):
        messages.error(request, 'You do not have permission to delete allowed emails for this club.')
        return redirect('people:user_profile')
    
    from people.models import AllowedEmail
    allowed_email = get_object_or_404(AllowedEmail, pk=email_pk, user_type='club_member', is_power_user=False, club=club)
    
    # Check if this email belongs to this club
    if allowed_email.club != club:
        messages.error(request, 'This email does not belong to this club.')
        return redirect('clubs:manage_allowed_emails', pk=club.pk)
    
    if request.method == 'POST':
        email_address = allowed_email.email
        
        # Check if member is in positions in this club - warn but allow deletion
        from clubs.models import ClubPosition
        positions_in_club = ClubPosition.objects.filter(club=club, club_member__base_user__email=email_address).exists()
        if positions_in_club:
            messages.warning(request, f'Warning: Member with email "{email_address}" is currently in a position in this club. Removing the allowed email will not remove them from positions, but they may lose access.')
        
        # Delete the allowed email (this only removes it from this club's list)
        # Since email is unique, this will delete the AllowedEmail entirely
        # TODO: In the future, consider making email non-unique or using a many-to-many relationship
        allowed_email.delete()
        messages.success(request, f'Allowed email "{email_address}" removed from this club successfully!')
        return redirect('clubs:manage_allowed_emails', pk=club.pk)
    
    context = {
        'club': club,
        'allowed_email': allowed_email,
    }
    return render(request, 'clubs/delete_allowed_email.html', context)


def activities(request):
    """
    Display all club posts from all clubs with search, filter, and sort functionality.
    """
    # Get all club posts from all clubs
    posts = ClubPost.objects.all().select_related('club', 'posted_by', 'last_edited_by')
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        posts = posts.filter(
            Q(short_title__icontains=search_query) |
            Q(long_title__icontains=search_query) |
            Q(tags__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(club__name__icontains=search_query)
        )
    
    # Filter by post type
    post_type_filter = request.GET.get('type', '')
    if post_type_filter:
        posts = posts.filter(post_type=post_type_filter)
    
    # Filter by club
    club_filter = request.GET.get('club', '')
    if club_filter:
        try:
            posts = posts.filter(club_id=int(club_filter))
        except (ValueError, TypeError):
            pass
    
    # Sort functionality
    sort_by = request.GET.get('sort', 'newest')
    if sort_by == 'oldest':
        posts = posts.order_by('created_at')
    elif sort_by == 'newest':
        posts = posts.order_by('-created_at')
    elif sort_by == 'club':
        posts = posts.order_by('club__name', '-created_at')
    elif sort_by == 'type':
        posts = posts.order_by('post_type', '-created_at')
    elif sort_by == 'pinned':
        # Pinned first, then by date
        posts = posts.order_by('-is_pinned', '-created_at')
    else:
        # Default: newest first
        posts = posts.order_by('-created_at')
    
    # Get all clubs for filter dropdown
    all_clubs = Club.objects.all().order_by('sl', 'name')
    
    # Count posts by type for stats
    total_posts_count = posts.count()
    posts_by_type = {}
    for code, display in CLUB_POST_TYPE_CHOICES:
        posts_by_type[code] = ClubPost.objects.filter(post_type=code).count()
    
    # Pagination - 12 posts per page
    paginator = Paginator(posts, 12)
    page = request.GET.get('page', 1)
    
    try:
        posts_page = paginator.page(page)
    except PageNotAnInteger:
        posts_page = paginator.page(1)
    except EmptyPage:
        posts_page = paginator.page(paginator.num_pages)
    
    context = {
        'posts': posts_page,
        'selected_type': post_type_filter,
        'selected_club': club_filter,
        'search_query': search_query,
        'sort_by': sort_by,
        'CLUB_POST_TYPE_CHOICES': CLUB_POST_TYPE_CHOICES,
        'posts_by_type': posts_by_type,
        'total_posts': total_posts_count,
        'all_clubs': all_clubs,
        'paginator': paginator,
        'is_paginated': posts_page.has_other_pages(),
    }
    return render(request, 'clubs/activities.html', context)
