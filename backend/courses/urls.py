from django.urls import path

from . import views

urlpatterns = [
    path("", views.CourseListView.as_view()),
    path("<slug:slug>/", views.CourseDetailView.as_view()),
    path("<slug:slug>/lessons/<str:key>/", views.LessonDetailView.as_view()),
    path("<slug:slug>/lessons/<str:key>/complete/", views.LessonCompleteView.as_view()),
]
