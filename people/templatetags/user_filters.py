from django import template
import re

register = template.Library()


@register.filter
def greeting_name(user):
    """
    Extract greeting name from user, handling titles like Dr., Prof., etc.
    Returns: "Dr. Durjoy" from "Dr. Durjoy Mistry" or "Prof. John" from "Prof. John Doe"
    Handles: "Dr.", "Dr", "Prof.", "Prof", "Prof. Dr.", "Dr. Prof.", etc.
    """
    if not user or not user.is_authenticated:
        return user.email if user else ""
    
    # Try to get name from profile first (Faculty, Staff, Officer, ClubMember)
    full_name = None
    
    if hasattr(user, 'faculty_profile') and user.faculty_profile:
        full_name = user.faculty_profile.name
    elif hasattr(user, 'staff_profile') and user.staff_profile:
        full_name = user.staff_profile.name
    elif hasattr(user, 'officer_profile') and user.officer_profile:
        full_name = user.officer_profile.name
    elif hasattr(user, 'club_member_profile') and user.club_member_profile:
        full_name = user.club_member_profile.name
    
    # If no profile name, try get_full_name() or first_name
    if not full_name:
        full_name = user.get_full_name() or user.first_name or ""
    
    # If still no name, return email
    if not full_name:
        return user.email
    
    # Normalize the name - remove extra spaces
    full_name = ' '.join(full_name.strip().split())
    
    # List of title patterns (case-insensitive matching)
    # Order matters - check longer patterns first
    title_patterns = [
        r'^(Prof\.?\s+Dr\.?|Dr\.?\s+Prof\.?)',  # "Prof. Dr." or "Dr. Prof."
        r'^(Prof\.|Prof\b)',  # "Prof." or "Prof"
        r'^(Dr\.|Dr\b)',  # "Dr." or "Dr"
        r'^(Professor\s+)',  # "Professor"
    ]
    
    # Try to match title patterns
    title_match = None
    for pattern in title_patterns:
        match = re.match(pattern, full_name, re.IGNORECASE)
        if match:
            title_match = match.group(0).strip()
            break
    
    # Remove the matched title from the name
    if title_match:
        # Remove title from the beginning
        remaining_name = full_name[len(title_match):].strip()
        name_parts = remaining_name.split()
        
        # Get the first word after the title
        if name_parts:
            first_name = name_parts[0]
            # Return title + first name, preserving original casing of title
            # Find the original title in the full_name to preserve casing
            title_in_original = full_name[:len(title_match)]
            return f"{title_in_original} {first_name}"
    
    # If no title found, return first word
    name_parts = full_name.split()
    if name_parts:
        return name_parts[0]
    
    return user.email


@register.filter
def get_item(dictionary, key):
    """Get an item from a dictionary using a variable key"""
    if dictionary is None:
        return None
    return dictionary.get(key)


@register.filter
def in_list(value, arg):
    """Check if value is in the given list/set"""
    if arg is None:
        return False
    return value in arg


@register.filter(name='call')
def call_method(obj, method_name):
    """Call a method on an object with optional arguments"""
    if obj is None:
        return False
    method = getattr(obj, method_name, None)
    if method and callable(method):
        # For has_permission, we need to pass the permission codename
        # This filter will be used like: user.has_permission|call:'permission_code'
        return method
    return False


@register.filter
def has_permission(user, permission_code):
    """Check if user has a specific permission (including superuser privileges)"""
    if not user:
        return False
    # Check if user has the has_permission method
    if not hasattr(user, 'has_permission'):
        return False
    # Call the method and ensure it returns a boolean
    try:
        result = user.has_permission(permission_code)
        return bool(result)
    except Exception:
        return False


@register.filter
def has_granted_permission(user, permission_code):
    """Check if user has been explicitly granted a permission (ignores superuser status)"""
    if not user:
        return False
    # Only check explicitly granted permissions, ignore superuser status
    from people.models import UserPermission
    try:
        return UserPermission.objects.filter(
            user=user,
            permission__codename=permission_code,
            is_active=True
        ).exists()
    except Exception:
        return False

