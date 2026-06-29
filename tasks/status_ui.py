"""Status presentation tokens for project-detail task cards and sections.

Centralizes Tailwind class strings and icon markup so templates stay DRY and
tests can assert the canonical blue / orange / green / gray mapping.
"""

from dataclasses import dataclass

from tasks.models import TaskStatus

# Inline SVG icons (14×14) — circle, clock, check-circle, x-circle.
_ICON_TODO = (
    '<svg class="shrink-0" width="12" height="12" viewBox="0 0 24 24" fill="none" '
    'stroke="currentColor" stroke-width="2.2" aria-hidden="true">'
    '<circle cx="12" cy="12" r="9"></circle></svg>'
)
_ICON_IN_PROGRESS = (
    '<svg class="shrink-0" width="12" height="12" viewBox="0 0 24 24" fill="none" '
    'stroke="currentColor" stroke-width="2.2" stroke-linecap="round" aria-hidden="true">'
    '<circle cx="12" cy="12" r="9"></circle>'
    '<polyline points="12 6 12 12 16 14"></polyline></svg>'
)
_ICON_DONE = (
    '<svg class="shrink-0" width="12" height="12" viewBox="0 0 24 24" fill="none" '
    'stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" '
    'aria-hidden="true">'
    '<path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path>'
    '<polyline points="22 4 12 14.01 9 11.01"></polyline></svg>'
)
_ICON_CANCELLED = (
    '<svg class="shrink-0" width="12" height="12" viewBox="0 0 24 24" fill="none" '
    'stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" '
    'aria-hidden="true">'
    '<circle cx="12" cy="12" r="9"></circle>'
    '<line x1="15" y1="9" x2="9" y2="15"></line>'
    '<line x1="9" y1="9" x2="15" y2="15"></line></svg>'
)


@dataclass(frozen=True)
class StatusUI:
    """Tailwind tokens and labels for one task status value."""

    label: str
    accent_border: str
    badge_classes: str
    section_label_classes: str
    section_dot_classes: str
    section_bg_classes: str
    section_count_classes: str
    card_classes: str
    title_classes: str
    icon_markup: str
    action_hint: str
    action_hover_classes: str


# Canonical mapping: todo=blue, in_progress=orange, done=green, cancelled=gray.
_STATUS_UI_MAP: dict[TaskStatus, StatusUI] = {
    TaskStatus.TODO: StatusUI(
        label="To do",
        accent_border="border-l-blue-600 dark:border-l-blue-500",
        badge_classes=(
            "bg-blue-100 text-blue-700 dark:bg-blue-500/15 dark:text-blue-300"
        ),
        section_label_classes="text-blue-600 dark:text-blue-400",
        section_dot_classes="bg-blue-600",
        section_bg_classes="bg-blue-50/60 dark:bg-blue-950/20",
        section_count_classes=(
            "bg-blue-100 text-blue-700 dark:bg-blue-500/15 dark:text-blue-300"
        ),
        card_classes="",
        title_classes="text-slate-900 dark:text-slate-100",
        icon_markup=_ICON_TODO,
        action_hint="Start",
        action_hover_classes=(
            "hover:border-blue-300 dark:hover:border-blue-600 "
            "hover:bg-blue-50 dark:hover:bg-blue-950/30"
        ),
    ),
    TaskStatus.IN_PROGRESS: StatusUI(
        label="In progress",
        accent_border="border-l-orange-600 dark:border-l-orange-500",
        badge_classes=(
            "bg-orange-100 text-orange-700 dark:bg-orange-500/15 dark:text-orange-300"
        ),
        section_label_classes="text-orange-600 dark:text-orange-400",
        section_dot_classes="bg-orange-600",
        section_bg_classes="bg-orange-50/60 dark:bg-orange-950/20",
        section_count_classes=(
            "bg-orange-100 text-orange-700 dark:bg-orange-500/15 dark:text-orange-300"
        ),
        card_classes=(
            "ring-1 ring-orange-200/60 dark:ring-orange-500/20"
        ),
        title_classes="text-slate-900 dark:text-slate-100",
        icon_markup=_ICON_IN_PROGRESS,
        action_hint="Complete",
        action_hover_classes=(
            "hover:border-orange-300 dark:hover:border-orange-600 "
            "hover:bg-orange-50 dark:hover:bg-orange-950/30"
        ),
    ),
    TaskStatus.DONE: StatusUI(
        label="Done",
        accent_border="border-l-green-600 dark:border-l-green-500",
        badge_classes=(
            "bg-green-100 text-green-700 dark:bg-green-500/15 dark:text-green-300"
        ),
        section_label_classes="text-green-600 dark:text-green-400",
        section_dot_classes="bg-green-600",
        section_bg_classes="bg-green-50/60 dark:bg-green-950/20",
        section_count_classes=(
            "bg-green-100 text-green-700 dark:bg-green-500/15 dark:text-green-300"
        ),
        card_classes="opacity-80",
        title_classes="line-through text-slate-400 dark:text-slate-500",
        icon_markup=_ICON_DONE,
        action_hint="Reopen",
        action_hover_classes=(
            "hover:border-slate-300 dark:hover:border-slate-600 "
            "hover:bg-slate-50 dark:hover:bg-slate-900"
        ),
    ),
    TaskStatus.CANCELLED: StatusUI(
        label="Cancelled",
        accent_border="border-l-slate-400 dark:border-l-slate-500",
        badge_classes=(
            "bg-slate-200 text-slate-500 dark:bg-slate-700 dark:text-slate-400"
        ),
        section_label_classes="text-slate-400 dark:text-slate-500",
        section_dot_classes="bg-slate-300 dark:bg-slate-600",
        section_bg_classes="bg-slate-100/80 dark:bg-slate-800/40",
        section_count_classes=(
            "bg-slate-200 text-slate-500 dark:bg-slate-700 dark:text-slate-400"
        ),
        card_classes="opacity-70",
        title_classes="line-through text-slate-400 dark:text-slate-500",
        icon_markup=_ICON_CANCELLED,
        action_hint="Restore",
        action_hover_classes=(
            "hover:border-slate-300 dark:hover:border-slate-600 "
            "hover:bg-slate-50 dark:hover:bg-slate-900"
        ),
    ),
}


def get_status_ui(status: str | TaskStatus) -> StatusUI:
    """Return presentation tokens for a task status string or enum member."""
    if isinstance(status, TaskStatus):
        status_key = status
    else:
        status_key = TaskStatus(status)

    return _STATUS_UI_MAP[status_key]
