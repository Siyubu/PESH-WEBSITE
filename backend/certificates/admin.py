from django.contrib import admin

from .models import Certificate, Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("created_at", "user", "course", "status", "amount", "currency", "phone_last4")
    list_filter = ("status", "course")
    search_fields = ("user__email", "reference")
    readonly_fields = [f.name for f in Payment._meta.fields]

    def has_add_permission(self, request):
        return False


@admin.register(Certificate)
class CertificateAdmin(admin.ModelAdmin):
    list_display = ("code", "learner_name", "course", "issued_at")
    list_filter = ("course",)
    search_fields = ("code", "learner_name", "user__email")
    readonly_fields = ("user", "course", "payment", "code", "issued_at")
