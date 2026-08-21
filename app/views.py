from decimal import Decimal

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render

from .forms import AnswerForm
from .models import QuizAttempt, QuizSet, UserAnswer


def register(request):
    if request.user.is_authenticated:
        return redirect('quiz_catalog')
    form = UserCreationForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        login(request, user)
        return redirect('quiz_catalog')
    return render(request, 'registration/register.html', {'form': form})


def quiz_catalog(request):
    return render(request, 'app/catalog.html', {'quizzes': QuizSet.objects.prefetch_related('questions')})


@login_required
def start_quiz(request, quiz_id):
    quiz = get_object_or_404(QuizSet, pk=quiz_id)
    if not quiz.questions.exists():
        messages.error(request, 'This quiz does not have any questions yet.')
        return redirect('quiz_catalog')
    attempt, _ = QuizAttempt.objects.get_or_create(user=request.user, quiz_set=quiz, status='in_progress')
    return redirect('quiz_question', attempt_id=attempt.pk, number=1)


def _attempt_for_user(request, attempt_id):
    return get_object_or_404(QuizAttempt.objects.select_related('quiz_set'), pk=attempt_id, user=request.user)


@login_required
def quiz_question(request, attempt_id, number):
    attempt = _attempt_for_user(request, attempt_id)
    if attempt.status == 'completed':
        return redirect('quiz_results', attempt_id=attempt.pk)

    questions = list(attempt.quiz_set.questions.prefetch_related('answers'))
    answered_ids = set(attempt.user_answers.values_list('question_id', flat=True))
    expected_number = next((index for index, question in enumerate(questions, 1) if question.pk not in answered_ids), None)
    if expected_number is None:
        return _complete_attempt(attempt)
    if number != expected_number:
        return redirect('quiz_question', attempt_id=attempt.pk, number=expected_number)

    question = questions[number - 1]
    # An empty POST must still bind the form so its required-field validation is shown.
    form = AnswerForm(request.POST if request.method == 'POST' else None, question=question)
    if request.method == 'POST' and form.is_valid():
        selected = set(form.cleaned_data['answers'])
        correct = set(question.answers.filter(is_correct=True))
        is_correct = selected == correct
        with transaction.atomic():
            UserAnswer.objects.filter(quiz_attempt=attempt, question=question).delete()
            UserAnswer.objects.bulk_create([
                UserAnswer(quiz_attempt=attempt, question=question, selected_answer=option, is_correct=is_correct)
                for option in selected
            ])
        if number == len(questions):
            return _complete_attempt(attempt)
        return redirect('quiz_question', attempt_id=attempt.pk, number=number + 1)
    return render(request, 'app/question.html', {
        'attempt': attempt, 'question': question, 'form': form, 'number': number, 'total': len(questions),
    })


def _complete_attempt(attempt):
    questions = list(attempt.quiz_set.questions.all())
    answered_correct = set(UserAnswer.objects.filter(quiz_attempt=attempt, is_correct=True).values_list('question_id', flat=True))
    correct_count = len(answered_correct)
    total = len(questions)
    attempt.correct_count = correct_count
    attempt.incorrect_count = total - correct_count
    attempt.score = (Decimal(correct_count) * Decimal('100') / total) if total else Decimal('0')
    attempt.status = 'completed'
    attempt.save(update_fields=('correct_count', 'incorrect_count', 'score', 'status'))
    return redirect('quiz_results', attempt_id=attempt.pk)


@login_required
def quiz_results(request, attempt_id):
    attempt = _attempt_for_user(request, attempt_id)
    if attempt.status != 'completed':
        return redirect('quiz_question', attempt_id=attempt.pk, number=1)
    return render(request, 'app/results.html', {'attempt': attempt})
