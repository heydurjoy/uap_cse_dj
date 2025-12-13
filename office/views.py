from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.http import JsonResponse, Http404, HttpResponse, FileResponse
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.urls import reverse
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from datetime import datetime
import os
from .models import Post, PostAttachment, AdmissionResult, POST_TYPE_CHOICES, ClassRoutine, SEMESTER_CHOICES
from django.utils import timezone


def post_list(request):
    """
    Display list of all posts with search, filter, and sort functionality.
    Includes both regular posts and club posts.
    """
    # Get all regular posts
    posts = Post.objects.all()
    
    # Get all club posts
    try:
        from clubs.models import ClubPost, Club
        club_posts = ClubPost.objects.all()
        all_clubs = Club.objects.all().order_by('sl', 'name')
    except (ImportError, AttributeError):
        # If clubs app doesn't exist, create empty queryset
        club_posts = Post.objects.none()  # Use Post queryset as fallback (will be empty)
        all_clubs = []
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        posts = posts.filter(
            Q(short_title__icontains=search_query) |
            Q(long_title__icontains=search_query) |
            Q(tags__icontains=search_query) |
            Q(description__icontains=search_query)
        )
        club_posts = club_posts.filter(
            Q(short_title__icontains=search_query) |
            Q(long_title__icontains=search_query) |
            Q(tags__icontains=search_query) |
            Q(description__icontains=search_query)
        )
    
    # Filter by post type
    post_type_filter = request.GET.get('type', '')
    if post_type_filter:
        posts = posts.filter(post_type=post_type_filter)
        club_posts = club_posts.filter(post_type=post_type_filter)
    
    # Filter by club
    club_filter = request.GET.get('club', '')
    if club_filter:
        club_posts = club_posts.filter(club_id=club_filter)
    
    # Create unified list with type indicator
    unified_posts = []
    
    # Add regular posts (only if no club filter is selected)
    if not club_filter:
        for post in posts:
            unified_posts.append({
                'type': 'post',
                'object': post,
                'is_pinned': post.is_pinned,
                'date': post.publish_date,
            })
    
    # Add club posts
    for club_post in club_posts:
        unified_posts.append({
            'type': 'club_post',
            'object': club_post,
            'is_pinned': club_post.is_pinned,
            'date': club_post.created_at,
        })
    
    # Sort functionality
    sort_by = request.GET.get('sort', 'pinned')
    if sort_by == 'oldest':
        unified_posts.sort(key=lambda p: p['date'])
    elif sort_by == 'newest':
        unified_posts.sort(key=lambda p: p['date'], reverse=True)
    elif sort_by == 'type':
        unified_posts.sort(key=lambda p: (p['object'].post_type if hasattr(p['object'], 'post_type') else '', p['date']), reverse=True)
    elif sort_by == 'club':
        unified_posts.sort(key=lambda p: (p['object'].club.name if p['type'] == 'club_post' else 'ZZZ', p['date']), reverse=True)
    elif sort_by == 'pinned':
        # Pinned first, then by date
        unified_posts.sort(key=lambda p: (not p['is_pinned'], p['date']), reverse=True)
    else:
        # Default: pinned first, then by date
        unified_posts.sort(key=lambda p: (not p['is_pinned'], p['date']), reverse=True)
    
    # Count posts by type for stats
    total_posts_count = len(unified_posts)
    posts_by_type = {}
    for code, display in POST_TYPE_CHOICES:
        posts_by_type[code] = Post.objects.filter(post_type=code).count()
        # Add club posts of same type
        posts_by_type[code] += club_posts.filter(post_type=code).count()
    
    # Pagination - 12 posts per page (matching activities page)
    paginator = Paginator(unified_posts, 12)
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
        'POST_TYPE_CHOICES': POST_TYPE_CHOICES,
        'posts_by_type': posts_by_type,
        'total_posts': total_posts_count,
        'all_clubs': all_clubs,
        'paginator': paginator,
        'is_paginated': posts_page.has_other_pages(),
    }
    return render(request, 'office/post_list.html', context)


def notifications_api(request):
    """
    API endpoint to fetch recent posts for notifications.
    Returns top 10 most recent posts.
    """
    posts = Post.objects.all().order_by('-is_pinned', '-publish_date')[:10]
    
    notifications = []
    for post in posts:
        notifications.append({
            'id': post.pk,
            'title': post.short_title,
            'description': post.long_title[:100] + '...' if len(post.long_title) > 100 else post.long_title,
            'type': post.post_type,
            'type_display': post.get_post_type_display(),
            'date': post.publish_date.isoformat(),
            'is_pinned': post.is_pinned,
            'url': reverse('office:post_detail', args=[post.pk]),
        })
    
    return JsonResponse({
        'notifications': notifications
    })


def post_detail(request, pk):
    """
    Display detailed view of a single post.
    """
    post = get_object_or_404(Post, pk=pk)
    
    context = {
        'post': post,
    }
    return render(request, 'office/post_detail.html', context)


def check_post_access(user):
    """Check if user has permission to create/manage posts"""
    if not user.is_authenticated:
        return False
    # Users with post_notices or manage_all_posts can create posts
    return user.has_permission('post_notices') or user.has_permission('manage_all_posts')


