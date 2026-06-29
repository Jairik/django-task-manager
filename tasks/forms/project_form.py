"""Form for creating and editing projects."""

from django import forms

from tasks.limits import MAX_DESCRIPTION_LENGTH, MAX_TAG_LENGTH
from tasks.models import Project


class ProjectForm(forms.ModelForm):
    """Validate project fields and map up to three tag inputs to the tags array."""

    # Bounded CharField overrides the model TextField for web-form validation.
    description = forms.CharField(
        max_length=MAX_DESCRIPTION_LENGTH,
        required=False,
        widget=forms.Textarea(
            attrs={"rows": 3, "maxlength": MAX_DESCRIPTION_LENGTH},
        ),
    )

    # Tags live on the model as an ArrayField; the template groups them under one "tags" label.
    tag_1 = forms.CharField(max_length=MAX_TAG_LENGTH, required=False, label="")
    tag_2 = forms.CharField(max_length=MAX_TAG_LENGTH, required=False, label="")
    tag_3 = forms.CharField(max_length=MAX_TAG_LENGTH, required=False, label="")

    class Meta:
        model = Project
        fields = ["name", "due_date", "priority", "description"]

    def __init__(self, *args, **kwargs):
        """Pre-fill tag inputs when editing an existing project."""
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

    def save(self, commit: bool = True) -> Project:
        """Persist the project row and its tag array."""
        project = super().save(commit=False)
        project.tags = self._collect_tags()

        if commit:
            project.save()

        return project
