import json
from pathlib import Path

from django.core.management.base import BaseCommand
from django.db import transaction

from courses.models import Course, Lesson

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
ORDER = ["word", "excel", "internet", "scratch"]


class Command(BaseCommand):
    help = "Load course content from courses/data/*.json (generated from the PESH Word curricula)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--only-new",
            action="store_true",
            help="Only create courses/lessons that do not exist yet; never overwrite content edited in the admin.",
        )

    @transaction.atomic
    def handle(self, *args, only_new=False, **opts):
        for path in sorted(DATA_DIR.glob("*.json")):
            data = json.loads(path.read_text(encoding="utf-8"))
            slug = data["id"]
            order = ORDER.index(slug) if slug in ORDER else len(ORDER)
            course_fields = dict(
                title=data["title"], icon=data.get("icon", ""), level=data.get("level", "Beginner"),
                description=data.get("description", ""), order=order,
            )
            if only_new:
                course, created = Course.objects.get_or_create(slug=slug, defaults=course_fields)
            else:
                course, created = Course.objects.update_or_create(slug=slug, defaults=course_fields)
            made = 0
            for i, l in enumerate(data["lessons"]):
                fields = dict(
                    order=i, title=l["title"], summary=l.get("summary", ""), goals=l.get("goals", []), blocks=l["blocks"]
                )
                if only_new:
                    _, was_new = Lesson.objects.get_or_create(course=course, key=l["id"], defaults=fields)
                else:
                    _, was_new = Lesson.objects.update_or_create(course=course, key=l["id"], defaults=fields)
                made += was_new
            self.stdout.write(f"{slug}: {'created' if created else 'exists'}, {made} new lessons, {len(data['lessons'])} total")
