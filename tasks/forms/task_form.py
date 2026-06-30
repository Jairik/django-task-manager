"""Form for creating and editing tasks."""

from tasks.forms.tagged_description_mixin import TaggedDescriptionFormMixin
from tasks.models import Task


class TaskForm(TaggedDescriptionFormMixin):
    """Validate task fields and map up to three tag inputs to the tags array."""

    class Meta:
        model = Task
        # `status` is shown on the edit form only; new tasks use the model default.
        fields = ["name", "description", "priority", "due_date", "status"]

    def __init__(self, *args, **kwargs):
        """Pre-fill tag inputs when editing; hide status on the create form."""
        super().__init__(*args, **kwargs)

        if not self.instance.pk:
            # Create flow omits status — the model default ("todo") applies on save.
            del self.fields["status"]

    def save(self, commit: bool = True) -> Task:
        """Persist the task row and its tag array.

        The caller is responsible for setting ``task.project`` before a commit,
        so callers that pass ``commit=False`` can attach the parent project.
        """
        return super().save(commit=commit)
