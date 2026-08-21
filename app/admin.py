import nested_admin
from django.contrib import admin
from django.core.exceptions import ValidationError
from nested_admin.formsets import NestedInlineFormSet

from .models import AnswerOption, Question, QuizSet


class AnswerOptionInlineFormSet(NestedInlineFormSet):
    """Ensure each saved question has both correct and incorrect choices."""

    def clean(self):
        super().clean()
        if any(self.errors):
            return

        options = [
            form.cleaned_data
            for form in self.forms
            if form.cleaned_data and not form.cleaned_data.get('DELETE', False)
        ]
        correct_count = sum(option.get('is_correct', False) for option in options)
        if not correct_count:
            raise ValidationError('Mark at least one answer option as correct.')
        if correct_count == len(options):
            raise ValidationError('At least one answer option must be incorrect.')


class AnswerOptionInline(nested_admin.NestedTabularInline):
    model = AnswerOption
    formset = AnswerOptionInlineFormSet
    extra = 2


class QuestionInline(nested_admin.NestedStackedInline):
    model = Question
    extra = 1
    fields = ('question_text', 'order_index')
    ordering = ('order_index',)
    inlines = (AnswerOptionInline,)


@admin.register(QuizSet)
class QuizSetAdmin(nested_admin.NestedModelAdmin):
    list_display = ('title', 'created_at')
    search_fields = ('title',)
    inlines = (QuestionInline,)


@admin.register(Question)
class QuestionAdmin(nested_admin.NestedModelAdmin):
    list_display = ('question_text', 'quiz_set', 'order_index')
    list_filter = ('quiz_set',)
    ordering = ('quiz_set', 'order_index')
    inlines = (AnswerOptionInline,)


@admin.register(AnswerOption)
class AnswerOptionAdmin(admin.ModelAdmin):
    list_display = ('answer_text', 'question', 'is_correct')
    list_filter = ('is_correct', 'question__quiz_set')
