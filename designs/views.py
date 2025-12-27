from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Max
from django.http import FileResponse, HttpResponse, JsonResponse
from django.views.decorators.http import require_http_methods
from ckeditor.fields import RichTextField
from .models import FeatureCard, AdmissionElement, AcademicCalendar, HeroTags, Curricula


def feature_cards_list(request):
    """Display all active feature cards"""
    cards = FeatureCard.objects.filter(is_active=True).order_by('sl_number')
    return render(request, 'designs/feature_cards_list.html', {'cards': cards})


def feature_card_detail(request, pk):
    """Display detailed view of a feature card"""
    card = get_object_or_404(FeatureCard, pk=pk, is_active=True)
    return render(request, 'designs/feature_card_detail.html', {'card': card})


@login_required
def manage_feature_cards(request):
    """Manage all feature cards - only for users with edit_feature_cards permission"""
    if not request.user.has_permission('edit_feature_cards'):
        messages.error(request, 'You do not have permission to manage feature cards.')
        return redirect('people:user_profile')
    
    # Exclude first 2 cards (lowest sl_number) - managed by super admin
    all_cards = FeatureCard.objects.all().order_by('sl_number')
    # Get the first 2 cards' sl_numbers
    first_two_sl_numbers = list(all_cards[:2].values_list('sl_number', flat=True))
    # Exclude those from the queryset
    cards = all_cards.exclude(sl_number__in=first_two_sl_numbers)
    
    context = {
        'cards': cards,
    }
    return render(request, 'designs/manage_feature_cards.html', context)


@login_required
def create_feature_card(request):
    """Create a new feature card"""
    if not request.user.has_permission('edit_feature_cards'):
        messages.error(request, 'You do not have permission to create feature cards.')
        return redirect('people:user_profile')
    
    if request.method == 'POST':
        try:
            card = FeatureCard()
            
            # Handle sl_number
            sl_number_str = request.POST.get('sl_number', '').strip()
            if sl_number_str:
                card.sl_number = int(sl_number_str)
            else:
                # Auto-assign sl_number if not provided
                max_sl = FeatureCard.objects.aggregate(max_sl=Max('sl_number'))['max_sl']
                card.sl_number = (max_sl + 1) if max_sl else 1
            
            card.caption = request.POST.get('caption', '').strip()
            card.title = request.POST.get('title', '').strip()
            card.description = request.POST.get('description', '')
            card.is_active = request.POST.get('is_active') == 'on'
            
            # Handle image upload
            if 'picture' in request.FILES:
                card.picture = request.FILES['picture']
            
            # Handle cropping field
            cropping = request.POST.get('cropping', '').strip()
            if cropping:
                card.cropping = cropping
            
            card.full_clean()
            card.save()
            
            messages.success(request, 'Feature card created successfully!')
            return redirect('designs:manage_feature_cards')
        except Exception as e:
            messages.error(request, f'Error creating feature card: {str(e)}')
            # Repopulate form
            context = {
                'card_data': request.POST,
            }
            return render(request, 'designs/create_feature_card.html', context)
    
    # Get next available sl_number
    max_sl = FeatureCard.objects.aggregate(max_sl=Max('sl_number'))['max_sl']
    next_sl = (max_sl + 1) if max_sl else 1
    
    context = {
        'next_sl': next_sl,
    }
    return render(request, 'designs/create_feature_card.html', context)


