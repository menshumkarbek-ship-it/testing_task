from django.contrib import admin
from django.core.exceptions import ValidationError
from django.forms.models import BaseInlineFormSet

from .models import AnswerOption, Question, QuizAttempt, QuizSet, UserAnswer


class AnswerOptionInlineFormSet(BaseInlineFormSet):
    """Require each question to have a mix of correct and incorrect choices."""

    def clean(self):
        super().clean()
        if any(self.errors):
            return
        options = [
            form.cleaned_data for form in self.forms
            if form.cleaned_data and not form.cleaned_data.get('DELETE', False)
        ]
        correct_count = sum(option.get('is_correct', False) for option in options)
        if not correct_count:
            raise ValidationError('Mark at least one answer option as correct.')
        if correct_count == len(options):
            raise ValidationError('At least one answer option must be incorrect.')


class AnswerOptionInline(admin.TabularInline):
    model = AnswerOption
    formset = AnswerOptionInlineFormSet
    extra = 2


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('question_text', 'quiz_set', 'order_index')
    list_filter = ('quiz_set',)
    ordering = ('quiz_set', 'order_index')
    inlines = (AnswerOptionInline,)


class QuestionInline(admin.TabularInline):
    model = Question
    extra = 1
    fields = ('question_text', 'order_index')
    ordering = ('order_index',)


@admin.register(QuizSet)
class QuizSetAdmin(admin.ModelAdmin):
    list_display = ('title', 'created_at')
    search_fields = ('title',)
    inlines = (QuestionInline,)


@admin.register(AnswerOption)
class AnswerOptionAdmin(admin.ModelAdmin):
    list_display = ('answer_text', 'question', 'is_correct')
    list_filter = ('is_correct', 'question__quiz_set')


@admin.register(QuizAttempt)
class QuizAttemptAdmin(admin.ModelAdmin):
    list_display = ('user', 'quiz_set', 'status', 'score', 'correct_count', 'incorrect_count', 'timestamp')
    list_filter = ('status', 'quiz_set')
    readonly_fields = ('score', 'correct_count', 'incorrect_count', 'timestamp')


@admin.register(UserAnswer)
class UserAnswerAdmin(admin.ModelAdmin):
    list_display = ('quiz_attempt', 'question', 'selected_answer', 'is_correct')
    list_filter = ('is_correct',)
