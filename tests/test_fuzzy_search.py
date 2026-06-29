"""Tests for shared fuzzy search query helpers."""

import pytest

from tasks.models import Project, Task, TaskStatus
from tasks.queries.fuzzy_search import (
    apply_fuzzy_search,
    build_fuzzy_name_description_q,
    build_fuzzy_tags_q,
)


@pytest.mark.django_db
def test_apply_fuzzy_search_empty_query_returns_all_projects() -> None:
    """An empty search term must not filter the queryset."""
    Project.objects.create(name="Alpha")
    Project.objects.create(name="Beta")

    results = list(apply_fuzzy_search(Project.objects.all(), ""))

    assert len(results) == 2


@pytest.mark.django_db
def test_fuzzy_name_typo_matches_project() -> None:
    """Trigram similarity tolerates minor typos in project names."""
    project = Project.objects.create(name="Alpha Release")
    Project.objects.create(name="Unrelated")

    matches = list(
        apply_fuzzy_search(Project.objects.all(), "Alpa Release")
    )

    assert [item.pk for item in matches] == [project.pk]


@pytest.mark.django_db
def test_fuzzy_description_substring_matches_project() -> None:
    """Substring search on description still works alongside trigram."""
    project = Project.objects.create(
        name="Docs",
        description="Quarterly roadmap planning",
    )
    Project.objects.create(name="Other", description="Unrelated notes")

    matches = list(apply_fuzzy_search(Project.objects.all(), "roadmap"))

    assert [item.pk for item in matches] == [project.pk]


@pytest.mark.django_db
def test_fuzzy_partial_tag_matches_project() -> None:
    """Partial tag text matches via unnest + ILIKE."""
    project = Project.objects.create(name="API refactor", tags=["backend"])
    Project.objects.create(name="UI polish", tags=["frontend"])

    matches = list(apply_fuzzy_search(Project.objects.all(), "back"))

    assert [item.pk for item in matches] == [project.pk]


@pytest.mark.django_db
def test_fuzzy_typo_tag_matches_project() -> None:
    """Typo-tolerant tag matching uses pg_trgm similarity on array elements."""
    project = Project.objects.create(name="API refactor", tags=["backend"])
    Project.objects.create(name="UI polish", tags=["frontend"])

    matches = list(apply_fuzzy_search(Project.objects.all(), "bakend"))

    assert [item.pk for item in matches] == [project.pk]


@pytest.mark.django_db
def test_fuzzy_task_search_scoped_to_queryset() -> None:
    """Task fuzzy search respects the caller's base queryset (project scope)."""
    project_a = Project.objects.create(name="Board A")
    project_b = Project.objects.create(name="Board B")
    task_a = Task.objects.create(
        project=project_a,
        name="Deploy release",
        status=TaskStatus.TODO,
    )
    Task.objects.create(
        project=project_b,
        name="Deploy elsewhere",
        status=TaskStatus.TODO,
    )

    base = Task.objects.filter(project_id=project_a.pk)
    matches = list(apply_fuzzy_search(base, "depliy"))

    assert [item.pk for item in matches] == [task_a.pk]


@pytest.mark.django_db
def test_fuzzy_no_match_returns_empty() -> None:
    """A term with no plausible hit returns an empty queryset."""
    Project.objects.create(name="Alpha Release")

    matches = list(apply_fuzzy_search(Project.objects.all(), "zzzznomatch"))

    assert matches == []


@pytest.mark.django_db
def test_build_fuzzy_name_description_q_combines_lookups() -> None:
    """Name/description Q object includes substring and trigram branches."""
    query = build_fuzzy_name_description_q(
        "alpha",
        model=Project,
        name_field="name",
        description_field="description",
    )

    assert query.children  # non-empty OR tree


@pytest.mark.django_db
def test_fuzzy_tag_search_percent_is_literal_not_wildcard() -> None:
    """A search for % must not match every project that has any tag."""
    tagged = Project.objects.create(name="Percent tag", tags=["100%"])
    Project.objects.create(name="Plain tag", tags=["backend"])

    matches = list(apply_fuzzy_search(Project.objects.all(), "%"))

    assert [item.pk for item in matches] == [tagged.pk]


@pytest.mark.django_db
def test_fuzzy_tag_search_underscore_is_literal_not_wildcard() -> None:
    """A search for _ must not treat underscore as a single-character wildcard."""
    underscored = Project.objects.create(name="Underscore tag", tags=["foo_bar"])
    Project.objects.create(name="No underscore", tags=["fooxbar"])

    matches = list(apply_fuzzy_search(Project.objects.all(), "_"))

    assert [item.pk for item in matches] == [underscored.pk]


@pytest.mark.django_db
def test_build_fuzzy_tags_q_matches_exact_tag() -> None:
    """Exact tag strings still match through the tag helper."""
    project = Project.objects.create(name="Tagged", tags=["backend"])

    tag_q = build_fuzzy_tags_q(Project, "backend", tags_field="tags")
    matches = list(Project.objects.filter(tag_q))

    assert [item.pk for item in matches] == [project.pk]
