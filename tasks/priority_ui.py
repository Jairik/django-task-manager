"""Priority presentation tokens for project and task badges.

Centralizes Tailwind class strings so templates stay DRY and tests can assert
the canonical red / amber / slate mapping for high, medium, and low tiers.
"""

from dataclasses import dataclass

from tasks.models import Priority


@dataclass(frozen=True)
class PriorityUI:
    """Tailwind tokens for one priority value."""

    badge_classes: str
    compact_badge_classes: str
    text_classes: str


# high/very_high -> red, medium -> amber, low/very_low -> slate.
_PRIORITY_UI_MAP: dict[Priority, PriorityUI] = {
    Priority.VERY_HIGH: PriorityUI(
        badge_classes=(
            "bg-red-100 text-red-700 dark:bg-red-500/15 dark:text-red-300"
        ),
        compact_badge_classes=(
            "bg-red-50 text-red-600 dark:bg-red-500/10 dark:text-red-400"
        ),
        text_classes="text-red-700 dark:text-red-400",
    ),
    Priority.HIGH: PriorityUI(
        badge_classes=(
            "bg-red-100 text-red-700 dark:bg-red-500/15 dark:text-red-300"
        ),
        compact_badge_classes=(
            "bg-red-50 text-red-600 dark:bg-red-500/10 dark:text-red-400"
        ),
        text_classes="text-red-700 dark:text-red-400",
    ),
    Priority.MEDIUM: PriorityUI(
        badge_classes=(
            "bg-amber-100 text-amber-700 dark:bg-amber-500/15 dark:text-amber-300"
        ),
        compact_badge_classes=(
            "bg-amber-50 text-amber-600 dark:bg-amber-500/10 dark:text-amber-400"
        ),
        text_classes="text-amber-700 dark:text-amber-400",
    ),
    Priority.LOW: PriorityUI(
        badge_classes=(
            "bg-slate-200 text-slate-600 dark:bg-slate-700 dark:text-slate-300"
        ),
        compact_badge_classes=(
            "bg-slate-100 text-slate-500 dark:bg-slate-700/60 dark:text-slate-400"
        ),
        text_classes="text-slate-500 dark:text-slate-400",
    ),
    Priority.VERY_LOW: PriorityUI(
        badge_classes=(
            "bg-slate-200 text-slate-600 dark:bg-slate-700 dark:text-slate-300"
        ),
        compact_badge_classes=(
            "bg-slate-100 text-slate-500 dark:bg-slate-700/60 dark:text-slate-400"
        ),
        text_classes="text-slate-500 dark:text-slate-400",
    ),
}


def get_priority_ui(priority: str | Priority) -> PriorityUI:
    """Return presentation tokens for a priority string or enum member."""
    if isinstance(priority, Priority):
        priority_key = priority
    else:
        priority_key = Priority(priority)

    return _PRIORITY_UI_MAP[priority_key]
