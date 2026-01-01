from django.shortcuts import render
from rest_framework import viewsets, permissions
from .models import Course, Category
from .serializers import CourseSerializer, CategorySerializer
from .permissions import IsCourseOwnerOrReadOnly
from users.permissions import IsInstructor
from .models import Enrollment, QuizAttempt, Answer
from .serializers import EnrollmentSerializer,QuizAttemptSerializer# (Create this in next step)
from .permissions import IsEnrolledOrInstructor
from django.db.models import Count, Q
from .models import LessonProgress
from rest_framework.decorators import action  # <--- THIS WAS MISSING

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

class CourseViewSet(viewsets.ModelViewSet):
    serializer_class = CourseSerializer
    
    def get_permissions(self):
        # Allow anyone to view lists, but only Instructors to Create
        if self.action == 'create':
            return [permissions.IsAuthenticated(), IsInstructor()]
        # For Update/Delete, check if they own it
        if self.action in ['update', 'partial_update', 'destroy']:
            return [permissions.IsAuthenticated(), IsCourseOwnerOrReadOnly()]
        return [permissions.IsAuthenticatedOrReadOnly()]

    def get_queryset(self):
        user = self.request.user
        
        # FIX: Check if user is authenticated BEFORE accessing 'role'
        if user.is_authenticated and getattr(user, 'role', '') == 'instructor':
             return Course.objects.filter(instructor=user) | Course.objects.filter(is_published=True)
        
        # Everyone else (Students + Anonymous/Docs) sees only published courses
        return Course.objects.filter(is_published=True)

    def perform_create(self, serializer):
        serializer.save(instructor=self.request.user)
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from .models import Lesson, Quiz, Course, Enrollment
from .serializers import LessonSerializer, QuizSerializer
from .permissions import IsCourseOwnerOrReadOnly, IsEnrolledOrInstructor

class LessonViewSet(viewsets.ModelViewSet):
    """
    API for managing lessons.
    - **GET (List)**: View lesson titles/ordering (Public/Auth).
    - **GET (Retrieve)**: View lesson content (Video/PDF) - **Requires Enrollment**.
    - **POST**: Create lesson (Instructor only).
    - **PATCH/DELETE**: Edit lesson (Instructor only).
    """
    serializer_class = LessonSerializer
    # Remove 'put' to enforce partial updates only (PATCH)
    http_method_names = ['get', 'post', 'patch', 'delete', 'head', 'options']

    def get_queryset(self):
        queryset = Lesson.objects.all()
        # Filter by course: /api/v1/lessons/?course_id=5
        course_id = self.request.query_params.get('course_id')
        if course_id:
            queryset = queryset.filter(course_id=course_id)
        return queryset

    def get_permissions(self):
        """
        Dynamic permissions based on action.
        """
        # 1. Destructive Actions (Create/Edit/Delete) -> Instructor Only
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAuthenticated(), IsCourseOwnerOrReadOnly()]
        
        # 2. Viewing Content (Retrieve) -> Must be Enrolled
        if self.action == 'retrieve':
            return [permissions.IsAuthenticated(), IsEnrolledOrInstructor()]
        
        # 3. Listing Titles -> Open (good for "Curriculum Preview" before buying)
        return [permissions.AllowAny()]

    def perform_create(self, serializer):
        # Ensure the course exists and user is the owner
        course_id = self.request.data.get('course')
        if course_id:
             # Basic validation (Serializer handles the rest)
             pass 
        serializer.save()

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def mark_complete(self, request, pk=None):
        lesson = self.get_object()
        # Ensure enrolled
        if not Enrollment.objects.filter(student=request.user, course=lesson.course).exists():
             return Response({"error": "Not enrolled"}, status=status.HTTP_403_FORBIDDEN)
             
        progress, _ = LessonProgress.objects.get_or_create(student=request.user, lesson=lesson)
        progress.is_completed = True
        progress.save()
        
        return Response({"status": "Lesson marked complete", "progress": True})