@login_required
def edit_feature_card(request, pk):
    """Edit an existing feature card"""
    if not request.user.has_permission('edit_feature_cards'):
        messages.error(request, 'You do not have permission to edit feature cards.')
        return redirect('people:user_profile')
    
    card = get_object_or_404(FeatureCard, pk=pk)
    
    # Prevent editing first 2 cards (managed by super admin)
    all_cards = FeatureCard.objects.all().order_by('sl_number')
    first_two_sl_numbers = list(all_cards[:2].values_list('sl_number', flat=True))
    if card.sl_number in first_two_sl_numbers:
        messages.error(request, 'This feature card is managed by super admin and cannot be edited here.')
        return redirect('designs:manage_feature_cards')
    
    if request.method == 'POST':
        try:
            sl_number_str = request.POST.get('sl_number', '').strip()
            if sl_number_str:
                card.sl_number = int(sl_number_str)
            card.caption = request.POST.get('caption', '').strip()
            card.title = request.POST.get('title', '').strip()
            card.description = request.POST.get('description', '')
            card.is_active = request.POST.get('is_active') == 'on'
            
            # Handle image upload (only if new image provided)
            if 'picture' in request.FILES:
                card.picture = request.FILES['picture']
            
            # Handle cropping field
            cropping = request.POST.get('cropping', '').strip()
            if cropping:
                card.cropping = cropping
            
            card.full_clean()
            card.save()
            
            messages.success(request, 'Feature card updated successfully!')
            return redirect('designs:manage_feature_cards')
        except Exception as e:
            messages.error(request, f'Error updating feature card: {str(e)}')
    
    context = {
        'card': card,
    }
    return render(request, 'designs/edit_feature_card.html', context)


@login_required
def delete_feature_card(request, pk):
    """Delete a feature card"""
    if not request.user.has_permission('edit_feature_cards'):
        messages.error(request, 'You do not have permission to delete feature cards.')
        return redirect('people:user_profile')
    
    card = get_object_or_404(FeatureCard, pk=pk)
    
    # Prevent deleting first 2 cards (managed by super admin)
    all_cards = FeatureCard.objects.all().order_by('sl_number')
    first_two_sl_numbers = list(all_cards[:2].values_list('sl_number', flat=True))
    if card.sl_number in first_two_sl_numbers:
        messages.error(request, 'This feature card is managed by super admin and cannot be deleted here.')
        return redirect('designs:manage_feature_cards')
    
    if request.method == 'POST':
        card_name = card.title
        card.delete()
        messages.success(request, f'Feature card "{card_name}" deleted successfully!')
        return redirect('designs:manage_feature_cards')
    
    context = {
        'card': card,
    }
    return render(request, 'designs/delete_feature_card.html', context)


@login_required
def manage_head_message(request):
    """Manage the head message (first feature card)"""
    if not request.user.has_permission('edit_head_message'):
        messages.error(request, 'You do not have permission to edit the head message.')
        return redirect('people:user_profile')
    
    # Get the first feature card (head message)
    hod_card = FeatureCard.objects.filter(is_active=True).order_by('sl_number').first()
    
    # If no card exists, create one
    if not hod_card:
        max_sl = FeatureCard.objects.aggregate(max_sl=Max('sl_number'))['max_sl']
        hod_card = FeatureCard.objects.create(
            sl_number=0 if max_sl is None else (max_sl - 1 if max_sl > 0 else 0),
            caption='Head of the Department',
            title='Dr. Shah Murtaza Rashid Al Masud',
            description='Welcome to the Department of Computer Science and Engineering (CSE) at University of Asia Pacific (UAP), Bangladesh.',
            is_active=True
        )
    
    if request.method == 'POST':
        try:
            hod_card.caption = request.POST.get('caption', '').strip()
            hod_card.title = request.POST.get('title', '').strip()
            hod_card.description = request.POST.get('description', '')
            hod_card.is_active = request.POST.get('is_active') == 'on'
            
            # Handle image upload (only if new image provided)
            if 'picture' in request.FILES:
                hod_card.picture = request.FILES['picture']
            
            hod_card.full_clean()
            hod_card.save()
            
            messages.success(request, 'Head message updated successfully!')
            return redirect('designs:manage_head_message')
        except Exception as e:
            messages.error(request, f'Error updating head message: {str(e)}')
    
    context = {
        'card': hod_card,
    }
    return render(request, 'designs/manage_head_message.html', context)


