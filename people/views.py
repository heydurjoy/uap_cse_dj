from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate
from django.contrib import messages
from django.db import transaction, models
from django.utils import timezone
from django.db.models import Q, Max
from django.http import JsonResponse, FileResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.core.exceptions import ObjectDoesNotExist
from django.core.files.uploadedfile import UploadedFile
from types import SimpleNamespace
from .models import Faculty, Staff, Officer, ClubMember, BaseUser, Permission, UserPermission, AllowedEmail, Publication
from clubs.models import Club, ClubPosition
from .permissions import PERMISSION_DEFINITIONS
import re
import os


def faculty_list(request):
    """
    Display list of all faculties, grouped by:
    - Full Time Faculty (active, not on study leave)
    - Faculty on Study Leave
    - Former Faculty
    """
    from datetime import date
    
    # Get all faculties with base_user for email access
    all_faculties = Faculty.objects.all().select_related('base_user')
    
    # Define designation order for sorting within groups
    designation_order = {
        'Professor': 1,
        'Associate Professor': 2,
        'Assistant Professor': 3,
        'Lecturer': 4,
        'Teaching Assistant': 5,
    }
    
    # Separate former faculty (with last_office_date) from active faculty
    former_faculties = [f for f in all_faculties if f.last_office_date]
    active_faculties = [f for f in all_faculties if not f.last_office_date]
    
    # Separate active faculties on study leave from others
    faculties_on_leave = [f for f in active_faculties if f.is_on_study_leave]
    faculties_active = [f for f in active_faculties if not f.is_on_study_leave]
    
    # Separate head faculty from regular active faculty
    head_faculty = [f for f in faculties_active if f.is_head]
    regular_active = [f for f in faculties_active if not f.is_head]
    
    # Separate inter-departmental and visiting faculty from regular active
    inter_departmental_faculties = [f for f in regular_active if f.is_inter_departmental]
    visiting_faculties = [f for f in regular_active if f.is_visiting]
    full_time_faculties = [f for f in regular_active if not f.is_inter_departmental and not f.is_visiting]
    
    # Sort full time faculties: by designation, then by sl
    sorted_full_time = sorted(
        full_time_faculties,
        key=lambda f: (
            designation_order.get(f.designation, 999) if f.designation else 999,
            f.sl if f.sl else 999
        )
    )
    
    # Sort inter-departmental faculties: by designation, then by sl
    sorted_inter_departmental = sorted(
        inter_departmental_faculties,
        key=lambda f: (
            designation_order.get(f.designation, 999) if f.designation else 999,
            f.sl if f.sl else 999
        )
    )
    
    # Sort visiting faculties: by designation, then by sl
    sorted_visiting = sorted(
        visiting_faculties,
        key=lambda f: (
            designation_order.get(f.designation, 999) if f.designation else 999,
            f.sl if f.sl else 999
        )
    )
    
    # Sort faculties on leave: by designation, then by sl
    sorted_on_leave = sorted(
        faculties_on_leave,
        key=lambda f: (
            designation_order.get(f.designation, 999) if f.designation else 999,
            f.sl if f.sl else 999
        )
    )
    
    # Sort former faculties: by last_office_date (most recent first), then by designation, then by sl
    sorted_former = sorted(
        former_faculties,
        key=lambda f: (
            f.last_office_date if f.last_office_date else date.min,  # Most recent first
            designation_order.get(f.designation, 999) if f.designation else 999,
            f.sl if f.sl else 999
        ),
        reverse=True  # Most recent last_office_date first
    )
    
    # Group faculties into categories (no designation separation)
    faculties_by_designation = {}
    
    # Full Time Faculty group
    if sorted_full_time:
        faculties_by_designation['Full Time Faculty'] = sorted_full_time
    
    # Inter-departmental Faculty group
    if sorted_inter_departmental:
        faculties_by_designation['Inter-departmental Faculty'] = sorted_inter_departmental
    
    # Visiting Faculty group
    if sorted_visiting:
        faculties_by_designation['Visiting Faculty'] = sorted_visiting
    
    # Faculty on Study Leave group
    if sorted_on_leave:
        faculties_by_designation['Faculty on Study Leave'] = sorted_on_leave
    
    # Former Faculty group (will be shown separately in template)
    former_faculties_by_designation = {}
    if sorted_former:
        former_faculties_by_designation['Former Faculty'] = sorted_former
    
    # For table view, only show active faculties (exclude those on leave and former)
    all_faculties_for_table = sorted_full_time + sorted_inter_departmental + sorted_visiting
    
    # Get head faculty (should be only one, but handle multiple)
    head_faculty_obj = head_faculty[0] if head_faculty else None
    
    context = {
        'faculties': all_faculties_for_table,
        'faculties_by_designation': faculties_by_designation,
        'former_faculties': sorted_former,
        'former_faculties_by_designation': former_faculties_by_designation,
        'head_faculty': head_faculty_obj,
    }
    
    return render(request, 'people/faculty_list.html', context)


