from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login as auth_login, authenticate, logout as auth_logout
from django.contrib import messages
from django.db import transaction
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse
from designs.models import FeatureCard, HeroTags
from people.models import AllowedEmail, BaseUser, Faculty, Staff, Officer, ClubMember, PasswordResetToken, Contributor


def home(request):
    # Get active feature cards for the hero section
    all_cards = list(FeatureCard.objects.filter(is_active=True).order_by('sl_number'))
    # Start from the second card and include the rest
    feature_cards = all_cards[1:] if len(all_cards) > 1 else all_cards
    # Get all active hero tags ordered by serial number
    hero_tags = HeroTags.objects.filter(is_active=True).order_by('sl')
    # Use the first active feature card as the HoD highlight (editable via admin)
    hod_card = FeatureCard.objects.filter(is_active=True).order_by('sl_number').first()

    # Check if stats should be hidden
    show_stats = request.GET.get('stats', 'show').lower() != 'none'

    # Calculate lifetime_stats for BSc program (for PO, Blooms, K, P, A tables)
    lifetime_stats = None
    program_outcomes = None
    try:
        from academics.models import Program, ProgramOutcome, Course, CourseOutcome

        # Get BSc program
        program = Program.objects.filter(name__icontains='BSc').first()

        if program:
            # Get all Program Outcomes for the program and sort numerically
            import re
            pos_list = list(ProgramOutcome.objects.filter(program=program))
            # Sort by extracting the numeric part from the code (e.g., "PO1" -> 1, "PO10" -> 10)
            pos_list.sort(key=lambda po: int(re.search(r'\d+', po.code).group()) if re.search(r'\d+', po.code) else 0)
            program_outcomes = pos_list

            # Initialize lifetime statistics
            lifetime_stats = {
                'program_outcomes': {},  # PO1-PO12: {credits, marks}
                'blooms': {},  # K1-K6: {credits, marks}
                'knowledge': {},  # K1-K8: {credits, marks}
                'problem': {},  # P1-P7: {credits, marks}
                'activity': {},  # A1-A5: {credits, marks}
            }

            # Get all courses for the program
            courses = Course.objects.filter(program=program)

            for course in courses:
                outcomes = course.outcomes.all()
                course_credit = float(course.credit_hours)

                for outcome in outcomes:
                    # Program Outcomes
                    if outcome.program_outcome:
                        po_code = outcome.program_outcome.code
                        if po_code not in lifetime_stats['program_outcomes']:
                            lifetime_stats['program_outcomes'][po_code] = {'credits': 0, 'marks': 0}
                        lifetime_stats['program_outcomes'][po_code]['credits'] += course_credit
                        lifetime_stats['program_outcomes'][po_code]['marks'] += outcome.total_assessment_marks

                    # Bloom's taxonomy
                    blooms = outcome.blooms_level
                    if blooms:
                        if blooms not in lifetime_stats['blooms']:
                            lifetime_stats['blooms'][blooms] = {'credits': 0, 'marks': 0}
                        lifetime_stats['blooms'][blooms]['credits'] += course_credit
                        lifetime_stats['blooms'][blooms]['marks'] += outcome.total_assessment_marks

                    # Knowledge profiles
                    kp = outcome.knowledge_profile
                    if kp:
                        if kp not in lifetime_stats['knowledge']:
                            lifetime_stats['knowledge'][kp] = {'credits': 0, 'marks': 0}
                        lifetime_stats['knowledge'][kp]['credits'] += course_credit
                        lifetime_stats['knowledge'][kp]['marks'] += outcome.total_assessment_marks

                    # Problem attributes
                    pa = outcome.problem_attribute
                    if pa:
                        if pa not in lifetime_stats['problem']:
                            lifetime_stats['problem'][pa] = {'credits': 0, 'marks': 0}
                        lifetime_stats['problem'][pa]['credits'] += course_credit
                        lifetime_stats['problem'][pa]['marks'] += outcome.total_assessment_marks

                    # Activity attributes
                    aa = outcome.activity_attribute
                    if aa:
                        if aa not in lifetime_stats['activity']:
                            lifetime_stats['activity'][aa] = {'credits': 0, 'marks': 0}
                        lifetime_stats['activity'][aa]['credits'] += course_credit
                        lifetime_stats['activity'][aa]['marks'] += outcome.total_assessment_marks

            # Calculate total marks for each category for percentage calculations
            if lifetime_stats:
                lifetime_stats['totals'] = {
                    'program_outcomes': sum(data['marks'] for data in lifetime_stats['program_outcomes'].values()),
                    'blooms': sum(data['marks'] for data in lifetime_stats['blooms'].values()),
                    'knowledge': sum(data['marks'] for data in lifetime_stats['knowledge'].values()),
                    'problem': sum(data['marks'] for data in lifetime_stats['problem'].values()),
                    'activity': sum(data['marks'] for data in lifetime_stats['activity'].values()),
                }
    except ImportError:
        # Academics app not available or models not migrated yet
        lifetime_stats = None
        program_outcomes = None
    except Exception:
        # Handle any other errors gracefully
        lifetime_stats = None
        program_outcomes = None

    return render(request, 'home.html', {
        'feature_cards': feature_cards,
        'hero_tags': hero_tags,
        'hod_card': hod_card,
        'lifetime_stats': lifetime_stats,
        'program_outcomes': program_outcomes,
    })


