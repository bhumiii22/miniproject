from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.contrib import messages
from django.http import HttpResponseForbidden
from django.db.models import Count, Avg, Q
from django.core.paginator import Paginator
from .forms import (
    StudentRegistrationForm, TeacherRegistrationForm, LoginForm,
    QuizForm, QuestionForm, ChoiceFormSet, ExcelUploadForm, AnswerForm
)
from .models import User, Quiz, Question, Choice, QuizAttempt, Answer
import pandas as pd
import json
from datetime import timedelta

def home(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'quiz_app/home.html')

def student_register(request):
    if request.method == 'POST':
        form = StudentRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('dashboard')
    else:
        form = StudentRegistrationForm()
    return render(request, 'quiz_app/register.html', {'form': form, 'user_type': 'Student'})

def teacher_register(request):
    if request.method == 'POST':
        form = TeacherRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('dashboard')
    else:
        form = TeacherRegistrationForm()
    return render(request, 'quiz_app/register.html', {'form': form, 'user_type': 'Teacher'})

def user_login(request):
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('dashboard')
    else:
        form = LoginForm()
    return render(request, 'quiz_app/login.html', {'form': form})

@login_required
def dashboard(request):
    user = request.user
    
    if user.user_type == 'student':
        # Get available quizzes (that the student hasn't completed)
        completed_quiz_ids = QuizAttempt.objects.filter(
            student=user, completed=True
        ).values_list('quiz_id', flat=True)
        
        available_quizzes = Quiz.objects.exclude(id__in=completed_quiz_ids)
        
        # Get completed quizzes with scores
        completed_attempts = QuizAttempt.objects.filter(
            student=user, completed=True
        ).select_related('quiz')
        
        context = {
            'available_quizzes': available_quizzes,
            'completed_attempts': completed_attempts,
        }
        return render(request, 'quiz_app/student_dashboard.html', context)
    
    elif user.user_type == 'teacher':
        # Get quizzes created by this teacher
        quizzes = Quiz.objects.filter(teacher=user)
        
        # Get statistics for each quiz
        quiz_stats = []
        for quiz in quizzes:
            stats = {
                'quiz': quiz,
                'attempt_count': QuizAttempt.objects.filter(quiz=quiz, completed=True).count(),
                'avg_score': QuizAttempt.objects.filter(quiz=quiz, completed=True).aggregate(Avg('score'))['score__avg'] or 0,
            }
            quiz_stats.append(stats)
        
        context = {
            'quiz_stats': quiz_stats,
        }
        return render(request, 'quiz_app/teacher_dashboard.html', context)
    
    return HttpResponseForbidden("Invalid user type")

@login_required
def create_quiz(request):
    if request.user.user_type != 'teacher':
        return HttpResponseForbidden("Only teachers can create quizzes")
    
    if request.method == 'POST':
        form = QuizForm(request.POST)
        if form.is_valid():
            quiz = form.save(commit=False)
            quiz.teacher = request.user
            quiz.save()
            return redirect('edit_quiz', quiz_id=quiz.id)
    else:
        form = QuizForm()
    
    return render(request, 'quiz_app/create_quiz.html', {'form': form})

@login_required
def edit_quiz(request, quiz_id):
    if request.user.user_type != 'teacher':
        return HttpResponseForbidden("Only teachers can edit quizzes")
    
    quiz = get_object_or_404(Quiz, id=quiz_id, teacher=request.user)
    questions = Question.objects.filter(quiz=quiz)
    
    return render(request, 'quiz_app/edit_quiz.html', {
        'quiz': quiz,
        'questions': questions,
    })

@login_required
def add_question(request, quiz_id):
    if request.user.user_type != 'teacher':
        return HttpResponseForbidden("Only teachers can add questions")
    
    quiz = get_object_or_404(Quiz, id=quiz_id, teacher=request.user)
    
    if request.method == 'POST':
        question_form = QuestionForm(request.POST)
        
        if question_form.is_valid():
            question = question_form.save(commit=False)
            question.quiz = quiz
            question.save()
            
            choice_formset = ChoiceFormSet(request.POST, instance=question)
            if question.question_type != 'short_answer' and choice_formset.is_valid():
                choice_formset.save()
            
            return redirect('edit_quiz', quiz_id=quiz.id)
    else:
        question_form = QuestionForm()
        choice_formset = ChoiceFormSet()
    
    return render(request, 'quiz_app/add_question.html', {
        'quiz': quiz,
        'question_form': question_form,
        'choice_formset': choice_formset,
    })