def faculty_detail(request, pk):
    """
    Display detailed view of a single faculty member.
    """
    from datetime import date, datetime
    from django.utils import timezone
    
    faculty = get_object_or_404(Faculty, pk=pk)
    
    # Calculate detailed years of service
    service_data = None
    is_former = faculty.last_office_date is not None
    
    if faculty.joining_date:
        # For former faculty, use last_office_date as end date; otherwise use today
        if is_former:
            end_date = faculty.last_office_date
            end_datetime = timezone.make_aware(datetime.combine(end_date, datetime.max.time()))
        else:
            end_date = timezone.now().date()
            end_datetime = timezone.now()
        
        joining_datetime = timezone.make_aware(datetime.combine(faculty.joining_date, datetime.min.time()))
        
        # Calculate total time difference
        delta = end_datetime - joining_datetime
        
        total_days = delta.days
        total_seconds = delta.total_seconds()
        hours = int((total_seconds % 86400) // 3600)
        minutes = int((total_seconds % 3600) // 60)
        
        # Calculate years and months
        end_date_obj = end_date
        joining = faculty.joining_date
        
        years = end_date_obj.year - joining.year
        months = end_date_obj.month - joining.month
        days_in_month = end_date_obj.day - joining.day
        
        # Adjust for negative months/days
        if days_in_month < 0:
            months -= 1
            # Get days in previous month
            if end_date_obj.month == 1:
                from calendar import monthrange
                days_in_prev_month = monthrange(end_date_obj.year - 1, 12)[1]
            else:
                from calendar import monthrange
                days_in_prev_month = monthrange(end_date_obj.year, end_date_obj.month - 1)[1]
            days_in_month += days_in_prev_month
        
        if months < 0:
            years -= 1
            months += 12
        
        service_data = {
            'total_days': total_days,
            'hours': hours,
            'minutes': minutes,
            'years': years,
            'months': months,
            'is_former': is_former,
            'last_office_date': faculty.last_office_date,
        }
    
    # Get publications for this faculty
    publications = faculty.publications.all().order_by('-pub_year', 'title')
    
    # Calculate publication stats
    from datetime import datetime
    current_year = datetime.now().year
    
    pub_stats = {
        'total': publications.count(),
        'q1': publications.filter(ranking='q1').count(),
        'current_year': publications.filter(pub_year=current_year).count(),
    }
    
    # Check if user can manage publications (own or with permission)
    from people.permissions import Permissions
    can_manage_publications = False
    if hasattr(request.user, 'faculty_profile') and request.user.faculty_profile.pk == faculty.pk:
        can_manage_publications = True
    elif request.user.is_authenticated and request.user.has_permission(Permissions.MANAGE_ALL_PUBLICATIONS):
        can_manage_publications = True
    
    context = {
        'faculty': faculty,
        'service_data': service_data,
        'publications': publications,
        'pub_stats': pub_stats,
        'can_manage_publications': can_manage_publications,
    }
    
    return render(request, 'people/faculty_detail.html', context)


def serve_faculty_cv(request, pk):
    """
    Serve faculty CV PDF with proper headers for iframe embedding.
    Public access - no authentication required.
    """
    faculty = get_object_or_404(Faculty, pk=pk)
    
    if not faculty.cv:
        return HttpResponse("CV not found", status=404)
    
    try:
        # Check if file exists on disk
        if hasattr(faculty.cv, 'path'):
            file_path = faculty.cv.path
            if not os.path.exists(file_path):
                return HttpResponse("CV file not found on server", status=404)
        
        # Open the file using Django's file field (handles storage backends properly)
        cv_file = faculty.cv.open('rb')
        
        # Serve the file with proper headers for iframe embedding
        response = FileResponse(
            cv_file,
            content_type='application/pdf'
        )
        # Use inline disposition for iframe embedding
        filename = os.path.basename(faculty.cv.name) if faculty.cv.name else 'cv.pdf'
        response['Content-Disposition'] = f'inline; filename="{filename}"'
        response['X-Content-Type-Options'] = 'nosniff'
        
        # Allow iframe embedding from same origin
        response['X-Frame-Options'] = 'SAMEORIGIN'
        
        return response
    except FileNotFoundError:
        return HttpResponse("CV file not found on server", status=404)
    except Exception as e:
        return HttpResponse(f"Error serving CV: {str(e)}", status=500)


def club_member_list(request):
    """
    Display list of all club members grouped by club, sorted by serial number.
    Faculty positions shown first, then student positions.
    """
    # Get search query
    search_query = request.GET.get('search', '').strip()
    
    # Get sort parameter
    sort_by = request.GET.get('sort', 'club_serial')  # Default: sort by club serial
    
    # Get all clubs ordered by serial number
    clubs = Club.objects.all().order_by('sl', 'name')
    
    # Structure to hold clubs with their members
    clubs_data = []
    
    for club in clubs:
        # Get all positions for this club, ordered by serial number
        positions = ClubPosition.objects.filter(club=club).select_related('faculty', 'club_member').order_by('sl')
        
        # Separate faculty and club members
        faculty_positions = []
        member_positions = []
        
        # Add convener from club object (if exists)
        if club.convener:
            # Check if search matches
            include_convener = True
            if search_query:
                search_lower = search_query.lower()
                person_name = club.convener.name.lower()
                club_name = club.name.lower()
                
                include_convener = (search_lower in person_name or 
                                   search_lower in club_name or 
                                   search_lower in 'convener' or 
                                   search_lower in 'advisor')
            
            if include_convener:
                # Create a simple object-like dict for convener
                convener_obj = SimpleNamespace(
                    faculty=club.convener,
                    club_member=None,
                    position_title='Convener',
                    is_convener=True,
                )
                faculty_positions.insert(0, convener_obj)  # Insert at beginning
        
        # Add president from club object (if exists)
        if club.president:
            # Check if search matches
            include_president = True
            if search_query:
                search_lower = search_query.lower()
                person_name = club.president.name.lower()
                club_name = club.name.lower()
                
                include_president = (search_lower in person_name or 
                                   search_lower in club_name or 
                                   search_lower in 'president')
            
            if include_president:
                # Create a simple object-like dict for president
                president_obj = SimpleNamespace(
                    faculty=None,
                    club_member=club.president,
                    position_title='President',
                    is_president=True,
                )
                member_positions.insert(0, president_obj)  # Insert at beginning
        
        for position in positions:
            # Apply search filter if provided
            if search_query:
                search_lower = search_query.lower()
                person_name = position.get_person_name().lower()
                position_title = position.position_title.lower()
                club_name = club.name.lower()
                
                if (search_lower not in person_name and 
                    search_lower not in position_title and 
                    search_lower not in club_name):
                    continue
            
            if position.faculty:
                faculty_positions.append(position)
            elif position.club_member:
                member_positions.append(position)
        
        # Combine all positions with faculty first, then students
        all_positions = faculty_positions + member_positions
        
        # Only add club if it has positions (after filtering)
        if all_positions:
            clubs_data.append({
                'club': club,
                'all_positions': all_positions,
            })
    
    # Apply sorting
    if sort_by == 'name':
        # Sort clubs by name
        clubs_data.sort(key=lambda x: x['club'].name)
    elif sort_by == 'club_serial':
        # Sort by club serial (already sorted, but ensure it)
        clubs_data.sort(key=lambda x: (x['club'].sl or 9999, x['club'].name))
    
    # Get all unique clubs for filter dropdown
    all_clubs = Club.objects.all().order_by('sl', 'name')
    
    # Get selected club filter
    club_filter = request.GET.get('club', '')
    if club_filter:
        try:
            selected_club = Club.objects.get(pk=club_filter)
            # Filter clubs_data to only show selected club
            clubs_data = [cd for cd in clubs_data if cd['club'].pk == selected_club.pk]
        except Club.DoesNotExist:
            pass
    
    context = {
        'clubs_data': clubs_data,
        'all_clubs': all_clubs,
        'search_query': search_query,
        'sort_by': sort_by,
        'club_filter': club_filter,
    }
    
    return render(request, 'people/club_member_list.html', context)


def club_member_detail(request, pk):
    """
    Display detailed view of a single club member.
    """
    club_member = get_object_or_404(ClubMember, pk=pk)
    
    # Get club positions for this member
    positions = ClubPosition.objects.filter(club_member=club_member).select_related('club').order_by('-academic_year', 'semester', 'sl')
    
    # Get clubs where this member is president
    clubs_as_president = Club.objects.filter(president=club_member).select_related('convener')
    
    context = {
        'club_member': club_member,
        'positions': positions,
        'clubs_as_president': clubs_as_president,
    }
    
    return render(request, 'people/club_member_detail.html', context)


def officer_list(request):
    """
    Display list of all officers, sorted by serial number.
    """
    officers = Officer.objects.all().order_by('sl')
    
    context = {
        'officers': officers,
    }
    
    return render(request, 'people/officer_list.html', context)


def officer_detail(request, pk):
    """
    Display detailed view of a single officer.
    """
    from datetime import date, datetime
    from django.utils import timezone
    
    officer = get_object_or_404(Officer, pk=pk)
    
    # Calculate detailed years of service
    service_data = None
    if officer.joining_date:
        today = timezone.now()
        joining_datetime = timezone.make_aware(datetime.combine(officer.joining_date, datetime.min.time()))
        
        # Calculate total time difference
        delta = today - joining_datetime
        
        total_days = delta.days
        total_seconds = delta.total_seconds()
        hours = int((total_seconds % 86400) // 3600)
        minutes = int((total_seconds % 3600) // 60)
        
        # Calculate years and months
        today_date = today.date()
        joining = officer.joining_date
        
        years = today_date.year - joining.year
        months = today_date.month - joining.month
        days_in_month = today_date.day - joining.day
        
        # Adjust for negative months/days
        if days_in_month < 0:
            months -= 1
            # Get days in previous month
            if today_date.month == 1:
                from calendar import monthrange
                days_in_prev_month = monthrange(today_date.year - 1, 12)[1]
            else:
                from calendar import monthrange
                days_in_prev_month = monthrange(today_date.year, today_date.month - 1)[1]
            days_in_month += days_in_prev_month
        
        if months < 0:
            years -= 1
            months += 12
        
        service_data = {
            'total_days': total_days,
            'hours': hours,
            'minutes': minutes,
            'years': years,
            'months': months,
        }
    
    context = {
        'officer': officer,
        'service_data': service_data,
    }
    
    return render(request, 'people/officer_detail.html', context)


def staff_list(request):
    """
    Display list of all staff members, sorted by serial number.
    """
    staff_members = Staff.objects.all().order_by('sl').select_related('base_user')
    
    context = {
        'staff_members': staff_members,
    }
    
    return render(request, 'people/staff_list.html', context)


def staff_detail(request, pk):
    """
    Display detailed view of a single staff member.
    """
    from datetime import date, datetime
    from django.utils import timezone
    
    staff = get_object_or_404(Staff, pk=pk)
    
    # Calculate detailed years of service
    service_data = None
    if staff.joining_date:
        today = timezone.now()
        joining_datetime = timezone.make_aware(datetime.combine(staff.joining_date, datetime.min.time()))
        
        # Calculate total time difference
        delta = today - joining_datetime
        
        total_days = delta.days
        total_seconds = delta.total_seconds()
        hours = int((total_seconds % 86400) // 3600)
        minutes = int((total_seconds % 3600) // 60)
        
        # Calculate years and months
        today_date = today.date()
        joining = staff.joining_date
        
        years = today_date.year - joining.year
        months = today_date.month - joining.month
        days_in_month = today_date.day - joining.day
        
        # Adjust for negative months/days
        if days_in_month < 0:
            months -= 1
            # Get days in previous month
            if today_date.month == 1:
                from calendar import monthrange
                days_in_prev_month = monthrange(today_date.year - 1, 12)[1]
            else:
                from calendar import monthrange
                days_in_prev_month = monthrange(today_date.year, today_date.month - 1)[1]
            days_in_month += days_in_prev_month
        
        if months < 0:
            years -= 1
            months += 12
        
        service_data = {
            'total_days': total_days,
            'hours': hours,
            'minutes': minutes,
            'years': years,
            'months': months,
        }
    
    context = {
        'staff': staff,
        'service_data': service_data,
    }
    
    return render(request, 'people/staff_detail.html', context)


@login_required
def user_profile(request):
    """
    Display the current user's profile based on their user_type.
    """
    user = request.user
    
    # Get the user's profile based on user_type
    profile = None
    profile_type = None
    
    if hasattr(user, 'faculty_profile'):
        profile = user.faculty_profile
        profile_type = 'faculty'
    elif hasattr(user, 'staff_profile'):
        profile = user.staff_profile
        profile_type = 'staff'
    elif hasattr(user, 'officer_profile'):
        profile = user.officer_profile
        profile_type = 'officer'
    elif hasattr(user, 'club_member_profile'):
        profile = user.club_member_profile
        profile_type = 'club_member'
    
    # Get clubs associated with the user
    associated_clubs = []
    if profile_type == 'faculty' and profile:
        # Clubs where user is convener
        from clubs.models import Club
        convened_clubs = Club.objects.filter(convener=profile).select_related('convener', 'president')
        for club in convened_clubs:
            associated_clubs.append({
                'club': club,
                'role': 'convener',
                'can_manage_info': True,
                'can_manage_members': True,
                'can_manage_posts': True,
            })
        
        # Clubs where user is in a position
        from clubs.models import ClubPosition
        positions = ClubPosition.objects.filter(faculty=profile).select_related('club')
        for position in positions:
            # Check if already added as convener
            if not any(c['club'].pk == position.club.pk for c in associated_clubs):
                associated_clubs.append({
                    'club': position.club,
                    'role': position.position_title,
                    'can_manage_info': False,
                    'can_manage_members': False,
                    'can_manage_posts': False,
                })
    
    elif profile_type == 'club_member' and profile:
        # Clubs where user is president
        from clubs.models import Club
        led_clubs = Club.objects.filter(president=profile).select_related('convener', 'president')
        for club in led_clubs:
            associated_clubs.append({
                'club': club,
                'role': 'president',
                'can_manage_info': False,
                'can_manage_members': False,
                'can_manage_posts': True,
            })
        
        # Clubs where user is in a position
        from clubs.models import ClubPosition
        positions = ClubPosition.objects.filter(club_member=profile).select_related('club')
        for position in positions:
            # Check if already added as president
            if not any(c['club'].pk == position.club.pk for c in associated_clubs):
                associated_clubs.append({
                    'club': position.club,
                    'role': position.position_title,
                    'can_manage_info': False,
                    'can_manage_members': False,
                    'can_manage_posts': True,
                })
    
    context = {
        'user': user,
        'profile': profile,
        'profile_type': profile_type,
        'associated_clubs': associated_clubs,
    }
    
    return render(request, 'people/user_profile.html', context)


@login_required
@require_http_methods(["GET"])
def get_power_users(request):
    """
    API endpoint to get list of power users for the "Need More Permissions" modal.
    Returns JSON with power users' information.
    """
    power_users = BaseUser.objects.filter(
        is_power_user=True,
        is_active=True
    ).select_related('faculty_profile', 'staff_profile', 'officer_profile', 'club_member_profile').order_by('first_name', 'last_name', 'email')
    
    power_users_list = []
    for user in power_users:
        # Get user's name based on profile type
        name = None
        try:
            if user.faculty_profile:
                name = user.faculty_profile.name
            elif user.staff_profile:
                name = user.staff_profile.name
            elif user.officer_profile:
                name = user.officer_profile.name
            elif user.club_member_profile:
                name = user.club_member_profile.name
        except:
            pass
        
        # Fallback to full name or email
        if not name:
            name = user.get_full_name() or user.email or user.username
        
        power_users_list.append({
            'id': user.id,
            'name': name,
            'email': user.email or user.username,
            'user_type': user.user_type or 'N/A',
        })
    
    return JsonResponse({
        'success': True,
        'power_users': power_users_list
    })


@login_required
def edit_profile(request):
    """
    Allow users to edit their own profile information.
    Excludes: user_type, sl (serial number), permissions (managed separately)
    """
    user = request.user
    
    # Optimize: Get the user with related profile in a single query
    # Refresh user from database with select_related to avoid N+1 queries
    user = BaseUser.objects.select_related(
        'faculty_profile',
        'staff_profile', 
        'officer_profile',
        'club_member_profile'
    ).get(pk=user.pk)
    
    # Get the user's profile based on user_type
    profile = None
    profile_type = None
    
    if hasattr(user, 'faculty_profile') and user.faculty_profile:
        profile = user.faculty_profile
        profile_type = 'faculty'
    elif hasattr(user, 'staff_profile') and user.staff_profile:
        profile = user.staff_profile
        profile_type = 'staff'
    elif hasattr(user, 'officer_profile') and user.officer_profile:
        profile = user.officer_profile
        profile_type = 'officer'
    elif hasattr(user, 'club_member_profile') and user.club_member_profile:
        profile = user.club_member_profile
        profile_type = 'club_member'
    
    if not profile:
        messages.error(request, 'No profile found. Please contact the administrator.')
        return redirect('people:user_profile')
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # Update BaseUser fields
                if 'first_name' in request.POST:
                    user.first_name = request.POST.get('first_name', '').strip()
                if 'last_name' in request.POST:
                    user.last_name = request.POST.get('last_name', '').strip()
                if 'phone_number' in request.POST:
                    user.phone_number = request.POST.get('phone_number', '').strip() or None
                
                # Only update BaseUser.profile_picture if user is NOT a faculty member
                # For faculty members, profile picture should go to Faculty.profile_pic
                if 'profile_picture' in request.FILES and profile_type != 'faculty':
                    user.profile_picture = request.FILES['profile_picture']
                
                user.save()
                
                # Update profile-specific fields
                if profile_type == 'faculty':
                    if 'name' in request.POST:
                        profile.name = request.POST.get('name', '').strip()
                    if 'shortname' in request.POST:
                        profile.shortname = request.POST.get('shortname', '').strip()
                    if 'designation' in request.POST:
                        profile.designation = request.POST.get('designation', '').strip() or None
                    if 'phone' in request.POST:
                        profile.phone = request.POST.get('phone', '').strip() or None
                    if 'bio' in request.POST:
                        profile.bio = request.POST.get('bio', '').strip() or None
                    if 'about' in request.POST:
                        profile.about = request.POST.get('about', '').strip() or None
                    if 'joining_date' in request.POST:
                        date_str = request.POST.get('joining_date', '').strip()
                        if date_str:
                            from datetime import datetime
                            try:
                                profile.joining_date = datetime.strptime(date_str, '%Y-%m-%d').date()
                            except:
                                pass
                        else:
                            profile.joining_date = None
                    if 'citation' in request.POST:
                        citation_str = request.POST.get('citation', '').strip()
                        profile.citation = int(citation_str) if citation_str.isdigit() else None
                    # Helper function to clean URL values
                    def clean_url(value):
                        val = value.strip() if value else ''
                        return None if not val or val.lower() == 'none' else val
                    
                    if 'google_scholar_url' in request.POST:
                        profile.google_scholar_url = clean_url(request.POST.get('google_scholar_url', ''))
                    if 'researchgate_url' in request.POST:
                        profile.researchgate_url = clean_url(request.POST.get('researchgate_url', ''))
                    if 'orcid_url' in request.POST:
                        profile.orcid_url = clean_url(request.POST.get('orcid_url', ''))
                    if 'scopus_url' in request.POST:
                        profile.scopus_url = clean_url(request.POST.get('scopus_url', ''))
                    if 'linkedin_url' in request.POST:
                        profile.linkedin_url = clean_url(request.POST.get('linkedin_url', ''))
                    if 'researches' in request.POST:
                        researches_content = request.POST.get('researches', '').strip()
                        profile.researches = researches_content if researches_content else None
                    if 'routine' in request.POST:
                        routine_content = request.POST.get('routine', '').strip()
                        profile.routine = routine_content if routine_content else None
                    if 'is_phd' in request.POST:
                        profile.is_phd = request.POST.get('is_phd') == 'on'
                    else:
                        profile.is_phd = False
                    if 'is_masters' in request.POST:
                        profile.is_masters = request.POST.get('is_masters') == 'on'
                    else:
                        profile.is_masters = False
                    if 'educational_qualification' in request.POST:
                        educational_qualification_content = request.POST.get('educational_qualification', '').strip()
                        profile.educational_qualification = educational_qualification_content if educational_qualification_content else None
                    if 'course_conducted' in request.POST:
                        course_conducted_content = request.POST.get('course_conducted', '').strip()
                        profile.course_conducted = course_conducted_content if course_conducted_content else None
                    
                    # Handle image uploads (simple replacement, same as staff flow)
                    if 'profile_pic' in request.FILES:
                        profile.profile_pic = request.FILES['profile_pic']
                    elif 'profile_picture' in request.FILES:
                        profile.profile_pic = request.FILES['profile_picture']
                    
                    # Handle CV upload (PDF only, max 2MB)
                    if 'cv' in request.FILES:
                        cv_file = request.FILES['cv']
                        # Validate file type
                        if cv_file.content_type != 'application/pdf':
                            messages.error(request, 'CV must be a PDF file.')
                            return redirect('people:edit_profile')
                        # Validate file size (2MB = 2 * 1024 * 1024 bytes)
                        if cv_file.size > 2 * 1024 * 1024:
                            messages.error(request, 'CV file size must not exceed 2 MB.')
                            return redirect('people:edit_profile')
                        profile.cv = cv_file
                    else:
                        # Only check for missing files if no new upload
                        # Check if it's a new upload (UploadedFile) vs existing file
                        is_new_upload = isinstance(profile.cv, UploadedFile)
                        if not is_new_upload and profile.cv and hasattr(profile.cv, 'path'):
                            try:
                                if profile.cv.path and not os.path.exists(profile.cv.path):
                                    profile.cv = None
                            except Exception:
                                pass
                    
                elif profile_type == 'staff':
                    if 'name' in request.POST:
                        profile.name = request.POST.get('name', '').strip()
                    if 'designation' in request.POST:
                        profile.designation = request.POST.get('designation', '').strip()
                    if 'phone' in request.POST:
                        profile.phone = request.POST.get('phone', '').strip() or None
                    if 'bio' in request.POST:
                        profile.bio = request.POST.get('bio', '').strip() or None
                    if 'joining_date' in request.POST:
                        date_str = request.POST.get('joining_date', '').strip()
                        if date_str:
                            from datetime import datetime
                            try:
                                profile.joining_date = datetime.strptime(date_str, '%Y-%m-%d').date()
                            except:
                                pass
                        else:
                            profile.joining_date = None
                    if 'lab_number' in request.POST:
                        profile.lab_number = request.POST.get('lab_number', '').strip() or None
                    if 'lab_address' in request.POST:
                        profile.lab_address = request.POST.get('lab_address', '').strip() or None
                    if 'profile_pic' in request.FILES:
                        profile.profile_pic = request.FILES['profile_pic']
                    
                elif profile_type == 'officer':
                    if 'name' in request.POST:
                        profile.name = request.POST.get('name', '').strip()
                    if 'position' in request.POST:
                        profile.position = request.POST.get('position', '').strip() or None
                    if 'phone' in request.POST:
                        profile.phone = request.POST.get('phone', '').strip() or None
                    if 'bio' in request.POST:
                        profile.bio = request.POST.get('bio', '').strip() or None
                    if 'about' in request.POST:
                        about_content = request.POST.get('about', '').strip()
                        profile.about = about_content if about_content else None
                    if 'joining_date' in request.POST:
                        date_str = request.POST.get('joining_date', '').strip()
                        if date_str:
                            from datetime import datetime
                            try:
                                profile.joining_date = datetime.strptime(date_str, '%Y-%m-%d').date()
                            except:
                                pass
                        else:
                            profile.joining_date = None
                    if 'profile_pic' in request.FILES:
                        profile.profile_pic = request.FILES['profile_pic']
                    
                elif profile_type == 'club_member':
                    if 'name' in request.POST:
                        profile.name = request.POST.get('name', '').strip()
                    if 'student_id' in request.POST:
                        profile.student_id = request.POST.get('student_id', '').strip() or None
                    if 'last_club_position' in request.POST:
                        profile.last_club_position = request.POST.get('last_club_position', '').strip() or None
                    if 'about' in request.POST:
                        about_content = request.POST.get('about', '').strip()
                        profile.about = about_content if about_content else None
                    if 'profile_pic' in request.FILES:
                        profile.profile_pic = request.FILES['profile_pic']
                
                profile.save()
                messages.success(request, 'Profile updated successfully!')
                return redirect('people:user_profile')
                
        except Exception as e:
            messages.error(request, f'Error updating profile: {str(e)}')
    
    context = {
        'user': user,
        'profile': profile,
        'profile_type': profile_type,
    }
    
    return render(request, 'people/edit_profile.html', context)


def check_can_grant_permissions(user):
    """Helper function to check if user can grant permissions"""
    if not user.is_authenticated:
        return False
    return user.can_grant_permissions()


@login_required
def manage_user_permissions_list(request):
    """
    List/search users for permission management.
    Only accessible to power users. If they don't have manage_user_permissions permission,
    they can still access to grant it to themselves.
    Supports filtering by user type and search.
    """
    if not request.user.is_power_user:
        messages.error(request, 'Only power users can manage permissions.')
        return redirect('people:user_profile')
    
    # Get active tab (permissions or allowed_emails)
    active_tab = request.GET.get('tab', 'permissions')
    
    # Get filters
    search_query = request.GET.get('search', '').strip()
    user_type_filter = request.GET.get('user_type', 'all')
    
    # Get all users, excluding club members (they don't need permissions)
    users = BaseUser.objects.filter(is_active=True).exclude(user_type='club_member').select_related('allowed_email')
    
    # Filter by user type
    if user_type_filter != 'all':
        users = users.filter(user_type=user_type_filter)
    
    # Filter by search query
    if search_query:
        users = users.filter(
            Q(email__icontains=search_query) |
            Q(username__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query)
        )
    
    # Order by user type, then by date joined
    users = users.order_by('user_type', '-date_joined')
    
    # Limit to 100 results for performance
    users = users[:100]
    
    # Get permission counts for each user
    user_permission_counts = {}
    for user in users:
        user_permission_counts[user.id] = UserPermission.objects.filter(
            user=user,
            is_active=True
        ).count()
    
    # Get user type choices for filter dropdown (including club_member for allowed emails tab)
    user_type_choices = [
        ('all', 'All Types'),
        ('faculty', 'Faculty'),
        ('staff', 'Staff'),
        ('officer', 'Officer'),
        ('club_member', 'Club Member'),
    ]
    
    # Get allowed emails (all, including club members)
    allowed_emails = AllowedEmail.objects.all().select_related('created_by')
    
    # Filter allowed emails by search
    if search_query:
        allowed_emails = allowed_emails.filter(email__icontains=search_query)
    
    # Filter by user type for allowed emails
    if user_type_filter != 'all':
        allowed_emails = allowed_emails.filter(user_type=user_type_filter)
    
    allowed_emails = allowed_emails.order_by('user_type', '-created_at')[:100]
    
    context = {
        'users': users,
        'allowed_emails': allowed_emails,
        'search_query': search_query,
        'user_type_filter': user_type_filter,
        'user_type_choices': user_type_choices,
        'user_permission_counts': user_permission_counts,
        'active_tab': active_tab,
    }
    
    return render(request, 'people/manage_user_permissions_list.html', context)


@login_required
def manage_user_permissions(request, user_id=None):
    """
    Manage permissions for a specific user.
    Only accessible to power users. If they don't have manage_user_permissions permission,
    they can still access to grant it to themselves or others.
    Power users can manage their own permissions too.
    """
    if not request.user.is_power_user:
        messages.error(request, 'Only power users can manage permissions.')
        return redirect('people:user_profile')
    
    # Handle 'self' or check if managing own permissions
    if user_id == 'self' or user_id is None:
        target_user = request.user
    elif isinstance(user_id, (int, str)) and str(user_id).isdigit() and int(user_id) == request.user.id:
        target_user = request.user
    else:
        target_user = get_object_or_404(BaseUser, pk=user_id, is_active=True)
    
    # Get all active permissions grouped by category
    # Exclude 'manage_user_permissions' - only super admin can grant this
    all_permissions = Permission.objects.filter(
        is_active=True
    ).exclude(codename='manage_user_permissions').order_by('category', 'priority', 'name')
    permissions_by_category = {}
    for perm in all_permissions:
        category = perm.category or 'other'
        if category not in permissions_by_category:
            permissions_by_category[category] = []
        permissions_by_category[category].append(perm)
    
    # Get user's current permissions (active grants)
    user_permissions = UserPermission.objects.filter(
        user=target_user,
        is_active=True
    ).select_related('permission', 'granted_by')
    user_permission_codenames = set(up.permission.codename for up in user_permissions)
    
    # Get revoked permissions (inactive UserPermissions)
    revoked_permissions = UserPermission.objects.filter(
        user=target_user,
        is_active=False
    ).select_related('permission')
    revoked_permission_codenames = set(up.permission.codename for up in revoked_permissions)
    
    # For power users: all permissions are granted by default unless explicitly revoked
    # So we need to determine which permissions should appear as checked
    if target_user.is_power_user:
        # Power users have all permissions except revoked ones
        # Get all permission codenames
        all_permission_codenames = {perm.codename for perm in all_permissions}
        # Permissions that should appear as checked = all permissions minus revoked ones
        user_permission_codenames = all_permission_codenames - revoked_permission_codenames
    
    # Create permission status dict
    permission_status = {}
    for up in user_permissions:
        permission_status[up.permission.codename] = {
            'granted': True,
            'granted_by': up.granted_by,
            'granted_at': up.granted_at,
            'user_permission': up,
        }
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # Get selected permissions from form
                selected_permissions = request.POST.getlist('permissions')
                selected_permission_set = set(selected_permissions)
                
                # Get all permission codenames for reference
                all_permission_codenames = {perm.codename for perm in all_permissions}
                
                # Handle power users differently
                if target_user.is_power_user:
                    # For power users: unchecking a permission means revoking it (creating inactive UserPermission)
                    # Checking a permission means unrevoking it (deleting inactive UserPermission if exists)
                    
                    # Permissions that should be granted (checked)
                    for perm_codename in selected_permission_set:
                        try:
                            permission = Permission.objects.get(codename=perm_codename, is_active=True)
                            # Delete any revoked (inactive) UserPermission for this permission
                            UserPermission.objects.filter(
                                user=target_user,
                                permission=permission,
                                is_active=False
                            ).delete()
                            # Create active grant if it doesn't exist (optional, but good for tracking)
                            if not UserPermission.objects.filter(
                                user=target_user,
                                permission=permission,
                                is_active=True
                            ).exists():
                                UserPermission.objects.create(
                                    user=target_user,
                                    permission=permission,
                                    granted_by=request.user,
                                    notes=request.POST.get(f'notes_{perm_codename}', '').strip() or None,
                                )
                        except Permission.DoesNotExist:
                            messages.warning(request, f'Permission "{perm_codename}" not found. Skipping.')
                    
                    # Permissions that should be revoked (unchecked)
                    for perm_codename in all_permission_codenames:
                        if perm_codename not in selected_permission_set:
                            try:
                                permission = Permission.objects.get(codename=perm_codename)
                                # Delete any active UserPermission for this permission
                                UserPermission.objects.filter(
                                    user=target_user,
                                    permission=permission,
                                    is_active=True
                                ).delete()
                                # Create inactive UserPermission to mark it as revoked
                                UserPermission.objects.get_or_create(
                                    user=target_user,
                                    permission=permission,
                                    defaults={
                                        'is_active': False,
                                        'revoked_by': request.user,
                                        'revoked_at': timezone.now(),
                                    }
                                )
                            except Permission.DoesNotExist:
                                pass
                else:
                    # Regular users: normal grant/revoke logic
                    # Grant new permissions
                    for perm_codename in selected_permission_set:
                        if perm_codename not in user_permission_codenames:
                            try:
                                permission = Permission.objects.get(codename=perm_codename, is_active=True)
                                
                                # Revoke any existing inactive grants for this permission
                                UserPermission.objects.filter(
                                    user=target_user,
                                    permission=permission,
                                    is_active=False
                                ).delete()
                                
                                # Create new permission grant
                                UserPermission.objects.create(
                                    user=target_user,
                                    permission=permission,
                                    granted_by=request.user,
                                    notes=request.POST.get(f'notes_{perm_codename}', '').strip() or None,
                                )
                            except Permission.DoesNotExist:
                                messages.warning(request, f'Permission "{perm_codename}" not found. Skipping.')
                    
                    # Revoke permissions that were unchecked
                    for perm_codename in user_permission_codenames:
                        if perm_codename not in selected_permission_set:
                            try:
                                permission = Permission.objects.get(codename=perm_codename)
                                user_perm = UserPermission.objects.get(
                                    user=target_user,
                                    permission=permission,
                                    is_active=True
                                )
                                
                                # Revoke permission
                                user_perm.is_active = False
                                user_perm.revoked_by = request.user
                                user_perm.revoked_at = timezone.now()
                                user_perm.save()
                            except (Permission.DoesNotExist, UserPermission.DoesNotExist):
                                pass
                
                messages.success(request, f'Permissions updated successfully for {target_user.email}!')
                return redirect('people:manage_user_permissions', user_id=target_user.id)
                
        except Exception as e:
            messages.error(request, f'Error updating permissions: {str(e)}')
    
    context = {
        'target_user': target_user,
        'permissions_by_category': permissions_by_category,
        'user_permission_codenames': user_permission_codenames,
        'permission_status': permission_status,
    }
    
    return render(request, 'people/manage_user_permissions.html', context)


@login_required
def create_allowed_email(request):
    """
    Create a new allowed email entry.
    Only accessible to power users.
    """
    if not request.user.is_power_user:
        messages.error(request, 'Only power users can create allowed emails.')
        return redirect('people:user_profile')
    
    if request.method == 'POST':
        try:
            email = request.POST.get('email', '').strip().lower()
            user_type = request.POST.get('user_type', '')
            is_power_user = request.POST.get('is_power_user') == 'on'
            is_active = request.POST.get('is_active') != 'off'  # Default to True
            
            if not email:
                messages.error(request, 'Email is required.')
                return render(request, 'people/create_allowed_email.html', {
                    'form_data': request.POST,
                })
            
            if not user_type:
                messages.error(request, 'User type is required.')
                return render(request, 'people/create_allowed_email.html', {
                    'form_data': request.POST,
                })
            
            # Check if email already exists
            if AllowedEmail.objects.filter(email=email).exists():
                messages.error(request, f'Email {email} is already in the allowed list.')
                return render(request, 'people/create_allowed_email.html', {
                    'form_data': request.POST,
                })
            
            # Create allowed email
            allowed_email = AllowedEmail.objects.create(
                email=email,
                user_type=user_type,
                is_power_user=is_power_user,
                is_active=is_active,
                created_by=request.user,
            )
            
            messages.success(request, f'Allowed email "{email}" created successfully!')
            return redirect('people:manage_users')
            
        except Exception as e:
            messages.error(request, f'Error creating allowed email: {str(e)}')
            return render(request, 'people/create_allowed_email.html', {
                'form_data': request.POST,
            })
    
    # GET request - show form
    user_type_choices = AllowedEmail.USER_TYPE_CHOICES
    
    context = {
        'user_type_choices': user_type_choices,
    }
    
    return render(request, 'people/create_allowed_email.html', context)


@login_required
def edit_allowed_email(request, pk):
    """
    Edit an existing allowed email entry.
    Only accessible to power users.
    """
    if not request.user.is_power_user:
        messages.error(request, 'Only power users can edit allowed emails.')
        return redirect('people:user_profile')
    
    allowed_email = get_object_or_404(AllowedEmail, pk=pk)
    
    if request.method == 'POST':
        try:
            email = request.POST.get('email', '').strip().lower()
            user_type = request.POST.get('user_type', '')
            is_power_user = request.POST.get('is_power_user') == 'on'
            is_active = request.POST.get('is_active') == 'on'
            is_blocked = request.POST.get('is_blocked') == 'on'
            block_reason = request.POST.get('block_reason', '').strip()
            
            if not email:
                messages.error(request, 'Email is required.')
                return render(request, 'people/edit_allowed_email.html', {
                    'allowed_email': allowed_email,
                    'form_data': request.POST,
                })
            
            if not user_type:
                messages.error(request, 'User type is required.')
                return render(request, 'people/edit_allowed_email.html', {
                    'allowed_email': allowed_email,
                    'form_data': request.POST,
                })
            
            # Check if email already exists (excluding current)
            if AllowedEmail.objects.filter(email=email).exclude(pk=pk).exists():
                messages.error(request, f'Email {email} is already in use by another entry.')
                return render(request, 'people/edit_allowed_email.html', {
                    'allowed_email': allowed_email,
                    'form_data': request.POST,
                })
            
            # Update allowed email
            old_email = allowed_email.email
            old_user_type = allowed_email.user_type
            old_is_power_user = allowed_email.is_power_user
            
            allowed_email.email = email
            allowed_email.user_type = user_type
            allowed_email.is_power_user = is_power_user
            allowed_email.is_active = is_active
            
            # Handle blocking
            if is_blocked and not allowed_email.is_blocked:
                allowed_email.is_blocked = True
                allowed_email.blocked_at = timezone.now()
                allowed_email.block_reason = block_reason
            elif not is_blocked and allowed_email.is_blocked:
                allowed_email.is_blocked = False
                allowed_email.blocked_at = None
                allowed_email.block_reason = None
            elif is_blocked:
                allowed_email.block_reason = block_reason
            
            allowed_email.save()
            
            # If user_type or is_power_user changed, sync to BaseUser if exists
            if allowed_email.base_user:
                user = allowed_email.base_user
                if user.user_type != user_type:
                    user.user_type = user_type
                if user.is_power_user != is_power_user:
                    user.is_power_user = is_power_user
                user.save()
            
            messages.success(request, f'Allowed email "{email}" updated successfully!')
            return redirect('people:manage_users')
            
        except Exception as e:
            messages.error(request, f'Error updating allowed email: {str(e)}')
            return render(request, 'people/edit_allowed_email.html', {
                'allowed_email': allowed_email,
                'form_data': request.POST,
            })
    
    # GET request - show form
    user_type_choices = AllowedEmail.USER_TYPE_CHOICES
    
    context = {
        'allowed_email': allowed_email,
        'user_type_choices': user_type_choices,
    }
    
    return render(request, 'people/edit_allowed_email.html', context)


@login_required
def manage_users(request):
    """
    Manage allowed emails - create, edit, and bulk delete.
    Only accessible to power users.
    """
    if not request.user.is_power_user:
        messages.error(request, 'Only power users can manage users.')
        return redirect('people:user_profile')
    
    # Get filters
    search_query = request.GET.get('search', '').strip()
    user_type_filter = request.GET.get('user_type', 'all')
    
    # Get user type choices for filter dropdown
    user_type_choices = [
        ('all', 'All Types'),
        ('faculty', 'Faculty'),
        ('staff', 'Staff'),
        ('officer', 'Officer'),
        ('club_member', 'Club Member'),
    ]
    
    # Get allowed emails (all, including club members)
    allowed_emails = AllowedEmail.objects.all().select_related('created_by', 'base_user')
    
    # Filter allowed emails by search
    if search_query:
        allowed_emails = allowed_emails.filter(email__icontains=search_query)
    
    # Filter by user type for allowed emails
    if user_type_filter != 'all':
        allowed_emails = allowed_emails.filter(user_type=user_type_filter)
    
    allowed_emails = allowed_emails.order_by('user_type', '-created_at')
    
    context = {
        'allowed_emails': allowed_emails,
        'search_query': search_query,
        'user_type_filter': user_type_filter,
        'user_type_choices': user_type_choices,
    }
    
    return render(request, 'people/manage_users.html', context)


@login_required
def get_user_posts(request, email_id):
    """
    Get all posts created by a user associated with an allowed email.
    Only accessible to power users.
    """
    if not request.user.is_power_user:
        return JsonResponse({
            'success': False,
            'message': 'You do not have permission to view posts.'
        }, status=403)
    
    try:
        allowed_email = get_object_or_404(AllowedEmail, pk=email_id)
        
        # Check if base_user exists
        try:
            base_user = allowed_email.base_user
        except AttributeError:
            return JsonResponse({
                'success': False,
                'message': 'No user account associated with this email.'
            }, status=404)
        
        from clubs.models import ClubPost
        posts = ClubPost.objects.filter(posted_by=base_user).select_related('club').order_by('-created_at')
        
        posts_data = []
        for post in posts:
            posts_data.append({
                'id': post.id,
                'short_title': post.short_title,
                'long_title': post.long_title,
                'post_type': post.get_post_type_display(),
                'club_name': post.club.name,
                'club_short_name': post.club.short_name or post.club.name,
                'created_at': post.created_at.strftime('%B %d, %Y'),
                'is_pinned': post.is_pinned,
                'tags': post.tags or '',
            })
        
        return JsonResponse({
            'success': True,
            'user_name': base_user.get_full_name() or base_user.email,
            'post_count': posts.count(),
            'posts': posts_data
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error fetching posts: {str(e)}'
        }, status=500)


@login_required
def bulk_delete_allowed_emails(request):
    """
    Delete multiple allowed emails at once.
    Only accessible to power users.
    Accepts 'action' parameter: 'delete_posts' or 'keep_posts'
    """
    if not request.user.is_power_user:
        return JsonResponse({
            'success': False,
            'message': 'You do not have permission to delete allowed emails.'
        }, status=403)
    
    email_ids = request.POST.getlist('email_ids[]')
    action = request.POST.get('action', '')  # 'delete_posts' or 'keep_posts'
    
    if not email_ids:
        return JsonResponse({
            'success': False,
            'message': 'No emails selected for deletion.'
        })
    
    try:
        # Get allowed emails to delete with related base_user
        emails_to_delete = AllowedEmail.objects.filter(pk__in=email_ids).select_related('base_user')
        deleted_count = emails_to_delete.count()
        email_addresses = [email.email for email in emails_to_delete]
        
        # Check if any have associated BaseUser accounts with posts
        emails_with_posts = []
        emails_with_posts_details = []  # Store (email_obj, base_user, post_count) tuples
        base_users_to_delete = []  # Store base_user objects to delete
        
        for email in emails_to_delete:
            # Safely check if base_user exists
            # OneToOneField reverse relationship raises RelatedObjectDoesNotExist (subclass of AttributeError) if no related object exists
            try:
                base_user = email.base_user
                base_users_to_delete.append(base_user)
                # Check if this user has created any club posts
                from clubs.models import ClubPost
                post_count = ClubPost.objects.filter(posted_by=base_user).count()
                if post_count > 0:
                    # Get user's name (full name or email as fallback)
                    user_name = base_user.get_full_name() or base_user.email
                    emails_with_posts.append(f"{user_name} ({post_count} post{'s' if post_count > 1 else ''})")
                    emails_with_posts_details.append((email, base_user, post_count))
            except AttributeError:
                # No base_user associated with this allowed email (RelatedObjectDoesNotExist is a subclass of AttributeError)
                # Safe to delete
                pass
            except ObjectDoesNotExist:
                # Catch any other DoesNotExist exceptions
                pass
        
        # If there are posts and no action specified, return error with details
        if emails_with_posts and not action:
            return JsonResponse({
                'success': False,
                'has_posts': True,
                'message': f'Cannot delete emails with active accounts that have created posts: {", ".join(emails_with_posts)}.',
                'users_with_posts': [
                    {
                        'email_id': email.id,
                        'user_name': base_user.get_full_name() or base_user.email,
                        'post_count': post_count
                    }
                    for email, base_user, post_count in emails_with_posts_details
                ]
            }, status=400)
        
        # Handle posts based on action
        if action == 'delete_posts':
            # Delete all posts created by users being deleted
            from clubs.models import ClubPost
            posts_deleted = 0
            for email, base_user, post_count in emails_with_posts_details:
                deleted = ClubPost.objects.filter(posted_by=base_user).delete()
                posts_deleted += deleted[0] if deleted else 0
        elif action == 'keep_posts':
            # Keep posts but remove user reference (set posted_by to None)
            # Ensure posted_by_name and posted_by_email are populated before removing the FK
            from clubs.models import ClubPost
            posts_updated = 0
            for email, base_user, post_count in emails_with_posts_details:
                # Get user's name based on their type (same logic as ClubPost model)
                user_name = None
                user_email = base_user.email or ''
                
                if base_user.user_type == 'faculty' and hasattr(base_user, 'faculty_profile'):
                    user_name = base_user.faculty_profile.name if base_user.faculty_profile else None
                elif base_user.user_type == 'officer' and hasattr(base_user, 'officer_profile'):
                    user_name = base_user.officer_profile.name if base_user.officer_profile else None
                elif base_user.user_type == 'club_member' and hasattr(base_user, 'club_member_profile'):
                    user_name = base_user.club_member_profile.name if base_user.club_member_profile else None
                elif base_user.user_type == 'staff' and hasattr(base_user, 'staff_profile'):
                    user_name = base_user.staff_profile.name if base_user.staff_profile else None
                else:
                    # Fallback to full name or email
                    user_name = base_user.get_full_name() or base_user.email or ''
                
                user_name = user_name or user_email
                
                # Update posts: set posted_by to None and ensure name/email are preserved
                posts = ClubPost.objects.filter(posted_by=base_user)
                for post in posts:
                    # Ensure name and email are set (they should be, but just in case)
                    if not post.posted_by_name:
                        post.posted_by_name = user_name
                    if not post.posted_by_email:
                        post.posted_by_email = user_email
                    post.posted_by = None
                    post.save()
                posts_updated += posts.count()
        
        # Delete associated BaseUser accounts first (this will cascade to AllowedEmail)
        users_deleted = 0
        for base_user in base_users_to_delete:
            try:
                base_user.delete()
                users_deleted += 1
            except Exception as e:
                # If user deletion fails, log but continue
                print(f"Error deleting user {base_user.email}: {str(e)}")
        
        # Delete the allowed emails (if not already deleted by cascade)
        # Note: BaseUser.allowed_email has CASCADE, so deleting BaseUser will set AllowedEmail.base_user to NULL
        # But we still need to delete the AllowedEmail entries themselves
        remaining_emails = AllowedEmail.objects.filter(pk__in=email_ids)
        remaining_emails.delete()
        
        # Build success message
        success_message = f'Successfully deleted {deleted_count} allowed email(s)'
        if users_deleted > 0:
            success_message += f' and {users_deleted} user account(s)'
        success_message += '.'
        
        if action == 'delete_posts' and emails_with_posts_details:
            total_posts = sum(post_count for _, _, post_count in emails_with_posts_details)
            success_message += f' Deleted {total_posts} related post(s).'
        elif action == 'keep_posts' and emails_with_posts_details:
            total_posts = sum(post_count for _, _, post_count in emails_with_posts_details)
            success_message += f' Kept {total_posts} post(s) with preserved author names.'
        
        return JsonResponse({
            'success': True,
            'message': success_message,
            'deleted_emails': email_addresses
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error deleting allowed emails: {str(e)}'
        }, status=500)


@login_required
def manage_faculty(request):
    """
    Manage faculty list with drag-and-drop reordering, search, and sorting.
    Separates faculty into tabs: Active, On Leave, and Former.
    Only accessible to power users.
    """
    if not request.user.is_power_user:
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('people:user_profile')
    
    # Get active tab from request
    active_tab = request.GET.get('tab', 'active')
    
    # Get all faculties
    all_faculties = Faculty.objects.all().select_related('base_user')
    
    # Separate into categories
    former_faculties = all_faculties.filter(last_office_date__isnull=False)
    active_faculties = all_faculties.filter(last_office_date__isnull=True)
    faculties_on_leave = active_faculties.filter(is_on_study_leave=True)
    faculties_active = active_faculties.filter(is_on_study_leave=False)
    
    # Search functionality
    search_query = request.GET.get('search', '').strip()
    search_filter = Q()
    if search_query:
        search_filter = (
            Q(name__icontains=search_query) |
            Q(designation__icontains=search_query) |
            Q(base_user__email__icontains=search_query) |
            Q(phone__icontains=search_query)
        )
    
    # Apply search to each category
    if search_query:
        faculties_active = faculties_active.filter(search_filter)
        faculties_on_leave = faculties_on_leave.filter(search_filter)
        former_faculties = former_faculties.filter(search_filter)
    
    # Sort by designation
    sort_by = request.GET.get('sort', 'sl')
    designation_order = {
        'Professor': 1,
        'Associate Professor': 2,
        'Assistant Professor': 3,
        'Lecturer': 4,
        'Teaching Assistant': 5,
    }
    
    def sort_faculties(faculties_queryset):
        """Helper function to sort faculties"""
        # If no serial numbers, assign them first
        if isinstance(faculties_queryset, list):
            # Already a list, check if any have sl
            if not any(f.sl for f in faculties_queryset):
                for index, faculty in enumerate(faculties_queryset, start=1):
                    faculty.sl = index
                    faculty.save()
        elif faculties_queryset.exists() and not any(f.sl for f in faculties_queryset):
            for index, faculty in enumerate(faculties_queryset, start=1):
                faculty.sl = index
                faculty.save()
        
        # Apply sorting
        if sort_by == 'designation':
            # Convert to list and sort by designation
            if not isinstance(faculties_queryset, list):
                faculties_list = list(faculties_queryset)
            else:
                faculties_list = faculties_queryset
            faculties_list.sort(key=lambda f: (
                designation_order.get(f.designation, 999) if f.designation else 999,
                f.sl if f.sl else 999
            ))
            return faculties_list
        else:
            # Default: sort by serial number
            if isinstance(faculties_queryset, list):
                # Convert list back to queryset for ordering
                pks = [f.pk for f in faculties_queryset]
                return Faculty.objects.filter(pk__in=pks).select_related('base_user').order_by('sl')
            return faculties_queryset.order_by('sl')
    
    # Sort each category
    faculties_active = sort_faculties(faculties_active)
    faculties_on_leave = sort_faculties(faculties_on_leave)
    former_faculties = sort_faculties(former_faculties)
    
    # Get the current tab's faculties
    if active_tab == 'leave':
        current_faculties = faculties_on_leave
    elif active_tab == 'former':
        current_faculties = former_faculties
    else:  # default to 'active'
        current_faculties = faculties_active
    
    # Get unique designations for filter dropdown
    all_designations = Faculty.objects.exclude(designation__isnull=True).exclude(designation='').values_list('designation', flat=True).distinct().order_by('designation')
    
    context = {
        'faculties': current_faculties,
        'faculties_active': faculties_active,
        'faculties_on_leave': faculties_on_leave,
        'former_faculties': former_faculties,
        'active_tab': active_tab,
        'search_query': search_query,
        'sort_by': sort_by,
        'all_designations': all_designations,
    }
    
    return render(request, 'people/manage_faculty.html', context)


@login_required
def edit_faculty(request, pk):
    """
    Edit faculty details.
    Only accessible to power users.
    """
    if not request.user.is_power_user:
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('people:user_profile')
    
    faculty = get_object_or_404(Faculty, pk=pk)
    
    if request.method == 'POST':
        try:
            # Update basic fields
            faculty.name = request.POST.get('name', '').strip()
            faculty.shortname = request.POST.get('shortname', '').strip()
            faculty.designation = request.POST.get('designation', '').strip() or None
            faculty.phone = request.POST.get('phone', '').strip() or None
            faculty.bio = request.POST.get('bio', '').strip() or None
            faculty.about = request.POST.get('about', '')
            
            # Handle profile picture (simple replacement, identical to staff flow)
            if 'profile_pic' in request.FILES:
                faculty.profile_pic = request.FILES['profile_pic']
            elif 'profile_picture' in request.FILES:
                faculty.profile_pic = request.FILES['profile_picture']
            
            # Update joining date
            joining_date_str = request.POST.get('joining_date', '').strip()
            if joining_date_str:
                from datetime import datetime
                try:
                    faculty.joining_date = datetime.strptime(joining_date_str, '%Y-%m-%d').date()
                except ValueError:
                    pass
            else:
                faculty.joining_date = None
            
            # Update last office date
            last_office_date_str = request.POST.get('last_office_date', '').strip()
            if last_office_date_str:
                try:
                    from datetime import datetime
                    faculty.last_office_date = datetime.strptime(last_office_date_str, '%Y-%m-%d').date()
                except ValueError:
                    pass
            else:
                faculty.last_office_date = None
            
            # Update research links - convert empty strings and "None" to None
            def clean_url(value):
                val = value.strip() if value else ''
                return None if not val or val.lower() == 'none' else val
            
            faculty.google_scholar_url = clean_url(request.POST.get('google_scholar_url', ''))
            faculty.researchgate_url = clean_url(request.POST.get('researchgate_url', ''))
            faculty.orcid_url = clean_url(request.POST.get('orcid_url', ''))
            faculty.scopus_url = clean_url(request.POST.get('scopus_url', ''))
            faculty.linkedin_url = clean_url(request.POST.get('linkedin_url', ''))
            
            # Update research information
            faculty.researches = request.POST.get('researches', '')
            citation_str = request.POST.get('citation', '0').strip()
            if citation_str:
                try:
                    faculty.citation = int(citation_str)
                except ValueError:
                    pass
            
            # Update routine
            faculty.routine = request.POST.get('routine', '')
            
            # Update special roles
            new_is_head = request.POST.get('is_head') == 'on'
            
            # If setting this faculty as head, unset any existing head
            if new_is_head and not faculty.is_head:
                # Unset any other faculty who is currently head
                Faculty.objects.filter(is_head=True).exclude(base_user=faculty.base_user).update(is_head=False)
            
            faculty.is_head = new_is_head
            faculty.is_dept_proctor = request.POST.get('is_dept_proctor') == 'on'
            faculty.is_bsc_admission_coordinator = request.POST.get('is_bsc_admission_coordinator') == 'on'
            faculty.is_mcse_admission_coordinator = request.POST.get('is_mcse_admission_coordinator') == 'on'
            faculty.is_on_study_leave = request.POST.get('is_on_study_leave') == 'on'
            faculty.is_inter_departmental = request.POST.get('is_inter_departmental') == 'on'
            faculty.is_visiting = request.POST.get('is_visiting') == 'on'
            
            # Update qualification fields
            faculty.is_phd = request.POST.get('is_phd') == 'on'
            faculty.is_masters = request.POST.get('is_masters') == 'on'
            faculty.educational_qualification = request.POST.get('educational_qualification', '')
            faculty.course_conducted = request.POST.get('course_conducted', '')
            
            # Update CV if provided (simple replace, like staff photo handling)
            if 'cv' in request.FILES:
                cv_file = request.FILES['cv']
                # Validate file size (5MB = 5 * 1024 * 1024 bytes)
                if cv_file.size > 5 * 1024 * 1024:
                    messages.error(request, 'CV file size must not exceed 5 MB.')
                    return redirect('people:edit_faculty', pk=faculty.pk)
                faculty.cv = cv_file
            else:
                # Only check for missing files if no new upload
                # Check if it's a new upload (UploadedFile) vs existing file
                is_new_upload = isinstance(faculty.cv, UploadedFile)
                if not is_new_upload and faculty.cv and hasattr(faculty.cv, 'path'):
                    try:
                        if faculty.cv.path and not os.path.exists(faculty.cv.path):
                            faculty.cv = None
                    except Exception:
                        pass
            
            # Update cropping if provided
            if 'cropping' in request.POST:
                faculty.cropping = request.POST.get('cropping', '')
            
            faculty.save()
            
            messages.success(request, f'Faculty "{faculty.name}" updated successfully!')
            return redirect('people:manage_faculty')
            
        except Exception as e:
            messages.error(request, f'Error updating faculty: {str(e)}')
    
    context = {
        'faculty': faculty,
        'DESIGNATION_CHOICES': Faculty.DESIGNATION_CHOICES,
    }
    
    return render(request, 'people/edit_faculty.html', context)


@login_required
@require_http_methods(["POST"])
def update_faculty_order(request):
    """
    Update the order (serial numbers) of faculty via drag and drop.
    Expects JSON: {"faculty_ids": [1, 2, 3, ...]}
    Only accessible to power users.
    """
    if not request.user.is_power_user:
        return JsonResponse({
            'success': False,
            'message': 'You do not have permission to update faculty order.'
        }, status=403)
    
    try:
        import json
        data = json.loads(request.body)
        faculty_ids = data.get('faculty_ids', [])
        
        if not faculty_ids:
            return JsonResponse({
                'success': False,
                'message': 'Missing required data: faculty_ids.'
            }, status=400)
        
        # Verify all faculty IDs exist
        faculties = Faculty.objects.filter(pk__in=faculty_ids)
        
        if faculties.count() != len(faculty_ids):
            return JsonResponse({
                'success': False,
                'message': 'Some faculty IDs do not exist.'
            }, status=400)
        
        # Update serial numbers based on the order provided
        for index, faculty_id in enumerate(faculty_ids, start=1):
            Faculty.objects.filter(pk=faculty_id).update(sl=index)
        
        return JsonResponse({
            'success': True,
            'message': 'Faculty order updated successfully!'
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


@login_required
def create_faculty(request):
    """
    Create a new faculty member.
    Only accessible to power users.
    """
    if not request.user.is_power_user:
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('people:user_profile')
    
    if request.method == 'POST':
        try:
            # Get the next available serial number
            max_sl = Faculty.objects.aggregate(Max('sl'))['sl__max'] or 0
            next_sl = max_sl + 1
            
            # Create BaseUser first
            email = request.POST.get('email', '').strip()
            if not email:
                messages.error(request, 'Email is required.')
                return redirect('people:create_faculty')
            
            # Check if user already exists
            if BaseUser.objects.filter(email=email).exists():
                messages.error(request, f'A user with email "{email}" already exists.')
                return redirect('people:create_faculty')
            
            # Create BaseUser
            base_user = BaseUser.objects.create_user(
                username=email.split('@')[0],
                email=email,
                user_type='faculty',
                password='temp_password_123'  # Should be changed by user
            )
            
            # Check if setting as head, and unset any existing head
            new_is_head = request.POST.get('is_head') == 'on'
            if new_is_head:
                # Unset any other faculty who is currently head
                Faculty.objects.filter(is_head=True).update(is_head=False)
            
            # Create Faculty profile
            faculty = Faculty.objects.create(
                base_user=base_user,
                name=request.POST.get('name', '').strip(),
                shortname=request.POST.get('shortname', '').strip(),
                designation=request.POST.get('designation', '').strip() or None,
                phone=request.POST.get('phone', '').strip() or None,
                bio=request.POST.get('bio', '').strip() or None,
                about=request.POST.get('about', ''),
                sl=next_sl,
                is_head=new_is_head,
                is_dept_proctor=request.POST.get('is_dept_proctor') == 'on',
                is_bsc_admission_coordinator=request.POST.get('is_bsc_admission_coordinator') == 'on',
                is_mcse_admission_coordinator=request.POST.get('is_mcse_admission_coordinator') == 'on',
                is_on_study_leave=request.POST.get('is_on_study_leave') == 'on',
                is_inter_departmental=request.POST.get('is_inter_departmental') == 'on',
                is_visiting=request.POST.get('is_visiting') == 'on',
            )
            
            # Update profile picture if provided
            if 'profile_pic' in request.FILES:
                faculty.profile_pic = request.FILES['profile_pic']
                faculty.save()
            
            # Update joining date
            joining_date_str = request.POST.get('joining_date', '').strip()
            if joining_date_str:
                from datetime import datetime
                try:
                    faculty.joining_date = datetime.strptime(joining_date_str, '%Y-%m-%d').date()
                    faculty.save()
                except ValueError:
                    pass
            
            # Update last office date
            last_office_date_str = request.POST.get('last_office_date', '').strip()
            if last_office_date_str:
                try:
                    from datetime import datetime
                    faculty.last_office_date = datetime.strptime(last_office_date_str, '%Y-%m-%d').date()
                    faculty.save()
                except ValueError:
                    pass
            
            # Update research links - convert empty strings and "None" to None
            def clean_url(value):
                val = value.strip() if value else ''
                return None if not val or val.lower() == 'none' else val
            
            faculty.google_scholar_url = clean_url(request.POST.get('google_scholar_url', ''))
            faculty.researchgate_url = clean_url(request.POST.get('researchgate_url', ''))
            faculty.orcid_url = clean_url(request.POST.get('orcid_url', ''))
            faculty.scopus_url = clean_url(request.POST.get('scopus_url', ''))
            faculty.linkedin_url = clean_url(request.POST.get('linkedin_url', ''))
            
            # Update research information
            faculty.researches = request.POST.get('researches', '')
            citation_str = request.POST.get('citation', '0').strip()
            if citation_str:
                try:
                    faculty.citation = int(citation_str)
                except ValueError:
                    pass
            
            # Update routine
            faculty.routine = request.POST.get('routine', '')
            
            # Update special roles
            new_is_head = request.POST.get('is_head') == 'on'
            
            # If setting this faculty as head, unset any existing head
            if new_is_head and not faculty.is_head:
                # Unset any other faculty who is currently head
                Faculty.objects.filter(is_head=True).exclude(base_user=faculty.base_user).update(is_head=False)
            
            faculty.is_head = new_is_head
            faculty.is_dept_proctor = request.POST.get('is_dept_proctor') == 'on'
            faculty.is_bsc_admission_coordinator = request.POST.get('is_bsc_admission_coordinator') == 'on'
            faculty.is_mcse_admission_coordinator = request.POST.get('is_mcse_admission_coordinator') == 'on'
            faculty.is_on_study_leave = request.POST.get('is_on_study_leave') == 'on'
            faculty.is_inter_departmental = request.POST.get('is_inter_departmental') == 'on'
            faculty.is_visiting = request.POST.get('is_visiting') == 'on'
            
            # Update qualification fields
            faculty.is_phd = request.POST.get('is_phd') == 'on'
            faculty.is_masters = request.POST.get('is_masters') == 'on'
            faculty.educational_qualification = request.POST.get('educational_qualification', '')
            faculty.course_conducted = request.POST.get('course_conducted', '')
            
            # Update CV if provided
            if 'cv' in request.FILES:
                faculty.cv = request.FILES['cv']
            
            # Update cropping if provided
            if 'cropping' in request.POST:
                faculty.cropping = request.POST.get('cropping', '')
            
            faculty.save()
            
            messages.success(request, f'Faculty "{faculty.name}" created successfully!')
            return redirect('people:manage_faculty')
            
        except Exception as e:
            messages.error(request, f'Error creating faculty: {str(e)}')
    
    context = {
        'DESIGNATION_CHOICES': Faculty.DESIGNATION_CHOICES,
    }
    
    return render(request, 'people/create_faculty.html', context)


@login_required
@require_http_methods(["POST"])
def bulk_delete_faculty(request):
    """
    Bulk delete faculty members.
    Only accessible to power users.
    """
    if not request.user.is_power_user:
        return JsonResponse({
            'success': False,
            'message': 'You do not have permission to delete faculty.'
        }, status=403)
    
    try:
        import json
        data = json.loads(request.body)
        faculty_ids = data.get('faculty_ids', [])
        
        if not faculty_ids:
            return JsonResponse({
                'success': False,
                'message': 'No faculty selected for deletion.'
            }, status=400)
        
        # Get faculties to delete
        faculties_to_delete = Faculty.objects.filter(pk__in=faculty_ids)
        
        if faculties_to_delete.count() != len(faculty_ids):
            return JsonResponse({
                'success': False,
                'message': 'Some faculty IDs do not exist.'
            }, status=400)
        
        # Get names for response
        faculty_names = [f.name for f in faculties_to_delete]
        
        # Delete associated BaseUser objects
        base_user_ids = [f.base_user_id for f in faculties_to_delete if f.base_user_id]
        BaseUser.objects.filter(pk__in=base_user_ids).delete()
        
        # Faculty objects will be deleted via CASCADE
        
        # Reassign serial numbers to remaining faculties
        remaining_faculties = Faculty.objects.all().order_by('sl')
        for index, faculty in enumerate(remaining_faculties, start=1):
            faculty.sl = index
            faculty.save()
        
        return JsonResponse({
            'success': True,
            'message': f'Successfully deleted {len(faculty_names)} faculty member(s).',
            'deleted_faculties': faculty_names
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error deleting faculty: {str(e)}'
        }, status=500)


@login_required
def manage_publications(request, faculty_id):
    """
    Manage publications for a faculty member.
    Accessible to the faculty member themselves or users with manage_all_publications permission.
    """
    from people.permissions import Permissions
    
    faculty = get_object_or_404(Faculty, pk=faculty_id)
    
    # Check permissions - allow if user is the faculty member OR power user OR has manage_all_publications permission
    can_manage = False
    if hasattr(request.user, 'faculty_profile') and request.user.faculty_profile.pk == faculty.pk:
        can_manage = True
    elif request.user.is_power_user or request.user.has_permission(Permissions.MANAGE_ALL_PUBLICATIONS):
        can_manage = True
    
    if not can_manage:
        messages.error(request, 'You do not have permission to manage publications for this faculty member.')
        return redirect('people:user_profile')
    
    publications = faculty.publications.all().order_by('-pub_year', 'title')
    
    # Check if user is managing their own publications or has permission
    is_own_publications = (hasattr(request.user, 'faculty_profile') and request.user.faculty_profile.pk == faculty.pk)
    has_manage_all_permission = request.user.has_permission(Permissions.MANAGE_ALL_PUBLICATIONS)
    
    context = {
        'faculty': faculty,
        'publications': publications,
        'is_own_publications': is_own_publications,
        'has_manage_all_permission': has_manage_all_permission,
    }
    
    return render(request, 'people/manage_publications.html', context)


@login_required
@transaction.atomic
def add_publication(request, faculty_id):
    """
    Add a single publication for a faculty member.
    Accessible to the faculty member themselves or users with manage_all_publications permission.
    """
    from people.permissions import Permissions
    
    faculty = get_object_or_404(Faculty, pk=faculty_id)
    
    # Check permissions - allow if user is the faculty member OR power user OR has manage_all_publications permission
    can_manage = False
    if hasattr(request.user, 'faculty_profile') and request.user.faculty_profile.pk == faculty.pk:
        can_manage = True
    elif request.user.is_power_user or request.user.has_permission(Permissions.MANAGE_ALL_PUBLICATIONS):
        can_manage = True
    
    if not can_manage:
        messages.error(request, 'You do not have permission to add publications for this faculty member.')
        return redirect('people:user_profile')
    
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        pub_year = request.POST.get('pub_year', '').strip()
        type = request.POST.get('type', '').strip()
        ranking = request.POST.get('ranking', '').strip()
        link = request.POST.get('link', '').strip()
        doi = request.POST.get('doi', '').strip()
        published_at = request.POST.get('published_at', '').strip()
        contribution = request.POST.get('contribution', '').strip()
        
        # Validation
        if not title:
            messages.error(request, 'Title is required.')
            return redirect('people:add_publication', faculty_id=faculty_id)
        
        if not pub_year:
            messages.error(request, 'Publication year is required.')
            return redirect('people:add_publication', faculty_id=faculty_id)
        
        try:
            pub_year = int(pub_year)
            if pub_year < 1900 or pub_year > 2100:
                raise ValueError()
        except ValueError:
            messages.error(request, 'Please enter a valid year between 1900 and 2100.')
            return redirect('people:add_publication', faculty_id=faculty_id)
        
        # Type is optional, but if provided, must be valid
        if type and type not in dict(Publication.TYPE_CHOICES):
            messages.error(request, 'Please select a valid publication type.')
            return redirect('people:add_publication', faculty_id=faculty_id)
        
        if not ranking or ranking not in dict(Publication.RANKING_CHOICES):
            messages.error(request, 'Please select a valid ranking.')
            return redirect('people:add_publication', faculty_id=faculty_id)
        
        # Create publication
        publication = Publication.objects.create(
            faculty=faculty,
            title=title,
            pub_year=pub_year,
            type=type if type else None,
            ranking=ranking,
            link=link if link else None,
            doi=doi if doi else None,
            published_at=published_at if published_at else None,
            contribution=contribution if contribution else None,
        )
        
        messages.success(request, f'Publication "{title}" added successfully.')
        return redirect('people:manage_publications', faculty_id=faculty_id)
    
    context = {
        'faculty': faculty,
        'type_choices': Publication.TYPE_CHOICES,
        'ranking_choices': Publication.RANKING_CHOICES,
    }
    
    return render(request, 'people/add_publication.html', context)


@login_required
@transaction.atomic
def add_multiple_publications(request, faculty_id):
    """
    Add multiple publications at once for a faculty member.
    Accessible to the faculty member themselves or users with manage_all_publications permission.
    """
    from people.permissions import Permissions
    
    faculty = get_object_or_404(Faculty, pk=faculty_id)
    
    # Check permissions - allow if user is the faculty member OR power user OR has manage_all_publications permission
    can_manage = False
    if hasattr(request.user, 'faculty_profile') and request.user.faculty_profile.pk == faculty.pk:
        can_manage = True
    elif request.user.is_power_user or request.user.has_permission(Permissions.MANAGE_ALL_PUBLICATIONS):
        can_manage = True
    
    if not can_manage:
        messages.error(request, 'You do not have permission to add publications for this faculty member.')
        return redirect('people:user_profile')
    
    if request.method == 'POST':
        # Get number of publications to add
        num_publications = int(request.POST.get('num_publications', 1))
        created_count = 0
        errors = []
        
        for i in range(num_publications):
            title = request.POST.get(f'title_{i}', '').strip()
            pub_year = request.POST.get(f'pub_year_{i}', '').strip()
            type = request.POST.get(f'type_{i}', '').strip()
            ranking = request.POST.get(f'ranking_{i}', '').strip()
            link = request.POST.get(f'link_{i}', '').strip()
            doi = request.POST.get(f'doi_{i}', '').strip()
            published_at = request.POST.get(f'published_at_{i}', '').strip()
            contribution = request.POST.get(f'contribution_{i}', '').strip()
            
            # Skip if title is empty (optional fields)
            if not title:
                continue
            
            # Validate required fields
            if not pub_year:
                errors.append(f'Publication {i+1}: Year is required.')
                continue
            
            try:
                pub_year = int(pub_year)
                if pub_year < 1900 or pub_year > 2100:
                    raise ValueError()
            except ValueError:
                errors.append(f'Publication {i+1}: Please enter a valid year between 1900 and 2100.')
                continue
            
            # Type is optional, but if provided, must be valid
            if type and type not in dict(Publication.TYPE_CHOICES):
                errors.append(f'Publication {i+1}: Please select a valid publication type.')
                continue
            
            if not ranking or ranking not in dict(Publication.RANKING_CHOICES):
                errors.append(f'Publication {i+1}: Please select a valid ranking.')
                continue
            
            # Create publication
            try:
                Publication.objects.create(
                    faculty=faculty,
                    title=title,
                    pub_year=pub_year,
                    type=type if type else None,
                    ranking=ranking,
                    link=link if link else None,
                    doi=doi if doi else None,
                    published_at=published_at if published_at else None,
                    contribution=contribution if contribution else None,
                )
                created_count += 1
            except Exception as e:
                errors.append(f'Publication {i+1}: Error creating publication - {str(e)}')
        
        if created_count > 0:
            messages.success(request, f'Successfully added {created_count} publication(s).')
        if errors:
            for error in errors:
                messages.error(request, error)
        
        return redirect('people:manage_publications', faculty_id=faculty_id)
    
    # Get number of publications to add from query parameter
    num_publications = int(request.GET.get('num', 5))
    if num_publications < 1:
        num_publications = 1
    if num_publications > 20:
        num_publications = 20
    
    context = {
        'faculty': faculty,
        'type_choices': Publication.TYPE_CHOICES,
        'ranking_choices': Publication.RANKING_CHOICES,
        'num_publications': num_publications,
    }
    
    return render(request, 'people/add_multiple_publications.html', context)


def _detect_format_2(non_empty_lines):
    """
    Detect if the input is Format 2 (noisy format with metadata).
    Format 2 characteristics:
    - Contains Q rankings (Q1, Q2, Q3, Q4) as standalone lines
    - Contains metadata like "NA", "ABS NA", "ABDC NA"
    - Contains numeric metrics like "0.849", "SJR Q1"
    - Years appear with numbers before them (e.g., "48    2023", "13    2024")
    """
    if len(non_empty_lines) < 5:
        return False
    
    # Check for Format 2 indicators
    q_ranking_count = 0
    na_count = 0
    sjr_count = 0
    year_with_prefix_count = 0
    
    for line in non_empty_lines:
        line_stripped = line.strip()
        # Check for standalone Q rankings
        if re.match(r'^Q[1-4]$', line_stripped):
            q_ranking_count += 1
        # Check for NA patterns
        if re.match(r'^(NA|ABS NA|ABDC NA)$', line_stripped):
            na_count += 1
        # Check for SJR patterns
        if 'SJR' in line_stripped:
            sjr_count += 1
        # Check for standalone numeric metrics (like "0.849")
        if re.match(r'^\d+\.\d+$', line_stripped) and len(line_stripped) < 10:
            sjr_count += 1
        # Check for year with prefix (e.g., "48    2023", "13    2024")
        if re.match(r'^\d+\s+20\d{2}$', line_stripped):
            year_with_prefix_count += 1
    
    # Format 2 is likely if we have:
    # - At least one Q ranking AND at least one year with prefix, OR
    # - Multiple Q rankings, OR
    # - Q ranking + multiple NA patterns + year with prefix
    has_q_rankings = q_ranking_count >= 1
    has_year_prefixes = year_with_prefix_count >= 1
    has_metadata = na_count >= 2 or sjr_count >= 1
    
    return (has_q_rankings and has_year_prefixes) or (q_ranking_count >= 2) or (has_q_rankings and has_metadata and has_year_prefixes)


def _parse_format_2(non_empty_lines, original_line_nums):
    """
    Parse Format 2 (noisy format with metadata).
    Strategy:
    1. Find all year anchors (lines containing 20\d{2})
    2. For each year:
       - Extract the last occurrence of year from the line
       - Scan upward to find Q ranking (Q1-Q4)
       - Scan upward to find title (first non-metadata line)
    """
    parsed_publications = []
    
    # Find all year anchors
    year_anchors = []
    for i, line in enumerate(non_empty_lines):
        # Look for year pattern - find the last occurrence
        year_matches = list(re.finditer(r'20\d{2}', line))
        if year_matches:
            # Get the last match
            last_match = year_matches[-1]
            year_str = last_match.group()
            try:
                year = int(year_str)
                if 2000 <= year <= 2100:
                    year_anchors.append({
                        'line_index': i,
                        'line': line,
                        'year': year,
                        'year_pos': last_match.end()
                    })
            except ValueError:
                continue
    
    # Process each year anchor
    for anchor in year_anchors:
        year = anchor['year']
        year_line_index = anchor['line_index']
        
        # Scan upward from year line to find Q ranking
        q_rank = None
        q_rank_line_index = None
        for scan_idx in range(year_line_index - 1, -1, -1):
            line = non_empty_lines[scan_idx].strip()
            # Check for exact Q ranking match
            q_match = re.match(r'^Q[1-4]$', line)
            if q_match:
                q_rank = q_match.group()
                q_rank_line_index = scan_idx
                break
            # Stop if we hit another year (different publication)
            if re.search(r'20\d{2}', line):
                break
        
        # Scan upward from year line (or Q ranking line if found) to find title
        start_index = year_line_index - 1
        if q_rank and q_rank_line_index is not None:
            # Start from line before Q ranking
            start_index = q_rank_line_index - 1
        
        title = None
        for i in range(start_index, -1, -1):
            line = non_empty_lines[i].strip()
            
            # Skip if this is metadata (including author lines)
            if _is_metadata_line(line):
                continue
            
            # Skip if this is another year (different publication)
            if re.search(r'20\d{2}', line):
                break
            
            # Skip if this is a Q ranking
            if re.match(r'^Q[1-4]$', line):
                continue
            
            # Additional check: skip lines that look like author lists
            # Author lines typically have: initials (1-3 letters) + space + capitalized name, repeated with commas
            if ',' in line:
                parts = [p.strip() for p in line.split(',')]
                if len(parts) >= 2:
                    # Check if most parts match author pattern (initials + name)
                    author_pattern = re.compile(r'^[A-Z]{1,3}\s+[A-Z][a-z]+')
                    author_matches = sum(1 for part in parts[:min(3, len(parts))] if author_pattern.match(part))
                    if author_matches >= 2:
                        continue  # Skip this line, it's an author list
            
            # This looks like a title
            if len(line) >= 10:  # Minimum title length
                title = line
                break
        
        # Add if we found title (Q ranking is optional)
        if title:
            parsed_publications.append({
                'title': title,
                'authors': None,
                'venue': None,
                'cited': None,
                'year': str(year),
                'q_rank': q_rank.lower() if q_rank else None,  # Convert to lowercase to match choice values
                'line_num': original_line_nums[year_line_index],
            })
    
    return parsed_publications


def _is_metadata_line(line):
    """
    Check if a line is metadata that should be ignored.
    Metadata includes:
    - NA, ABS NA, ABDC NA
    - Numeric metrics (0.849, etc.)
    - SJR patterns
    - Author lists (lines with commas and names/initials)
    - Journal names that are repeated
    - Lines that are purely numeric
    """
    line_stripped = line.strip()
    
    # Exact metadata matches
    if re.match(r'^(NA|ABS NA|ABDC NA)$', line_stripped):
        return True
    
    # Pure numeric (metrics)
    if re.match(r'^\d+\.?\d*$', line_stripped) and len(line_stripped) < 10:
        return True
    
    # SJR patterns
    if 'SJR' in line_stripped:
        return True
    
    # Q ranking (already handled separately, but skip here too)
    if re.match(r'^Q[1-4]$', line_stripped):
        return True
    
    # Year with prefix (e.g., "48    2023")
    if re.match(r'^\d+\s+20\d{2}$', line_stripped):
        return True
    
    # Very short lines (likely metadata)
    if len(line_stripped) < 5:
        return True
    
    # Author lines: typically have commas, initials (single letters), and names
    # Pattern: "D Mistry, MF Mridha, M Safran" or "BS Diba, JD Plabon, MDM Rahman"
    # Check for multiple comma-separated parts with initials (1-3 letters followed by space and name)
    if ',' in line_stripped:
        # Split by comma and check if parts look like author names
        parts = [p.strip() for p in line_stripped.split(',')]
        if len(parts) >= 2:
            # Check if parts look like author names (initials + name pattern)
            author_pattern = re.compile(r'^[A-Z]{1,3}\s+[A-Z][a-z]+')
            author_count = sum(1 for part in parts if author_pattern.match(part.strip()))
            # If at least 2 parts look like author names, it's likely an author line
            if author_count >= 2:
                return True
            # Also check for patterns like "D Mistry" or "MF Mridha" (1-3 letters + space + capitalized word)
            if all(re.match(r'^[A-Z]{1,3}\s+[A-Z]', p.strip()) for p in parts[:min(3, len(parts))]):
                return True
    
    # Journal/venue lines that are likely repeated (same text appears multiple times)
    # These are usually shorter and don't have the complexity of titles
    # Skip very short lines that might be journal names
    if len(line_stripped) < 20 and not any(char.isdigit() for char in line_stripped):
        # Check if it looks like a journal name (capitalized words, no special punctuation)
        if re.match(r'^[A-Z][a-zA-Z\s]+$', line_stripped) and line_stripped.count(' ') < 5:
            # Might be a journal name, but be careful - could also be a short title
            # Only skip if it's very short
            if len(line_stripped) < 15:
                return True
    
    return False


@login_required
def bulk_import_publications(request, faculty_id):
    """
    Bulk import publications from Google Scholar copy-paste text.
    Shows a preview page for confirmation before saving.
    Accessible to the faculty member themselves or users with manage_all_publications permission.
    """
    from people.permissions import Permissions
    
    faculty = get_object_or_404(Faculty, pk=faculty_id)
    
    # Check permissions - allow if user is the faculty member OR power user OR has manage_all_publications permission
    can_manage = False
    if hasattr(request.user, 'faculty_profile') and request.user.faculty_profile.pk == faculty.pk:
        can_manage = True
    elif request.user.is_power_user or request.user.has_permission(Permissions.MANAGE_ALL_PUBLICATIONS):
        can_manage = True
    
    if not can_manage:
        messages.error(request, 'You do not have permission to import publications for this faculty member.')
        return redirect('people:user_profile')
    
    if request.method == 'POST':
        # Check if this is the confirmation step
        if 'confirm_import' in request.POST:
            # Process confirmed publications
            created_count = 0
            errors = []
            
            # Get all publication data from the form
            i = 0
            while True:
                title = request.POST.get(f'title_{i}', '').strip()
                if not title:
                    break
                
                pub_year = request.POST.get(f'pub_year_{i}', '').strip()
                type_val = request.POST.get(f'type_{i}', '').strip()
                ranking = request.POST.get(f'ranking_{i}', '').strip()
                published_at = request.POST.get(f'published_at_{i}', '').strip()
                doi = request.POST.get(f'doi_{i}', '').strip()
                link = request.POST.get(f'link_{i}', '').strip()
                contribution = request.POST.get(f'contribution_{i}', '').strip()
                
                # Skip if not confirmed
                if not request.POST.get(f'confirm_{i}', ''):
                    i += 1
                    continue
                
                # Validate required fields
                if not pub_year:
                    errors.append(f'Publication {i+1}: Year is required.')
                    i += 1
                    continue
                
                try:
                    pub_year = int(pub_year)
                    if pub_year < 1900 or pub_year > 2100:
                        raise ValueError()
                except ValueError:
                    errors.append(f'Publication {i+1}: Please enter a valid year between 1900 and 2100.')
                    i += 1
                    continue
                
                # Type is optional, but if provided, must be valid
                if type_val and type_val not in dict(Publication.TYPE_CHOICES):
                    errors.append(f'Publication {i+1}: Please select a valid publication type.')
                    i += 1
                    continue
                
                if not ranking or ranking not in dict(Publication.RANKING_CHOICES):
                    errors.append(f'Publication {i+1}: Please select a valid ranking.')
                    i += 1
                    continue
                
                # Check for duplicate by title (case-insensitive)
                existing = Publication.objects.filter(
                    faculty=faculty,
                    title__iexact=title
                ).first()
                
                if existing:
                    errors.append(f'Publication {i+1}: A publication with this title already exists.')
                    i += 1
                    continue
                
                # Create publication
                try:
                    Publication.objects.create(
                        faculty=faculty,
                        title=title,
                        pub_year=pub_year,
                        type=type_val if type_val else None,
                        ranking=ranking,
                        link=link if link else None,
                        doi=doi if doi else None,
                        published_at=published_at if published_at else None,
                        contribution=contribution if contribution else None,
                    )
                    created_count += 1
                except Exception as e:
                    errors.append(f'Publication {i+1}: Error creating publication - {str(e)}')
                
                i += 1
            
            if created_count > 0:
                messages.success(request, f'Successfully imported {created_count} publication(s).')
            if errors:
                for error in errors:
                    messages.error(request, error)
            
            return redirect('people:manage_publications', faculty_id=faculty_id)
        
        # Parse the pasted text
        pasted_text = request.POST.get('pasted_text', '').strip()
        
        if not pasted_text:
            messages.error(request, 'Please paste the publication data.')
            return redirect('people:bulk_import_publications', faculty_id=faculty_id)
        
        # Parse the text - supports two formats:
        # Format 1: Clean Google Scholar format (Title, Authors, Venue, Year)
        # Format 2: Noisy format with metadata (Title, metadata, Q ranking, Year)
        
        parsed_publications = []
        lines = pasted_text.split('\n')
        
        # Remove empty lines and strip whitespace, keep track of original line numbers
        non_empty_lines = []
        original_line_nums = []
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if stripped:
                non_empty_lines.append(stripped)
                original_line_nums.append(i)
        
        # Detect format type
        is_format_2 = _detect_format_2(non_empty_lines)
        
        if is_format_2:
            # Format 2: Noisy format with metadata
            parsed_publications = _parse_format_2(non_empty_lines, original_line_nums)
        else:
            # Format 1: Clean Google Scholar format
            # Line 1: Title
            # Line 2: Authors (ignore)
            # Line 3: Venue (ignore)
            # Line 4: Citations Year (extract year using 20\d{2})
            # Strategy: Find lines with year pattern (20\d{2}), title is 3 lines before
            
            # Common header keywords to skip
            header_keywords = ['title', 'cited', 'year', 'author', 'publication', 'venue', 'journal']
            
            # Iterate through lines looking for year pattern (20\d{2})
            for i, line in enumerate(non_empty_lines):
                # Skip header rows
                line_lower = line.lower()
                is_header = False
                for keyword in header_keywords:
                    if keyword in line_lower and len(line) < 30:
                        is_header = True
                        break
                if is_header:
                    continue
                
                # Look for year pattern in this line (20\d{2})
                year_match = re.search(r'20\d{2}', line)
                if year_match:
                    year_str = year_match.group()
                    try:
                        year = int(year_str)
                        if 2000 <= year <= 2100:  # Valid year range
                            # Title is 3 lines before the year line
                            title_index = i - 3
                            
                            if title_index >= 0 and title_index < len(non_empty_lines):
                                title = non_empty_lines[title_index].strip()
                                
                                # Skip if title looks like a header
                                title_lower = title.lower()
                                is_title_header = False
                                for keyword in header_keywords:
                                    if keyword in title_lower and len(title) < 30:
                                        is_title_header = True
                                        break
                                
                                # Validate title (should be meaningful, not too short)
                                if not is_title_header and len(title) >= 10:
                                    parsed_publications.append({
                                        'title': title,
                                        'authors': None,
                                        'venue': None,
                                        'cited': None,
                                        'year': str(year),
                                        'line_num': original_line_nums[i],
                                    })
                    except ValueError:
                        continue
        
        if not parsed_publications:
            messages.error(request, 'No publications could be parsed from the pasted text. Please check the format.')
            return redirect('people:bulk_import_publications', faculty_id=faculty_id)
        
        # Check for duplicates and mark them
        existing_titles = set(
            Publication.objects.filter(faculty=faculty)
            .values_list('title', flat=True)
        )
        
        for pub in parsed_publications:
            pub['is_duplicate'] = pub['title'].lower() in [t.lower() for t in existing_titles]
        
        context = {
            'faculty': faculty,
            'parsed_publications': parsed_publications,
            'type_choices': Publication.TYPE_CHOICES,
            'ranking_choices': Publication.RANKING_CHOICES,
        }
        
        return render(request, 'people/bulk_import_confirm.html', context)
    
    # GET request - show the paste form
    context = {
        'faculty': faculty,
    }
    
    return render(request, 'people/bulk_import_publications.html', context)


@login_required
@transaction.atomic
def edit_publication(request, publication_id):
    """
    Edit a publication.
    Accessible to the faculty member themselves or users with manage_all_publications permission.
    """
    from people.permissions import Permissions
    
    publication = get_object_or_404(Publication, pk=publication_id)
    faculty = publication.faculty
    
    # Check permissions - allow if user is the faculty member OR power user OR has manage_all_publications permission
    can_manage = False
    if hasattr(request.user, 'faculty_profile') and request.user.faculty_profile.pk == faculty.pk:
        can_manage = True
    elif request.user.is_power_user or request.user.has_permission(Permissions.MANAGE_ALL_PUBLICATIONS):
        can_manage = True
    
    if not can_manage:
        messages.error(request, 'You do not have permission to edit publications for this faculty member.')
        return redirect('people:user_profile')
    
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        pub_year = request.POST.get('pub_year', '').strip()
        type = request.POST.get('type', '').strip()
        ranking = request.POST.get('ranking', '').strip()
        link = request.POST.get('link', '').strip()
        doi = request.POST.get('doi', '').strip()
        published_at = request.POST.get('published_at', '').strip()
        contribution = request.POST.get('contribution', '').strip()
        
        # Validation
        if not title:
            messages.error(request, 'Title is required.')
            return redirect('people:edit_publication', publication_id=publication_id)
        
        if not pub_year:
            messages.error(request, 'Publication year is required.')
            return redirect('people:edit_publication', publication_id=publication_id)
        
        try:
            pub_year = int(pub_year)
            if pub_year < 1900 or pub_year > 2100:
                raise ValueError()
        except ValueError:
            messages.error(request, 'Please enter a valid year between 1900 and 2100.')
            return redirect('people:edit_publication', publication_id=publication_id)
        
        # Type is optional, but if provided, must be valid
        if type and type not in dict(Publication.TYPE_CHOICES):
            messages.error(request, 'Please select a valid publication type.')
            return redirect('people:edit_publication', publication_id=publication_id)
        
        if not ranking or ranking not in dict(Publication.RANKING_CHOICES):
            messages.error(request, 'Please select a valid ranking.')
            return redirect('people:edit_publication', publication_id=publication_id)
        
        # Update publication
        publication.title = title
        publication.pub_year = pub_year
        publication.type = type if type else None
        publication.ranking = ranking
        publication.link = link if link else None
        publication.doi = doi if doi else None
        publication.published_at = published_at if published_at else None
        publication.contribution = contribution if contribution else None
        publication.save()
        
        messages.success(request, f'Publication "{title}" updated successfully.')
        return redirect('people:manage_publications', faculty_id=faculty.pk)
    
    context = {
        'publication': publication,
        'faculty': faculty,
        'type_choices': Publication.TYPE_CHOICES,
        'ranking_choices': Publication.RANKING_CHOICES,
    }
    
    return render(request, 'people/edit_publication.html', context)


@login_required
@transaction.atomic
def delete_publication(request, publication_id):
    """
    Delete a publication.
    Accessible to the faculty member themselves or users with manage_all_publications permission.
    """
    from people.permissions import Permissions
    
    publication = get_object_or_404(Publication, pk=publication_id)
    faculty = publication.faculty
    
    # Check permissions - allow if user is the faculty member OR power user OR has manage_all_publications permission
    can_manage = False
    if hasattr(request.user, 'faculty_profile') and request.user.faculty_profile.pk == faculty.pk:
        can_manage = True
    elif request.user.is_power_user or request.user.has_permission(Permissions.MANAGE_ALL_PUBLICATIONS):
        can_manage = True
    
    if not can_manage:
        messages.error(request, 'You do not have permission to delete publications for this faculty member.')
        return redirect('people:user_profile')
    
    if request.method == 'POST':
        title = publication.title
        publication.delete()
        messages.success(request, f'Publication "{title}" deleted successfully.')
        return redirect('people:manage_publications', faculty_id=faculty.pk)
    
    context = {
        'publication': publication,
        'faculty': faculty,
    }
    
    return render(request, 'people/delete_publication.html', context)


@login_required
@require_http_methods(["POST"])
@transaction.atomic
def bulk_delete_publications(request, faculty_id):
    """
    Bulk delete publications.
    Accessible to the faculty member themselves or users with manage_all_publications permission.
    """
    from people.permissions import Permissions
    from django.http import JsonResponse
    import json
    
    faculty = get_object_or_404(Faculty, pk=faculty_id)
    
    # Check permissions - allow if user is the faculty member OR power user OR has manage_all_publications permission
    can_manage = False
    if hasattr(request.user, 'faculty_profile') and request.user.faculty_profile.pk == faculty.pk:
        can_manage = True
    elif request.user.is_power_user or request.user.has_permission(Permissions.MANAGE_ALL_PUBLICATIONS):
        can_manage = True
    
    if not can_manage:
        return JsonResponse({
            'success': False,
            'message': 'You do not have permission to delete publications for this faculty member.'
        }, status=403)
    
    try:
        data = json.loads(request.body)
        publication_ids = data.get('publication_ids', [])
        
        if not publication_ids:
            return JsonResponse({
                'success': False,
                'message': 'No publications selected for deletion.'
            }, status=400)
        
        # Get publications to delete - ensure they belong to this faculty
        publications_to_delete = Publication.objects.filter(
            pk__in=publication_ids,
            faculty=faculty
        )
        
        if publications_to_delete.count() != len(publication_ids):
            return JsonResponse({
                'success': False,
                'message': 'Some publication IDs do not exist or do not belong to this faculty.'
            }, status=400)
        
        # Get titles for response
        publication_titles = [pub.title for pub in publications_to_delete]
        deleted_count = publications_to_delete.count()
        
        # Delete publications
        publications_to_delete.delete()
        
        return JsonResponse({
            'success': True,
            'message': f'Successfully deleted {deleted_count} publication(s).',
            'deleted_count': deleted_count
        })
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': 'Invalid request data.'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error deleting publications: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["POST"])
def confirm_single_publication(request, faculty_id):
    """
    AJAX endpoint to confirm and save a single publication from bulk import.
    Accessible to the faculty member themselves or users with manage_all_publications permission.
    """
    from people.permissions import Permissions
    
    faculty = get_object_or_404(Faculty, pk=faculty_id)
    
    # Check permissions - allow if user is the faculty member OR power user OR has manage_all_publications permission
    can_manage = False
    if hasattr(request.user, 'faculty_profile') and request.user.faculty_profile.pk == faculty.pk:
        can_manage = True
    elif request.user.is_power_user or request.user.has_permission(Permissions.MANAGE_ALL_PUBLICATIONS):
        can_manage = True
    
    if not can_manage:
        return JsonResponse({'success': False, 'error': 'Permission denied'}, status=403)
    
    try:
        title = request.POST.get('title', '').strip()
        pub_year = request.POST.get('pub_year', '').strip()
        type_val = request.POST.get('type', '').strip()
        ranking = request.POST.get('ranking', '').strip()
        published_at = request.POST.get('published_at', '').strip()
        doi = request.POST.get('doi', '').strip()
        link = request.POST.get('link', '').strip()
        contribution = request.POST.get('contribution', '').strip()
        
        # Validate required fields
        if not title:
            return JsonResponse({'success': False, 'error': 'Title is required'}, status=400)
        
        if not pub_year:
            return JsonResponse({'success': False, 'error': 'Year is required'}, status=400)
        
        try:
            pub_year = int(pub_year)
            if pub_year < 1900 or pub_year > 2100:
                raise ValueError()
        except ValueError:
            return JsonResponse({'success': False, 'error': 'Please enter a valid year between 1900 and 2100'}, status=400)
        
        # Type is optional, but if provided, must be valid
        if type_val and type_val not in dict(Publication.TYPE_CHOICES):
            return JsonResponse({'success': False, 'error': 'Please select a valid publication type'}, status=400)
        
        if not ranking or ranking not in dict(Publication.RANKING_CHOICES):
            return JsonResponse({'success': False, 'error': 'Please select a valid ranking'}, status=400)
        
        # Check for duplicate by title (case-insensitive)
        existing = Publication.objects.filter(
            faculty=faculty,
            title__iexact=title
        ).first()
        
        if existing:
            return JsonResponse({'success': False, 'error': 'A publication with this title already exists', 'is_duplicate': True}, status=400)
        
        # Create publication
        publication = Publication.objects.create(
            faculty=faculty,
            title=title,
            pub_year=pub_year,
            type=type_val if type_val else None,
            ranking=ranking,
            link=link if link else None,
            doi=doi if doi else None,
            published_at=published_at if published_at else None,
            contribution=contribution if contribution else None,
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Publication added successfully',
            'publication_id': publication.id
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


def departmental_research(request):
    """
    Display departmental research page with all publications from current faculty.
    Shows statistics, faculty-wise scores, and publications table.
    Excludes faculty on leave and former faculty.
    """
    from django.db.models import Count, Sum, Q, Avg, Min, Max
    from datetime import datetime
    from collections import defaultdict
    
    # Get current faculty (not on leave, not former)
    current_faculty = Faculty.objects.filter(
        last_office_date__isnull=True,
        is_on_study_leave=False
    ).select_related('base_user')
    
    # Get filters
    period = request.GET.get('period', 'all_time')
    pub_type = request.GET.get('type', 'all')
    ranking_filter = request.GET.get('ranking', 'all')
    year_from = request.GET.get('year_from', '')
    year_to = request.GET.get('year_to', '')
    sort_by = request.GET.get('sort', 'year_desc')
    
    current_year = datetime.now().year
    
    # Filter publications
    publications = Publication.objects.filter(faculty__in=current_faculty)
    
    # Apply time period filter
    if period == 'current_year':
        publications = publications.filter(pub_year=current_year)
    elif period == 'last_2_years':
        publications = publications.filter(pub_year__gte=current_year - 1)
    elif period == 'custom':
        if year_from:
            try:
                year_from_int = int(year_from)
                publications = publications.filter(pub_year__gte=year_from_int)
            except ValueError:
                pass
        if year_to:
            try:
                year_to_int = int(year_to)
                publications = publications.filter(pub_year__lte=year_to_int)
            except ValueError:
                pass
    
    # Apply type filter
    if pub_type != 'all':
        publications = publications.filter(type=pub_type)
    
    # Apply ranking filter
    if ranking_filter != 'all':
        publications = publications.filter(ranking=ranking_filter)
    
    # Sort publications
    if sort_by == 'year_desc':
        publications = publications.order_by('-pub_year', 'title')
    elif sort_by == 'year_asc':
        publications = publications.order_by('pub_year', 'title')
    elif sort_by == 'title_asc':
        publications = publications.order_by('title', '-pub_year')
    elif sort_by == 'title_desc':
        publications = publications.order_by('-title', '-pub_year')
    
    publications = publications.select_related('faculty')
    
    # Scoring system
    SCORING = {
        'q1': 10,
        'q2': 7,
        'q3': 5,
        'q4': 3,
        'a_star': 8,
        'a': 6,
        'b': 4,
        'c': 2,
        'wos_scopus_indexed': 2,
        'not_indexed': 1,
    }
    
    # Calculate statistics
    total_pubs = publications.count()
    
    # Count by ranking
    stats_by_ranking = {}
    for ranking_code, ranking_label in Publication.RANKING_CHOICES:
        count = publications.filter(ranking=ranking_code).count()
        stats_by_ranking[ranking_code] = {
            'label': ranking_label,
            'count': count,
            'score': count * SCORING.get(ranking_code, 0)
        }
    
    # Total citations (sum of faculty citations)
    total_citations = current_faculty.aggregate(
        total=Sum('citation')
    )['total'] or 0
    
    # Average publications per faculty
    num_faculty = current_faculty.count()
    avg_pubs_per_faculty = round(total_pubs / num_faculty, 2) if num_faculty > 0 else 0
    
    # Average citations per faculty
    avg_citations_per_faculty = round(total_citations / num_faculty, 2) if num_faculty > 0 else 0
    
    # Statistics by publication type
    stats_by_type = {}
    for type_code, type_label in Publication.TYPE_CHOICES:
        count = publications.filter(type=type_code).count()
        stats_by_type[type_code] = {
            'label': type_label,
            'count': count,
        }
    
    # Statistics by year (for line chart)
    if publications.exists():
        min_year = publications.aggregate(Min('pub_year'))['pub_year__min']
        max_year = publications.aggregate(Max('pub_year'))['pub_year__max']
    else:
        min_year = current_year - 5
        max_year = current_year
    
    # Create year-by-year data
    publications_by_year = []
    for year in range(min_year, max_year + 1):
        count = publications.filter(pub_year=year).count()
        publications_by_year.append({
            'year': year,
            'count': count,
        })
    
    # Calculate faculty-wise scores
    faculty_scores = []
    for faculty in current_faculty:
        faculty_pubs = publications.filter(faculty=faculty)
        pub_count = faculty_pubs.count()
        
        # Calculate score
        score = 0
        pub_years = []
        for pub in faculty_pubs:
            score += SCORING.get(pub.ranking, 0)
            pub_years.append(pub.pub_year)
        
        # Calculate publication year span (for tie-breaking)
        # Smaller span = more concentrated publications = better
        year_span = 0
        if pub_years:
            faculty_min_year = min(pub_years)
            faculty_max_year = max(pub_years)
            year_span = faculty_max_year - faculty_min_year if faculty_max_year != faculty_min_year else 0
        
        faculty_scores.append({
            'faculty': faculty,
            'publication_count': pub_count,
            'score': score,
            'citations': faculty.citation or 0,
            'year_span': year_span,  # For tie-breaking
        })
    
    # Sort faculty by SL (serial number) for "All Faculties" tab to match faculty list page
    # Add SL to each item and sort by SL first, then by score
    for item in faculty_scores:
        item['sl'] = item['faculty'].sl if item['faculty'].sl else 999
    
    # Sort by SL first, then by score (for "All Faculties" tab)
    faculty_scores.sort(key=lambda x: (x['sl'], -x['score'], x['year_span']))
    
    # ===== SECTION 1: Most Cited Researchers (All Time) =====
    # Rank strictly by total citation count (descending)
    most_cited = []
    for faculty in current_faculty:
        most_cited.append({
            'faculty': faculty,
            'citations': faculty.citation or 0,
            'score': 0,  # Not used for this ranking
            'publication_count': 0,  # Not used for this ranking
        })
    # Sort by citations (descending)
    most_cited.sort(key=lambda x: -x['citations'])
    most_cited_researchers = most_cited[:4]  # Top 4
    
    # Get set of top 4 most cited faculty IDs for badge checking
    top_4_most_cited_ids = {item['faculty'].pk for item in most_cited_researchers}
    
    # ===== SECTION 2: Leading Active Researchers (Past 2yr) =====
    # Consider only the last 2 years of research data
    recent_publications = Publication.objects.filter(
        faculty__in=current_faculty,
        pub_year__gte=current_year - 1
    ).select_related('faculty')
    
    # Calculate scores for last 2 years only
    recent_faculty_scores = []
    for faculty in current_faculty:
        faculty_recent_pubs = recent_publications.filter(faculty=faculty)
        pub_count = faculty_recent_pubs.count()
        
        # Calculate score for recent publications only
        score = 0
        for pub in faculty_recent_pubs:
            score += SCORING.get(pub.ranking, 0)
        
        recent_faculty_scores.append({
            'faculty': faculty,
            'publication_count': pub_count,
            'score': score,
            'citations': faculty.citation or 0,  # For display only
        })
    
    # Sort by score only (highest first)
    recent_faculty_scores.sort(key=lambda x: -x['score'])
    leading_active_researchers = recent_faculty_scores[:4]  # Top 4
    
    # Get set of top 4 leading active faculty IDs for badge checking
    top_4_leading_active_ids = {item['faculty'].pk for item in leading_active_researchers}
    
    # ===== SECTION 3: Top Researchers (Designation Wise) =====
    # Get top researcher from each designation using existing ranking logic
    top_by_designation = {}
    designations = ['Professor', 'Associate Professor', 'Assistant Professor', 'Lecturer']
    
    for designation in designations:
        designation_faculty = [item for item in faculty_scores if item['faculty'].designation == designation]
        # Get only the top 1 (best researcher in this designation)
        if designation_faculty:
            top_by_designation[designation] = designation_faculty[0]
        else:
            top_by_designation[designation] = None
    
    # Convert to list format for template (only include non-None entries)
    top_researchers_designation_wise = [
        top_by_designation[designation] 
        for designation in designations 
        if top_by_designation[designation] is not None
    ]
    
    # Get set of top by designation faculty IDs for badge checking
    top_by_designation_ids = {item['faculty'].pk for item in top_researchers_designation_wise}
    
    # Add badge information to faculty_scores for "All Faculties" tab
    for item in faculty_scores:
        faculty_id = item['faculty'].pk
        badges = []
        if faculty_id in top_4_most_cited_ids:
            badges.append('most_cited')
        if faculty_id in top_4_leading_active_ids:
            badges.append('leading_active')
        if faculty_id in top_by_designation_ids:
            badges.append('top_designation')
        item['badges'] = badges
    
    # Create sorted lists for Most Cited and Leading Active tabs (all faculty, not just top 4)
    # Most Cited - all faculty sorted by citations
    all_faculty_most_cited = []
    for item in faculty_scores:
        all_faculty_most_cited.append({
            'faculty': item['faculty'],
            'citations': item['citations'],
            'score': item['score'],
            'publication_count': item['publication_count'],
            'is_top_4': item['faculty'].pk in top_4_most_cited_ids,
        })
    all_faculty_most_cited.sort(key=lambda x: -x['citations'])
    
    # Leading Active - all faculty sorted by recent score
    all_faculty_leading_active = []
    for item in recent_faculty_scores:
        all_faculty_leading_active.append({
            'faculty': item['faculty'],
            'citations': item['citations'],
            'score': item['score'],
            'publication_count': item['publication_count'],
            'is_top_4': item['faculty'].pk in top_4_leading_active_ids,
        })
    all_faculty_leading_active.sort(key=lambda x: -x['score'])
    
    # Top by Designation - create two separate lists:
    # 1. Most cited in (sorted by citations)
    # 2. Most active in (sorted by score)
    all_faculty_most_cited_by_designation = []
    all_faculty_most_active_by_designation = []
    designations_order = ['Professor', 'Associate Professor', 'Assistant Professor', 'Lecturer']
    
    for designation in designations_order:
        designation_faculty = [item for item in faculty_scores if item['faculty'].designation == designation]
        
        # Most cited - sorted by citations (descending)
        designation_faculty_cited = sorted(designation_faculty, key=lambda x: (-x['citations'], -x['score']))
        top_cited_value = designation_faculty_cited[0]['citations'] if designation_faculty_cited else 0
        for item in designation_faculty_cited:
            all_faculty_most_cited_by_designation.append({
                'faculty': item['faculty'],
                'citations': item['citations'],
                'score': item['score'],
                'publication_count': item['publication_count'],
                'designation': designation,
                'is_top_1_cited': item['citations'] == top_cited_value and top_cited_value > 0,
            })
        
        # Most active - sorted by score (descending)
        designation_faculty_active = sorted(designation_faculty, key=lambda x: (-x['score'], -x['citations']))
        top_active_value = designation_faculty_active[0]['score'] if designation_faculty_active else 0
        for item in designation_faculty_active:
            all_faculty_most_active_by_designation.append({
                'faculty': item['faculty'],
                'citations': item['citations'],
                'score': item['score'],
                'publication_count': item['publication_count'],
                'designation': designation,
                'is_top_1_active': item['score'] == top_active_value and top_active_value > 0,
            })
    
    # Keep old variable for backward compatibility but use new structure
    all_faculty_designation_wise = all_faculty_most_active_by_designation
    
    context = {
        'publications': publications,
        'current_faculty': current_faculty,
        'period': period,
        'current_year': current_year,
        'total_pubs': total_pubs,
        'stats_by_ranking': stats_by_ranking,
        'stats_by_type': stats_by_type,
        'total_citations': total_citations,
        'avg_pubs_per_faculty': avg_pubs_per_faculty,
        'avg_citations_per_faculty': avg_citations_per_faculty,
        'publications_by_year': publications_by_year,
        'faculty_scores': faculty_scores,
        'num_faculty': num_faculty,
        'ranking_choices': dict(Publication.RANKING_CHOICES),
        'type_choices': dict(Publication.TYPE_CHOICES),
        'most_cited_researchers': most_cited_researchers,
        'leading_active_researchers': leading_active_researchers,
        'top_researchers_designation_wise': top_researchers_designation_wise,
        'all_faculty_most_cited': all_faculty_most_cited,
        'all_faculty_leading_active': all_faculty_leading_active,
        'all_faculty_designation_wise': all_faculty_designation_wise,
        'all_faculty_most_cited_by_designation': all_faculty_most_cited_by_designation,
        'all_faculty_most_active_by_designation': all_faculty_most_active_by_designation,
        'scoring_system': SCORING,
        'pub_type': pub_type,
        'ranking_filter': ranking_filter,
        'year_from': year_from,
        'year_to': year_to,
        'sort_by': sort_by,
        'min_year': min_year if publications.exists() else current_year - 10,
        'max_year': max_year if publications.exists() else current_year,
    }
    
    return render(request, 'people/departmental_research.html', context)


# ==============================================================================
# PERMISSION OBJECTS MANAGEMENT (Power Users Only)
# ==============================================================================

@login_required
def manage_permissions(request):
    """Manage Permission objects - CRUD operations for power users"""
    if not request.user.is_power_user:
        messages.error(request, 'Only power users can manage permission objects.')
        return redirect('people:user_profile')
    
    # Get filters
    search_query = request.GET.get('search', '').strip()
    category_filter = request.GET.get('category', 'all')
    
    # Get all permissions
    permissions = Permission.objects.all()
    
    # Filter by category
    if category_filter != 'all':
        permissions = permissions.filter(category=category_filter)
    
    # Filter by search query
    if search_query:
        permissions = permissions.filter(
            Q(codename__icontains=search_query) |
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query)
        )
    
    # Order by category, priority, name
    permissions = permissions.order_by('category', 'priority', 'name')
    
    # Get category choices
    category_choices = [
        ('all', 'All Categories'),
        ('office', 'Office'),
        ('clubs', 'Clubs'),
        ('designs', 'Designs'),
        ('users', 'User Management'),
        ('academics', 'Academics'),
    ]
    
    context = {
        'permissions': permissions,
        'search_query': search_query,
        'category_filter': category_filter,
        'category_choices': category_choices,
    }
    
    return render(request, 'people/manage_permissions.html', context)


@login_required
def create_permission(request):
    """Create a new Permission object"""
    if not request.user.is_power_user:
        messages.error(request, 'Only power users can create permission objects.')
        return redirect('people:user_profile')
    
    if request.method == 'POST':
        try:
            permission = Permission()
            permission.codename = request.POST.get('codename', '').strip()
            permission.name = request.POST.get('name', '').strip()
            permission.description = request.POST.get('description', '').strip()
            permission.category = request.POST.get('category', '').strip() or None
            
            # Handle requires_role (JSON field)
            requires_role_str = request.POST.get('requires_role', '').strip()
            if requires_role_str:
                # Split by comma and clean
                roles = [r.strip() for r in requires_role_str.split(',') if r.strip()]
                permission.requires_role = roles
            else:
                permission.requires_role = []
            
            # Handle priority
            priority_str = request.POST.get('priority', '100').strip()
            if priority_str:
                permission.priority = int(priority_str)
            else:
                permission.priority = 100
            
            permission.is_active = request.POST.get('is_active') == 'on'
            
            permission.full_clean()
            permission.save()
            
            messages.success(request, f'Permission "{permission.name}" created successfully!')
            return redirect('people:manage_permissions')
        except Exception as e:
            messages.error(request, f'Error creating permission: {str(e)}')
            return render(request, 'people/create_permission.html', {
                'permission_data': request.POST,
                'category_choices': Permission.CATEGORY_CHOICES,
            })
    
    context = {
        'category_choices': Permission.CATEGORY_CHOICES,
    }
    return render(request, 'people/create_permission.html', context)


@login_required
def edit_permission(request, pk):
    """Edit an existing Permission object"""
    if not request.user.is_power_user:
        messages.error(request, 'Only power users can edit permission objects.')
        return redirect('people:user_profile')
    
    permission = get_object_or_404(Permission, pk=pk)
    
    if request.method == 'POST':
        try:
            permission.codename = request.POST.get('codename', '').strip()
            permission.name = request.POST.get('name', '').strip()
            permission.description = request.POST.get('description', '').strip()
            permission.category = request.POST.get('category', '').strip() or None
            
            # Handle requires_role (JSON field)
            requires_role_str = request.POST.get('requires_role', '').strip()
            if requires_role_str:
                roles = [r.strip() for r in requires_role_str.split(',') if r.strip()]
                permission.requires_role = roles
            else:
                permission.requires_role = []
            
            # Handle priority
            priority_str = request.POST.get('priority', '100').strip()
            if priority_str:
                permission.priority = int(priority_str)
            
            permission.is_active = request.POST.get('is_active') == 'on'
            
            permission.full_clean()
            permission.save()
            
            messages.success(request, f'Permission "{permission.name}" updated successfully!')
            return redirect('people:manage_permissions')
        except Exception as e:
            messages.error(request, f'Error updating permission: {str(e)}')
    
    context = {
        'permission': permission,
        'category_choices': Permission.CATEGORY_CHOICES,
    }
    return render(request, 'people/edit_permission.html', context)


@login_required
def delete_permission(request, pk):
    """Delete a Permission object"""
    if not request.user.is_power_user:
        messages.error(request, 'Only power users can delete permission objects.')
        return redirect('people:user_profile')
    
    permission = get_object_or_404(Permission, pk=pk)
    
    # Check if permission is in use
    user_permissions_count = UserPermission.objects.filter(permission=permission, is_active=True).count()
    
    if request.method == 'POST':
        name = permission.name
        permission.delete()
        messages.success(request, f'Permission "{name}" deleted successfully!')
        return redirect('people:manage_permissions')
    
    context = {
        'permission': permission,
        'user_permissions_count': user_permissions_count,
    }
    return render(request, 'people/delete_permission.html', context)