@login_required
def manage_posts(request):
    """
    Manage posts view with filtering.
    - Level 4+ users: Can manage all posts, filter by creator and pinned status
    - Level 3 users: Can only manage their own posts
    """
    if not check_post_access(request.user):
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('people:user_profile')
    
    # Check permissions
    can_manage_all = request.user.has_permission('manage_all_posts')
    can_post_notices = request.user.has_permission('post_notices')
    
    # Base queryset
    if can_manage_all:
        # Users with manage_all_posts can see all posts
        posts = Post.objects.all()
    elif can_post_notices:
        # Users with post_notices can only see their own posts
        posts = Post.objects.filter(created_by=request.user)
    else:
        # No permission - should not reach here due to check_post_access, but handle gracefully
        posts = Post.objects.none()
    
    # Filter by creator (only for users who can manage all)
    created_by_filter = request.GET.get('created_by', 'all')
    if can_manage_all:
        if created_by_filter == 'own':
            posts = posts.filter(created_by=request.user)
    
    # Filter by pinned status
    pinned_filter = request.GET.get('pinned', 'all')
    if pinned_filter == 'yes':
        posts = posts.filter(is_pinned=True)
    elif pinned_filter == 'no':
        posts = posts.filter(is_pinned=False)
    
    # Filter by post type
    post_type_filter = request.GET.get('post_type', '')
    if post_type_filter:
        posts = posts.filter(post_type=post_type_filter)
    
    # Search
    search_query = request.GET.get('search', '')
    if search_query:
        posts = posts.filter(
            Q(short_title__icontains=search_query) |
            Q(long_title__icontains=search_query) |
            Q(tags__icontains=search_query)
        )
    
    # Order by pinned first, then by date
    posts = posts.order_by('-is_pinned', '-publish_date')
    
    context = {
        'posts': posts,
        'can_manage_all': can_manage_all,
        'can_post_notices': can_post_notices,
        'created_by_filter': created_by_filter,
        'pinned_filter': pinned_filter,
        'post_type_filter': post_type_filter,
        'search_query': search_query,
        'POST_TYPE_CHOICES': POST_TYPE_CHOICES,
    }
    return render(request, 'office/manage_posts.html', context)


@login_required
def create_post(request):
    """
    Create a new post.
    Only level 3+ users can create posts.
    """
    if not check_post_access(request.user):
        messages.error(request, 'You do not have permission to create posts.')
        return redirect('people:user_profile')
    
    if request.method == 'POST':
        try:
            from ckeditor.fields import RichTextField
            from django.utils import timezone
            
            post = Post()
            post.post_type = request.POST.get('post_type', 'notice')
            post.short_title = request.POST.get('short_title', '').strip()
            post.long_title = request.POST.get('long_title', '').strip()
            post.tags = request.POST.get('tags', '').strip()
            post.description = request.POST.get('description', '')
            post.is_pinned = request.POST.get('is_pinned') == 'on'
            post.created_by = request.user
            
            # Check permissions
            can_manage_all = request.user.has_permission('manage_all_posts')
            
            # Handle pinned posts limit - automatically unpin oldest if needed
            if post.is_pinned:
                other_pinned = Post.objects.filter(is_pinned=True)
                if other_pinned.count() >= 3:
                    # Find and unpin the oldest pinned post
                    oldest_pinned = other_pinned.order_by('publish_date').first()
                    if oldest_pinned:
                        oldest_pinned.is_pinned = False
                        oldest_pinned.save()
                        messages.info(request, f'Automatically unpinned the oldest pinned post: "{oldest_pinned.short_title}" to make room for this post.')
            
            post.full_clean()  # This will trigger model validation
            post.save()
            
            # Handle file attachments
            files = request.FILES.getlist('attachments')
            if files:
                for file in files[:10]:  # Max 10 attachments
                    PostAttachment.objects.create(post=post, file=file)
            
            messages.success(request, 'Post created successfully!')
            return redirect('office:manage_posts')
        except Exception as e:
            messages.error(request, f'Error creating post: {str(e)}')
            # Try to get post data from POST to repopulate form
            post_data = {
                'post_type': request.POST.get('post_type', 'notice'),
                'short_title': request.POST.get('short_title', ''),
                'long_title': request.POST.get('long_title', ''),
                'tags': request.POST.get('tags', ''),
                'description': request.POST.get('description', ''),
            }
            can_manage_all = request.user.has_permission('manage_all_posts')
            return render(request, 'office/create_post.html', {
                'POST_TYPE_CHOICES': POST_TYPE_CHOICES,
                'post': post_data,
                'can_manage_all': can_manage_all,
            })
    
    # Check permissions
    can_manage_all = request.user.has_permission('manage_all_posts')
    
    # Get post_type from GET parameter (for direct links to create notice)
    default_post_type = request.GET.get('post_type', 'notice')
    
    context = {
        'POST_TYPE_CHOICES': POST_TYPE_CHOICES,
        'can_manage_all': can_manage_all,
        'default_post_type': default_post_type,
    }
    return render(request, 'office/create_post.html', context)