def admission_element_detail(request, pk):
    """Display admission element content dynamically"""
    element = get_object_or_404(AdmissionElement, pk=pk)
    
    # Check if this admission element is related to a program (e.g., "BSc in CSE")
    program = None
    courses = None
    lifetime_stats = None
    
    try:
        from academics.models import Program, Course
        
        # Try to find a program that matches the admission element title
        title_lower = element.title.lower()
        
        # Direct match: check if any program name is contained in the title or vice versa
        all_programs = Program.objects.all()
        for prog in all_programs:
            if prog.name.lower() in title_lower or title_lower in prog.name.lower():
                program = prog
                break
        
        # If no direct match, try matching common program patterns
        if not program:
            if 'bsc' in title_lower and ('cse' in title_lower or 'computer' in title_lower):
                program = Program.objects.filter(name__icontains='BSc').first()
            elif 'mcse' in title_lower or ('msc' in title_lower and 'cse' in title_lower):
                program = Program.objects.filter(name__icontains='MSc').first()
            # Fallback: use first program if title suggests it's a program page
            elif 'program' in title_lower or 'curriculum' in title_lower or 'course' in title_lower:
                program = Program.objects.first()
        
        # If we found a program, get its courses with outcomes and calculate stats
        if program:
            courses_list = []
            lifetime_stats = {
                'program_outcomes': {},  # PO1-PO12: {credits, marks}
                'blooms': {},  # K1-K6: {credits, marks}
                'knowledge': {},  # K1-K8: {credits, marks}
                'problem': {},  # P1-P7: {credits, marks}
                'activity': {},  # A1-A5: {credits, marks}
            }
            
            courses_queryset = Course.objects.filter(program=program).prefetch_related(
                'outcomes__program_outcome',
                'prerequisites'
            ).order_by('year_semester', 'course_code')
            
            # Calculate statistics for each course and lifetime statistics
            for course in courses_queryset:
                outcomes = course.outcomes.all()
                
                # Calculate unique counts
                unique_pos = set(outcome.program_outcome.code for outcome in outcomes)
                unique_ks = set(outcome.knowledge_profile for outcome in outcomes)
                unique_ps = set(outcome.problem_attribute for outcome in outcomes)
                unique_as = set(outcome.activity_attribute for outcome in outcomes if outcome.activity_attribute)
                unique_blooms = set(outcome.blooms_level for outcome in outcomes)
                
                # Add computed stats to course object
                course.stats = {
                    'co_count': len(outcomes),
                    'po_count': len(unique_pos),
                    'k_count': len(unique_ks),
                    'p_count': len(unique_ps),
                    'a_count': len(unique_as),
                    'blooms_count': len(unique_blooms),
                }
                
                # Calculate lifetime statistics
                course_credit = float(course.credit_hours)
                
                for outcome in outcomes:
                    # Program Outcomes (most important - Washington Accord)
                    po_code = outcome.program_outcome.code
                    if po_code:
                        if po_code not in lifetime_stats['program_outcomes']:
                            lifetime_stats['program_outcomes'][po_code] = {'credits': 0, 'marks': 0}
                        lifetime_stats['program_outcomes'][po_code]['credits'] += course_credit
                        lifetime_stats['program_outcomes'][po_code]['marks'] += outcome.total_assessment_marks
                    
                    # Bloom's levels
                    bloom = outcome.blooms_level
                    if bloom:
                        if bloom not in lifetime_stats['blooms']:
                            lifetime_stats['blooms'][bloom] = {'credits': 0, 'marks': 0}
                        lifetime_stats['blooms'][bloom]['credits'] += course_credit
                        lifetime_stats['blooms'][bloom]['marks'] += outcome.total_assessment_marks
                    
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
                
                courses_list.append(course)
            
            courses = courses_list
            
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
    except Exception:
        # Handle any other errors gracefully
        lifetime_stats = None
    
    # Get all Program Outcomes for the program
    program_outcomes = None
    if program:
        try:
            from academics.models import ProgramOutcome
            import re
            # Fetch all POs and sort them numerically by the number in the code
            pos_list = list(ProgramOutcome.objects.filter(program=program))
            # Sort by extracting the numeric part from the code (e.g., "PO1" -> 1, "PO10" -> 10)
            pos_list.sort(key=lambda po: int(re.search(r'\d+', po.code).group()) if re.search(r'\d+', po.code) else 0)
            program_outcomes = pos_list
        except ImportError:
            pass
        except Exception:
            # Fallback to simple ordering if regex fails
            try:
                from academics.models import ProgramOutcome
                program_outcomes = ProgramOutcome.objects.filter(program=program).order_by('code')
            except ImportError:
                pass
    
    # Get curricula based on admission element title
    # Normalize title for better pattern matching - handle variations like:
    # "BSc in CSE", "B.Sc. in CSE", "BSC in CSE", "Bachelor in Computer Science"
    # "MCSE", "MSc in CSE", "M.Sc. in CSE", "Master in Computer Science"
    import re
    curricula = None
    
    # Normalize: remove punctuation, convert to lowercase, normalize whitespace
    title_normalized = re.sub(r'[^\w\s]', '', element.title.lower())
    title_normalized = re.sub(r'\s+', ' ', title_normalized).strip()
    
    # Check for Bachelor program variations
    # Patterns: bsc, b.sc, bachelor, bachelor's, bachelor of science
    # Combined with: cse, computer, computer science, engineering
    is_bachelor = False
    is_master = False
    
    # Bachelor patterns - check for common variations
    bachelor_patterns = [
        r'\bb\.?sc\.?\b',  # BSc, B.Sc., BSC, B.S.C.
        r'\bbachelor',      # bachelor, bachelor's
        r'\bundergraduate', # undergraduate
    ]
    
    # CSE/Computer Science patterns
    cse_patterns = [
        r'\bcse\b',         # CSE
        r'\bcomputer',      # computer
        r'\bengineering',   # engineering
    ]
    
    # Check if title matches bachelor patterns
    has_bachelor = any(re.search(pattern, title_normalized, re.IGNORECASE) for pattern in bachelor_patterns)
    has_cse = any(re.search(pattern, title_normalized, re.IGNORECASE) for pattern in cse_patterns)
    
    # Bachelor program detected if it has bachelor keyword AND CSE keyword
    if has_bachelor and has_cse:
        is_bachelor = True
    
    # Master patterns - check for common variations
    master_patterns = [
        r'\bmcse\b',        # MCSE
        r'\bm\.?sc\.?\b',   # MSc, M.Sc., MSC, M.S.C.
        r'\bmaster',        # master, master's, masters
        r'\bgraduate',      # graduate
        r'\bpostgraduate',  # postgraduate
    ]
    
    # Check if title matches master patterns
    has_master = any(re.search(pattern, title_normalized, re.IGNORECASE) for pattern in master_patterns)
    
    # Master program detected if it has master keyword AND CSE keyword, OR just MCSE
    if has_master and has_cse:
        is_master = True
    elif re.search(r'\bmcse\b', title_normalized, re.IGNORECASE):
        # MCSE alone is enough (it's a specific program name)
        is_master = True
    
    # Filter curricula based on detected program
    from django.db.models import Case, When, IntegerField
    
    if is_bachelor and program:
        # Filter by program ForeignKey
        curricula = Curricula.objects.filter(program=program).annotate(
            semester_order=Case(
                When(running_since_semester='spring', then=1),
                When(running_since_semester='fall', then=2),
                default=3,
                output_field=IntegerField()
            )
        ).order_by('-running_since_year', 'semester_order', '-version')
    elif is_master and program:
        # Filter by program ForeignKey
        curricula = Curricula.objects.filter(program=program).annotate(
            semester_order=Case(
                When(running_since_semester='spring', then=1),
                When(running_since_semester='fall', then=2),
                default=3,
                output_field=IntegerField()
            )
        ).order_by('-running_since_year', 'semester_order', '-version')
    
    context = {
        'element': element,
        'program': program,
        'courses': courses,
        'lifetime_stats': lifetime_stats if program and courses else None,
        'program_outcomes': program_outcomes,
        'curricula': curricula,
    }
    
    return render(request, 'designs/admission_element_detail.html', context)


