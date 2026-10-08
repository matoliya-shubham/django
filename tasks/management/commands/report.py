from django.core.management.base import BaseCommand
from django.db.models import Count
from django.utils import timezone
from django.db import connection
from django.test.utils import CaptureQueriesContext
from tasks.models import Task


class Command(BaseCommand):
    help = "Print a summary report of tasks."

    def handle(self, *args, **options):
        with CaptureQueriesContext(connection) as ctx:
            self.stdout.write(self.style.SUCCESS("Tasks by status"))

            by_status = (
                Task.objects
                .values("status")              # GROUP BY status
                .annotate(count=Count("id"))   # COUNT(*) per group
                .order_by("status")
            )
            for row in by_status:
                self.stdout.write(f"  {row['status']:<12} {row['count']}")

            today = timezone.now().date()
            overdue = Task.objects.filter(due_date__lt=today).exclude(status="done")

            self.stdout.write(self.style.SUCCESS(f"\nOverdue ({overdue.count()})"))
            for task in overdue:
                self.stdout.write(f"  {task.due_date}  {task.title}")

            recent_tasks = Task.objects.select_related("project").order_by("-updated_at")[:5]
            self.stdout.write(self.style.SUCCESS(f"\n Recent tasks ({recent_tasks.count()})"))
            for task in recent_tasks:
                self.stdout.write(f"  {task.updated_at}  {task.title}  [{task.project}]")
                self.stdout.write(f"  {task.updated_at}  {task.title}")
            self.stdout.write(f"\n{len(ctx)} queries")