"""Shared fuzzy search filters for project and task list querysets.

Uses PostgreSQL ``pg_trgm`` for typo-tolerant name/description matching and
partial + fuzzy tag matching via ``unnest`` on the tags array.
"""

from django.db.models import Q, QuerySet
from django.db.models.expressions import RawSQL

# Default pg_trgm similarity cutoff; rows below this do not match on trigram alone.
FUZZY_SIMILARITY_THRESHOLD = 0.3

# PostgreSQL ILIKE treats % and _ as wildcards; backslash is the escape character
# when the query uses ``ESCAPE E'\\'``.
LIKE_ESCAPE_CHAR = "\\"


def escape_like_literal(value: str) -> str:
    """Escape user text before embedding it in an ILIKE pattern with ESCAPE."""
    escaped = value.replace(LIKE_ESCAPE_CHAR, LIKE_ESCAPE_CHAR + LIKE_ESCAPE_CHAR)
    escaped = escaped.replace("%", LIKE_ESCAPE_CHAR + "%")
    return escaped.replace("_", LIKE_ESCAPE_CHAR + "_")


def build_fuzzy_name_description_q(
    search: str,
    *,
    model: type,
    name_field: str,
    description_field: str,
) -> Q:
    """Return a Q object matching name or description by substring or trigram."""
    table = model._meta.db_table
    threshold = FUZZY_SIMILARITY_THRESHOLD

    # Substring and whole-string trigram lookups cover most cases.
    text_q = (
        Q(**{f"{name_field}__icontains": search})
        | Q(**{f"{name_field}__trigram_similar": search})
        | Q(**{f"{description_field}__icontains": search})
        | Q(**{f"{description_field}__trigram_similar": search})
    )

    # Word-level similarity uses our app threshold (pg_trgm default is stricter).
    word_similarity_q = Q(
        pk__in=RawSQL(
            f"""
            SELECT id FROM {table}
            WHERE word_similarity(%s, {name_field}) >= %s
               OR word_similarity(%s, {description_field}) >= %s
            """,
            [search, threshold, search, threshold],
        )
    )

    return text_q | word_similarity_q


def build_fuzzy_tags_q(
    model: type,
    search: str,
    *,
    tags_field: str,
) -> Q:
    """Return a Q object matching when any tag partially or fuzzily hits the term.

    Unnests the PostgreSQL varchar array and checks ``ILIKE`` (partial) or
    ``similarity()`` (typo tolerance) against each element.
    """
    table = model._meta.db_table
    # Escape LIKE metacharacters so user input is matched literally (e.g. "%").
    pattern = f"%{escape_like_literal(search)}%"

    # Subquery lists primary keys whose tag array contains a partial/fuzzy hit.
    tag_match_subquery = RawSQL(
        f"""
        SELECT id FROM {table}
        WHERE EXISTS (
            SELECT 1 FROM unnest({tags_field}) AS tag
            WHERE tag ILIKE %s ESCAPE E'\\\\'
               OR similarity(tag, %s) >= %s
        )
        """,
        [pattern, search, FUZZY_SIMILARITY_THRESHOLD],
    )

    return Q(pk__in=tag_match_subquery)


def apply_fuzzy_search(
    queryset: QuerySet,
    search: str,
    *,
    name_field: str = "name",
    description_field: str = "description",
    tags_field: str = "tags",
) -> QuerySet:
    """Filter a queryset with fuzzy name, description, and tag matching.

    Returns the queryset unchanged when ``search`` is empty so callers can
    always pass the normalized query string from the view layer.
    """
    if not search:
        return queryset

    name_description_q = build_fuzzy_name_description_q(
        search,
        model=queryset.model,
        name_field=name_field,
        description_field=description_field,
    )
    tags_q = build_fuzzy_tags_q(
        queryset.model,
        search,
        tags_field=tags_field,
    )

    return queryset.filter(name_description_q | tags_q)