def academic_calendar_view(request):
    """Public view - Display the latest academic calendar"""
    latest_calendar = AcademicCalendar.objects.order_by('-created_at').first()
    all_calendars = AcademicCalendar.objects.order_by('-created_at')
    
    context = {
        'latest_calendar': latest_calendar,
        'all_calendars': all_calendars,
    }
    return render(request, 'designs/academic_calendar.html', context)


def serve_academic_calendar_pdf(request, pk):
    """
    Serve academic calendar PDF with proper headers for iframe embedding.
    Public access - no authentication required.
    """
    calendar = get_object_or_404(AcademicCalendar, pk=pk)
    
    if not calendar.pdf:
        return HttpResponse("PDF not found", status=404)
    
    try:
        # Get the file path
        file_path = calendar.pdf.path
        
        # Serve the file with proper headers
        response = FileResponse(
            open(file_path, 'rb'),
            content_type='application/pdf'
        )
        response['Content-Disposition'] = f'inline; filename="{calendar.pdf.name}"'
        response['X-Content-Type-Options'] = 'nosniff'
        
        # Allow iframe embedding from same origin
        response['X-Frame-Options'] = 'SAMEORIGIN'
        
        return response
    except FileNotFoundError:
        return HttpResponse("PDF file not found on server", status=404)
    except Exception as e:
        return HttpResponse(f"Error serving PDF: {str(e)}", status=500)


