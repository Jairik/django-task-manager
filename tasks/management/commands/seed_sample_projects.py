"""Insert two large, realistic sample projects for manual and UI testing.

Usage (from repo root, with PostgreSQL env loaded):

    set -a && source .env.testing && set +a
    uv run python manage.py seed_sample_projects

Re-run safely: existing seed projects (matched by name) are skipped unless
``--force`` is passed, which deletes and recreates them.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from typing import Any

from django.core.management.base import BaseCommand
from django.db import transaction

from tasks.models import Priority, Project, Task, TaskStatus
from tasks.queries.project_tasks import refresh_project_soonest_due_date

# Stable names so the command can detect prior runs and support ``--force``.
SEED_PROJECT_NAMES: tuple[str, str] = (
    "Q3 Product Launch — TeamFlow",
    "Backyard Patio & Deck Renovation",
)


@dataclass(frozen=True)
class SeedTaskSpec:
    """One task row to create under a seeded project."""

    name: str
    description: str
    priority: Priority
    status: TaskStatus
    due_date: date | None = None
    tags: tuple[str, ...] = ()


@dataclass(frozen=True)
class SeedProjectSpec:
    """Project metadata plus the task list inserted beneath it."""

    name: str
    description: str
    priority: Priority
    due_date: date | None
    tags: tuple[str, ...]
    tasks: tuple[SeedTaskSpec, ...]


def _days_from_today(offset: int) -> date:
    """Return a calendar date relative to the current local day."""
    return date.today() + timedelta(days=offset)


def build_seed_project_specs() -> tuple[SeedProjectSpec, SeedProjectSpec]:
    """Build two realistic projects with many tasks for search and kanban testing."""
    product_launch = SeedProjectSpec(
        name=SEED_PROJECT_NAMES[0],
        description=(
            "Coordinate engineering, design, and go-to-market work for the TeamFlow "
            "self-serve launch. Tracks billing integration, onboarding polish, "
            "security review, and launch-week support runbooks."
        ),
        priority=Priority.VERY_HIGH,
        due_date=_days_from_today(95),
        tags=("saas", "launch", "q3"),
        tasks=(
            SeedTaskSpec(
                name="Finalize pricing tiers and entitlements matrix",
                description=(
                    "Document Free, Pro, and Business limits. Confirm seat-based "
                    "billing rules with finance and update the public pricing page copy."
                ),
                priority=Priority.HIGH,
                status=TaskStatus.DONE,
                due_date=_days_from_today(-21),
                tags=("pricing", "product"),
            ),
            SeedTaskSpec(
                name="Stripe webhook idempotency audit",
                description=(
                    "Review checkout.session.completed and invoice.paid handlers. "
                    "Add replay protection and structured logging for failed events."
                ),
                priority=Priority.VERY_HIGH,
                status=TaskStatus.IN_PROGRESS,
                due_date=_days_from_today(7),
                tags=("billing", "backend"),
            ),
            SeedTaskSpec(
                name="Implement trial-to-paid conversion funnel",
                description=(
                    "Add in-app upgrade prompts at day 7 and day 13 of trial. "
                    "Instrument conversion events for the launch dashboard."
                ),
                priority=Priority.HIGH,
                status=TaskStatus.IN_PROGRESS,
                due_date=_days_from_today(14),
                tags=("growth", "frontend"),
            ),
            SeedTaskSpec(
                name="SOC 2 readiness checklist — access controls",
                description=(
                    "Export admin audit logs, verify MFA enforcement for staff "
                    "accounts, and attach evidence to the compliance folder."
                ),
                priority=Priority.MEDIUM,
                status=TaskStatus.TODO,
                due_date=_days_from_today(28),
                tags=("security", "compliance"),
            ),
            SeedTaskSpec(
                name="Load test signup and workspace creation",
                description=(
                    "Simulate 500 concurrent signups in staging. Capture p95 latency "
                    "for project bootstrap and first-task creation flows."
                ),
                priority=Priority.HIGH,
                status=TaskStatus.TODO,
                due_date=_days_from_today(21),
                tags=("perf", "qa"),
            ),
            SeedTaskSpec(
                name="Design onboarding empty states",
                description=(
                    "Illustrations and copy for zero projects, zero tasks, and first "
                    "invite-sent states. Hand off SVG assets to frontend."
                ),
                priority=Priority.MEDIUM,
                status=TaskStatus.DONE,
                due_date=_days_from_today(-10),
                tags=("design", "ux"),
            ),
            SeedTaskSpec(
                name="Write launch-day incident runbook",
                description=(
                    "Pager rotation, rollback steps for billing, and comms templates "
                    "for status page updates during the first 72 hours post-launch."
                ),
                priority=Priority.VERY_HIGH,
                status=TaskStatus.TODO,
                due_date=_days_from_today(42),
                tags=("ops", "launch"),
            ),
            SeedTaskSpec(
                name="Email templates — welcome and trial ending",
                description=(
                    "Finalize HTML and plain-text variants. Confirm unsubscribe "
                    "footer and CAN-SPAM address block with legal."
                ),
                priority=Priority.MEDIUM,
                status=TaskStatus.IN_PROGRESS,
                due_date=_days_from_today(18),
                tags=("email", "marketing"),
            ),
            SeedTaskSpec(
                name="API rate limiting for public endpoints",
                description=(
                    "Apply per-IP and per-token limits on read-heavy routes. "
                    "Return 429 with Retry-After headers and document limits."
                ),
                priority=Priority.HIGH,
                status=TaskStatus.TODO,
                due_date=_days_from_today(35),
                tags=("backend", "security"),
            ),
            SeedTaskSpec(
                name="Migrate legacy CSV importers to background jobs",
                description=(
                    "Move synchronous import path to Celery (or Django-Q) workers "
                    "so large customer uploads do not block web workers."
                ),
                priority=Priority.MEDIUM,
                status=TaskStatus.CANCELLED,
                due_date=None,
                tags=("backend", "deferred"),
            ),
            SeedTaskSpec(
                name="Customer success training deck",
                description=(
                    "60-minute session covering billing edge cases, seat changes, "
                    "and how to escalate webhook reconciliation issues."
                ),
                priority=Priority.LOW,
                status=TaskStatus.TODO,
                due_date=_days_from_today(56),
                tags=("enablement",),
            ),
            SeedTaskSpec(
                name="Fix mobile nav overlap on project detail",
                description=(
                    "Toolbar buttons wrap incorrectly below 390px width. Adjust "
                    "flex layout and verify on iOS Safari and Chrome Android."
                ),
                priority=Priority.MEDIUM,
                status=TaskStatus.DONE,
                due_date=_days_from_today(-3),
                tags=("frontend", "bugfix"),
            ),
            SeedTaskSpec(
                name="Draft launch blog post and changelog",
                description=(
                    "Highlight task templates, fuzzy search, and team invites. "
                    "Coordinate publish time with Product Hunt listing."
                ),
                priority=Priority.MEDIUM,
                status=TaskStatus.IN_PROGRESS,
                due_date=_days_from_today(49),
                tags=("marketing", "content"),
            ),
            SeedTaskSpec(
                name="Pen test remediation — XSS in task descriptions",
                description=(
                    "Sanitize rich text on save and add CSP report-only headers in "
                    "staging before re-test with the external vendor."
                ),
                priority=Priority.VERY_HIGH,
                status=TaskStatus.TODO,
                due_date=_days_from_today(10),
                tags=("security", "bugfix"),
            ),
            SeedTaskSpec(
                name="Set up launch metrics dashboard",
                description=(
                    "Daily active workspaces, trial starts, paid conversions, and "
                    "support ticket volume. Share read-only link with leadership."
                ),
                priority=Priority.MEDIUM,
                status=TaskStatus.TODO,
                due_date=_days_from_today(63),
                tags=("analytics",),
            ),
            SeedTaskSpec(
                name="Update terms of service for self-serve billing",
                description=(
                    "Legal review of auto-renew language and refund policy. Publish "
                    "PDF and in-app acceptance banner for existing users."
                ),
                priority=Priority.HIGH,
                status=TaskStatus.TODO,
                due_date=_days_from_today(30),
                tags=("legal",),
            ),
            SeedTaskSpec(
                name="Smoke test production deploy pipeline",
                description=(
                    "Verify blue/green deploy, database migration ordering, and "
                    "feature flag defaults immediately after cutover."
                ),
                priority=Priority.HIGH,
                status=TaskStatus.DONE,
                due_date=_days_from_today(-14),
                tags=("devops", "qa"),
            ),
            SeedTaskSpec(
                name="Partner integration — Slack notifications",
                description=(
                    "Post task status changes to configured channels. Handle token "
                    "rotation and workspace uninstall cleanup."
                ),
                priority=Priority.LOW,
                status=TaskStatus.TODO,
                due_date=_days_from_today(70),
                tags=("integrations",),
            ),
            SeedTaskSpec(
                name="Overdue: finalize demo environment seed data",
                description=(
                    "Staging should mirror realistic project/task volume for sales "
                    "demos. This slipped last sprint and blocks AE rehearsals."
                ),
                priority=Priority.HIGH,
                status=TaskStatus.IN_PROGRESS,
                due_date=_days_from_today(-5),
                tags=("staging", "sales"),
            ),
            SeedTaskSpec(
                name="Localization pass for onboarding strings",
                description=(
                    "Extract copy to PO files and deliver French and Spanish "
                    "translations for signup and billing screens."
                ),
                priority=Priority.LOW,
                status=TaskStatus.CANCELLED,
                due_date=None,
                tags=("i18n",),
            ),
            SeedTaskSpec(
                name="Launch webinar rehearsal",
                description=(
                    "Dry run with PM, eng lead, and support. Timebox to 45 minutes "
                    "and collect FAQ additions for the help center."
                ),
                priority=Priority.MEDIUM,
                status=TaskStatus.TODO,
                due_date=_days_from_today(88),
                tags=("marketing", "launch"),
            ),
        ),
    )

    patio_renovation = SeedProjectSpec(
        name=SEED_PROJECT_NAMES[1],
        description=(
            "Plan and execute a full backyard refresh: demo the old deck, pour a "
            "stamped concrete patio, install low-voltage lighting, and rebuild "
            "planters along the fence line. Includes permit, material lead times, "
            "and contractor coordination."
        ),
        priority=Priority.MEDIUM,
        due_date=_days_from_today(74),
        tags=("home", "renovation"),
        tasks=(
            SeedTaskSpec(
                name="Submit deck replacement permit to city",
                description=(
                    "Include current site plan, footing details, and railing height "
                    "specs. Pay fee online and post the approval letter on the fridge."
                ),
                priority=Priority.VERY_HIGH,
                status=TaskStatus.DONE,
                due_date=_days_from_today(-35),
                tags=("permit",),
            ),
            SeedTaskSpec(
                name="Get three quotes for composite decking",
                description=(
                    "Compare Trex vs TimberTech for 12x16 layout. Ask about lead "
                    "times and hidden-fastener labor rates."
                ),
                priority=Priority.HIGH,
                status=TaskStatus.DONE,
                due_date=_days_from_today(-28),
                tags=("materials",),
            ),
            SeedTaskSpec(
                name="Schedule utility locate before demo",
                description=(
                    "Call 811 and mark gas, electric, and irrigation lines. Photograph "
                    "flags before the crew starts jackhammer work."
                ),
                priority=Priority.VERY_HIGH,
                status=TaskStatus.DONE,
                due_date=_days_from_today(-18),
                tags=("safety",),
            ),
            SeedTaskSpec(
                name="Demo existing deck and haul away debris",
                description=(
                    "Rent 20-yard dumpster. Salvage usable lumber for garden beds "
                    "and confirm haul-away includes nails and old footings."
                ),
                priority=Priority.HIGH,
                status=TaskStatus.DONE,
                due_date=_days_from_today(-12),
                tags=("demo", "contractor"),
            ),
            SeedTaskSpec(
                name="Pour stamped concrete patio — ashlar slate pattern",
                description=(
                    "Base prep, rebar grid, and integral color. Cure for 7 days before "
                    "furniture placement; seal after 28 days."
                ),
                priority=Priority.HIGH,
                status=TaskStatus.IN_PROGRESS,
                due_date=_days_from_today(5),
                tags=("concrete", "contractor"),
            ),
            SeedTaskSpec(
                name="Install new deck framing and composite boards",
                description=(
                    "Pressure-treated posts on sono tubes, ledger bolt pattern per "
                    "permit, and picture-frame border on the stair landing."
                ),
                priority=Priority.HIGH,
                status=TaskStatus.IN_PROGRESS,
                due_date=_days_from_today(12),
                tags=("deck", "contractor"),
            ),
            SeedTaskSpec(
                name="Run low-voltage cable for path lights",
                description=(
                    "12-gauge wire from transformer near the garage. Leave extra loop "
                    "at each fixture for future repositioning."
                ),
                priority=Priority.MEDIUM,
                status=TaskStatus.TODO,
                due_date=_days_from_today(20),
                tags=("electrical",),
            ),
            SeedTaskSpec(
                name="Select outdoor dining set and umbrella",
                description=(
                    "Table for six with UV-resistant cushions. Confirm umbrella "
                    "clearance over the new patio slope."
                ),
                priority=Priority.LOW,
                status=TaskStatus.TODO,
                due_date=_days_from_today(45),
                tags=("furniture",),
            ),
            SeedTaskSpec(
                name="Build cedar planters along south fence",
                description=(
                    "Three 8-foot boxes with drainage and landscape fabric. Fill "
                    "with raised-bed mix before planting herbs."
                ),
                priority=Priority.MEDIUM,
                status=TaskStatus.TODO,
                due_date=_days_from_today(32),
                tags=("carpentry",),
            ),
            SeedTaskSpec(
                name="Regrade soil away from foundation",
                description=(
                    "Ensure 6-inch drop over first 10 feet. Extend downspout "
                    "extensions after gutter cleaning."
                ),
                priority=Priority.MEDIUM,
                status=TaskStatus.TODO,
                due_date=_days_from_today(25),
                tags=("drainage",),
            ),
            SeedTaskSpec(
                name="Overdue: confirm railing picket spacing with inspector",
                description=(
                    "Inspector wants 4-inch sphere rule verified on stair guard. "
                    "Contractor to adjust before final walkthrough."
                ),
                priority=Priority.HIGH,
                status=TaskStatus.IN_PROGRESS,
                due_date=_days_from_today(-2),
                tags=("permit", "inspection"),
            ),
            SeedTaskSpec(
                name="Order outdoor kitchen propane line extension",
                description=(
                    "Licensed plumber to tee from main line and install shutoff "
                    "behind the future grill cabinet."
                ),
                priority=Priority.MEDIUM,
                status=TaskStatus.TODO,
                due_date=_days_from_today(38),
                tags=("plumbing",),
            ),
            SeedTaskSpec(
                name="Seed lawn repair along fence line",
                description=(
                    "Top-dress bare patches after equipment traffic. Hold off until "
                    "heavy foot traffic from deck install is finished."
                ),
                priority=Priority.LOW,
                status=TaskStatus.TODO,
                due_date=_days_from_today(52),
                tags=("landscaping",),
            ),
            SeedTaskSpec(
                name="Install drip irrigation for planters",
                description=(
                    "Connect to existing zone with timer override. Label valves "
                    "in the garage utility panel."
                ),
                priority=Priority.LOW,
                status=TaskStatus.TODO,
                due_date=_days_from_today(40),
                tags=("irrigation",),
            ),
            SeedTaskSpec(
                name="Stain deck skirt and stair stringers",
                description=(
                    "Two coats of solid hide stain to match railing. Mask concrete "
                    "edges before brushing."
                ),
                priority=Priority.MEDIUM,
                status=TaskStatus.TODO,
                due_date=_days_from_today(28),
                tags=("finishing",),
            ),
            SeedTaskSpec(
                name="Final inspection walkthrough",
                description=(
                    "Book morning slot with city inspector. Have permit card, "
                    "fastener schedule, and railing height measurements ready."
                ),
                priority=Priority.VERY_HIGH,
                status=TaskStatus.TODO,
                due_date=_days_from_today(60),
                tags=("permit", "inspection"),
            ),
            SeedTaskSpec(
                name="Host backyard reveal party",
                description=(
                    "Invite neighbors and family. Rent propane fire pit and prep "
                    "simple menu; rain date one week later."
                ),
                priority=Priority.LOW,
                status=TaskStatus.TODO,
                due_date=_days_from_today(74),
                tags=("personal",),
            ),
            SeedTaskSpec(
                name="Cancel hot tub pad extension",
                description=(
                    "Deferred until next season — focus budget on deck and patio "
                    "this year. Revisit quotes in spring."
                ),
                priority=Priority.LOW,
                status=TaskStatus.CANCELLED,
                due_date=None,
                tags=("deferred",),
            ),
            SeedTaskSpec(
                name="Power wash house siding before party",
                description=(
                    "Use wide fan tip on vinyl; avoid windows and light fixtures. "
                    "Best done after concrete dust settles."
                ),
                priority=Priority.LOW,
                status=TaskStatus.TODO,
                due_date=_days_from_today(68),
                tags=("cleanup",),
            ),
            SeedTaskSpec(
                name="Measure and order custom pergola kit",
                description=(
                    "10x12 aluminum pergola with retractable shade. Confirm frost "
                    "depth requirements for anchor bolts."
                ),
                priority=Priority.MEDIUM,
                status=TaskStatus.TODO,
                due_date=_days_from_today(48),
                tags=("structure",),
            ),
        ),
    )

    return product_launch, patio_renovation


def insert_seed_project(spec: SeedProjectSpec) -> tuple[Project, int]:
    """Create one project and its tasks, then refresh ``soonest_due_date``."""
    project = Project.objects.create(
        name=spec.name,
        description=spec.description,
        priority=spec.priority,
        due_date=spec.due_date,
        tags=list(spec.tags),
    )

    task_rows: list[Task] = []
    for task_spec in spec.tasks:
        task_rows.append(
            Task(
                project=project,
                name=task_spec.name,
                description=task_spec.description,
                priority=task_spec.priority,
                status=task_spec.status,
                due_date=task_spec.due_date,
                tags=list(task_spec.tags),
            )
        )

    Task.objects.bulk_create(task_rows)
    refresh_project_soonest_due_date(project)

    return project, len(task_rows)


class Command(BaseCommand):
    """Management command entry point for sample project seeding."""

    help = "Insert two large sample projects with realistic tasks for testing."

    def add_arguments(self, parser: Any) -> None:
        """Register ``--force`` to replace existing seed projects."""
        parser.add_argument(
            "--force",
            action="store_true",
            help="Delete existing seed projects (by name) and recreate them.",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        """Insert seed data or skip when projects already exist."""
        force: bool = options["force"]
        existing = Project.objects.filter(name__in=SEED_PROJECT_NAMES)

        if existing.exists() and not force:
            names = ", ".join(existing.values_list("name", flat=True))
            self.stdout.write(
                self.style.WARNING(
                    f"Seed projects already exist ({names}). "
                    "Use --force to delete and recreate them."
                )
            )
            return

        with transaction.atomic():
            if force:
                deleted_count, _ = existing.delete()
                if deleted_count:
                    self.stdout.write(
                        self.style.WARNING(
                            f"Removed {deleted_count} existing seed row(s)."
                        )
                    )

            specs = build_seed_project_specs()
            for spec in specs:
                project, task_count = insert_seed_project(spec)
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Created {project.name!r} with {task_count} tasks "
                        f"(soonest due: {project.soonest_due_date})."
                    )
                )
