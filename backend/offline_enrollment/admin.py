from django.contrib import admin
from django.utils.html import format_html

from courses.services import published_courses

from .models import OfflineCertificate, OfflineLearner, new_offline_code


@admin.register(OfflineLearner)
class OfflineLearnerAdmin(admin.ModelAdmin):
    list_display = ("full_name", "country", "date_of_birth", "age", "is_student", "grade", "school", "registered_by", "created_at", "has_certificate")
    list_filter = ("is_student", "country")
    search_fields = ("first_name", "last_name", "school")
    readonly_fields = ("client_id", "registered_by", "created_at", "synced_at", "age")
    actions = ["issue_combined_certificate"]

    def full_name(self, obj):
        return obj.full_name()

    @admin.display(boolean=True, description="Has certificate")
    def has_certificate(self, obj):
        return hasattr(obj, "certificate")

    @admin.action(description="Issue combined certificate (all courses) for selected learners")
    def issue_combined_certificate(self, request, queryset):
        titles = list(published_courses().order_by("order", "title").values_list("title", flat=True))
        if not titles:
            self.message_user(request, "There are no published courses to put on the certificate.", level="error")
            return
        created = skipped = 0
        for learner in queryset:
            if hasattr(learner, "certificate"):
                skipped += 1
                continue
            OfflineCertificate.objects.create(learner=learner, code=new_offline_code(), course_titles=titles, issued_by=request.user)
            created += 1
        msg = f"Issued {created} certificate(s)."
        if skipped:
            msg += f" {skipped} learner(s) already had one."
        self.message_user(request, msg)


@admin.register(OfflineCertificate)
class OfflineCertificateAdmin(admin.ModelAdmin):
    list_display = ("code", "learner", "issued_by", "issued_at")
    search_fields = ("code", "learner__first_name", "learner__last_name")
    readonly_fields = ("learner", "code", "course_titles", "issued_by", "issued_at", "pdf_link")
    fields = ("learner", "code", "course_titles", "issued_by", "issued_at", "pdf_link")

    def has_add_permission(self, request):
        return False

    @admin.display(description="Certificate PDF")
    def pdf_link(self, obj):
        if not obj.pk:
            return "-"
        return format_html('<a class="button" href="/api/offline-certificates/{}/pdf/" target="_blank">Download PDF</a>', obj.code)
