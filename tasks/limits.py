"""App-layer input length limits for forms and search queries.

These caps defend against oversized POST bodies and search strings. Model
``TextField`` columns (e.g. description) remain unbounded at the DB level;
writes through the web UI are validated in forms instead.
"""

# Match model CharField / ArrayField base_field sizes.
MAX_NAME_LENGTH = 255
MAX_TAG_LENGTH = 50

# App-layer cap for description text areas (DB column stays TEXT).
MAX_DESCRIPTION_LENGTH = 5000

# Truncate home and project-detail ?q= before queryset filters run.
MAX_SEARCH_QUERY_LENGTH = 200


def normalize_search_query(raw: str) -> str:
    """Strip whitespace and truncate a search query to the allowed max length."""
    return raw.strip()[:MAX_SEARCH_QUERY_LENGTH]
