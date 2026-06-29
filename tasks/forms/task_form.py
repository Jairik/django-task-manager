"""Form for creating and editing tasks."""

from django import forms

from tasks.models import Task


class TaskForm(forms.ModelForm):
    """Validate task fields and map up to three tag inputs to the tags array."""

    # Tags live on the model as an ArrayField; the template groups them under one "tags" label.
    tag_1 = forms.CharField(max_length=50, required=False, label="")
    tag_2 = forms.CharField(max_length=50, required=False, label="")
    tag_3 = forms.CharField(max_length=50, required=False, label="")

    class Meta:
        model = Task
        # `status` is intentionally omitted: new tasks start as "To do" (the model default).
        fields = ["name", "description", "priority", "due_date"]

    def __init__(self, *args, **kwargs):
        """Pre-fill tag inputs when editing an existing task."""
        super().__init__(*args, **kwargs)

        if self.instance.pk:
            existing_tags = self.instance.tags or []
            for index, value in enumerate(existing_tags[:3], start=1):
                self.fields[f"tag_{index}"].initial = value

    def _collect_tags(self) -> list[str]:
        """Return non-empty tag values from the three tag fields."""
        tags: list[str] = []

        for field_name in ("tag_1", "tag_2", "tag_3"):
            value = self.cleaned_data.get(field_name, "").strip()
            if value:
                tags.append(value)

        return tags

    def save(self, commit: bool = True) -> Task:
        """Persist the task row and its tag array.

        The caller is responsible for setting ``task.project`` before a commit,
        so callers that pass ``commit=False`` can attach the parent project.
        """
        task = super().save(commit=False)
        task.tags = self._collect_tags()

        if commit:
            task.save()

        return task