@login_required
def edit_post(request, pk):
    """
    Edit an existing post.
    Level 3 users can only edit their own posts.
    Level 4+ users can edit any post.
    """
    if not check_post_access(request.user):
        messages.error(request, 'You do not have permission to edit posts.')
        return redirect('people:user_profile')
    
    post = get_object_or_404(Post, pk=pk)
    
    # Check if user can edit this post
    can_manage_all = request.user.has_permission('manage_all_posts')
    
    if not can_manage_all and post.created_by != request.user:
        messages.error(request, 'You can only edit your own posts.')
        return redirect('office:manage_posts')
    
    if request.method == 'POST':
        try:
            post.post_type = request.POST.get('post_type', 'notice')
            post.short_title = request.POST.get('short_title', '').strip()
            post.long_title = request.POST.get('long_title', '').strip()
            post.tags = request.POST.get('tags', '').strip()
            post.description = request.POST.get('description', '')
            
            # Handle pinned status
            new_pinned = request.POST.get('is_pinned') == 'on'
            if new_pinned and not post.is_pinned:
                # Check if we need to unpin oldest to make room
                other_pinned = Post.objects.filter(is_pinned=True).exclude(pk=post.pk)
                if other_pinned.count() >= 3:
                    # Find and unpin the oldest pinned post
                    oldest_pinned = other_pinned.order_by('publish_date').first()
                    if oldest_pinned:
                        oldest_pinned.is_pinned = False
                        oldest_pinned.save()
                        messages.info(request, f'Automatically unpinned the oldest pinned post: "{oldest_pinned.short_title}" to make room for this post.')
            
            post.is_pinned = new_pinned
            
            post.full_clean()  # This will trigger model validation
            post.save()
            
            # Handle new file attachments
            files = request.FILES.getlist('attachments')
            existing_count = post.attachments.count()
            remaining_slots = 10 - existing_count
            
            if files and remaining_slots > 0:
                for file in files[:remaining_slots]:
                    PostAttachment.objects.create(post=post, file=file)
            
            # Handle deletion of attachments
            delete_attachments = request.POST.getlist('delete_attachments')
            if delete_attachments:
                PostAttachment.objects.filter(pk__in=delete_attachments, post=post).delete()
            
            messages.success(request, 'Post updated successfully!')
            return redirect('office:manage_posts')
        except Exception as e:
            messages.error(request, f'Error updating post: {str(e)}')
    
    # Calculate remaining attachment slots
    existing_count = post.attachments.count()
    remaining_slots = max(0, 10 - existing_count)
    
    context = {
        'post': post,
        'POST_TYPE_CHOICES': POST_TYPE_CHOICES,
        'remaining_slots': remaining_slots,
    }
    return render(request, 'office/edit_post.html', context)


@login_required
def delete_post(request, pk):
    """
    Delete a post.
    Level 3 users can only delete their own posts.
    Level 4+ users can delete any post.
    """
    if not check_post_access(request.user):
        messages.error(request, 'You do not have permission to delete posts.')
        return redirect('people:user_profile')
    
    post = get_object_or_404(Post, pk=pk)
    
    # Check if user can delete this post
    can_manage_all = request.user.has_permission('manage_all_posts')
    
    if not can_manage_all and post.created_by != request.user:
        messages.error(request, 'You can only delete your own posts.')
        return redirect('office:manage_posts')
    
    if request.method == 'POST':
        post.delete()
        messages.success(request, 'Post deleted successfully!')
        return redirect('office:manage_posts')
    
    context = {
        'post': post,
    }
    return render(request, 'office/delete_post.html', context)


@login_required
@require_http_methods(["POST"])
def delete_posts(request):
    """
    Bulk delete posts via AJAX.
    Level 3 users can only delete their own posts.
    Level 4+ users can delete any posts.
    """
    if not check_post_access(request.user):
        return JsonResponse({'success': False, 'error': 'You do not have permission to delete posts.'}, status=403)
    
    # Get user access level
    # Check permissions
    can_manage_all = request.user.has_permission('manage_all_posts')
    
    # Get post IDs from request
    post_ids = request.POST.getlist('post_ids[]')
    if not post_ids:
        return JsonResponse({'success': False, 'error': 'No posts selected.'}, status=400)
    
    try:
        post_ids = [int(pk) for pk in post_ids]
    except (ValueError, TypeError):
        return JsonResponse({'success': False, 'error': 'Invalid post IDs.'}, status=400)
    
    # Get posts
    posts = Post.objects.filter(pk__in=post_ids)
    
    # Filter by permission
    can_manage_all = request.user.has_permission('manage_all_posts')
    if not can_manage_all:
        # Users without manage_all_posts can only delete their own posts
        posts = posts.filter(created_by=request.user)
        # Check if all requested posts are owned by user
        if posts.count() != len(post_ids):
            return JsonResponse({'success': False, 'error': 'You can only delete your own posts.'}, status=403)
    
    # Delete posts
    deleted_count = posts.count()
    posts.delete()
    
    return JsonResponse({
        'success': True,
        'message': f'Successfully deleted {deleted_count} post(s).'
    })


# ==============================================================================
# CLASS ROUTINE MANAGEMENT VIEWS
# ==============================================================================

def check_routine_access(user):
    """Check if user has post_routines permission"""
    if not user.is_authenticated:
        return False
    return user.has_permission('post_routines')