@login_required
def edit_question(request, question_id):
    if request.user.user_type != 'teacher':
        return HttpResponseForbidden("Only teachers can edit questions")
    
    question = get_object_or_404(Question, id=question_id, quiz__teacher=request.user)
    
    if request.method == 'POST':
        question_form = QuestionForm(request.POST, instance=question)
        
        if question_form.is_valid():
            question = question_form.save()
            
            if question.question_type != 'short_answer':
                choice_formset = ChoiceFormSet(request.POST, instance=question)
                if choice_formset.is_valid():
                    choice_formset.save()
            
            return redirect('edit_quiz', quiz_id=question.quiz.id)
    else:
        question_form = QuestionForm(instance=question)
        choice_formset = ChoiceFormSet(instance=question)
    
    return render(request, 'quiz_app/edit_question.html', {
        'question': question,
        'question_form': question_form,
        'choice_formset': choice_formset,
    })

@login_required
def delete_question(request, question_id):
    if request.user.user_type != 'teacher':
        return HttpResponseForbidden("Only teachers can delete questions")
    
    question = get_object_or_404(Question, id=question_id, quiz__teacher=request.user)
    quiz_id = question.quiz.id
    question.delete()
    
    return redirect('edit_quiz', quiz_id=quiz_id)

@login_required
def upload_quiz(request):
    if request.user.user_type != 'teacher':
        return HttpResponseForbidden("Only teachers can upload quizzes")
    
    if request.method == 'POST':
        form = ExcelUploadForm(request.POST, request.FILES)
        if form.is_valid():
            excel_file = request.FILES['excel_file']
            
            # Create a new quiz
            quiz_title = excel_file.name.split('.')[0]
            quiz = Quiz.objects.create(
                title=quiz_title,
                teacher=request.user,
                time_limit=30  # Default time limit
            )
            
            # Process the Excel file
            df = pd.read_excel(excel_file)
            
            for _, row in df.iterrows():
                # Create question
                question = Question.objects.create(
                    quiz=quiz,
                    question_text=row['question_text'],
                    question_type=row['question_type'],
                    points=row['points']
                )
                
                # Create choices if applicable
                if question.question_type != 'short_answer':
                    # Check if choices are in the Excel file
                    choices_data = []
                    for i in range(1, 5):
                        choice_key = f'choice_{i}'
                        is_correct_key = f'is_correct_{i}'
                        
                        if choice_key in row and pd.notna(row[choice_key]):
                            is_correct = row.get(is_correct_key, False)
                            if pd.isna(is_correct):
                                is_correct = False
                                
                            choices_data.append({
                                'text': row[choice_key],
                                'is_correct': bool(is_correct)
                            })
                    
                    # Create choices
                    for choice_data in choices_data:
                        Choice.objects.create(
                            question=question,
                            choice_text=choice_data['text'],
                            is_correct=choice_data['is_correct']
                        )
            
            messages.success(request, f"Quiz '{quiz.title}' created successfully with {df.shape[0]} questions.")
            return redirect('edit_quiz', quiz_id=quiz.id)
    else:
        form = ExcelUploadForm()
    
    return render(request, 'quiz_app/upload_quiz.html', {'form': form})

@login_required
def take_quiz(request, quiz_id):
    if request.user.user_type != 'student':
        return HttpResponseForbidden("Only students can take quizzes")
    
    quiz = get_object_or_404(Quiz, id=quiz_id)
    
    # Check if student has already completed this quiz
    if QuizAttempt.objects.filter(student=request.user, quiz=quiz, completed=True).exists():
        messages.warning(request, "You have already completed this quiz.")
        return redirect('dashboard')
    
    # Check if there's an existing incomplete attempt
    attempt = QuizAttempt.objects.filter(
        student=request.user, quiz=quiz, completed=False
    ).first()
    
    if not attempt:
        # Create a new attempt
        attempt = QuizAttempt.objects.create(
            student=request.user,
            quiz=quiz
        )
    
    # Calculate time remaining
    time_limit_seconds = quiz.time_limit * 60
    elapsed_seconds = (timezone.now() - attempt.start_time).total_seconds()
    time_remaining = max(0, time_limit_seconds - elapsed_seconds)
    
    # If time is up, auto-submit
    if time_remaining <= 0:
        return redirect('submit_quiz', attempt_id=attempt.id)
    
    # Get all questions for this quiz
    questions = Question.objects.filter(quiz=quiz)
    
    # Get existing answers for this attempt
    answers = Answer.objects.filter(attempt=attempt)
    answered_question_ids = answers.values_list('question_id', flat=True)
    
    context = {
        'quiz': quiz,
        'attempt': attempt,
        'questions': questions,
        'answers': {answer.question_id: answer for answer in answers},
        'answered_question_ids': answered_question_ids,
        'time_remaining': time_remaining,
    }
    
    return render(request, 'quiz_app/take_quiz.html', context)

