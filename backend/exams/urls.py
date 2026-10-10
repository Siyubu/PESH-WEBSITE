from django.urls import path

from . import views

urlpatterns = [
    path("attempts/<int:attempt_id>/", views.AttemptView.as_view()),
    path("attempts/<int:attempt_id>/submit/", views.SubmitView.as_view()),
    path("<slug:slug>/", views.ExamInfoView.as_view()),
    path("<slug:slug>/start/", views.StartView.as_view()),
]
