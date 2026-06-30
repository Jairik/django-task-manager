"""Form for creating and editing projects."""

from tasks.forms.tagged_description_mixin import TaggedDescriptionFormMixin
from tasks.models import Project


class ProjectForm(TaggedDescriptionFormMixin):
    """Validate project fields and map up to three tag inputs to the tags array."""

    class Meta:
        model = Project
        fields = ["name", "due_date", "priority", "description"]
