# courses/admin.py
from django.contrib import admin
from .models import Course, Category

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('title', 'slug', 'created_at')
    prepopulated_fields = {'slug': ('title',)}

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('title', 'instructor', 'price', 'is_published', 'created_at')
    list_filter = ('is_published', 'category')
    search_fields = ('title', 'description', 'instructor__username')
from .models import Course, Category, Lesson, Quiz, Question, Answer, QuizAttempt

class AnswerInline(admin.TabularInline):
    model = Answer

class QuestionInline(admin.TabularInline):
    model = Question
    show_change_link = True # Allows clicking to edit answers

class QuizInline(admin.StackedInline):
    model = Quiz

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    inlines = [AnswerInline] # Edit answers inside the question page

@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'order')
    inlines = [QuizInline] # Add a quiz directly inside a lesson

admin.site.register(QuizAttempt)
admin.site.register(Quiz)