def routine_list(request):
    """
    Display list of all class routines with search and filter functionality.
    Public view - anyone can view routines.
    """
    routines = ClassRoutine.objects.all()
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        routines = routines.filter(
            Q(academic_year__icontains=search_query) |
            Q(semester__icontains=search_query) |
            Q(year_semester__icontains=search_query) |
            Q(section__icontains=search_query)
        )
    
    # Filter by academic year
    year_filter = request.GET.get('year', '')
    if year_filter:
        try:
            routines = routines.filter(academic_year=int(year_filter))
        except ValueError:
            pass
    
    # Filter by semester
    semester_filter = request.GET.get('semester', '')
    if semester_filter:
        routines = routines.filter(semester=semester_filter)
    
    # Filter by year-semester
    year_semester_filter = request.GET.get('year_semester', '')
    if year_semester_filter:
        routines = routines.filter(year_semester=year_semester_filter)
    
    # Filter by section
    section_filter = request.GET.get('section', '')
    if section_filter:
        routines = routines.filter(section=section_filter)
    
    # Sort by academic year (descending), then semester, then year_semester, then section
    routines = routines.order_by('-academic_year', 'semester', 'year_semester', 'section')
    
    # Pagination
    paginator = Paginator(routines, 12)  # 12 routines per page
    page = request.GET.get('page', 1)
    try:
        routines = paginator.page(page)
    except PageNotAnInteger:
        routines = paginator.page(1)
    except EmptyPage:
        routines = paginator.page(paginator.num_pages)
    
    # Get unique years for filter dropdown
    years = ClassRoutine.objects.values_list('academic_year', flat=True).distinct().order_by('-academic_year')
    
    context = {
        'routines': routines,
        'search_query': search_query,
        'year_filter': year_filter,
        'semester_filter': semester_filter,
        'year_semester_filter': year_semester_filter,
        'section_filter': section_filter,
        'years': years,
        'SEMESTER_CHOICES': ClassRoutine._meta.get_field('semester').choices,
        'YEAR_SEMESTER_CHOICES': ClassRoutine._meta.get_field('year_semester').choices,
        'SECTION_CHOICES': ClassRoutine._meta.get_field('section').choices,
    }
    
    return render(request, 'office/routine_list.html', context)


def routine_detail(request, pk):
    """
    Display detailed view of a class routine.
    Public view - anyone can view routine details.
    """
    routine = get_object_or_404(ClassRoutine, pk=pk)
    
    # Check if user can manage routines
    can_manage = check_routine_access(request.user) if request.user.is_authenticated else False
    
    context = {
        'routine': routine,
        'can_manage': can_manage,
    }
    
    return render(request, 'office/routine_detail.html', context)


@login_required
def manage_routines(request):
    """
    Manage routines view with filtering.
    Only Level 3+ users can access this view.
    """
    if not check_routine_access(request.user):
        messages.error(request, 'You do not have permission to manage class routines.')
        return redirect('office:routine_list')
    
    routines = ClassRoutine.objects.all()
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        routines = routines.filter(
            Q(academic_year__icontains=search_query) |
            Q(semester__icontains=search_query) |
            Q(year_semester__icontains=search_query) |
            Q(section__icontains=search_query)
        )
    
    # Filter by academic year
    year_filter = request.GET.get('year', '')
    if year_filter:
        try:
            routines = routines.filter(academic_year=int(year_filter))
        except ValueError:
            pass
    
    # Filter by semester
    semester_filter = request.GET.get('semester', '')
    if semester_filter:
        routines = routines.filter(semester=semester_filter)
    
    # Sort by academic year (descending), then semester, then year_semester, then section
    routines = routines.order_by('-academic_year', 'semester', 'year_semester', 'section')
    
    # Get unique years for filter dropdown
    years = ClassRoutine.objects.values_list('academic_year', flat=True).distinct().order_by('-academic_year')
    
    context = {
        'routines': routines,
        'search_query': search_query,
        'year_filter': year_filter,
        'semester_filter': semester_filter,
        'SEMESTER_CHOICES': ClassRoutine._meta.get_field('semester').choices,
        'YEAR_SEMESTER_CHOICES': ClassRoutine._meta.get_field('year_semester').choices,
        'SECTION_CHOICES': ClassRoutine._meta.get_field('section').choices,
        'years': years,
    }
    
    return render(request, 'office/manage_routines.html', context)


@login_required
def create_routine(request):
    """
    Create a new class routine.
    Only Level 3+ users can create routines.
    """
    if not check_routine_access(request.user):
        messages.error(request, 'You do not have permission to create class routines.')
        return redirect('office:routine_list')
    
    if request.method == 'POST':
        try:
            academic_year = int(request.POST.get('academic_year'))
            semester = request.POST.get('semester')
            year_semester = request.POST.get('year_semester')
            section = request.POST.get('section')
            routine_image = request.FILES.get('routine_image')
            
            # Validate required fields
            if not all([academic_year, semester, year_semester, section, routine_image]):
                messages.error(request, 'All fields are required.')
                return render(request, 'office/create_routine.html', {
                    'SEMESTER_CHOICES': ClassRoutine._meta.get_field('semester').choices,
                    'YEAR_SEMESTER_CHOICES': ClassRoutine._meta.get_field('year_semester').choices,
                    'SECTION_CHOICES': ClassRoutine._meta.get_field('section').choices,
                    'form_data': request.POST,
                })
            
            # Check for duplicate
            if ClassRoutine.objects.filter(
                academic_year=academic_year,
                semester=semester,
                year_semester=year_semester,
                section=section
            ).exists():
                messages.error(request, 'A routine with these parameters already exists.')
                return render(request, 'office/create_routine.html', {
                    'SEMESTER_CHOICES': ClassRoutine._meta.get_field('semester').choices,
                    'YEAR_SEMESTER_CHOICES': ClassRoutine._meta.get_field('year_semester').choices,
                    'SECTION_CHOICES': ClassRoutine._meta.get_field('section').choices,
                    'form_data': request.POST,
                })
            
            # Create routine
            routine = ClassRoutine.objects.create(
                academic_year=academic_year,
                semester=semester,
                year_semester=year_semester,
                section=section,
                routine_image=routine_image,
                created_by=request.user
            )
            
            messages.success(request, f'Class routine created successfully!')
            return redirect('office:routine_detail', pk=routine.pk)
            
        except ValueError:
            messages.error(request, 'Invalid academic year.')
        except Exception as e:
            messages.error(request, f'Error creating routine: {str(e)}')
    
    # Get current year for default value
    current_year = datetime.now().year
    
    context = {
        'SEMESTER_CHOICES': ClassRoutine._meta.get_field('semester').choices,
        'YEAR_SEMESTER_CHOICES': ClassRoutine._meta.get_field('year_semester').choices,
        'SECTION_CHOICES': ClassRoutine._meta.get_field('section').choices,
        'current_year': current_year,
    }
    
    return render(request, 'office/create_routine.html', context)