@login_required
def manage_academic_calendars(request):
    """Manage academic calendars - only for users with manage_academic_calendars permission"""
    if not request.user.has_permission('manage_academic_calendars'):
        messages.error(request, 'You do not have permission to manage academic calendars.')
        return redirect('people:user_profile')
    
    calendars = AcademicCalendar.objects.order_by('-created_at')
    
    context = {
        'calendars': calendars,
    }
    return render(request, 'designs/manage_academic_calendars.html', context)


@login_required
def create_academic_calendar(request):
    """Create a new academic calendar"""
    if not request.user.has_permission('manage_academic_calendars'):
        messages.error(request, 'You do not have permission to create academic calendars.')
        return redirect('people:user_profile')
    
    if request.method == 'POST':
        try:
            calendar = AcademicCalendar()
            calendar.year = request.POST.get('year', '').strip()
            
            if 'pdf' in request.FILES:
                calendar.pdf = request.FILES['pdf']
            else:
                messages.error(request, 'PDF file is required.')
                return render(request, 'designs/create_academic_calendar.html', {
                    'calendar_data': request.POST,
                })
            
            calendar.full_clean()
            calendar.save()
            
            messages.success(request, f'Academic calendar for {calendar.year} created successfully!')
            return redirect('designs:manage_academic_calendars')
        except Exception as e:
            messages.error(request, f'Error creating academic calendar: {str(e)}')
            return render(request, 'designs/create_academic_calendar.html', {
                'calendar_data': request.POST,
            })
    
    return render(request, 'designs/create_academic_calendar.html')


@login_required
def edit_academic_calendar(request, pk):
    """Edit an existing academic calendar"""
    if not request.user.has_permission('manage_academic_calendars'):
        messages.error(request, 'You do not have permission to edit academic calendars.')
        return redirect('people:user_profile')
    
    calendar = get_object_or_404(AcademicCalendar, pk=pk)
    
    if request.method == 'POST':
        try:
            calendar.year = request.POST.get('year', '').strip()
            
            # Handle PDF upload (only if new file provided)
            if 'pdf' in request.FILES:
                calendar.pdf = request.FILES['pdf']
            
            calendar.full_clean()
            calendar.save()
            
            messages.success(request, f'Academic calendar for {calendar.year} updated successfully!')
            return redirect('designs:manage_academic_calendars')
        except Exception as e:
            messages.error(request, f'Error updating academic calendar: {str(e)}')
    
    context = {
        'calendar': calendar,
    }
    return render(request, 'designs/edit_academic_calendar.html', context)


