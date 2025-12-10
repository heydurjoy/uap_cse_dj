from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.urls import reverse
from .models import Post, PostAttachment, AdmissionResult, POST_TYPE_CHOICES


def post_list(request):
    """
    Display list of all posts with search, filter, and sort functionality.
    """
    posts = Post.objects.all()
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        posts = posts.filter(
            Q(short_title__icontains=search_query) |
            Q(long_title__icontains=search_query) |
            Q(tags__icontains=search_query) |
            Q(description__icontains=search_query)
        )
    
    # Filter by post type
    post_type_filter = request.GET.get('type', '')
    if post_type_filter:
        posts = posts.filter(post_type=post_type_filter)
    
    # Sort functionality
    sort_by = request.GET.get('sort', 'pinned')
    if sort_by == 'oldest':
        posts = posts.order_by('publish_date')
    elif sort_by == 'newest':
        posts = posts.order_by('-publish_date')
    elif sort_by == 'type':
        posts = posts.order_by('post_type', '-publish_date')
    elif sort_by == 'pinned':
        # Pinned first, then by date
        posts = posts.order_by('-is_pinned', '-publish_date')
    else:
        # Default: pinned first, then by date
        posts = posts.order_by('-is_pinned', '-publish_date')
    
    # Count posts by type for stats (before pagination)
    total_posts_count = posts.count()
    posts_by_type = {}
    for code, display in POST_TYPE_CHOICES:
        posts_by_type[code] = Post.objects.filter(post_type=code).count()
    
    # Pagination - 9 posts per page
    paginator = Paginator(posts, 9)
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
        'search_query': search_query,
        'sort_by': sort_by,
        'POST_TYPE_CHOICES': POST_TYPE_CHOICES,
        'posts_by_type': posts_by_type,
        'total_posts': total_posts_count,
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
    """Check if user has access level 3 or higher"""
    if not user.is_authenticated:
        return False
    try:
        access_level = int(user.access_level) if user.access_level else 0
        return access_level >= 3
    except (ValueError, TypeError):
        return False


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
    
    # Get user access level
    try:
        access_level = int(request.user.access_level) if request.user.access_level else 0
    except (ValueError, TypeError):
        access_level = 0
    
    # Base queryset
    if access_level >= 4:
        # Level 4+ can see all posts
        posts = Post.objects.all()
    else:
        # Level 3 can only see their own posts
        posts = Post.objects.filter(created_by=request.user)
    
    # Filter by creator (only for level 4+)
    created_by_filter = request.GET.get('created_by', 'all')
    if access_level >= 4:
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
        'access_level': access_level,
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
            
            # Get user access level
            try:
                access_level = int(request.user.access_level) if request.user.access_level else 0
            except (ValueError, TypeError):
                access_level = 0
            
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
            # Get user access level for error context
            try:
                access_level = int(request.user.access_level) if request.user.access_level else 0
            except (ValueError, TypeError):
                access_level = 0
            # Try to get post data from POST to repopulate form
            post_data = {
                'post_type': request.POST.get('post_type', 'notice'),
                'short_title': request.POST.get('short_title', ''),
                'long_title': request.POST.get('long_title', ''),
                'tags': request.POST.get('tags', ''),
                'description': request.POST.get('description', ''),
            }
            return render(request, 'office/create_post.html', {
                'POST_TYPE_CHOICES': POST_TYPE_CHOICES,
                'post': post_data,
                'access_level': access_level,
            })
    
    # Get user access level
    try:
        access_level = int(request.user.access_level) if request.user.access_level else 0
    except (ValueError, TypeError):
        access_level = 0
    
    # Get post_type from GET parameter (for direct links to create notice)
    default_post_type = request.GET.get('post_type', 'notice')
    
    context = {
        'POST_TYPE_CHOICES': POST_TYPE_CHOICES,
        'access_level': access_level,
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
    try:
        access_level = int(request.user.access_level) if request.user.access_level else 0
    except (ValueError, TypeError):
        access_level = 0
    
    if access_level < 4 and post.created_by != request.user:
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
    try:
        access_level = int(request.user.access_level) if request.user.access_level else 0
    except (ValueError, TypeError):
        access_level = 0
    
    if access_level < 4 and post.created_by != request.user:
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
    try:
        access_level = int(request.user.access_level) if request.user.access_level else 0
    except (ValueError, TypeError):
        access_level = 0
    
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
    if access_level < 4:
        # Level 3 can only delete their own posts
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