@login_required
def edit_routine(request, pk):
    """
    Edit an existing class routine.
    Only Level 3+ users can edit routines.
    """
    if not check_routine_access(request.user):
        messages.error(request, 'You do not have permission to edit class routines.')
        return redirect('office:routine_list')
    
    routine = get_object_or_404(ClassRoutine, pk=pk)
    
    if request.method == 'POST':
        try:
            academic_year = int(request.POST.get('academic_year'))
            semester = request.POST.get('semester')
            year_semester = request.POST.get('year_semester')
            section = request.POST.get('section')
            routine_image = request.FILES.get('routine_image')
            
            # Validate required fields (except image, which is optional on update)
            if not all([academic_year, semester, year_semester, section]):
                messages.error(request, 'All fields except image are required.')
                return render(request, 'office/edit_routine.html', {
                    'routine': routine,
                    'SEMESTER_CHOICES': ClassRoutine._meta.get_field('semester').choices,
                    'YEAR_SEMESTER_CHOICES': ClassRoutine._meta.get_field('year_semester').choices,
                    'SECTION_CHOICES': ClassRoutine._meta.get_field('section').choices,
                })
            
            # Check for duplicate (excluding current routine)
            duplicate = ClassRoutine.objects.filter(
                academic_year=academic_year,
                semester=semester,
                year_semester=year_semester,
                section=section
            ).exclude(pk=routine.pk)
            
            if duplicate.exists():
                messages.error(request, 'A routine with these parameters already exists.')
                return render(request, 'office/edit_routine.html', {
                    'routine': routine,
                    'SEMESTER_CHOICES': ClassRoutine._meta.get_field('semester').choices,
                    'YEAR_SEMESTER_CHOICES': ClassRoutine._meta.get_field('year_semester').choices,
                    'SECTION_CHOICES': ClassRoutine._meta.get_field('section').choices,
                })
            
            # Update routine
            routine.academic_year = academic_year
            routine.semester = semester
            routine.year_semester = year_semester
            routine.section = section
            if routine_image:
                routine.routine_image = routine_image
            routine.save()
            
            messages.success(request, 'Class routine updated successfully!')
            return redirect('office:routine_detail', pk=routine.pk)
            
        except ValueError:
            messages.error(request, 'Invalid academic year.')
        except Exception as e:
            messages.error(request, f'Error updating routine: {str(e)}')
    
    context = {
        'routine': routine,
        'SEMESTER_CHOICES': ClassRoutine._meta.get_field('semester').choices,
        'YEAR_SEMESTER_CHOICES': ClassRoutine._meta.get_field('year_semester').choices,
        'SECTION_CHOICES': ClassRoutine._meta.get_field('section').choices,
    }
    
    return render(request, 'office/edit_routine.html', context)


@login_required
def delete_routine(request, pk):
    """
    Delete a class routine.
    Only Level 3+ users can delete routines.
    """
    if not check_routine_access(request.user):
        messages.error(request, 'You do not have permission to delete class routines.')
        return redirect('office:routine_list')
    
    routine = get_object_or_404(ClassRoutine, pk=pk)
    
    if request.method == 'POST':
        routine.delete()
        messages.success(request, 'Class routine deleted successfully!')
        return redirect('office:manage_routines')
    
    context = {
        'routine': routine,
    }
    
    return render(request, 'office/delete_routine.html', context)


# ==============================================================================
# ADMISSION RESULTS PUBLIC SEARCH VIEWS
# ==============================================================================

