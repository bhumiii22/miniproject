from django.contrib import admin
from .models import User, Quiz, Question, Choice, QuizAttempt, Answer

admin.site.register(User)
admin.site.register(Quiz)
admin.site.register(Question)
admin.site.register(Choice)
admin.site.register(QuizAttempt)
admin.site.register(Answer)