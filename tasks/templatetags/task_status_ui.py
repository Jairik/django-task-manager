"""Template tags for task status presentation on the project detail page."""

from django import template
from django.utils.safestring import mark_safe

from tasks.status_ui import StatusUI, get_status_ui

register = template.Library()


@register.simple_tag
def status_ui(status: str) -> StatusUI:
    """Return StatusUI tokens for a task status value (e.g. ``task.status``)."""
    return get_status_ui(status)


@register.filter
def status_icon(icon_markup: str) -> str:
    """Mark icon SVG markup safe for template output."""
    return mark_safe(icon_markup)