@login_required
def delete_academic_calendar(request, pk):
    """Delete an academic calendar"""
    if not request.user.has_permission('manage_academic_calendars'):
        messages.error(request, 'You do not have permission to delete academic calendars.')
        return redirect('people:user_profile')
    
    calendar = get_object_or_404(AcademicCalendar, pk=pk)
    
    if request.method == 'POST':
        year = calendar.year
        calendar.delete()
        messages.success(request, f'Academic calendar for {year} deleted successfully!')
        return redirect('designs:manage_academic_calendars')
    
    context = {
        'calendar': calendar,
    }
    return render(request, 'designs/delete_academic_calendar.html', context)


# ==============================================================================
# HERO TAGS MANAGEMENT (Power Users Only)
# ==============================================================================

@login_required
def manage_hero_tags(request):
    """Manage hero tags - only for power users"""
    if not request.user.is_power_user:
        messages.error(request, 'Only power users can manage hero tags.')
        return redirect('people:user_profile')
    
    hero_tags = HeroTags.objects.all().order_by('sl')
    
    context = {
        'hero_tags': hero_tags,
    }
    return render(request, 'designs/manage_hero_tags.html', context)


@login_required
def create_hero_tag(request):
    """Create a new hero tag"""
    if not request.user.is_power_user:
        messages.error(request, 'Only power users can create hero tags.')
        return redirect('people:user_profile')
    
    if request.method == 'POST':
        try:
            tag = HeroTags()
            
            # Handle sl
            sl_str = request.POST.get('sl', '').strip()
            if sl_str:
                tag.sl = int(sl_str)
            else:
                # Auto-assign sl if not provided
                max_sl = HeroTags.objects.aggregate(max_sl=Max('sl'))['max_sl']
                tag.sl = (max_sl + 1) if max_sl else 1
            
            tag.title = request.POST.get('title', '').strip()
            tag.is_active = request.POST.get('is_active') == 'on'
            
            tag.full_clean()
            tag.save()
            
            messages.success(request, 'Hero tag created successfully!')
            return redirect('designs:manage_hero_tags')
        except Exception as e:
            messages.error(request, f'Error creating hero tag: {str(e)}')
            return render(request, 'designs/create_hero_tag.html', {
                'tag_data': request.POST,
            })
    
    # Get next available sl
    max_sl = HeroTags.objects.aggregate(max_sl=Max('sl'))['max_sl']
    next_sl = (max_sl + 1) if max_sl else 1
    
    context = {
        'next_sl': next_sl,
    }
    return render(request, 'designs/create_hero_tag.html', context)


@login_required
def edit_hero_tag(request, pk):
    """Edit an existing hero tag"""
    if not request.user.is_power_user:
        messages.error(request, 'Only power users can edit hero tags.')
        return redirect('people:user_profile')
    
    tag = get_object_or_404(HeroTags, pk=pk)
    
    if request.method == 'POST':
        try:
            sl_str = request.POST.get('sl', '').strip()
            if sl_str:
                tag.sl = int(sl_str)
            tag.title = request.POST.get('title', '').strip()
            tag.is_active = request.POST.get('is_active') == 'on'
            
            tag.full_clean()
            tag.save()
            
            messages.success(request, 'Hero tag updated successfully!')
            return redirect('designs:manage_hero_tags')
        except Exception as e:
            messages.error(request, f'Error updating hero tag: {str(e)}')
    
    context = {
        'tag': tag,
    }
    return render(request, 'designs/edit_hero_tag.html', context)


@login_required
def delete_hero_tag(request, pk):
    """Delete a hero tag"""
    if not request.user.is_power_user:
        messages.error(request, 'Only power users can delete hero tags.')
        return redirect('people:user_profile')
    
    tag = get_object_or_404(HeroTags, pk=pk)
    
    if request.method == 'POST':
        tag_title = tag.title
        tag.delete()
        messages.success(request, f'Hero tag "{tag_title}" deleted successfully!')
        return redirect('designs:manage_hero_tags')
    
    context = {
        'tag': tag,
    }
    return render(request, 'designs/delete_hero_tag.html', context)