class QuizViewSet(viewsets.ModelViewSet):
    """
    API for managing quizzes.
    - **GET**: View Quiz Details - **Requires Enrollment**.
    - **POST/PATCH/DELETE**: Manage Quiz - **Instructor Only**.
    """
    queryset = Quiz.objects.all()
    serializer_class = QuizSerializer
    # Remove 'put'
    http_method_names = ['get', 'post', 'patch', 'delete', 'head', 'options']

    def get_permissions(self):
        # 1. Instructors can manage quizzes
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
             # Note: logic for 'IsCourseOwner' is tricky on Quiz because it links to Lesson.
             # We rely on IsAuthenticated + the serializer validation for safety here.
            return [permissions.IsAuthenticated()]

        # 2. Students need enrollment to see the quiz
        return [permissions.IsAuthenticated(), IsEnrolledOrInstructor()]



class QuizAttemptViewSet(viewsets.ModelViewSet):
    """
    POST: Submit quiz answers.
    Body: { "quiz": 1, "answers": { "question_id": "answer_id", ... } }
    """
    queryset = QuizAttempt.objects.all()
    serializer_class = QuizAttemptSerializer
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        quiz_id = request.data.get('quiz')
        user_answers = request.data.get('answers', {}) # Dict: {q_id: a_id}

        quiz = Quiz.objects.get(pk=quiz_id)
        total_questions = quiz.questions.count()
        correct_count = 0

        # Grading Logic
        for q_id, a_id in user_answers.items():
            try:
                answer = Answer.objects.get(pk=a_id, question_id=q_id)
                if answer.is_correct:
                    correct_count += 1
            except Answer.DoesNotExist:
                pass

        score = (correct_count / total_questions) * 100 if total_questions > 0 else 0
        passed = score >= quiz.pass_score

        # Save Attempt
        attempt = QuizAttempt.objects.create(
            user=request.user,
            quiz=quiz,
            score=score,
            passed=passed
        )

        return Response(QuizAttemptSerializer(attempt).data)



# 1. New ViewSet for Enrolling
class EnrollmentViewSet(viewsets.ModelViewSet):
    """
    POST: Enroll in a course.
    """
    queryset = Enrollment.objects.all()
    serializer_class = EnrollmentSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ['get', 'post', 'head', 'options'] # No PUT/DELETE for now

    def perform_create(self, serializer):
        serializer.save(student=self.request.user)



from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from .models import Course

# --- HTML VIEWS ---
from django.views.generic import ListView
from .models import Course

class CourseListView(ListView):
    model = Course
    template_name = 'home.html' # <--- Changed from 'courses/course_list.html'
    context_object_name = 'courses'
    
    def get_queryset(self):
        # Instructors see everything, Students see only published
        if self.request.user.is_authenticated and getattr(self.request.user, 'role', '') == 'instructor':
            return Course.objects.all().order_by('-created_at')
        return Course.objects.filter(is_published=True).order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # We can add extra context here if needed (e.g. Categories)
        return context
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import CreateView, UpdateView, DeleteView
from django.shortcuts import get_object_or_404, redirect

# Import your forms (we will verify these exist in a moment)
# If you don't have a forms.py yet, we will create it next.
from .models import Course, Lesson

# ===========================
# 1. COURSE MANAGEMENT VIEWS
# ===========================

class CourseCreateView(LoginRequiredMixin, CreateView):
    model = Course
    fields = ['title', 'category', 'description', 'price', 'image', 'is_published']
    template_name = 'courses/course_form.html'
    success_url = reverse_lazy('instructor-dashboard')

    def form_valid(self, form):
        # Automatically set the instructor to the current logged-in user
        form.instance.instructor = self.request.user
        return super().form_valid(form)

class CourseUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Course
    fields = ['title', 'category', 'description', 'price', 'image', 'is_published']
    template_name = 'courses/course_form.html'
    
    def get_success_url(self):
        return reverse_lazy('instructor-dashboard')

    def test_func(self):
        # Security: Only the owner can edit
        course = self.get_object()
        return self.request.user == course.instructor

class CourseDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Course
    template_name = 'courses/course_confirm_delete.html'
    success_url = reverse_lazy('instructor-dashboard')

    def test_func(self):
        # Security: Only the owner can delete
        course = self.get_object()
        return self.request.user == course.instructor


# ===========================
# 2. LESSON MANAGEMENT VIEWS
# ===========================
# In courses/views.py

class LessonCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Lesson
    # REMOVED 'is_preview' from this list
    fields = ['title', 'lesson_type', 'video_url', 'pdf_file', 'text_content', 'order'] 
    template_name = 'courses/lesson_form.html'

    def dispatch(self, request, *args, **kwargs):
        # Capture the course from the URL before the view loads
        self.course = get_object_or_404(Course, pk=self.kwargs['course_id'])
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        # Link the lesson to the specific course
        form.instance.course = self.course
        return super().form_valid(form)

    def get_success_url(self):
        # Go back to the course detail page after adding a lesson
        return reverse_lazy('course-detail', kwargs={'pk': self.course.id})

    def test_func(self):
        # Security: Only the course instructor can add lessons
        course = get_object_or_404(Course, pk=self.kwargs['course_id'])
        return self.request.user == course.instructor



from django.views.generic import DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.db.models import Count
from .models import Course, Lesson, Enrollment, LessonProgress, Certificate

class CourseDetailView(DetailView):
    model = Course
    template_name = 'courses/course_detail.html'
    context_object_name = 'course'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # 1. Handle Anonymous Users (Sales Page View)
        if not self.request.user.is_authenticated:
            context['is_enrolled'] = False
            return context

        user = self.request.user
        course = self.object

        # 2. Check Enrollment & Ownership
        is_enrolled = Enrollment.objects.filter(student=user, course=course).exists()
        is_instructor = (user == course.instructor)
        
        context['is_enrolled'] = is_enrolled
        context['is_instructor'] = is_instructor

        # 3. Learning Data (Only if Enrolled or Instructor)
        if is_enrolled or is_instructor:
            # Calculate Progress
            total_lessons = course.lessons.count()
            completed_lessons = LessonProgress.objects.filter(
                student=user, 
                lesson__course=course, 
                is_completed=True
            ).count()

            if total_lessons > 0:
                progress = (completed_lessons / total_lessons) * 100
            else:
                progress = 0
            
            context['progress'] = round(progress, 1)

            # Get Completed Lesson IDs (for checkmarks)
            context['completed_ids'] = list(LessonProgress.objects.filter(
                student=user, lesson__course=course, is_completed=True
            ).values_list('lesson_id', flat=True))

            # Find "Next Lesson" to Resume
            completed_ids_queryset = LessonProgress.objects.filter(
                student=user, lesson__course=course, is_completed=True
            ).values_list('lesson_id', flat=True)
            
            context['next_lesson'] = course.lessons.exclude(id__in=completed_ids_queryset).order_by('order').first()

            # Check for Certificate
            if progress == 100:
                context['certificate'] = Certificate.objects.filter(student=user, course=course).first()

        return context

        

from django.shortcuts import get_object_or_404, redirect
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Quiz, Answer

@login_required
def take_quiz(request, pk):
    quiz = get_object_or_404(Quiz, pk=pk)
    
    if request.method == 'POST':
        score = 0
        total_questions = quiz.questions.count()
        
        # Loop through questions to check answers
        for question in quiz.questions.all():
            # Get the selected answer ID from the form data
            selected_answer_id = request.POST.get(f'question_{question.id}')
            
            if selected_answer_id:
                answer = Answer.objects.get(id=selected_answer_id)
                if answer.is_correct:
                    score += 1
        
        # Calculate percentage
        if total_questions > 0:
            percentage = (score / total_questions) * 100
        else:
            percentage = 0
            
        passed = percentage >= quiz.pass_score

        # Render Result Page
        return render(request, 'courses/quiz_result.html', {
            'quiz': quiz,
            'score': round(percentage, 1),
            'passed': passed
        })

    # Render Quiz Form (GET request)
    return render(request, 'courses/quiz_take.html', {'quiz': quiz})


from django.contrib.auth.decorators import login_required

@login_required
def enroll_course(request, course_id):
    course = get_object_or_404(Course, pk=course_id)
    
    # Check if already enrolled
    if Enrollment.objects.filter(student=request.user, course=course).exists():
        return redirect('course-detail', pk=course.id)
    
    # Create Enrollment
    Enrollment.objects.create(student=request.user, course=course)
    
    return redirect('course-detail', pk=course.id)

