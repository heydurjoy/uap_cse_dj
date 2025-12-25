"""
Permission constants for the application.
All permission codenames should be defined here for type safety and easy refactoring.
"""


class Permissions:
    """Permission codenames used throughout the application"""
    
    # Office permissions
    POST_NOTICES = 'post_notices'
    MANAGE_ALL_POSTS = 'manage_all_posts'
    POST_ROUTINES = 'post_routines'
    POST_ADMISSION_RESULTS = 'post_admission_results'
    
    # Club permissions
    MANAGE_ALL_CLUBS = 'manage_club_settings'  # Renamed from MANAGE_CLUB_SETTINGS for clarity
    
    # Design permissions
    EDIT_FEATURE_CARDS = 'edit_feature_cards'
    EDIT_HEAD_MESSAGE = 'edit_head_message'
    MANAGE_ACADEMIC_CALENDARS = 'manage_academic_calendars'
    
    # User management permissions
    MANAGE_USER_PERMISSIONS = 'manage_user_permissions'
    
    # People/Publications permissions
    MANAGE_ALL_PUBLICATIONS = 'manage_all_publications'
    
    # Permission categories
    CATEGORY_OFFICE = 'office'
    CATEGORY_CLUBS = 'clubs'
    CATEGORY_DESIGNS = 'designs'
    CATEGORY_USERS = 'users'
    CATEGORY_ACADEMICS = 'academics'


# Permission definitions for auto-registration
PERMISSION_DEFINITIONS = [
    {
        'codename': Permissions.POST_NOTICES,
        'name': 'Post Notices',
        'description': 'Can create and edit office notices',
        'category': Permissions.CATEGORY_OFFICE,
        'requires_role': ['faculty', 'officer'],
        'priority': 10,
    },
    {
        'codename': Permissions.MANAGE_ALL_POSTS,
        'name': 'Manage All Posts',
        'description': 'Can create, edit, and delete all office posts',
        'category': Permissions.CATEGORY_OFFICE,
        'requires_role': ['faculty', 'officer'],
        'priority': 20,
    },
    {
        'codename': Permissions.POST_ROUTINES,
        'name': 'Post Routines',
        'description': 'Can create and manage class routines',
        'category': Permissions.CATEGORY_OFFICE,
        'requires_role': ['faculty', 'officer'],
        'priority': 30,
    },
    {
        'codename': Permissions.POST_ADMISSION_RESULTS,
        'name': 'Post Admission Results',
        'description': 'Can publish admission test results',
        'category': Permissions.CATEGORY_OFFICE,
        'requires_role': ['faculty', 'officer'],
        'priority': 40,
    },
    {
        'codename': Permissions.MANAGE_ALL_CLUBS,
        'name': 'Manage All Clubs',
        'description': 'Can create, edit, and manage all clubs',
        'category': Permissions.CATEGORY_CLUBS,
        'requires_role': ['faculty', 'officer'],
        'priority': 10,
    },
    {
        'codename': Permissions.EDIT_FEATURE_CARDS,
        'name': 'Edit Feature Cards',
        'description': 'Can edit feature cards on the homepage',
        'category': Permissions.CATEGORY_DESIGNS,
        'requires_role': [],
        'priority': 10,
    },
    {
        'codename': Permissions.EDIT_HEAD_MESSAGE,
        'name': 'Edit Head Message',
        'description': 'Can edit message from the head',
        'category': Permissions.CATEGORY_DESIGNS,
        'requires_role': [],
        'priority': 20,
    },
    {
        'codename': Permissions.MANAGE_ACADEMIC_CALENDARS,
        'name': 'Manage Academic Calendars',
        'description': 'Can create, edit, and delete academic calendars',
        'category': Permissions.CATEGORY_DESIGNS,
        'requires_role': ['faculty', 'officer'],
        'priority': 30,
    },
    {
        'codename': Permissions.MANAGE_USER_PERMISSIONS,
        'name': 'Manage User Permissions',
        'description': 'Can grant/revoke permissions and create users',
        'category': Permissions.CATEGORY_USERS,
        'requires_role': [],
        'priority': 10,
    },
    {
        'codename': Permissions.MANAGE_ALL_PUBLICATIONS,
        'name': 'Manage All Publications',
        'description': 'Can manage publications for all faculty members',
        'category': Permissions.CATEGORY_USERS,
        'requires_role': [],
        'priority': 20,
    },
]

