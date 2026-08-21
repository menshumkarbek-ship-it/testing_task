from django.contrib.auth.models import User
from django.db import models


class QuizSet(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('title',)

    def __str__(self):
        return self.title


class Question(models.Model):
    quiz_set = models.ForeignKey(QuizSet, on_delete=models.CASCADE, related_name='questions')
    question_text = models.TextField()
    order_index = models.PositiveIntegerField()

    class Meta:
        ordering = ('order_index',)
        constraints = [models.UniqueConstraint(fields=('quiz_set', 'order_index'), name='unique_question_order')]

    def __str__(self):
        return f'{self.quiz_set}: {self.order_index}'


class AnswerOption(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='answers')
    answer_text = models.CharField(max_length=255)
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return self.answer_text


class QuizAttempt(models.Model):
    quiz_set = models.ForeignKey(QuizSet, on_delete=models.CASCADE, related_name='attempts')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='quiz_attempts')
    status = models.CharField(max_length=12, choices=(('in_progress', 'In progress'), ('completed', 'Completed')), default='in_progress')
    score = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    correct_count = models.PositiveIntegerField(default=0)
    incorrect_count = models.PositiveIntegerField(default=0)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('-timestamp',)

    def __str__(self):
        return f'{self.user} — {self.quiz_set} ({self.get_status_display()})'


class UserAnswer(models.Model):
    quiz_attempt = models.ForeignKey(QuizAttempt, on_delete=models.CASCADE, related_name='user_answers')
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    selected_answer = models.ForeignKey(AnswerOption, on_delete=models.CASCADE, related_name='selected_by')
    is_correct = models.BooleanField(default=False)

    class Meta:
        constraints = [models.UniqueConstraint(fields=('quiz_attempt', 'question', 'selected_answer'), name='unique_selected_answer_per_question')]
