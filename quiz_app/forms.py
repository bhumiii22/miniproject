from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.core.exceptions import ValidationError
from .models import User, Quiz, Question, Choice, Answer
import pandas as pd

class StudentRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    
    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if not email.endswith('@gst.sies.edu.in'):
            raise ValidationError('Student email must end with @gst.sies.edu.in')
        return email
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.user_type = 'student'
        if commit:
            user.save()
        return user

class TeacherRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    
    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if not email.endswith('@sies.edu.in'):
            raise ValidationError('Teacher email must end with @sies.edu.in')
        return email
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.user_type = 'teacher'
        if commit:
            user.save()
        return user

class LoginForm(AuthenticationForm):
    username = forms.CharField(label='Email / Username')

class QuizForm(forms.ModelForm):
    class Meta:
        model = Quiz
        fields = ['title', 'description', 'time_limit']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }

class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ['question_text', 'question_type', 'points']
        widgets = {
            'question_text': forms.Textarea(attrs={'rows': 2}),
        }

class ChoiceForm(forms.ModelForm):
    class Meta:
        model = Choice
        fields = ['choice_text', 'is_correct']

ChoiceFormSet = forms.inlineformset_factory(
    Question, Choice, form=ChoiceForm, extra=4, can_delete=True, min_num=2, validate_min=True
)

class ExcelUploadForm(forms.Form):
    excel_file = forms.FileField(label='Upload Excel File')
    
    def clean_excel_file(self):
        excel_file = self.cleaned_data.get('excel_file')
        if not excel_file.name.endswith(('.xlsx', '.xls')):
            raise ValidationError('File must be an Excel file (.xlsx or .xls)')
        
        try:
            # Try to read the Excel file to validate its structure
            df = pd.read_excel(excel_file)
            required_columns = ['question_text', 'question_type', 'points']
            
            for col in required_columns:
                if col not in df.columns:
                    raise ValidationError(f"Excel file must contain a '{col}' column")
                    
            # Reset file pointer for later use
            excel_file.seek(0)
            
        except Exception as e:
            raise ValidationError(f"Error reading Excel file: {str(e)}")
            
        return excel_file

class AnswerForm(forms.ModelForm):
    class Meta:
        model = Answer
        fields = ['text_answer']
        widgets = {
            'text_answer': forms.Textarea(attrs={'rows': 3}),
        }