def themes(request):
    return render(request, 'themes.html')


def design_guidelines(request):
    return render(request, 'design_guidelines.html')


def login(request):
    if request.method == 'POST':
        username_or_email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        remember = request.POST.get('remember', False)
        
        if not username_or_email or not password:
            messages.error(request, 'Please provide both email/username and password.')
            return render(request, 'login.html')
        
        # Try to authenticate with username first
        user = authenticate(request, username=username_or_email, password=password)
        
        # If authentication fails, try with email
        if user is None:
            try:
                # Try to find user by email
                from people.models import BaseUser
                user_by_email = BaseUser.objects.get(email=username_or_email.lower())
                # Authenticate with the username (since Django authenticate uses username field)
                user = authenticate(request, username=user_by_email.username, password=password)
            except BaseUser.DoesNotExist:
                user = None
        
        if user is None:
            messages.error(request, 'Invalid email/username or password.')
            return render(request, 'login.html')
        
        # Check if user is blocked via AllowedEmail
        if user.allowed_email and user.allowed_email.is_blocked:
            messages.error(request, 'Your account has been blocked. Please contact the administrator.')
            return render(request, 'login.html')
        
        # Check if user account is active
        if not user.is_active:
            messages.error(request, 'Your account is inactive. Please contact the administrator.')
            return render(request, 'login.html')
        
        # Login the user
        auth_login(request, user)
        
        # Set session expiry based on remember me
        if not remember:
            request.session.set_expiry(0)  # Session expires when browser closes
        else:
            request.session.set_expiry(1209600)  # 2 weeks
        
        messages.success(request, f'Welcome back, {user.get_full_name() or user.email}!')
        return redirect('people:user_profile')
    
    return render(request, 'login.html')


