from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login as auth_login, authenticate, logout as auth_logout
from django.db import transaction
from django.utils import timezone
from django.conf import settings
from django.urls import reverse
from designs.models import FeatureCard, HeroTags
from people.models import AllowedEmail, BaseUser, Faculty, Staff, Officer, ClubMember, PasswordResetToken, Contributor
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
import os
import hashlib
import logging
import requests
import secrets
from django.contrib import messages
from django.core.mail import send_mail, get_connection
from django.utils.crypto import get_random_string
from django.contrib.auth import update_session_auth_hash
from django.db.models import Q
try:
    from .search_utils import generate_summary
except ImportError:
    # Fallback if search_utils doesn't exist
    def generate_summary(results, query):
        if not results or not any(results.values()):
            return f"I couldn't find any results matching '{query}'. Please try different keywords."
        total = sum(len(v) for v in results.values() if v)
        return f"I found {total} result(s) for '{query}'."


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

    # Get research data for home page
    research_stats = None
    top_researchers = None
    try:
        from people.models import Faculty, Publication
        from django.db.models import Sum
        from datetime import datetime
        
        # Get current faculty (not on leave, not former)
        current_faculty = Faculty.objects.filter(
            last_office_date__isnull=True,
            is_on_study_leave=False
        ).select_related('base_user')
        
        # Get all publications from current faculty
        publications = Publication.objects.filter(faculty__in=current_faculty)
        
        # Scoring system
        SCORING = {
            'q1': 10, 'q2': 7, 'q3': 5, 'q4': 3,
            'a1': 8, 'a2': 6, 'a3': 4, 'a4': 2,
            'not_indexed': 1,
        }
        
        # Calculate statistics
        total_pubs = publications.count()
        total_citations = current_faculty.aggregate(total=Sum('citation'))['total'] or 0
        num_faculty = current_faculty.count()
        avg_pubs_per_faculty = round(total_pubs / num_faculty, 2) if num_faculty > 0 else 0
        
        # Count by ranking
        stats_by_ranking = {}
        for ranking_code, ranking_label in Publication.RANKING_CHOICES:
            count = publications.filter(ranking=ranking_code).count()
            stats_by_ranking[ranking_code] = {
                'label': ranking_label,
                'count': count,
            }
        
        research_stats = {
            'total_pubs': total_pubs,
            'total_citations': total_citations,
            'avg_pubs_per_faculty': avg_pubs_per_faculty,
            'num_faculty': num_faculty,
            'stats_by_ranking': stats_by_ranking,
        }
        
        # Calculate faculty-wise scores
        faculty_scores = []
        for faculty in current_faculty:
            faculty_pubs = publications.filter(faculty=faculty)
            pub_count = faculty_pubs.count()
            
            score = 0
            pub_years = []
            for pub in faculty_pubs:
                score += SCORING.get(pub.ranking, 0)
                pub_years.append(pub.pub_year)
            
            # Calculate publication year span (for tie-breaking)
            year_span = 0
            if pub_years:
                min_year = min(pub_years)
                max_year = max(pub_years)
                year_span = max_year - min_year if max_year != min_year else 0
            
            faculty_scores.append({
                'faculty': faculty,
                'publication_count': pub_count,
                'score': score,
                'citations': faculty.citation or 0,
                'year_span': year_span,
            })
        
        # Sort faculty by score (highest first), then by year_span (smaller is better)
        faculty_scores.sort(key=lambda x: (-x['score'], x['year_span']))
        
        # Get top researchers by designation (only top 1 per designation)
        # Use OrderedDict to maintain order
        from collections import OrderedDict
        top_researchers = OrderedDict()
        designations = ['Professor', 'Associate Professor', 'Assistant Professor', 'Lecturer']
        
        for designation in designations:
            designation_faculty = [item for item in faculty_scores if item['faculty'].designation == designation]
            if designation_faculty:
                top_researchers[designation] = designation_faculty[0]
    except Exception:
        # Handle errors gracefully - research data is optional
        research_stats = None
        top_researchers = None

    return render(request, 'home.html', {
        'feature_cards': feature_cards,
        'hero_tags': hero_tags,
        'hod_card': hod_card,
        'lifetime_stats': lifetime_stats,
        'program_outcomes': program_outcomes,
        'research_stats': research_stats,
        'top_researchers': top_researchers,
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


def google_login(request):
    """
    Initiate Google OAuth login flow.
    Redirects user to Google OAuth consent screen.
    """
    from django.conf import settings
    import secrets
    
    # Generate state token for CSRF protection
    state = secrets.token_urlsafe(32)
    request.session['oauth_state'] = state
    request.session['oauth_next'] = request.GET.get('next', 'people:user_profile')
    
    # Google OAuth configuration
    client_id = os.getenv('GOOGLE_OAUTH_CLIENT_ID', '')
    redirect_uri = request.build_absolute_uri(reverse('google_callback'))
    
    if not client_id:
        messages.error(request, 'Google OAuth is not configured. Please contact the administrator.')
        return redirect('login')
    
    # Build Google OAuth URL (using modern Google Identity Services approach)
    # No Google+ API needed - using standard OAuth 2.0 with openid, email, profile scopes
    google_auth_url = (
        'https://accounts.google.com/o/oauth2/v2/auth?'
        f'client_id={client_id}&'
        f'redirect_uri={redirect_uri}&'
        'response_type=code&'
        'scope=openid email profile&'  # Modern scopes - no Google+ API needed
        f'state={state}&'
        'access_type=offline&'
        'prompt=consent'
    )
    
    return redirect(google_auth_url)


def google_callback(request):
    """
    Handle Google OAuth callback.
    Creates or logs in user based on Google account.
    """
    from django.conf import settings
    import requests
    
    # Verify state token
    state = request.GET.get('state')
    if not state or state != request.session.get('oauth_state'):
        messages.error(request, 'Invalid OAuth state. Please try again.')
        return redirect('login')
    
    code = request.GET.get('code')
    if not code:
        messages.error(request, 'Authorization failed. Please try again.')
        return redirect('login')
    
    # Exchange code for tokens
    client_id = os.getenv('GOOGLE_OAUTH_CLIENT_ID', '')
    client_secret = os.getenv('GOOGLE_OAUTH_CLIENT_SECRET', '')
    redirect_uri = request.build_absolute_uri(reverse('google_callback'))
    
    if not client_id or not client_secret:
        messages.error(request, 'Google OAuth is not configured. Please contact the administrator.')
        return redirect('login')
    
    # Exchange authorization code for access token
    token_url = 'https://oauth2.googleapis.com/token'
    token_data = {
        'code': code,
        'client_id': client_id,
        'client_secret': client_secret,
        'redirect_uri': redirect_uri,
        'grant_type': 'authorization_code',
    }
    
    try:
        token_response = requests.post(token_url, data=token_data, timeout=10)
        token_response.raise_for_status()
        tokens = token_response.json()
        access_token = tokens.get('access_token')
        
        if not access_token:
            messages.error(request, 'Failed to obtain access token from Google.')
            return redirect('login')
        
        # Get user info from Google (using modern OAuth 2.0 userinfo endpoint)
        # This works without Google+ API - uses standard OAuth 2.0 userinfo endpoint
        user_info_url = 'https://www.googleapis.com/oauth2/v2/userinfo'
        headers = {'Authorization': f'Bearer {access_token}'}
        user_info_response = requests.get(user_info_url, headers=headers, timeout=10)
        user_info_response.raise_for_status()
        user_info = user_info_response.json()
        
        email = user_info.get('email', '').lower()
        if not email:
            messages.error(request, 'Could not retrieve email from Google account.')
            return redirect('login')
        
        # Check if email is in AllowedEmail list
        from people.models import AllowedEmail, BaseUser, Faculty, Staff, Officer, ClubMember
        
        try:
            allowed_email = AllowedEmail.objects.get(email=email, is_active=True)
        except AllowedEmail.DoesNotExist:
            messages.error(
                request, 
                f'Your email ({email}) is not authorized to access this system. '
                'Please contact the administrator to get access.'
            )
            return redirect('login')
        
        # Check if user already exists
        try:
            user = BaseUser.objects.get(email=email)
        except BaseUser.DoesNotExist:
            # Create new user
            full_name = user_info.get('name', '')
            first_name = full_name.split()[0] if full_name.split() else ''
            last_name = ' '.join(full_name.split()[1:]) if len(full_name.split()) > 1 else ''
            
            with transaction.atomic():
                user = BaseUser.objects.create_user(
                    username=email,
                    email=email,
                    password=secrets.token_urlsafe(32),  # Random password (won't be used)
                    allowed_email=allowed_email,
                    user_type=allowed_email.user_type,
                    is_power_user=allowed_email.is_power_user,
                    first_name=first_name,
                    last_name=last_name,
                )
                # Mark password as unusable since user will login via OAuth
                user.set_unusable_password()
                user.save()
                
                # Create appropriate profile based on user_type
                if allowed_email.user_type == 'faculty':
                    name_parts = full_name.split()
                    if len(name_parts) >= 2:
                        shortname = ''.join([n[0].upper() for n in name_parts[:2]])
                    else:
                        shortname = full_name[:2].upper() if len(full_name) >= 2 else 'N/A'
                    
                    Faculty.objects.create(
                        base_user=user,
                        name=full_name or email,
                        shortname=shortname,
                    )
                elif allowed_email.user_type == 'staff':
                    Staff.objects.create(
                        base_user=user,
                        name=full_name or email,
                        designation='Lab Assistant',
                    )
                elif allowed_email.user_type == 'officer':
                    Officer.objects.create(
                        base_user=user,
                        name=full_name or email,
                    )
                elif allowed_email.user_type == 'club_member':
                    ClubMember.objects.create(
                        base_user=user,
                        name=full_name or email,
                    )
        
        # Check if user is blocked
        if user.allowed_email and user.allowed_email.is_blocked:
            messages.error(request, 'Your account has been blocked. Please contact the administrator.')
            return redirect('login')
        
        # Check if user account is active
        if not user.is_active:
            messages.error(request, 'Your account is inactive. Please contact the administrator.')
            return redirect('login')
        
        # Login the user
        auth_login(request, user)
        
        # Clear OAuth state
        if 'oauth_state' in request.session:
            del request.session['oauth_state']
        
        next_url = request.session.get('oauth_next', 'people:user_profile')
        if 'oauth_next' in request.session:
            del request.session['oauth_next']
        
        messages.success(request, f'Welcome, {user.get_full_name() or user.email}!')
        return redirect(next_url)
        
    except requests.RequestException as e:
        messages.error(request, f'Error communicating with Google: {str(e)}')
        return redirect('login')
    except Exception as e:
        messages.error(request, f'An error occurred during Google authentication: {str(e)}')
        return redirect('login')


def logout(request):
    auth_logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('home')

logger = logging.getLogger(__name__)
logger = logging.getLogger(__name__)

def forgot_password(request):
    """Handle forgot password request with Brevo API and SMTP fallback"""
    GENERIC_MESSAGE = (
        "If an account exists for this email, a password reset link has been sent."
    )

    if request.method == 'POST':
        email = request.POST.get('email', '').strip().lower()
        if not email:
            messages.error(request, 'Please enter your email address.')
            return render(request, 'forgot_password.html')

        # AllowedEmail check (silent)
        try:
            allowed_email = AllowedEmail.objects.get(email=email)
            if allowed_email.is_blocked or not allowed_email.is_active:
                messages.success(request, GENERIC_MESSAGE)
                return render(request, 'forgot_password.html')
        except AllowedEmail.DoesNotExist:
            messages.success(request, GENERIC_MESSAGE)
            return render(request, 'forgot_password.html')

        # User check (silent)
        try:
            user = BaseUser.objects.get(email=email, is_active=True)
        except BaseUser.DoesNotExist:
            messages.success(request, GENERIC_MESSAGE)
            return render(request, 'forgot_password.html')

        # Generate hashed token
        raw_token = PasswordResetToken.generate_token(user)
        
        # Get domain - prefer FRONTEND_DOMAIN env var, fallback to request
        FRONTEND_DOMAIN_ENV = os.getenv('FRONTEND_DOMAIN', '')
        if FRONTEND_DOMAIN_ENV:
            # Strip trailing slash to avoid double slashes
            DOMAIN = FRONTEND_DOMAIN_ENV.rstrip('/')
        else:
            # Fallback: use request host with appropriate protocol
            protocol = 'https' if request.is_secure() else 'http'
            DOMAIN = f"{protocol}://{request.get_host()}"
        
        reset_path = reverse('reset_password', kwargs={'token': raw_token})
        reset_url = f"{DOMAIN}{reset_path}"
        
        # Log domain configuration for debugging
        logger.info(f"FRONTEND_DOMAIN env var: {'SET' if FRONTEND_DOMAIN_ENV else 'NOT SET'}")
        if FRONTEND_DOMAIN_ENV:
            logger.info(f"Using FRONTEND_DOMAIN: {FRONTEND_DOMAIN_ENV}")
        else:
            logger.warning(f"FRONTEND_DOMAIN not set, using fallback: {DOMAIN}")

        BREVO_API_KEY = os.getenv('BREVO_API_KEY', '')
        EMAIL_FROM = os.getenv('EMAIL_FROM', 'noreply@uap-cse.edu')
        
        # Track if email was sent successfully
        email_sent = False
        email_error = None

        # Send email via Brevo API
        if BREVO_API_KEY:
            try:
                brevo_url = 'https://api.brevo.com/v3/smtp/email'
                headers = {
                    'accept': 'application/json',
                    'api-key': BREVO_API_KEY,
                    'content-type': 'application/json'
                }
                payload = {
                    'sender': {'name': 'CSE UAP', 'email': EMAIL_FROM},
                    'to': [{'email': user.email}],
                    'subject': 'Password Reset Request - CSE UAP',
                    'htmlContent': f'''
                        <p>Hello {user.get_full_name() or user.email},</p>
                        <p>Click the link below to reset your password:</p>
                        <p><a href="{reset_url}">{reset_url}</a></p>
                        <p>This link expires in 24 hours.</p>
                        <p>If you didn't request this, ignore this email.</p>
                    ''',
                    'textContent': f'''
Hello {user.get_full_name() or user.email},

Reset your password using the link below:
{reset_url}

This link expires in 24 hours.
                    '''
                }
                logger.info(f"Attempting to send password reset email to {user.email} via Brevo API")
                logger.info(f"Reset URL: {reset_url}")
                logger.info(f"EMAIL_FROM: {EMAIL_FROM}")
                response = requests.post(brevo_url, json=payload, headers=headers, timeout=10)
                response.raise_for_status()
                email_sent = True
                logger.info(f"✅ Password reset email sent successfully to {user.email} via Brevo API")
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
                        logger.info(f"Attempting SMTP fallback for {user.email}")
                        connection = get_connection(
                            host=EMAIL_HOST,
                            port=int(EMAIL_PORT),
                            username=EMAIL_HOST_USER,
                            password=EMAIL_HOST_PASSWORD,
                            use_tls=True,
                            fail_silently=False
                        )
                        send_mail(
                            subject='Password Reset Request - CSE UAP',
                            message=f"Reset your password: {reset_url}\nThis link expires in 24 hours.",
                            from_email=EMAIL_FROM,
                            recipient_list=[user.email],
                            connection=connection
                        )
                        email_sent = True
                        logger.info(f"✅ Password reset email sent successfully to {user.email} via SMTP fallback")
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
            logger.warning("⚠️ BREVO_API_KEY not set, attempting SMTP fallback")
            # Try SMTP if BREVO_API_KEY is not set
            try:
                EMAIL_HOST = os.getenv('EMAIL_HOST')
                EMAIL_PORT = os.getenv('EMAIL_PORT', '587')
                EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER')
                EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD')
                
                if EMAIL_HOST and EMAIL_HOST_USER and EMAIL_HOST_PASSWORD:
                    logger.info(f"Attempting to send password reset email to {user.email} via SMTP")
                    logger.info(f"Reset URL: {reset_url}")
                    connection = get_connection(
                        host=EMAIL_HOST,
                        port=int(EMAIL_PORT),
                        username=EMAIL_HOST_USER,
                        password=EMAIL_HOST_PASSWORD,
                        use_tls=True,
                        fail_silently=False
                    )
                    send_mail(
                        subject='Password Reset Request - CSE UAP',
                        message=f"Reset your password: {reset_url}\nThis link expires in 24 hours.",
                        from_email=EMAIL_FROM,
                        recipient_list=[user.email],
                        connection=connection
                    )
                    email_sent = True
                    logger.info(f"✅ Password reset email sent successfully to {user.email} via SMTP")
                else:
                    email_error = "Email configuration missing: BREVO_API_KEY not set and SMTP credentials incomplete"
                    logger.error(f"❌ {email_error}")
                    logger.error(f"EMAIL_HOST: {'SET' if EMAIL_HOST else 'NOT SET'}")
                    logger.error(f"EMAIL_HOST_USER: {'SET' if EMAIL_HOST_USER else 'NOT SET'}")
                    logger.error(f"EMAIL_HOST_PASSWORD: {'SET' if EMAIL_HOST_PASSWORD else 'NOT SET'}")
            except Exception as smtp_err:
                email_error = f"SMTP error: {str(smtp_err)}"
                logger.exception(f"❌ SMTP failed: {email_error}")

        # Show appropriate message based on email sending result
        if email_sent:
            messages.success(request, GENERIC_MESSAGE)
        else:
            # In production, still show generic message for security
            # But log the actual error for debugging
            if settings.DEBUG:
                messages.error(request, f'Failed to send email. Error: {email_error}')
            else:
                messages.success(request, GENERIC_MESSAGE)
                logger.error(f"Email sending failed but showing generic message. Error: {email_error}")
        
        return render(request, 'forgot_password.html')

    return render(request, 'forgot_password.html')


@transaction.atomic
def reset_password(request, token):
    """Reset password view that uses hashed tokens"""
    hashed_token = hashlib.sha256(token.encode()).hexdigest()
    try:
        reset_token = PasswordResetToken.objects.select_for_update().get(token=hashed_token)
    except PasswordResetToken.DoesNotExist:
        messages.error(request, 'Invalid or expired password reset link.')
        return redirect('forgot_password')

    if not reset_token.is_valid():
        messages.error(request, 'This password reset link has expired or has already been used.')
        return redirect('forgot_password')

    if request.method == 'POST':
        password = request.POST.get('password', '')
        confirm_password = request.POST.get('confirmPassword', '')

        if not password:
            messages.error(request, 'Please enter a new password.')
            return render(request, 'reset_password.html', {'token': token})

        if password != confirm_password:
            messages.error(request, 'Passwords do not match.')
            return render(request, 'reset_password.html', {'token': token})

        try:
            validate_password(password, reset_token.user)
        except ValidationError as e:
            messages.error(request, e.messages[0])
            return render(request, 'reset_password.html', {'token': token})

        # Update password
        user = reset_token.user
        user.set_password(password)
        user.save()

        # Mark token as used
        reset_token.used = True
        reset_token.save()

        update_session_auth_hash(request, user)
        messages.success(request, 'Your password has been reset successfully. You can now log in.')
        return redirect('login')

    return render(request, 'reset_password.html', {'token': token})

def system_documentation(request):
    """Display comprehensive system documentation"""
    return render(request, 'system_documentation.html')



from django.shortcuts import render

def features(request):
    return render(request, 'features.html')

def credits(request):
    # Query contributors from database, grouped by project_type
    # Sort by contribution: first by lines_added (descending), then by number_of_commits (descending), then by name
    # Handle None values by treating them as 0 for sorting purposes
    from django.db.models import Value, IntegerField
    from django.db.models.functions import Coalesce
    from people.models import Faculty
    
    final_contributors = Contributor.objects.filter(project_type='final').annotate(
        lines_added_sorted=Coalesce('lines_added', Value(0), output_field=IntegerField()),
        commits_sorted=Coalesce('number_of_commits', Value(0), output_field=IntegerField())
    ).order_by('-lines_added_sorted', '-commits_sorted', 'name')
    
    course_contributors = Contributor.objects.filter(project_type='course').annotate(
        lines_added_sorted=Coalesce('lines_added', Value(0), output_field=IntegerField()),
        commits_sorted=Coalesce('number_of_commits', Value(0), output_field=IntegerField())
    ).order_by('-lines_added_sorted', '-commits_sorted', 'name')
    
    # Get Durjoy's faculty object for linking
    durjoy_faculty = None
    try:
        durjoy_faculty = Faculty.objects.select_related('base_user').filter(
            base_user__email='durjoy@uap-bd.edu'
        ).first()
    except:
        pass
    
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
        "durjoy_faculty": durjoy_faculty,
    }

    return render(request, 'credits.html', context)


def search(request):
    """
    Comprehensive search across all models in the application.
    Searches: Faculty, Publications, Posts, Club Posts, Courses, Clubs, Staff, Officers
    """
    query = request.GET.get('q', '').strip()
    
    if not query:
        return render(request, 'search_results.html', {
            'query': '',
            'results': {},
            'summary': 'Please enter a search query.',
        })
    
    results = {}
    
    # Search Faculty
    try:
        from people.models import Faculty
        # Search in text fields (RichTextField needs special handling)
        faculty_results = Faculty.objects.filter(
            Q(name__icontains=query) |
            Q(designation__icontains=query) |
            Q(bio__icontains=query) |
            Q(shortname__icontains=query) |
            Q(about__icontains=query) |
            Q(researches__icontains=query)
        ).select_related('base_user')[:20]
        results['faculty'] = list(faculty_results)
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error searching faculty: {str(e)}")
        # Fallback: try simpler search
        try:
            from people.models import Faculty
            faculty_results = Faculty.objects.filter(
                Q(name__icontains=query) |
                Q(designation__icontains=query) |
                Q(bio__icontains=query) |
                Q(shortname__icontains=query)
            ).select_related('base_user')[:20]
            results['faculty'] = list(faculty_results)
        except:
            results['faculty'] = []
    
    # Search Publications
    try:
        from people.models import Publication
        publication_results = Publication.objects.filter(
            Q(title__icontains=query) |
            Q(published_at__icontains=query) |
            Q(contribution__icontains=query) |
            Q(doi__icontains=query)
        ).select_related('faculty')[:20]
        results['publications'] = list(publication_results)
    except Exception as e:
        results['publications'] = []
    
    # Search Posts
    try:
        from office.models import Post
        post_results = Post.objects.filter(
            Q(short_title__icontains=query) |
            Q(long_title__icontains=query) |
            Q(description__icontains=query) |
            Q(tags__icontains=query)
        ).select_related('created_by')[:20]
        results['posts'] = list(post_results)
    except Exception as e:
        results['posts'] = []
    
    # Search Club Posts
    try:
        from clubs.models import ClubPost
        club_post_results = ClubPost.objects.filter(
            Q(short_title__icontains=query) |
            Q(long_title__icontains=query) |
            Q(description__icontains=query) |
            Q(tags__icontains=query)
        ).select_related('club', 'posted_by')[:20]
        results['club_posts'] = list(club_post_results)
    except Exception as e:
        results['club_posts'] = []
    
    # Search Courses
    try:
        from academics.models import Course
        course_results = Course.objects.filter(
            Q(title__icontains=query) |
            Q(course_code__icontains=query)
        ).select_related('program')[:20]
        results['courses'] = list(course_results)
    except Exception as e:
        results['courses'] = []
    
    # Search Clubs
    try:
        from clubs.models import Club
        club_results = Club.objects.filter(
            Q(name__icontains=query) |
            Q(short_name__icontains=query) |
            Q(moto__icontains=query) |
            Q(description__icontains=query)
        ).select_related('convener')[:20]
        results['clubs'] = list(club_results)
    except Exception as e:
        results['clubs'] = []
    
    # Search Staff
    try:
        from people.models import Staff
        staff_results = Staff.objects.filter(
            Q(name__icontains=query) |
            Q(designation__icontains=query)
        ).select_related('base_user')[:20]
        results['staff'] = list(staff_results)
    except Exception as e:
        results['staff'] = []
    
    # Search Officers
    try:
        from people.models import Officer
        officer_results = Officer.objects.filter(
            Q(name__icontains=query) |
            Q(position__icontains=query)
        ).select_related('base_user')[:20]
        results['officers'] = list(officer_results)
    except Exception as e:
        results['officers'] = []
    
    # Generate summary using text-based algorithm
    summary = generate_summary(results, query)
    
    context = {
        'query': query,
        'results': results,
        'summary': summary,
    }
    
    return render(request, 'search_results.html', context)