@login_required
def toggle_lesson_completion(request, lesson_id):
    lesson = get_object_or_404(Lesson, pk=lesson_id)
    
    # Security: Check enrollment
    if not Enrollment.objects.filter(student=request.user, course=lesson.course).exists():
         return redirect('course-detail', pk=lesson.course.id)

    # Toggle Progress
    progress, created = LessonProgress.objects.get_or_create(student=request.user, lesson=lesson)
    progress.is_completed = not progress.is_completed # Flip True/False
    progress.save()

    return redirect('course-detail', pk=lesson.course.id)


from django.http import FileResponse, Http404
from .models import Certificate
import os
from .utils import generate_certificate_pdf

@login_required
def download_certificate(request, cert_id):
    cert = get_object_or_404(Certificate, pk=cert_id)

    # Security: Only owner (or staff) can download
    if request.user != cert.student and not request.user.is_staff:
        raise Http404("You are not authorized to view this certificate.")

    # FIX: Check if the file actually exists on the disk
    # 1. If the DB field is empty OR
    # 2. If the DB has a path, but the file is missing from the folder
    if not cert.pdf_file or not os.path.exists(cert.pdf_file.path):
        print(f"Generating missing certificate for {cert.id}...")
        pdf_path = generate_certificate_pdf(cert)
        cert.pdf_file = pdf_path
        cert.save()

    return FileResponse(open(cert.pdf_file.path, 'rb'), content_type='application/pdf')


from django.core.exceptions import ValidationError # Import this at the top if missing

def verify_certificate(request):
    """
    Public Page to verify certificates by ID
    """
    # 1. Get the ID from the URL (and strip whitespace)
    searched_id = request.GET.get('id', '').strip()
    cert = None

    if searched_id:
        try:
            # 2. Try to find the certificate
            cert = Certificate.objects.get(pk=searched_id)
        except (Certificate.DoesNotExist, ValueError, ValidationError):
            # If ID is wrong, invalid UUID format, or not found -> cert remains None
            cert = None
            
    # 3. Send 'searched_id' to the template so it knows we performed a search
    return render(request, 'courses/verify_cert.html', {'cert': cert, 'searched_id': searched_id})

    
from .forms import QuizForm, QuestionForm
from .models import Quiz, Question, Answer

# ... (keep your existing imports) ...

# 1. CREATE QUIZ VIEW
class QuizCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Quiz
    form_class = QuizForm
    template_name = 'courses/quiz_form.html'

    def dispatch(self, request, *args, **kwargs):
        self.course = get_object_or_404(Course, pk=self.kwargs['course_id'])
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.course = self.course
        return super().form_valid(form)

    def get_success_url(self):
        # After creating quiz, go to add questions
        return reverse_lazy('question-add', kwargs={'quiz_id': self.object.id})

    def test_func(self):
        course = get_object_or_404(Course, pk=self.kwargs['course_id'])
        return self.request.user == course.instructor


# 2. ADD QUESTION VIEW (The Smart One)
@login_required
def add_question(request, quiz_id):
    quiz = get_object_or_404(Quiz, pk=quiz_id)
    
    # Security: Only owner can add questions
    if request.user != quiz.course.instructor:
        return redirect('instructor-dashboard')

    if request.method == 'POST':
        form = QuestionForm(request.POST)
        if form.is_valid():
            # 1. Save the Question
            question = form.save(commit=False)
            question.quiz = quiz
            question.save()

            # 2. Save the 4 Answers
            options = [
                form.cleaned_data['option_1'],
                form.cleaned_data['option_2'],
                form.cleaned_data['option_3'],
                form.cleaned_data['option_4']
            ]
            correct_choice = form.cleaned_data['correct_choice'] # '1', '2', '3', or '4'

            for index, option_text in enumerate(options, start=1):
                Answer.objects.create(
                    question=question,
                    text=option_text,
                    is_correct=(str(index) == correct_choice)
                )

            messages.success(request, "Question added! Add another one?")
            return redirect('question-add', quiz_id=quiz.id)
    else:
        form = QuestionForm()

    return render(request, 'courses/question_form.html', {'form': form, 'quiz': quiz})