@login_required
def answer_question(request, attempt_id, question_id):
    if request.user.user_type != 'student':
        return HttpResponseForbidden("Only students can answer questions")
    
    attempt = get_object_or_404(QuizAttempt, id=attempt_id, student=request.user, completed=False)
    question = get_object_or_404(Question, id=question_id, quiz=attempt.quiz)
    
    # Check if time is up
    time_limit_seconds = attempt.quiz.time_limit * 60
    elapsed_seconds = (timezone.now() - attempt.start_time).total_seconds()
    if elapsed_seconds > time_limit_seconds:
        return redirect('submit_quiz', attempt_id=attempt.id)
    
    # Get or create answer
    answer, created = Answer.objects.get_or_create(
        attempt=attempt,
        question=question,
        defaults={'is_correct': False}
    )
    
    if request.method == 'POST':
        if question.question_type == 'short_answer':
            form = AnswerForm(request.POST, instance=answer)
            if form.is_valid():
                form.save()
        else:
            choice_id = request.POST.get('choice')
            if choice_id:
                choice = get_object_or_404(Choice, id=choice_id, question=question)
                answer.selected_choice = choice
                answer.is_correct = choice.is_correct
                answer.save()
        
        # Redirect to the next unanswered question or back to the quiz
        next_question = Question.objects.filter(
            quiz=attempt.quiz
        ).exclude(
            id__in=Answer.objects.filter(attempt=attempt).values_list('question_id', flat=True)
        ).first()
        
        if next_question:
            return redirect('answer_question', attempt_id=attempt.id, question_id=next_question.id)
        else:
            return redirect('take_quiz', quiz_id=attempt.quiz.id)
    
    if question.question_type == 'short_answer':
        form = AnswerForm(instance=answer)
    else:
        form = None
    
    context = {
        'attempt': attempt,
        'question': question,
        'answer': answer,
        'form': form,
    }
    
    return render(request, 'quiz_app/answer_question.html', context)

@login_required
def submit_quiz(request, attempt_id):
    if request.user.user_type != 'student':
        return HttpResponseForbidden("Only students can submit quizzes")
    
    attempt = get_object_or_404(QuizAttempt, id=attempt_id, student=request.user)
    
    if not attempt.completed:
        # Calculate score
        total_points = sum(question.points for question in Question.objects.filter(quiz=attempt.quiz))
        earned_points = sum(
            answer.question.points for answer in Answer.objects.filter(attempt=attempt, is_correct=True)
        )
        
        if total_points > 0:
            score_percentage = (earned_points / total_points) * 100
        else:
            score_percentage = 0
        
        # Update attempt
        attempt.end_time = timezone.now()
        attempt.score = score_percentage
        attempt.completed = True
        attempt.save()
    
    return redirect('quiz_results', attempt_id=attempt.id)

@login_required
def quiz_results(request, attempt_id):
    attempt = get_object_or_404(QuizAttempt, id=attempt_id, completed=True)
    
    # Check if the user is the student who took the quiz or the teacher who created it
    if request.user != attempt.student and request.user != attempt.quiz.teacher:
        return HttpResponseForbidden("You don't have permission to view these results")
    
    answers = Answer.objects.filter(attempt=attempt).select_related('question', 'selected_choice')
    
    context = {
        'attempt': attempt,
        'answers': answers,
        'quiz': attempt.quiz,
    }
    
    return render(request, 'quiz_app/quiz_results.html', context)

@login_required
def view_quiz_attempts(request, quiz_id):
    if request.user.user_type != 'teacher':
        return HttpResponseForbidden("Only teachers can view quiz attempts")
    
    quiz = get_object_or_404(Quiz, id=quiz_id, teacher=request.user)
    attempts = QuizAttempt.objects.filter(quiz=quiz, completed=True).select_related('student')
    
    context = {
        'quiz': quiz,
        'attempts': attempts,
    }
    
    return render(request, 'quiz_app/view_quiz_attempts.html', context)