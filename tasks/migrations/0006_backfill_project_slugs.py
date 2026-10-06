from django.db import migrations
from django.utils.text import slugify


def backfill_slugs(apps, schema_editor):
    # Historical model, NOT `from tasks.models import Project`.
    Project = apps.get_model("tasks", "Project")

    seen = set()
    for project in Project.objects.all().order_by("pk"):
        base = slugify(project.name) or f"project-{project.pk}"

        slug, n = base, 2
        while slug in seen:            # two projects named the same
            slug = f"{base}-{n}"
            n += 1

        seen.add(slug)
        project.slug = slug
        project.save(update_fields=["slug"])


class Migration(migrations.Migration):

    dependencies = [
        ("tasks", "0005_project_slug"),
    ]

    operations = [
        migrations.RunPython(backfill_slugs, migrations.RunPython.noop),
    ]