def signup(request):
    if request.method == 'POST':
        email = request.POST.get('email', '').strip().lower()
        fullname = request.POST.get('fullname', '').strip()
        password = request.POST.get('password', '')
        confirm_password = request.POST.get('confirmPassword', '')
        
        # Validation
        errors = []
        
        if not email:
            errors.append('Email is required.')
        if not fullname:
            errors.append('Full name is required.')
        if not password:
            errors.append('Password is required.')
        elif len(password) < 8:
            errors.append('Password must be at least 8 characters long.')
        if password != confirm_password:
            errors.append('Passwords do not match.')
        
        if errors:
            for error in errors:
                messages.error(request, error)
            return render(request, 'signup.html')
        
        # Check if email exists in AllowedEmail
        try:
            allowed_email = AllowedEmail.objects.get(email=email)
        except AllowedEmail.DoesNotExist:
            messages.error(request, 'This email is not authorized to sign up. Only faculty, staff, officers, and club members can create accounts.')
            return render(request, 'signup.html')
        
        # Check if email is active for signup
        if not allowed_email.is_active:
            messages.error(request, 'This email is not currently active for signup. Please contact the administrator.')
            return render(request, 'signup.html')
        
        # Check if email is blocked
        if allowed_email.is_blocked:
            messages.error(request, 'This email has been blocked. Please contact the administrator.')
            return render(request, 'signup.html')
        
        # Check if user already exists
        if BaseUser.objects.filter(email=email).exists():
            messages.error(request, 'An account with this email already exists. Please sign in instead.')
            return render(request, 'signup.html')
        
        # Create user
        try:
            with transaction.atomic():
                # Create BaseUser
                user = BaseUser.objects.create_user(
                    username=email,  # Use email as username
                    email=email,
                    password=password,
                    allowed_email=allowed_email,
                    user_type=allowed_email.user_type,
                    is_power_user=allowed_email.is_power_user,
                    first_name=fullname.split()[0] if fullname.split() else '',
                    last_name=' '.join(fullname.split()[1:]) if len(fullname.split()) > 1 else '',
                )
                
                # Create appropriate profile based on user_type
                if allowed_email.user_type == 'faculty':
                    # Generate shortname from first letters of first two words
                    name_parts = fullname.split()
                    if len(name_parts) >= 2:
                        shortname = ''.join([n[0].upper() for n in name_parts[:2]])
                    else:
                        shortname = fullname[:2].upper() if len(fullname) >= 2 else 'N/A'
                    
                    Faculty.objects.create(
                        base_user=user,
                        name=fullname,
                        shortname=shortname,
                    )
                elif allowed_email.user_type == 'staff':
                    Staff.objects.create(
                        base_user=user,
                        name=fullname,
                        designation='Lab Assistant',  # Default, can be changed later
                    )
                elif allowed_email.user_type == 'officer':
                    Officer.objects.create(
                        base_user=user,
                        name=fullname,
                    )
                elif allowed_email.user_type == 'club_member':
                    ClubMember.objects.create(
                        base_user=user,
                        name=fullname,
                    )
                
                # Auto-login the user
                auth_login(request, user)
                messages.success(request, f'Welcome, {fullname}! Your account has been created successfully.')
                return redirect('people:user_profile')
                
        except Exception as e:
            messages.error(request, f'An error occurred during signup: {str(e)}')
            return render(request, 'signup.html')
    
    return render(request, 'signup.html')


def logout(request):
    auth_logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('home')


def forgot_password(request):
    """Handle forgot password request"""
    if request.method == 'POST':
        email = request.POST.get('email', '').strip().lower()
        
        if not email:
            messages.error(request, 'Please enter your email address.')
            return render(request, 'forgot_password.html')
        
        # First check if email is in AllowedEmail list
        try:
            allowed_email = AllowedEmail.objects.get(email=email)
            
            # Check if email is blocked
            if allowed_email.is_blocked:
                messages.error(request, 'This email has been blocked. Please contact the administrator.')
                return render(request, 'forgot_password.html')
            
            # Check if email is active for signup (should be active to reset password)
            if not allowed_email.is_active:
                messages.error(request, 'This email is not currently active. Please contact the administrator.')
                return render(request, 'forgot_password.html')
            
        except AllowedEmail.DoesNotExist:
            # Email is not in the allowed list
            messages.error(request, 'This email is not authorized. Only faculty, staff, officers, and club members can reset their passwords.')
            return render(request, 'forgot_password.html')
        
        # Now check if user account exists
        try:
            user = BaseUser.objects.get(email=email)
            
            # Check if user is active
            if not user.is_active:
                messages.error(request, 'Your account is inactive. Please contact the administrator.')
                return render(request, 'forgot_password.html')
            
            # Generate reset token
            reset_token = PasswordResetToken.generate_token(user, hours=24)
            
            # Create reset URL
            reset_url = request.build_absolute_uri(
                reverse('reset_password', kwargs={'token': reset_token.token})
            )
            
            # Send email
            try:
                send_mail(
                    subject='Password Reset Request - CSE UAP',
                    message=f'''Hello {user.get_full_name() or user.email},

You requested to reset your password for your CSE UAP account.

Click the following link to reset your password:
{reset_url}

This link will expire in 24 hours.

If you did not request this password reset, please ignore this email.

Best regards,
CSE UAP Team''',
                    from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@uap-cse.edu'),
                    recipient_list=[user.email],
                    fail_silently=False,
                )
                messages.success(request, 'Password reset link has been sent to your email address. Please check your inbox.')
            except Exception as e:
                # If email sending fails, show error message
                messages.error(request, 'Failed to send password reset email. Please try again later or contact the administrator.')
                # Log the error for debugging
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f'Failed to send password reset email: {str(e)}')
            
            return render(request, 'forgot_password.html')
            
        except BaseUser.DoesNotExist:
            # Email is allowed but user account doesn't exist yet
            messages.info(request, 'This email is authorized but no account exists yet. Please sign up first.')
            return render(request, 'forgot_password.html')
    
    return render(request, 'forgot_password.html')