@login_required
@require_http_methods(["POST"])
def update_hero_tag_order(request):
    """Update the order (serial numbers) of hero tags via drag and drop"""
    if not request.user.is_power_user:
        return JsonResponse({
            'success': False,
            'message': 'Only power users can update hero tag order.'
        }, status=403)
    
    try:
        import json
        data = json.loads(request.body)
        tag_ids = data.get('tag_ids', [])
        
        if not tag_ids:
            return JsonResponse({
                'success': False,
                'message': 'No tags provided for reordering.'
            }, status=400)
        
        # Verify all tags exist
        tags = HeroTags.objects.filter(pk__in=tag_ids)
        if tags.count() != len(tag_ids):
            return JsonResponse({
                'success': False,
                'message': 'Some tags do not exist.'
            }, status=400)
        
        # Update serial numbers based on the order provided
        for index, tag_id in enumerate(tag_ids, start=1):
            HeroTags.objects.filter(pk=tag_id).update(sl=index)
        
        return JsonResponse({
            'success': True,
            'message': 'Hero tag order updated successfully!'
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
# CURRICULA MANAGEMENT
# ==============================================================================

@login_required
def manage_curricula(request):
    """Manage curricula - only for users with manage_academic_calendars permission"""
    if not request.user.has_permission('manage_academic_calendars'):
        messages.error(request, 'You do not have permission to manage curricula.')
        return redirect('people:user_profile')
    
    # Get all curricula and sort them properly
    # Spring should come before Fall, so we need custom sorting
    from django.db.models import Case, When, IntegerField
    curricula = Curricula.objects.annotate(
        semester_order=Case(
            When(running_since_semester='spring', then=1),
            When(running_since_semester='fall', then=2),
            default=3,
            output_field=IntegerField()
        )
    ).order_by('program', '-running_since_year', 'semester_order', '-version')
    
    context = {
        'curricula': curricula,
    }
    return render(request, 'designs/manage_curricula.html', context)


@login_required
def create_curriculum(request):
    """Create a new curriculum"""
    if not request.user.has_permission('manage_academic_calendars'):
        messages.error(request, 'You do not have permission to create curricula.')
        return redirect('people:user_profile')
    
    if request.method == 'POST':
        try:
            curriculum = Curricula()
            curriculum.short_title = request.POST.get('short_title', '').strip()
            curriculum.program = request.POST.get('program', 'bachelor')
            
            # Handle publishing_year
            publishing_year_str = request.POST.get('publishing_year', '').strip()
            if publishing_year_str:
                curriculum.publishing_year = int(publishing_year_str)
            else:
                messages.error(request, 'Publishing year is required.')
                return render(request, 'designs/create_curriculum.html', {
                    'curriculum_data': request.POST,
                })
            
            # Handle version
            version_str = request.POST.get('version', '').strip()
            if version_str:
                curriculum.version = float(version_str)
            else:
                messages.error(request, 'Version is required.')
                return render(request, 'designs/create_curriculum.html', {
                    'curriculum_data': request.POST,
                })
            
            # Handle running_since_year
            curriculum.running_since_year = request.POST.get('running_since_year', '').strip()
            if not curriculum.running_since_year:
                messages.error(request, 'Running since year is required.')
                return render(request, 'designs/create_curriculum.html', {
                    'curriculum_data': request.POST,
                })
            
            # Handle running_since_semester
            curriculum.running_since_semester = request.POST.get('running_since_semester', 'spring')
            
            if 'pdf' in request.FILES:
                curriculum.pdf = request.FILES['pdf']
            else:
                messages.error(request, 'PDF file is required.')
                return render(request, 'designs/create_curriculum.html', {
                    'curriculum_data': request.POST,
                })
            
            curriculum.full_clean()
            curriculum.save()
            
            messages.success(request, f'Curriculum "{curriculum.short_title}" created successfully!')
            return redirect('designs:manage_curricula')
        except ValueError as e:
            messages.error(request, f'Invalid input: {str(e)}')
            return render(request, 'designs/create_curriculum.html', {
                'curriculum_data': request.POST,
            })
        except Exception as e:
            messages.error(request, f'Error creating curriculum: {str(e)}')
            return render(request, 'designs/create_curriculum.html', {
                'curriculum_data': request.POST,
            })
    
    return render(request, 'designs/create_curriculum.html')


@login_required
def edit_curriculum(request, pk):
    """Edit an existing curriculum"""
    if not request.user.has_permission('manage_academic_calendars'):
        messages.error(request, 'You do not have permission to edit curricula.')
        return redirect('people:user_profile')
    
    curriculum = get_object_or_404(Curricula, pk=pk)
    
    if request.method == 'POST':
        try:
            curriculum.short_title = request.POST.get('short_title', '').strip()
            curriculum.program = request.POST.get('program', 'bachelor')
            
            # Handle publishing_year
            publishing_year_str = request.POST.get('publishing_year', '').strip()
            if publishing_year_str:
                curriculum.publishing_year = int(publishing_year_str)
            
            # Handle version
            version_str = request.POST.get('version', '').strip()
            if version_str:
                curriculum.version = float(version_str)
            
            # Handle running_since_year
            running_since_year = request.POST.get('running_since_year', '').strip()
            if running_since_year:
                curriculum.running_since_year = running_since_year
            
            # Handle running_since_semester
            running_since_semester = request.POST.get('running_since_semester', 'spring')
            if running_since_semester:
                curriculum.running_since_semester = running_since_semester
            
            # Handle PDF upload (only if new file provided)
            if 'pdf' in request.FILES:
                curriculum.pdf = request.FILES['pdf']
            
            curriculum.full_clean()
            curriculum.save()
            
            messages.success(request, f'Curriculum "{curriculum.short_title}" updated successfully!')
            return redirect('designs:manage_curricula')
        except ValueError as e:
            messages.error(request, f'Invalid input: {str(e)}')
        except Exception as e:
            messages.error(request, f'Error updating curriculum: {str(e)}')
    
    context = {
        'curriculum': curriculum,
    }
    return render(request, 'designs/edit_curriculum.html', context)


@login_required
def delete_curriculum(request, pk):
    """Delete a curriculum"""
    if not request.user.has_permission('manage_academic_calendars'):
        messages.error(request, 'You do not have permission to delete curricula.')
        return redirect('people:user_profile')
    
    curriculum = get_object_or_404(Curricula, pk=pk)
    
    if request.method == 'POST':
        short_title = curriculum.short_title
        curriculum.delete()
        messages.success(request, f'Curriculum "{short_title}" deleted successfully!')
        return redirect('designs:manage_curricula')
    
    context = {
        'curriculum': curriculum,
    }
    return render(request, 'designs/delete_curriculum.html', context)


def serve_curriculum_pdf(request, pk):
    """
    Serve curriculum PDF with proper headers for iframe embedding.
    Public access - no authentication required.
    """
    curriculum = get_object_or_404(Curricula, pk=pk)
    
    if not curriculum.pdf:
        return HttpResponse("PDF not found", status=404)
    
    try:
        # Get the file path
        file_path = curriculum.pdf.path
        
        # Serve the file with proper headers
        response = FileResponse(
            open(file_path, 'rb'),
            content_type='application/pdf'
        )
        response['Content-Disposition'] = f'inline; filename="{curriculum.pdf.name}"'
        response['X-Content-Type-Options'] = 'nosniff'
        
        # Allow iframe embedding from same origin
        response['X-Frame-Options'] = 'SAMEORIGIN'
        
        return response
    except FileNotFoundError:
        return HttpResponse("PDF file not found on server", status=404)
    except Exception as e:
        return HttpResponse(f"Error serving PDF: {str(e)}", status=500)