def search_admission_results(request):
    """
    Public view for admission test results.
    Shows latest result by default, allows search/filter.
    No authentication required - accessible to all users.
    """
    result = None
    latest_result = None
    search_performed = False
    selected_year = None
    selected_semester = None
    selected_slot = None
    
    # Get the latest result by default
    latest_result = AdmissionResult.objects.order_by('-publish_date', '-academic_year').first()
    
    # Get available years and semesters from existing results
    available_years = AdmissionResult.objects.values_list('academic_year', flat=True).distinct().order_by('-academic_year')
    
    # Handle GET request for filtering
    if request.method == 'GET':
        year_param = request.GET.get('year')
        semester_param = request.GET.get('semester')
        slot_param = request.GET.get('slot')
        
        # Check if any filters are provided
        if year_param or semester_param or slot_param:
            search_performed = True
            
            # Build filter query
            filter_kwargs = {}
            if year_param:
                try:
                    selected_year = int(year_param)
                    filter_kwargs['academic_year'] = selected_year
                except (ValueError, TypeError):
                    pass
            
            if semester_param:
                selected_semester = semester_param
                filter_kwargs['semester'] = selected_semester
            
            if slot_param:
                try:
                    selected_slot = int(slot_param)
                    filter_kwargs['slot'] = selected_slot
                except (ValueError, TypeError):
                    pass
            
            # If we have filters, search for results
            if filter_kwargs:
                # If all three filters are provided, get exact match
                if len(filter_kwargs) == 3:
                    result = AdmissionResult.objects.filter(**filter_kwargs).first()
                else:
                    # Partial filters - get the most recent matching result
                    result = AdmissionResult.objects.filter(**filter_kwargs).order_by('-publish_date', '-academic_year').first()
                    if result:
                        selected_year = result.academic_year
                        selected_semester = result.semester
                        selected_slot = result.slot
    
    # Handle POST request (form submission) - keep for backward compatibility
    elif request.method == 'POST':
        try:
            academic_year = int(request.POST.get('academic_year'))
            semester = request.POST.get('semester')
            slot = int(request.POST.get('slot'))
            
            selected_year = academic_year
            selected_semester = semester
            selected_slot = slot
            search_performed = True
            
            # Search for the result
            result = AdmissionResult.objects.filter(
                academic_year=academic_year,
                semester=semester,
                slot=slot
            ).first()
            
        except (ValueError, TypeError):
            messages.error(request, 'Invalid input. Please check your selections.')
    
    # If no specific result found and no search was performed, show latest
    if not result and not search_performed and latest_result:
        result = latest_result
        selected_year = latest_result.academic_year
        selected_semester = latest_result.semester
        selected_slot = latest_result.slot
    
    # Get available slots for the selected year and semester (for form state)
    available_slots = []
    if selected_year and selected_semester:
        available_slots = AdmissionResult.objects.filter(
            academic_year=selected_year,
            semester=selected_semester
        ).values_list('slot', flat=True).distinct().order_by('slot')
    elif latest_result:
        # Default to latest result's slots
        available_slots = AdmissionResult.objects.filter(
            academic_year=latest_result.academic_year,
            semester=latest_result.semester
        ).values_list('slot', flat=True).distinct().order_by('slot')
    
    # Build absolute URL for PDF if result exists
    pdf_url = None
    if result and result.official_pdf:
        pdf_url = request.build_absolute_uri(result.official_pdf.url)
    
    context = {
        'result': result,
        'latest_result': latest_result,
        'search_performed': search_performed,
        'available_years': available_years,
        'SEMESTER_CHOICES': SEMESTER_CHOICES,
        'available_slots': available_slots,
        'selected_year': selected_year or (latest_result.academic_year if latest_result else None),
        'selected_semester': selected_semester or (latest_result.semester if latest_result else None),
        'selected_slot': selected_slot or (latest_result.slot if latest_result else None),
        'pdf_url': pdf_url,
    }
    
    return render(request, 'office/search_admission_results.html', context)


def get_available_slots(request):
    """
    API endpoint to get available slots for a given year and semester.
    Used for dynamic dropdown population.
    """
    academic_year = request.GET.get('year')
    semester = request.GET.get('semester')
    
    if not academic_year or not semester:
        return JsonResponse({'slots': []})
    
    try:
        academic_year = int(academic_year)
        slots = AdmissionResult.objects.filter(
            academic_year=academic_year,
            semester=semester
        ).values_list('slot', flat=True).distinct().order_by('slot')
        
        return JsonResponse({
            'slots': list(slots)
        })
    except (ValueError, TypeError):
        return JsonResponse({'slots': []})


# ==============================================================================
# ADMISSION RESULTS MANAGEMENT VIEWS
# ==============================================================================

def check_admission_result_access(user):
    """Check if user has post_admission_results permission"""
    if not user.is_authenticated:
        return False
    return user.has_permission('post_admission_results')


@login_required
def manage_admission_results(request):
    """
    Manage admission results view with filtering.
    Only Level 3+ users (Faculty and Officers) can access this view.
    """
    if not check_admission_result_access(request.user):
        messages.error(request, 'You do not have permission to manage admission results.')
        return redirect('people:user_profile')
    
    # Check if user is faculty or officer
    profile_type = None
    if hasattr(request.user, 'faculty_profile') and request.user.faculty_profile:
        profile_type = 'faculty'
    elif hasattr(request.user, 'officer_profile') and request.user.officer_profile:
        profile_type = 'officer'
    
    if profile_type not in ['faculty', 'officer']:
        messages.error(request, 'Only Faculty and Officers can manage admission results.')
        return redirect('people:user_profile')
    
    results = AdmissionResult.objects.all()
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        results = results.filter(
            Q(academic_year__icontains=search_query) |
            Q(semester__icontains=search_query) |
            Q(slot__icontains=search_query)
        )
    
    # Filter by academic year
    year_filter = request.GET.get('year', '')
    if year_filter:
        try:
            results = results.filter(academic_year=int(year_filter))
        except ValueError:
            pass
    
    # Filter by semester
    semester_filter = request.GET.get('semester', '')
    if semester_filter:
        results = results.filter(semester=semester_filter)
    
    # Sort by academic year (descending), then semester, then slot
    results = results.order_by('-academic_year', 'semester', 'slot')
    
    # Get unique years for filter dropdown
    years = AdmissionResult.objects.values_list('academic_year', flat=True).distinct().order_by('-academic_year')
    
    context = {
        'results': results,
        'search_query': search_query,
        'year_filter': year_filter,
        'semester_filter': semester_filter,
        'SEMESTER_CHOICES': SEMESTER_CHOICES,
        'years': years,
    }
    
    return render(request, 'office/manage_admission_results.html', context)


