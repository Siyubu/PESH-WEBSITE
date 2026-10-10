import json
from pathlib import Path

from django.core.management.base import BaseCommand
from django.db import transaction

from courses.models import Course
from exams.models import Exam, Question

DATA_DIR = Path(__file__).resolve().parents[2] / "data"


class Command(BaseCommand):
    help = "Load exam question banks from exams/data/*.json."

    def add_arguments(self, parser):
        parser.add_argument("--only-new", action="store_true", help="Skip exams that already exist (keeps admin edits).")

    @transaction.atomic
    def handle(self, *args, only_new=False, **opts):
        for path in sorted(DATA_DIR.glob("*.json")):
            data = json.loads(path.read_text(encoding="utf-8"))
            course = Course.objects.filter(slug=data["course"]).first()
            if not course:
                self.stdout.write(f"{path.name}: course '{data['course']}' not found, skipped")
                continue
            exam, created = Exam.objects.get_or_create(course=course, defaults={"title": data.get("title", "Final exam")})
            if only_new and not created:
                self.stdout.write(f"{data['course']}: exam exists, skipped")
                continue
            for f in ("title", "pass_percent", "questions_per_attempt", "time_limit_minutes", "retake_wait_minutes"):
                if f in data:
                    setattr(exam, f, data[f])
            exam.save()
            # Update in place (matched by question text) so past attempts keep pointing at real rows.
            existing = {q.text: q for q in exam.questions.all()}
            seen = set()
            for i, q in enumerate(data["questions"]):
                seen.add(q["text"])
                if q["text"] in existing:
                    row = existing[q["text"]]
                    row.order, row.options, row.correct_index, row.active = i, q["options"], q["correct"], True
                    row.save()
                else:
                    Question.objects.create(exam=exam, order=i, text=q["text"], options=q["options"], correct_index=q["correct"])
            removed = exam.questions.exclude(text__in=seen).filter(active=True).update(active=False)
            self.stdout.write(f"{data['course']}: {len(data['questions'])} questions loaded" + (f", {removed} retired" if removed else ""))
