from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from .models import Program, Course, CourseOutcome, ProgramOutcome


def check_course_access(user):
    """Check if user has access level 3 or higher"""
    if not user.is_authenticated:
        return False
    try:
        access_level = int(user.access_level) if user.access_level else 0
        return access_level >= 3
    except (ValueError, TypeError):
        return False


@login_required
def manage_courses(request):
    """Course management view for level 3+ users"""
    if not check_course_access(request.user):
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('people:user_profile')

    # Get all programs and courses
    programs = Program.objects.all().prefetch_related('courses')

    courses = Course.objects.all() \
        .select_related('program') \
        .prefetch_related('outcomes') \
        .order_by('program', 'year_semester', 'course_type', 'course_code')

    # Filter by program if specified
    program_id = request.GET.get('program')
    if program_id:
        try:
            selected_program = Program.objects.get(pk=program_id)
            courses = courses.filter(program=selected_program)
        except Program.DoesNotExist:
            selected_program = None
    else:
        selected_program = None
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        courses = courses.filter(
            Q(course_code__icontains=search_query) |
            Q(title__icontains=search_query)
        )
    
    # Calculate total marks and check for warnings for each course
    for course in courses:
        total_marks = sum(co.total_assessment_marks for co in course.outcomes.all())
        course.total_marks = total_marks
        course.has_warnings = total_marks != 100 or not course.course_outline_pdf
    
    context = {
        'programs': programs,
        'courses': courses,
        'selected_program': selected_program,
        'search_query': search_query,
    }
    
    return render(request, 'academics/manage_courses.html', context)


@login_required
def edit_course(request, pk):
    """Edit a single course"""
    if not check_course_access(request.user):
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('people:user_profile')
    
    course = get_object_or_404(Course, pk=pk)
    programs = Program.objects.all()
    
    if request.method == 'POST':
        try:
            course.program = Program.objects.get(pk=request.POST.get('program'))
            course.course_code = request.POST.get('course_code', '').strip()
            course.title = request.POST.get('title', '').strip()
            course.credit_hours = float(request.POST.get('credit_hours', 0))
            course.contact_hours = float(request.POST.get('contact_hours', 0))
            course.course_type = request.POST.get('course_type', 'TH')
            course.year_semester = request.POST.get('year_semester', '1-1')
            
            if 'course_outline_pdf' in request.FILES:
                course.course_outline_pdf = request.FILES['course_outline_pdf']
            
            # Handle prerequisites
            prerequisite_ids = request.POST.getlist('prerequisites')
            course.prerequisites.set(prerequisite_ids)
            
            course.save()
            
            # Handle Course Learning Outcomes (CLOs) - create/update/delete
            # Process CO data from form - find all CO prefixes
            co_prefixes = set()
            for key in request.POST.keys():
                if key.startswith('co_') and '_sequence' in key:
                    # Extract prefix: co_123 or co_new_1
                    prefix = key.replace('_sequence', '')
                    co_prefixes.add(prefix)
            
            existing_co_ids = []
            
            for prefix in co_prefixes:
                co_id = request.POST.get(f'{prefix}_id', '').strip()
                sequence_num = request.POST.get(f'{prefix}_sequence', '').strip()
                statement = request.POST.get(f'{prefix}_statement', '').strip()
                po_id = request.POST.get(f'{prefix}_po', '').strip()
                blooms = request.POST.get(f'{prefix}_blooms', '').strip()
                kp = request.POST.get(f'{prefix}_kp', '').strip()
                pa = request.POST.get(f'{prefix}_pa', '').strip()
                aa = request.POST.get(f'{prefix}_aa', '').strip() or None
                marks = request.POST.get(f'{prefix}_marks', '0').strip()
                activity = request.POST.get(f'{prefix}_activity', '').strip()
                
                if sequence_num and statement and po_id and blooms and kp and pa:
                    try:
                        if co_id and co_id != 'new' and co_id != '':
                            # Update existing CO
                            co = CourseOutcome.objects.get(pk=int(co_id), course=course)
                            co.sequence_number = int(sequence_num)
                            co.statement = statement
                            co.program_outcome = ProgramOutcome.objects.get(pk=int(po_id))
                            co.blooms_level = blooms
                            co.knowledge_profile = kp
                            co.problem_attribute = pa
                            co.activity_attribute = aa
                            co.total_assessment_marks = int(marks) if marks else 0
                            co.activity = activity
                            co.save()
                            existing_co_ids.append(int(co_id))
                        else:
                            # Create new CO
                            new_co = CourseOutcome.objects.create(
                                course=course,
                                sequence_number=int(sequence_num),
                                statement=statement,
                                program_outcome=ProgramOutcome.objects.get(pk=int(po_id)),
                                blooms_level=blooms,
                                knowledge_profile=kp,
                                problem_attribute=pa,
                                activity_attribute=aa,
                                total_assessment_marks=int(marks) if marks else 0,
                                activity=activity
                            )
                            existing_co_ids.append(new_co.pk)
                    except (ValueError, CourseOutcome.DoesNotExist, ProgramOutcome.DoesNotExist) as e:
                        messages.warning(request, f'Error saving CO {sequence_num}: {str(e)}')
            
            # Delete COs that were removed (not in existing_co_ids)
            if existing_co_ids:
                CourseOutcome.objects.filter(course=course).exclude(pk__in=existing_co_ids).delete()
            else:
                # If no COs were submitted, delete all existing ones
                CourseOutcome.objects.filter(course=course).delete()
            
            messages.success(request, f'Course {course.course_code} updated successfully!')
            return redirect('academics:manage_courses')
        except Exception as e:
            messages.error(request, f'Error updating course: {str(e)}')
    
    # Get all courses for prerequisites (excluding current course)
    all_courses = Course.objects.exclude(pk=course.pk).order_by('course_code')
    
    # Get all Course Learning Outcomes for this course
    course_outcomes = CourseOutcome.objects.filter(course=course).select_related('program_outcome').order_by('sequence_number')
    
    # Get Program Learning Outcomes for the course's program
    program_outcomes = ProgramOutcome.objects.filter(program=course.program).order_by('code')
    
    # Calculate total marks
    total_marks = sum(co.total_assessment_marks for co in course_outcomes)
    
    context = {
        'course': course,
        'programs': programs,
        'all_courses': all_courses,
        'course_outcomes': course_outcomes,
        'program_outcomes': program_outcomes,
        'total_marks': total_marks,
    }
    
    return render(request, 'academics/edit_course.html', context)


