"""Template tags for priority badge and text styling."""

from django import template

from tasks.priority_ui import PriorityUI, get_priority_ui

register = template.Library()


@register.simple_tag
def priority_ui(priority: str) -> PriorityUI:
    """Return PriorityUI tokens for a priority value (e.g. ``project.priority``)."""
    return get_priority_ui(priority)


@register.filter
def priority_badge_classes(priority: str) -> str:
    """Tailwind classes for standard priority badges (home cards, project header)."""
    return get_priority_ui(priority).badge_classes


@register.filter
def priority_compact_badge_classes(priority: str) -> str:
    """Tailwind classes for compact priority badges on task rows."""
    return get_priority_ui(priority).compact_badge_classes


@register.filter
def priority_text_classes(priority: str) -> str:
    """Tailwind classes for inline priority text (edit form hints)."""
    return get_priority_ui(priority).text_classes
