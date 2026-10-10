from django.urls import path

from . import views

urlpatterns = [
    path("certificates/", views.MyCertificatesView.as_view()),
    path("certificates/verify/<str:code>/", views.VerifyView.as_view()),
    path("certificates/<slug:slug>/status/", views.CertificateStatusView.as_view()),
    path("certificates/<slug:slug>/pay/", views.PayView.as_view()),
    path("certificates/<slug:slug>/pdf/", views.CertificatePdfView.as_view()),
    path("momo/callback/<uuid:reference>/", views.MomoCallbackView.as_view()),
]
