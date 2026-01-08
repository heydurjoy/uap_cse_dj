from django.utils import timezone
from datetime import timedelta
from .models import Post


def uap_now_posts(request):
    """
    Context processor to provide posts for "UAP Now" space with dynamic carousel.
    Includes both regular posts and club posts.
    Priority Logic:
    1. Pinned posts stay permanently (they have priority)
    2. Non-pinned posts rotate in the carousel
    3. Posts sorted by date proximity to current date
    
    Note: Club post pins only affect their club page, not this carousel.
    """
    now = timezone.now()
    
    # Configuration
    MAX_VISIBLE_SLOTS = 4  # How many cards visible at once in the grid
    TOTAL_POSTS_FOR_CAROUSEL = 12  # Total posts to fetch for rotation
    
    # Get all regular posts
    all_posts = Post.objects.all()
    
    # Get all club posts
    try:
        from clubs.models import ClubPost
        all_club_posts = ClubPost.objects.all()
    except ImportError:
        all_club_posts = []
    
    # Create unified list with type indicator
    unified_posts = []
    
    # Add regular posts with type indicator
    for post in all_posts:
        unified_posts.append({
            'type': 'post',
            'object': post,
            'is_pinned': post.is_pinned,  # Regular posts use their actual pin status
            'date': post.publish_date,
        })
    
    # Add club posts - always treat as non-pinned for homepage carousel
    for club_post in all_club_posts:
        unified_posts.append({
            'type': 'club_post',
            'object': club_post,
            'is_pinned': False,  # Club pins don't affect homepage carousel
            'date': club_post.created_at,
        })
    
    # Separate pinned and non-pinned posts
    pinned_posts = [p for p in unified_posts if p['is_pinned']]
    non_pinned_posts = [p for p in unified_posts if not p['is_pinned']]
    
    # Sort pinned posts by date proximity to current date (closer = better)
    pinned_posts.sort(key=lambda p: abs((p['date'] - now).total_seconds()))
    
    # Sort non-pinned posts by date proximity to current date (closer = better)
    # Prioritize future dates slightly over past dates for non-pinned
    def non_pinned_sort_key(post):
        date_diff = abs((post['date'] - now).total_seconds())
        # Future posts get slight priority (subtract a small amount)
        if post['date'] > now:
            return date_diff - 86400  # 1 day advantage for future posts
        return date_diff
    
    non_pinned_posts.sort(key=non_pinned_sort_key)
    
    # Build the list: pinned first, then non-pinned for carousel
    uap_now_posts_list = []
    
    # Add pinned posts first (they stay permanently)
    for post in pinned_posts:
        if len(uap_now_posts_list) < TOTAL_POSTS_FOR_CAROUSEL:
            uap_now_posts_list.append(post)
    
    # Add non-pinned posts for carousel rotation
    for post in non_pinned_posts:
        if len(uap_now_posts_list) < TOTAL_POSTS_FOR_CAROUSEL:
            uap_now_posts_list.append(post)
    
    # Final sort: pinned first, then by date proximity
    def final_sort_key(post):
        # Pinned posts get priority (0 = highest)
        pinned_priority = 0 if post['is_pinned'] else 1
        # Date proximity (closer = better)
        date_diff = abs((post['date'] - now).total_seconds())
        return (pinned_priority, date_diff)
    
    uap_now_posts_list.sort(key=final_sort_key)
    
    return {
        'uap_now_posts': uap_now_posts_list[:TOTAL_POSTS_FOR_CAROUSEL]
    }

