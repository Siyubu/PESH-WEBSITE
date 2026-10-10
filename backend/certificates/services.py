import logging

from django.conf import settings
from django.db import transaction

from courses.services import is_course_complete
from exams.services import has_passed

from . import momo
from .models import Certificate, Payment, new_code

log = logging.getLogger(__name__)


def sync_payment(payment):
    """Ask MoMo for the payment's real status and update our records.

    The browser and the MoMo callback body are never trusted; only MoMo's own answer is.
    """
    if payment.status != Payment.PENDING:
        return payment
    try:
        tx = momo.get_status(payment.reference)
    except momo.MomoError as e:
        log.warning("MoMo status check failed for %s: %s", payment.reference, e)
        return payment

    state = tx.get("status")
    if state == "SUCCESSFUL":
        if str(tx.get("amount")) != str(payment.amount):
            log.error("Amount mismatch for %s: MoMo=%s ours=%s", payment.reference, tx.get("amount"), payment.amount)
            return payment
        with transaction.atomic():
            locked = Payment.objects.select_for_update().select_related("user", "course").get(pk=payment.pk)
            if locked.status == Payment.PENDING:
                locked.status = Payment.SUCCESSFUL
                locked.save(update_fields=["status", "updated_at"])
                Certificate.objects.get_or_create(
                    user=locked.user,
                    course=locked.course,
                    defaults={"payment": locked, "code": new_code(locked.course), "learner_name": locked.user.full_name},
                )
            payment = locked
    elif state == "FAILED":
        payment.status = Payment.FAILED
        payment.failure_reason = str(tx.get("reason", ""))[:100]
        payment.save(update_fields=["status", "failure_reason", "updated_at"])
    return payment


def start_payment(user, course, phone):
    """Create a pending payment and send the MoMo request. Raises MomoError on gateway failure."""
    payment = Payment.objects.create(
        user=user,
        course=course,
        amount=settings.CERTIFICATE_PRICE,
        currency=settings.MOMO["CURRENCY"],
        phone_last4=phone[-4:],
    )
    callback = None
    if settings.MOMO["USE_CALLBACK"]:
        callback = f"{settings.SITE_URL}/api/momo/callback/{payment.reference}/"
    try:
        momo.request_to_pay(
            reference=payment.reference,
            amount=payment.amount,
            currency=payment.currency,
            external_id=f"{user.pk}-{course.slug}",
            phone=phone,
            payer_message=f"PESH certificate: {course.title}"[:160],
            payee_note=f"Certificate {course.slug}",
            callback_url=callback,
        )
    except momo.MomoError:
        payment.status = Payment.FAILED
        payment.failure_reason = "gateway error"
        payment.save(update_fields=["status", "failure_reason", "updated_at"])
        raise
    return payment


def eligibility(user, course):
    """A certificate needs every lesson done AND the final exam passed."""
    return is_course_complete(user, course) and has_passed(user, course)
