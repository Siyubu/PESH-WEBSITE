from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/", include("accounts.urls")),
    path("api/courses/", include("courses.urls")),
    path("api/exams/", include("exams.urls")),
    path("api/", include("offline_enrollment.urls")),
    path("api/", include("certificates.urls")),
]
