"""Tests for centralized task status presentation tokens."""

import pytest

from tasks.models import TaskStatus
from tasks.status_ui import get_status_ui


@pytest.mark.parametrize(
    ("status", "accent_fragment", "action_hint"),
    [
        (TaskStatus.TODO, "border-l-blue-600", "Start"),
        (TaskStatus.IN_PROGRESS, "border-l-orange-600", "Complete"),
        (TaskStatus.DONE, "border-l-green-600", "Reopen"),
        (TaskStatus.CANCELLED, "border-l-slate-400", "Restore"),
    ],
)
def test_get_status_ui_returns_tokens_for_all_statuses(
    status: TaskStatus,
    accent_fragment: str,
    action_hint: str,
) -> None:
    """Each TaskStatus maps to accent colors and action labels."""
    ui = get_status_ui(status)

    assert ui.label == status.label
    assert accent_fragment in ui.accent_border
    assert action_hint == ui.action_hint
    assert ui.icon_markup.startswith("<svg")


def test_get_status_ui_accepts_string_values() -> None:
    """Status lookup accepts raw string values from model rows."""
    ui = get_status_ui("todo")

    assert ui.label == "To do"
    assert "blue" in ui.badge_classes
