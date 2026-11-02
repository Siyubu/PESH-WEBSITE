from django.urls import path

from . import views

urlpatterns = [
    path("mobile/login/", views.MobileLoginView.as_view()),
    path("mobile/offline-learners/", views.OfflineLearnerSyncView.as_view()),
    path("offline-certificates/<str:code>/pdf/", views.OfflineCertificatePdfView.as_view()),
]
