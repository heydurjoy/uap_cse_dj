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
    courses = Course.objects.all().select_related('program').prefetch_related('outcomes').order_by('program', 'year_semester', 'course_code')
    
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
            
            # Handle Course Outcomes (COs) - create/update/delete
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
    
    # Get all Course Outcomes for this course
    course_outcomes = CourseOutcome.objects.filter(course=course).select_related('program_outcome').order_by('sequence_number')
    
    # Get Program Outcomes for the course's program
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
