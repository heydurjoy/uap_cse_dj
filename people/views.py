from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate
from django.contrib import messages
from django.db import transaction, models
from django.utils import timezone
from django.db.models import Q, Max
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from .models import Faculty, Staff, Officer, ClubMember, BaseUser, Permission, UserPermission, AllowedEmail


def faculty_list(request):
    """
    Display list of all faculties, sorted by designation first, then by sl.
    Separates former faculty (with last_office_date) from active faculty.
    """
    # Get all faculties
    all_faculties = Faculty.objects.all()
    
    # Define designation order for sorting
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
    
    # Sort active faculties: first by is_head (heads first), then by designation, then by sl
    sorted_active = sorted(
        faculties_active,
        key=lambda f: (
            0 if f.is_head else 1,  # Heads first (0 < 1)
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
    
    # Combine: active first, then those on leave, then former
    sorted_faculties = sorted_active + sorted_on_leave
    
    # Group active faculties by designation for display
    faculties_by_designation = {}
    for faculty in sorted_faculties:
        # If head, create a special "Head of the Department" group
        if faculty.is_head:
            designation = 'Head of the Department'
        elif faculty.is_on_study_leave:
            designation = 'Faculty on Study Leave'
        else:
            designation = faculty.designation or 'Other'
        
        if designation not in faculties_by_designation:
            faculties_by_designation[designation] = []
        faculties_by_designation[designation].append(faculty)
    
    # Group former faculties by designation
    former_faculties_by_designation = {}
    for faculty in sorted_former:
        # Former faculty can also be heads, but we'll show them in their designation group
        designation = faculty.designation or 'Other'
        
        if designation not in former_faculties_by_designation:
            former_faculties_by_designation[designation] = []
        former_faculties_by_designation[designation].append(faculty)
    
    context = {
        'faculties': sorted_faculties,
        'faculties_by_designation': faculties_by_designation,
        'former_faculties': sorted_former,
        'former_faculties_by_designation': former_faculties_by_designation,
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
    
    context = {
        'faculty': faculty,
        'service_data': service_data,
    }
    
    return render(request, 'people/faculty_detail.html', context)


def club_member_detail(request, pk):
    """
    Display detailed view of a single club member.
    """
    from .models import ClubMember
    from clubs.models import ClubPosition, Club
    
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
def edit_profile(request):
    """
    Allow users to edit their own profile information.
    Excludes: user_type, sl (serial number), permissions (managed separately)
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
                if 'profile_picture' in request.FILES:
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
                    if 'google_scholar_url' in request.POST:
                        profile.google_scholar_url = request.POST.get('google_scholar_url', '').strip() or None
                    if 'researchgate_url' in request.POST:
                        profile.researchgate_url = request.POST.get('researchgate_url', '').strip() or None
                    if 'orcid_url' in request.POST:
                        profile.orcid_url = request.POST.get('orcid_url', '').strip() or None
                    if 'scopus_url' in request.POST:
                        profile.scopus_url = request.POST.get('scopus_url', '').strip() or None
                    if 'linkedin_url' in request.POST:
                        profile.linkedin_url = request.POST.get('linkedin_url', '').strip() or None
                    if 'researches' in request.POST:
                        researches_content = request.POST.get('researches', '').strip()
                        profile.researches = researches_content if researches_content else None
                    if 'routine' in request.POST:
                        routine_content = request.POST.get('routine', '').strip()
                        profile.routine = routine_content if routine_content else None
                    if 'profile_pic' in request.FILES:
                        profile.profile_pic = request.FILES['profile_pic']
                    if 'cropping' in request.POST:
                        profile.cropping = request.POST.get('cropping', '').strip()
                    
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
    
    # Get user's current permissions
    user_permissions = UserPermission.objects.filter(
        user=target_user,
        is_active=True
    ).select_related('permission', 'granted_by')
    user_permission_codenames = set(up.permission.codename for up in user_permissions)
    
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
                
                # Grant new permissions
                for perm_codename in selected_permission_set:
                    if perm_codename not in user_permission_codenames:
                        # Check if permission exists and is active
                        try:
                            permission = Permission.objects.get(codename=perm_codename, is_active=True)
                            
                            # Check role requirements
                            if permission.requires_role:
                                if not target_user.user_type or target_user.user_type not in permission.requires_role:
                                    messages.warning(
                                        request,
                                        f'Permission "{permission.name}" requires role: {", ".join(permission.requires_role)}. '
                                        f'User has role: {target_user.user_type or "None"}. Skipping.'
                                    )
                                    continue
                            
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
            return redirect('people:manage_user_permissions_list?tab=allowed_emails')
            
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
            return redirect('people:manage_user_permissions_list?tab=allowed_emails')
            
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
def bulk_delete_allowed_emails(request):
    """
    Delete multiple allowed emails at once.
    Only accessible to power users.
    """
    if not request.user.is_power_user:
        return JsonResponse({
            'success': False,
            'message': 'You do not have permission to delete allowed emails.'
        }, status=403)
    
    email_ids = request.POST.getlist('email_ids[]')
    
    if not email_ids:
        return JsonResponse({
            'success': False,
            'message': 'No emails selected for deletion.'
        })
    
    try:
        # Get allowed emails to delete
        emails_to_delete = AllowedEmail.objects.filter(pk__in=email_ids)
        deleted_count = emails_to_delete.count()
        email_addresses = [email.email for email in emails_to_delete]
        
        # Check if any have associated BaseUser accounts
        emails_with_accounts = []
        emails_with_posts = []
        
        for email in emails_to_delete:
            if email.base_user:
                emails_with_accounts.append(email.email)
                # Check if this user has created any club posts
                from clubs.models import ClubPost
                post_count = ClubPost.objects.filter(posted_by=email.base_user).count()
                if post_count > 0:
                    emails_with_posts.append(f"{email.email} ({post_count} post{'s' if post_count > 1 else ''})")
        
        if emails_with_accounts:
            if emails_with_posts:
                return JsonResponse({
                    'success': False,
                    'message': f'Cannot delete emails with active accounts that have created posts: {", ".join(emails_with_posts)}. Please delete or reassign the posts first, or delete the user accounts directly.'
                }, status=400)
            else:
                return JsonResponse({
                    'success': False,
                    'message': f'Cannot delete emails with active accounts: {", ".join(emails_with_accounts)}. Please delete the user accounts first.'
                }, status=400)
        
        # Delete the allowed emails
        emails_to_delete.delete()
        
        return JsonResponse({
            'success': True,
            'message': f'Successfully deleted {deleted_count} allowed email(s).',
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
            
            # Update profile picture if provided
            if 'profile_pic' in request.FILES:
                faculty.profile_pic = request.FILES['profile_pic']
            
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
            
            # Update research links
            faculty.google_scholar_url = request.POST.get('google_scholar_url', '').strip() or None
            faculty.researchgate_url = request.POST.get('researchgate_url', '').strip() or None
            faculty.orcid_url = request.POST.get('orcid_url', '').strip() or None
            faculty.scopus_url = request.POST.get('scopus_url', '').strip() or None
            faculty.linkedin_url = request.POST.get('linkedin_url', '').strip() or None
            
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
            faculty.is_head = request.POST.get('is_head') == 'on'
            faculty.is_dept_proctor = request.POST.get('is_dept_proctor') == 'on'
            faculty.is_bsc_admission_coordinator = request.POST.get('is_bsc_admission_coordinator') == 'on'
            faculty.is_mcse_admission_coordinator = request.POST.get('is_mcse_admission_coordinator') == 'on'
            faculty.is_on_study_leave = request.POST.get('is_on_study_leave') == 'on'
            
            # Update CV if provided
            if 'cv' in request.FILES:
                faculty.cv = request.FILES['cv']
            
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
            
            # Update research links
            faculty.google_scholar_url = request.POST.get('google_scholar_url', '').strip() or None
            faculty.researchgate_url = request.POST.get('researchgate_url', '').strip() or None
            faculty.orcid_url = request.POST.get('orcid_url', '').strip() or None
            faculty.scopus_url = request.POST.get('scopus_url', '').strip() or None
            faculty.linkedin_url = request.POST.get('linkedin_url', '').strip() or None
            
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
            faculty.is_head = request.POST.get('is_head') == 'on'
            faculty.is_dept_proctor = request.POST.get('is_dept_proctor') == 'on'
            faculty.is_bsc_admission_coordinator = request.POST.get('is_bsc_admission_coordinator') == 'on'
            faculty.is_mcse_admission_coordinator = request.POST.get('is_mcse_admission_coordinator') == 'on'
            faculty.is_on_study_leave = request.POST.get('is_on_study_leave') == 'on'
            
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
