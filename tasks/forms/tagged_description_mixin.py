"""Shared description and tag fields for project and task forms."""

from django import forms

from tasks.limits import MAX_DESCRIPTION_LENGTH, MAX_TAG_LENGTH


class TaggedDescriptionFormMixin(forms.ModelForm):
    """Add bounded description and up to three tag inputs mapped to ``tags`` array."""

    # Bounded CharField overrides the model TextField for web-form validation.
    description = forms.CharField(
        max_length=MAX_DESCRIPTION_LENGTH,
        required=False,
        widget=forms.Textarea(
            attrs={"rows": 3, "maxlength": MAX_DESCRIPTION_LENGTH},
        ),
    )

    # Tags live on the model as an ArrayField; the template groups them under one label.
    tag_1 = forms.CharField(max_length=MAX_TAG_LENGTH, required=False, label="")
    tag_2 = forms.CharField(max_length=MAX_TAG_LENGTH, required=False, label="")
    tag_3 = forms.CharField(max_length=MAX_TAG_LENGTH, required=False, label="")

    def __init__(self, *args, **kwargs):
        """Pre-fill tag inputs when editing an existing row."""
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

    def save(self, commit: bool = True):
        """Persist the model row and its tag array."""
        instance = super().save(commit=False)
        instance.tags = self._collect_tags()

        if commit:
            instance.save()

        return instance