def courses_list(request):
    """View all courses organized by program, year-semester - publicly accessible"""
    # Get all programs
    programs = Program.objects.all().order_by('name')
    
    # Get all courses with related data
    courses_queryset = Course.objects.select_related('program')\
        .prefetch_related('outcomes__program_outcome', 'prerequisites')\
        .order_by('program', 'year_semester', 'course_code')
    
    # Filter by program if specified
    program_id = request.GET.get('program')
    selected_program = None
    if program_id:
        try:
            selected_program = Program.objects.get(pk=program_id)
            courses_queryset = courses_queryset.filter(program=selected_program)
        except Program.DoesNotExist:
            selected_program = None
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        courses_queryset = courses_queryset.filter(
            Q(course_code__icontains=search_query) |
            Q(title__icontains=search_query)
        )
    
    # Calculate stats for each course
    courses_list = []
    for course in courses_queryset:
        outcomes = course.outcomes.all()
        
        # Calculate unique counts
        unique_pos = set(outcome.program_outcome.code for outcome in outcomes if outcome.program_outcome)
        unique_ks = set(outcome.knowledge_profile for outcome in outcomes if outcome.knowledge_profile)
        unique_ps = set(outcome.problem_attribute for outcome in outcomes if outcome.problem_attribute)
        unique_as = set(outcome.activity_attribute for outcome in outcomes if outcome.activity_attribute)
        unique_blooms = set(outcome.blooms_level for outcome in outcomes if outcome.blooms_level)
        
        # Add computed stats to course object
        course.stats = {
            'co_count': len(outcomes),
            'po_count': len(unique_pos),
            'k_count': len(unique_ks),
            'p_count': len(unique_ps),
            'a_count': len(unique_as),
            'blooms_count': len(unique_blooms),
        }
        
        courses_list.append(course)
    
    # Organize courses by program and calculate lifetime stats
    programs_with_courses = []
    for program in programs:
        program_courses = [c for c in courses_list if c.program == program]
        if program_courses or not selected_program:  # Show program if it has courses or if no filter is applied
            # Calculate lifetime statistics for this program
            lifetime_stats = {
                'program_outcomes': {},  # PO1-PO12: {credits, marks}
                'blooms': {},  # K1-K6: {credits, marks}
                'knowledge': {},  # K1-K8: {credits, marks}
                'problem': {},  # P1-P7: {credits, marks}
                'activity': {},  # A1-A5: {credits, marks}
            }
            
            for course in program_courses:
                outcomes = course.outcomes.all()
                course_credit = float(course.credit_hours)
                
                for outcome in outcomes:
                    # Program Outcomes
                    if outcome.program_outcome and outcome.program_outcome.code:
                        po_code = outcome.program_outcome.code
                        if po_code not in lifetime_stats['program_outcomes']:
                            lifetime_stats['program_outcomes'][po_code] = {'credits': 0, 'marks': 0}
                        lifetime_stats['program_outcomes'][po_code]['credits'] += course_credit
                        lifetime_stats['program_outcomes'][po_code]['marks'] += outcome.total_assessment_marks
                    
                    # Bloom's levels
                    if outcome.blooms_level:
                        bloom = outcome.blooms_level
                        if bloom not in lifetime_stats['blooms']:
                            lifetime_stats['blooms'][bloom] = {'credits': 0, 'marks': 0}
                        lifetime_stats['blooms'][bloom]['credits'] += course_credit
                        lifetime_stats['blooms'][bloom]['marks'] += outcome.total_assessment_marks
                    
                    # Knowledge profiles
                    if outcome.knowledge_profile:
                        kp = outcome.knowledge_profile
                        if kp not in lifetime_stats['knowledge']:
                            lifetime_stats['knowledge'][kp] = {'credits': 0, 'marks': 0}
                        lifetime_stats['knowledge'][kp]['credits'] += course_credit
                        lifetime_stats['knowledge'][kp]['marks'] += outcome.total_assessment_marks
                    
                    # Problem attributes
                    if outcome.problem_attribute:
                        pa = outcome.problem_attribute
                        if pa not in lifetime_stats['problem']:
                            lifetime_stats['problem'][pa] = {'credits': 0, 'marks': 0}
                        lifetime_stats['problem'][pa]['credits'] += course_credit
                        lifetime_stats['problem'][pa]['marks'] += outcome.total_assessment_marks
                    
                    # Activity attributes
                    if outcome.activity_attribute:
                        aa = outcome.activity_attribute
                        if aa not in lifetime_stats['activity']:
                            lifetime_stats['activity'][aa] = {'credits': 0, 'marks': 0}
                        lifetime_stats['activity'][aa]['credits'] += course_credit
                        lifetime_stats['activity'][aa]['marks'] += outcome.total_assessment_marks
            
            # Calculate total marks for each category
            lifetime_stats['totals'] = {
                'program_outcomes': sum(data['marks'] for data in lifetime_stats['program_outcomes'].values()),
                'blooms': sum(data['marks'] for data in lifetime_stats['blooms'].values()),
                'knowledge': sum(data['marks'] for data in lifetime_stats['knowledge'].values()),
                'problem': sum(data['marks'] for data in lifetime_stats['problem'].values()),
                'activity': sum(data['marks'] for data in lifetime_stats['activity'].values()),
            }
            
            # Get Program Outcomes for this program
            import re
            program_outcomes_list = list(ProgramOutcome.objects.filter(program=program))
            program_outcomes_list = sorted(
                program_outcomes_list,
                key=lambda po: int(re.search(r'\d+', po.code).group()) if re.search(r'\d+', po.code) else 0
            )
            
            programs_with_courses.append({
                'program': program,
                'courses': program_courses,
                'lifetime_stats': lifetime_stats,
                'program_outcomes': program_outcomes_list,
            })
    
    context = {
        'programs': programs,
        'programs_with_courses': programs_with_courses,
        'selected_program': selected_program,
        'search_query': search_query,
    }
    
    return render(request, 'academics/courses_list.html', context)


