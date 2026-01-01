from django import forms
from .models import Quiz, Question, Answer

class QuizForm(forms.ModelForm):
    class Meta:
        model = Quiz
        fields = ['title', 'pass_score'] # Add 'description' if your model has it

class QuestionForm(forms.ModelForm):
    # We manually add fields for 4 options to make it easy for the instructor
    option_1 = forms.CharField(required=True, label="Option 1 (Correct Answer)", widget=forms.TextInput(attrs={'class': 'form-control'}))
    option_2 = forms.CharField(required=True, label="Option 2", widget=forms.TextInput(attrs={'class': 'form-control'}))
    option_3 = forms.CharField(required=True, label="Option 3", widget=forms.TextInput(attrs={'class': 'form-control'}))
    option_4 = forms.CharField(required=True, label="Option 4", widget=forms.TextInput(attrs={'class': 'form-control'}))

    # Dropdown to pick which one is actually correct
    correct_choice = forms.ChoiceField(
        choices=[('1', 'Option 1'), ('2', 'Option 2'), ('3', 'Option 3'), ('4', 'Option 4')],
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    class Meta:
        model = Question
        fields = ['text'] # Assuming 'text' is the question body field name