@login_required
def create_admission_result(request):
    """
    Create a new admission result.
    Only Level 3+ users (Faculty and Officers) can create results.
    """
    if not check_admission_result_access(request.user):
        messages.error(request, 'You do not have permission to create admission results.')
        return redirect('people:user_profile')
    
    # Check if user is faculty or officer
    profile_type = None
    if hasattr(request.user, 'faculty_profile') and request.user.faculty_profile:
        profile_type = 'faculty'
    elif hasattr(request.user, 'officer_profile') and request.user.officer_profile:
        profile_type = 'officer'
    
    if profile_type not in ['faculty', 'officer']:
        messages.error(request, 'Only Faculty and Officers can create admission results.')
        return redirect('people:user_profile')
    
    if request.method == 'POST':
        try:
            academic_year = int(request.POST.get('academic_year'))
            semester = request.POST.get('semester')
            slot = int(request.POST.get('slot'))
            result_content = request.POST.get('result_content', '')
            official_pdf = request.FILES.get('official_pdf')
            
            # Validate required fields
            if not all([academic_year, semester, slot, official_pdf]):
                messages.error(request, 'All fields are required.')
                return render(request, 'office/create_admission_result.html', {
                    'SEMESTER_CHOICES': SEMESTER_CHOICES,
                    'form_data': request.POST,
                })
            
            # Check for duplicate
            if AdmissionResult.objects.filter(
                academic_year=academic_year,
                semester=semester,
                slot=slot
            ).exists():
                messages.error(request, 'An admission result with these parameters already exists.')
                return render(request, 'office/create_admission_result.html', {
                    'SEMESTER_CHOICES': SEMESTER_CHOICES,
                    'form_data': request.POST,
                })
            
            # Save file content before creating models (so we can use it for both)
            pdf_file_content = None
            pdf_file_name = None
            if official_pdf:
                pdf_file_content = official_pdf.read()
                pdf_file_name = official_pdf.name
                # Reset file pointer for saving to AdmissionResult
                official_pdf.seek(0)
            
            # Create result
            result = AdmissionResult.objects.create(
                academic_year=academic_year,
                semester=semester,
                slot=slot,
                result_content=result_content,
                official_pdf=official_pdf,
                created_by=request.user
            )
            
            # Automatically create a notice post for this admission result
            try:
                # Check if a notice already exists for this admission result
                semester_display = dict(SEMESTER_CHOICES).get(semester, semester)
                short_title = f"Admission {academic_year}"
                long_title = f"Admission Test Result - {academic_year} {semester_display}, Slot {slot}"
                
                # Check for existing notice with same title
                existing_notice = Post.objects.filter(
                    post_type='notice',
                    short_title=short_title[:20],
                    long_title=long_title[:255]
                ).first()
                
                if existing_notice:
                    # Notice already exists, show info message
                    messages.info(request, f'Admission result created successfully! Notice was already posted earlier.')
                else:
                    # Build description with result information
                    description = f"<p><strong>Admission Test Result Published</strong></p>"
                    description += f"<p><strong>Academic Year:</strong> {academic_year}</p>"
                    description += f"<p><strong>Semester:</strong> {semester_display}</p>"
                    description += f"<p><strong>Slot:</strong> {slot}</p>"
                    if result_content:
                        description += f"<div>{result_content}</div>"
                    description += f"<p><a href='{reverse('office:search_admission_results')}?year={academic_year}&semester={semester}&slot={slot}' target='_blank'>View and Download Result PDF →</a></p>"
                    
                    # Handle pinned posts limit - automatically unpin oldest if needed
                    other_pinned = Post.objects.filter(is_pinned=True)
                    if other_pinned.count() >= 3:
                        # Find and unpin the oldest pinned post
                        oldest_pinned = other_pinned.order_by('publish_date').first()
                        if oldest_pinned:
                            oldest_pinned.is_pinned = False
                            oldest_pinned.save()
                    
                    # Create the notice post with auto-pin
                    notice_post = Post(
                        post_type='notice',
                        short_title=short_title[:20],  # Ensure max 20 chars
                        long_title=long_title[:255],  # Ensure max 255 chars
                        description=description,
                        is_pinned=True,  # Auto-pin admission result notices
                        created_by=request.user
                    )
                    # Set publish_date explicitly to current time to fix timezone issues
                    notice_post.publish_date = timezone.now()
                    notice_post.full_clean()  # Validate before saving
                    notice_post.save()
                    
                    # Attach the PDF file to the post
                    if pdf_file_content and pdf_file_name:
                        try:
                            attachment_file = ContentFile(pdf_file_content, name=pdf_file_name)
                            PostAttachment.objects.create(
                                post=notice_post,
                                file=attachment_file
                            )
                        except Exception as file_error:
                            # If file attachment fails, log but don't fail the whole operation
                            import logging
                            logger = logging.getLogger(__name__)
                            logger.error(f'Failed to attach PDF to notice post: {str(file_error)}')
                            messages.warning(request, 'Notice created but PDF attachment failed. You can manually attach it later.')
                    
                    messages.success(request, f'Admission result created successfully! A notice has been automatically published and pinned.')
            except Exception as e:
                # If post creation fails, still show success for admission result
                # but warn about the notice
                messages.warning(request, f'Admission result created, but failed to create notice: {str(e)}')
            
            return redirect('office:manage_admission_results')
            
        except ValueError:
            messages.error(request, 'Invalid input. Please check your selections.')
        except Exception as e:
            messages.error(request, f'Error creating admission result: {str(e)}')
    
    # Get current year for default value
    current_year = datetime.now().year
    
    context = {
        'SEMESTER_CHOICES': SEMESTER_CHOICES,
        'current_year': current_year,
    }
    
    return render(request, 'office/create_admission_result.html', context)


