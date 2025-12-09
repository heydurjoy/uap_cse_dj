from django.shortcuts import render, get_object_or_404
from easy_thumbnails.files import get_thumbnailer
from .models import FeatureCard, AdmissionElement

def feature_cards_list(request):
    """Display all active feature cards"""
    cards = FeatureCard.objects.filter(is_active=True).order_by('sl_number')
    return render(request, 'designs/feature_cards_list.html', {'cards': cards})

def feature_card_detail(request, pk):
    """Display detailed view of a feature card"""
    card = get_object_or_404(FeatureCard, pk=pk, is_active=True)
    return render(request, 'designs/feature_card_detail.html', {'card': card})

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
    
    context = {
        'element': element,
        'program': program,
        'courses': courses,
        'lifetime_stats': lifetime_stats if program and courses else None,
        'program_outcomes': program_outcomes,
    }
    
    return render(request, 'designs/admission_element_detail.html', context)

