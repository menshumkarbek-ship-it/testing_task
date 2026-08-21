from django import forms

from .models import AnswerOption


class AnswerForm(forms.Form):
    answers = forms.ModelMultipleChoiceField(
        queryset=AnswerOption.objects.none(),
        widget=forms.CheckboxSelectMultiple,
        required=True,
        error_messages={'required': 'Select at least one answer before continuing.'},
    )

    def __init__(self, *args, question, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['answers'].queryset = question.answers.all()
