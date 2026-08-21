from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import AnswerOption, Question, QuizSet


class QuizFlowTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('learner', password='safe-password-123')
        self.quiz = QuizSet.objects.create(title='Basics')
        self.first = Question.objects.create(quiz_set=self.quiz, question_text='First?', order_index=1)
        self.second = Question.objects.create(quiz_set=self.quiz, question_text='Second?', order_index=2)
        self.first_correct = AnswerOption.objects.create(question=self.first, answer_text='Yes', is_correct=True)
        AnswerOption.objects.create(question=self.first, answer_text='No', is_correct=False)
        self.second_correct = AnswerOption.objects.create(question=self.second, answer_text='True', is_correct=True)
        AnswerOption.objects.create(question=self.second, answer_text='False', is_correct=False)
        self.client.login(username='learner', password='safe-password-123')

    def test_user_cannot_skip_a_question_and_exact_match_scores_correct(self):
        response = self.client.get(reverse('start_quiz', args=[self.quiz.pk]))
        attempt = self.user.quiz_attempts.get()
        self.assertRedirects(response, reverse('quiz_question', args=[attempt.pk, 1]))
        response = self.client.get(reverse('quiz_question', args=[attempt.pk, 2]))
        self.assertRedirects(response, reverse('quiz_question', args=[attempt.pk, 1]))

        self.client.post(reverse('quiz_question', args=[attempt.pk, 1]), {'answers': [self.first_correct.pk]})
        response = self.client.post(reverse('quiz_question', args=[attempt.pk, 2]), {'answers': [self.second_correct.pk]})
        self.assertRedirects(response, reverse('quiz_results', args=[attempt.pk]))
        attempt.refresh_from_db()
        self.assertEqual(attempt.status, 'completed')
        self.assertEqual(attempt.correct_count, 2)
        self.assertEqual(attempt.incorrect_count, 0)
        self.assertEqual(attempt.score, 100)

    def test_blank_answers_are_rejected(self):
        self.client.get(reverse('start_quiz', args=[self.quiz.pk]))
        attempt = self.user.quiz_attempts.get()
        response = self.client.post(reverse('quiz_question', args=[attempt.pk, 1]), {})
        self.assertContains(response, 'Select at least one answer')
