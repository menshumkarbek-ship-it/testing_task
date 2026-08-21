from django.contrib.auth.models import User
from django.contrib import admin
from django.test import TestCase
from django.test.client import RequestFactory
from django.urls import reverse

from .admin import AnswerOptionInline
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


class QuizAdminTests(TestCase):
    def setUp(self):
        self.admin_user = User.objects.create_superuser('admin', 'admin@example.com', 'safe-password-123')
        self.quiz = QuizSet.objects.create(title='Admin quiz')
        self.question = Question.objects.create(quiz_set=self.quiz, question_text='Question?', order_index=1)

    def _answer_formset(self, correct_values):
        data = {
            'answers-TOTAL_FORMS': str(len(correct_values)),
            'answers-INITIAL_FORMS': '0',
            'answers-MIN_NUM_FORMS': '0',
            'answers-MAX_NUM_FORMS': '1000',
        }
        for index, is_correct in enumerate(correct_values):
            data[f'answers-{index}-answer_text'] = f'Option {index}'
            if is_correct:
                data[f'answers-{index}-is_correct'] = 'on'
        request = RequestFactory().post('/')
        request.user = self.admin_user
        inline = AnswerOptionInline(Question, admin.site)
        formset_class = inline.get_formset(request, self.question)
        return formset_class(data=data, instance=self.question, prefix='answers')

    def test_quiz_change_page_contains_nested_answer_option_forms(self):
        AnswerOption.objects.create(question=self.question, answer_text='Correct', is_correct=True)
        AnswerOption.objects.create(question=self.question, answer_text='Incorrect', is_correct=False)

        self.client.force_login(self.admin_user)
        response = self.client.get(reverse('admin:app_quizset_change', args=[self.quiz.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'questions-0-answers-TOTAL_FORMS')

    def test_answer_options_require_at_least_one_correct_choice(self):
        formset = self._answer_formset([False, False])
        self.assertFalse(formset.is_valid())
        self.assertIn('Mark at least one answer option as correct.', formset.non_form_errors())

    def test_answer_options_cannot_all_be_correct(self):
        formset = self._answer_formset([True, True])
        self.assertFalse(formset.is_valid())
        self.assertIn('At least one answer option must be incorrect.', formset.non_form_errors())