def course_detail(request, pk):
    """View course details - publicly accessible"""
    course = get_object_or_404(
        Course.objects.select_related('program')
        .prefetch_related('prerequisites', 'outcomes__program_outcome'),
        pk=pk
    )
    
    # Get all Course Learning Outcomes for this course
    course_outcomes = CourseOutcome.objects.filter(course=course)\
        .select_related('program_outcome')\
        .order_by('sequence_number')
    
    # Get all Program Outcomes for the course's program
    # Sort numerically by extracting the number from the code (e.g., "PO1", "PO2", "PO10")
    import re
    program_outcomes = list(ProgramOutcome.objects.filter(program=course.program).all())
    # Sort by extracting numeric part from code
    program_outcomes = sorted(program_outcomes, key=lambda po: int(re.search(r'\d+', po.code).group()) if re.search(r'\d+', po.code) else 0)
    
    # Calculate total marks
    total_marks = sum(co.total_assessment_marks for co in course_outcomes)
    
    context = {
        'course': course,
        'course_outcomes': course_outcomes,
        'program_outcomes': program_outcomes,
        'total_marks': total_marks,
    }
    
    return render(request, 'academics/course_detail.html', context)


@login_required
@require_http_methods(["POST"])
def delete_courses(request):
    """Bulk delete courses"""
    if not check_course_access(request.user):
        return JsonResponse({'success': False, 'error': 'Permission denied'}, status=403)
    
    course_ids = request.POST.getlist('course_ids[]')
    if not course_ids:
        return JsonResponse({'success': False, 'error': 'No courses selected'})
    
    try:
        deleted_count = Course.objects.filter(pk__in=course_ids).delete()[0]
        return JsonResponse({
            'success': True,
            'message': f'{deleted_count} course(s) deleted successfully',
            'deleted_count': deleted_count
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})
