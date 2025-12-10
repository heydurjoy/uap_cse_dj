from django import template

register = template.Library()

@register.filter
def sort_by_type(courses):
    """
    Sort courses so that 'TH' (Theory) comes first, then 'LAB' (Lab)
    """
    type_order = {'TH': 0, 'LAB': 1}
    # Default to 99 if course_type not in mapping
    return sorted(courses, key=lambda c: type_order.get(c.course_type, 99))
