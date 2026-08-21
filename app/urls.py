from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

urlpatterns = [
    path('', views.quiz_catalog, name='quiz_catalog'),
    path('register/', views.register, name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('quizzes/<int:quiz_id>/start/', views.start_quiz, name='start_quiz'),
    path('attempts/<int:attempt_id>/question/<int:number>/', views.quiz_question, name='quiz_question'),
    path('attempts/<int:attempt_id>/results/', views.quiz_results, name='quiz_results'),
]
