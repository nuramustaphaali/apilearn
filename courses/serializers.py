from rest_framework import serializers
from .models import Course, Category, Lesson, Enrollment
from users.serializers import UserSerializer # To show instructor details


from .models import Quiz, Question, Answer, QuizAttempt


from rest_framework import serializers
from .models import Course, Category, Lesson, Quiz, Enrollment

class CourseSerializer(serializers.ModelSerializer):
    # We use source='...' to get data from related models
    instructor_name = serializers.ReadOnlyField(source='instructor.full_name')
    category_name = serializers.ReadOnlyField(source='category.title')
    
    class Meta:
        model = Course
        # REMOVED 'slug' from this list
        fields = ['id', 'title', 'description', 'price', 'image', 
                  'instructor_name', 'category_name', 'created_at']

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'

class LessonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lesson
        fields = '__all__'

class QuizSerializer(serializers.ModelSerializer):
    class Meta:
        model = Quiz
        fields = '__all__'

class EnrollmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Enrollment
        fields = '__all__'
class AnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Answer
        fields = ['id', 'text'] # Don't expose 'is_correct' to the frontend!

class QuestionSerializer(serializers.ModelSerializer):
    answers = AnswerSerializer(many=True, read_only=True)
    class Meta:
        model = Question
        fields = ['id', 'text', 'answers']


class QuizAttemptSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuizAttempt
        fields = ['id', 'quiz', 'score', 'passed', 'timestamp']
        read_only_fields = ['score', 'passed', 'user', 'timestamp']