def reset_password(request, token):
    """Handle password reset with token"""
    # Get the token
    try:
        reset_token = PasswordResetToken.objects.get(token=token)
    except PasswordResetToken.DoesNotExist:
        messages.error(request, 'Invalid or expired password reset link.')
        return redirect('forgot_password')
    
    # Check if token is valid
    if not reset_token.is_valid():
        messages.error(request, 'This password reset link has expired or has already been used.')
        return redirect('forgot_password')
    
    if request.method == 'POST':
        password = request.POST.get('password', '')
        confirm_password = request.POST.get('confirmPassword', '')
        
        # Validation
        if not password:
            messages.error(request, 'Please enter a new password.')
            return render(request, 'reset_password.html', {'token': token})
        
        if len(password) < 8:
            messages.error(request, 'Password must be at least 8 characters long.')
            return render(request, 'reset_password.html', {'token': token})
        
        if password != confirm_password:
            messages.error(request, 'Passwords do not match.')
            return render(request, 'reset_password.html', {'token': token})
        
        # Update password
        user = reset_token.user
        user.set_password(password)
        user.save()
        
        # Mark token as used
        reset_token.used = True
        reset_token.save()
        
        messages.success(request, 'Your password has been reset successfully. You can now log in with your new password.')
        return redirect('login')
    
    return render(request, 'reset_password.html', {'token': token})


def system_documentation(request):
    """Display comprehensive system documentation"""
    return render(request, 'system_documentation.html')



from django.shortcuts import render

def credits(request):
    # Query contributors from database, grouped by project_type
    # Sort by contribution: first by lines_added (descending), then by number_of_commits (descending), then by name
    # Handle None values by treating them as 0 for sorting purposes
    from django.db.models import Value, IntegerField
    from django.db.models.functions import Coalesce
    
    final_contributors = Contributor.objects.filter(project_type='final').annotate(
        lines_added_sorted=Coalesce('lines_added', Value(0), output_field=IntegerField()),
        commits_sorted=Coalesce('number_of_commits', Value(0), output_field=IntegerField())
    ).order_by('-lines_added_sorted', '-commits_sorted', 'name')
    
    course_contributors = Contributor.objects.filter(project_type='course').annotate(
        lines_added_sorted=Coalesce('lines_added', Value(0), output_field=IntegerField()),
        commits_sorted=Coalesce('number_of_commits', Value(0), output_field=IntegerField())
    ).order_by('-lines_added_sorted', '-commits_sorted', 'name')
    
    # Introductory text about the project
    intro_text = """Project Credits & Acknowledgement

This website is a token of love from UAPIANS.
It was built at zero (0.00) taka cost, driven purely by passion and commitment—no one was asked or paid to do this work.

The idea of developing the department website originated from my role as a course teacher of CSE 301: Object-Oriented Programming II (Visual and Web Programming). Over several semesters, I explored the possibility of building a real, usable system as part of the course coursework, so that students could learn by contributing to a live project rather than a simulated assignment.

During this period, I worked closely with multiple batches of students. Together, we experimented with designs, features, and early implementations. While these efforts showed promising results and strong learning outcomes, the project could not be completed within the constraints of a course timeline.

Later, I took the initiative to restart the project from scratch. I handled the core planning, architecture, and a major portion of the development myself, and subsequently collaborated with Tahiya, who played a key role in completing, refining, and deploying the final system.

Final Development & Deployment

Durjoy Mistry – Concept, system architecture, major development, technical supervision, integration, and final approval

Tahiya – Final implementation, feature completion, testing, optimization, and deployment

This phase resulted in the fully functional version of the UAP CSE website currently in use.

Course-Based Development (Initial Attempts)

The following students contributed during the course-based development phase of CSE 301. Their work involved idea exploration, UI concepts, feature trials, and prototype-level implementations.

These contributions were part of an academic learning process and helped shape the understanding that informed the final rebuild.

Closing Note

This project stands as a reflection of what students and teachers can create together when driven by ownership rather than obligation."""

    context = {
        "intro_text": intro_text,
        "final_contributors": final_contributors,
        "course_contributors": course_contributors,
    }

    return render(request, 'credits.html', context)

