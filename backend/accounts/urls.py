from django.urls import path

from . import views

urlpatterns = [
    path("session/", views.SessionView.as_view()),
    path("register/", views.RegisterView.as_view()),
    path("login/", views.LoginView.as_view()),
    path("logout/", views.LogoutView.as_view()),
    path("password-reset/", views.PasswordResetView.as_view()),
    path("password-reset/confirm/", views.PasswordResetConfirmView.as_view()),
]