@login_required
def edit_admission_result(request, pk):
    """
    Edit an existing admission result.
    Only Level 3+ users (Faculty and Officers) can edit results.
    """
    if not check_admission_result_access(request.user):
        messages.error(request, 'You do not have permission to edit admission results.')
        return redirect('people:user_profile')
    
    # Check if user is faculty or officer
    profile_type = None
    if hasattr(request.user, 'faculty_profile') and request.user.faculty_profile:
        profile_type = 'faculty'
    elif hasattr(request.user, 'officer_profile') and request.user.officer_profile:
        profile_type = 'officer'
    
    if profile_type not in ['faculty', 'officer']:
        messages.error(request, 'Only Faculty and Officers can edit admission results.')
        return redirect('people:user_profile')
    
    result = get_object_or_404(AdmissionResult, pk=pk)
    
    if request.method == 'POST':
        try:
            academic_year = int(request.POST.get('academic_year'))
            semester = request.POST.get('semester')
            slot = int(request.POST.get('slot'))
            result_content = request.POST.get('result_content', '')
            official_pdf = request.FILES.get('official_pdf')
            
            # Validate required fields (except PDF, which is optional on update)
            if not all([academic_year, semester, slot]):
                messages.error(request, 'All fields except PDF are required.')
                return render(request, 'office/edit_admission_result.html', {
                    'result': result,
                    'SEMESTER_CHOICES': SEMESTER_CHOICES,
                })
            
            # Check for duplicate (excluding current result)
            duplicate = AdmissionResult.objects.filter(
                academic_year=academic_year,
                semester=semester,
                slot=slot
            ).exclude(pk=result.pk)
            
            if duplicate.exists():
                messages.error(request, 'An admission result with these parameters already exists.')
                return render(request, 'office/edit_admission_result.html', {
                    'result': result,
                    'SEMESTER_CHOICES': SEMESTER_CHOICES,
                })
            
            # Update result
            result.academic_year = academic_year
            result.semester = semester
            result.slot = slot
            result.result_content = result_content
            if official_pdf:
                result.official_pdf = official_pdf
            result.save()
            
            messages.success(request, 'Admission result updated successfully!')
            return redirect('office:manage_admission_results')
            
        except ValueError:
            messages.error(request, 'Invalid input. Please check your selections.')
        except Exception as e:
            messages.error(request, f'Error updating admission result: {str(e)}')
    
    context = {
        'result': result,
        'SEMESTER_CHOICES': SEMESTER_CHOICES,
    }
    
    return render(request, 'office/edit_admission_result.html', context)


@login_required
def delete_admission_result(request, pk):
    """
    Delete an admission result.
    Only Level 3+ users (Faculty and Officers) can delete results.
    """
    if not check_admission_result_access(request.user):
        messages.error(request, 'You do not have permission to delete admission results.')
        return redirect('people:user_profile')
    
    # Check if user is faculty or officer
    profile_type = None
    if hasattr(request.user, 'faculty_profile') and request.user.faculty_profile:
        profile_type = 'faculty'
    elif hasattr(request.user, 'officer_profile') and request.user.officer_profile:
        profile_type = 'officer'
    
    if profile_type not in ['faculty', 'officer']:
        messages.error(request, 'Only Faculty and Officers can delete admission results.')
        return redirect('people:user_profile')
    
    result = get_object_or_404(AdmissionResult, pk=pk)
    
    if request.method == 'POST':
        result.delete()
        messages.success(request, 'Admission result deleted successfully!')
        return redirect('office:manage_admission_results')
    
    context = {
        'result': result,
    }
    
    return render(request, 'office/delete_admission_result.html', context)


def serve_admission_pdf(request, pk):
    """
    Serve admission result PDF with proper headers for iframe embedding.
    Public access - no authentication required.
    """
    result = get_object_or_404(AdmissionResult, pk=pk)
    
    if not result.official_pdf:
        return HttpResponse("PDF not found", status=404)
    
    try:
        # Get the file path
        file_path = result.official_pdf.path
        
        # Serve the file with proper headers
        response = FileResponse(
            open(file_path, 'rb'),
            content_type='application/pdf'
        )
        response['Content-Disposition'] = f'inline; filename="{result.official_pdf.name}"'
        response['X-Content-Type-Options'] = 'nosniff'
        
        # Allow iframe embedding from same origin
        response['X-Frame-Options'] = 'SAMEORIGIN'
        
        return response
    except FileNotFoundError:
        return HttpResponse("PDF file not found on server", status=404)
    except Exception as e:
        return HttpResponse(f"Error serving PDF: {str(e)}", status=500)


def serve_admission_pdf(request, pk):
    """
    Serve admission result PDF with proper headers for iframe embedding.
    """
    result = get_object_or_404(AdmissionResult, pk=pk)
    
    if not result.official_pdf:
        return HttpResponse("PDF not found", status=404)
    
    try:
        # Get the file path
        file_path = result.official_pdf.path
        
        # Serve the file with proper headers
        response = FileResponse(
            open(file_path, 'rb'),
            content_type='application/pdf'
        )
        response['Content-Disposition'] = f'inline; filename="{result.official_pdf.name}"'
        response['X-Content-Type-Options'] = 'nosniff'
        
        # Allow iframe embedding
        response['X-Frame-Options'] = 'SAMEORIGIN'
        
        return response
    except Exception as e:
        return HttpResponse(f"Error serving PDF: {str(e)}", status=500)
