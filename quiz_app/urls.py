from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', views.home, name='home'),
    path('student/register/', views.student_register, name='student_register'),
    path('teacher/register/', views.teacher_register, name='teacher_register'),
    path('login/', views.user_login, name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # Teacher URLs
    path('quiz/create/', views.create_quiz, name='create_quiz'),
    path('quiz/<int:quiz_id>/edit/', views.edit_quiz, name='edit_quiz'),
    path('quiz/<int:quiz_id>/question/add/', views.add_question, name='add_question'),
    path('question/<int:question_id>/edit/', views.edit_question, name='edit_question'),
    path('question/<int:question_id>/delete/', views.delete_question, name='delete_question'),
    path('quiz/upload/', views.upload_quiz, name='upload_quiz'),
    path('quiz/<int:quiz_id>/attempts/', views.view_quiz_attempts, name='view_quiz_attempts'),
    
    # Student URLs
    path('quiz/<int:quiz_id>/take/', views.take_quiz, name='take_quiz'),
    path('attempt/<int:attempt_id>/question/<int:question_id>/', views.answer_question, name='answer_question'),
    path('attempt/<int:attempt_id>/submit/', views.submit_quiz, name='submit_quiz'),
    path('attempt/<int:attempt_id>/results/', views.quiz_results, name='quiz_results'),
]