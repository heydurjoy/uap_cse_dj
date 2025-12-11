from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate
from django.contrib import messages
from django.db import transaction
from .models import Faculty, Staff, Officer, ClubMember, BaseUser


def faculty_list(request):
    """
    Display list of all faculties, sorted by designation first, then by sl.
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
    
    # Sort faculties: first by designation (using order dict), then by sl
    # Handle None values for designation and sl
    sorted_faculties = sorted(
        all_faculties,
        key=lambda f: (
            designation_order.get(f.designation, 999) if f.designation else 999,
            f.sl if f.sl else 999
        )
    )
    
    # Group by designation for display
    faculties_by_designation = {}
    for faculty in sorted_faculties:
        designation = faculty.designation or 'Other'
        if designation not in faculties_by_designation:
            faculties_by_designation[designation] = []
        faculties_by_designation[designation].append(faculty)
    
    context = {
        'faculties': sorted_faculties,
        'faculties_by_designation': faculties_by_designation,
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
    if faculty.joining_date:
        today = timezone.now()
        joining_datetime = timezone.make_aware(datetime.combine(faculty.joining_date, datetime.min.time()))
        
        # Calculate total time difference
        delta = today - joining_datetime
        
        total_days = delta.days
        total_seconds = delta.total_seconds()
        hours = int((total_seconds % 86400) // 3600)
        minutes = int((total_seconds % 3600) // 60)
        
        # Calculate years and months
        today_date = today.date()
        joining = faculty.joining_date
        
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
    Excludes: access_level, user_type, sl (serial number)
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
