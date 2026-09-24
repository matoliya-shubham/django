from django.contrib import admin
# Register your models here.
from .models import Task, Project

admin.site.register(Project)

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ("title", "status", "project", "due_date", "created_at")
    list_filter = ("status", "project")
    search_fields = ("title", "description")
    # FIX for N+1: "project" in list_display makes the admin fetch each row's
    # Project one by one (1 + 100 queries for 100 rows). This JOINs it into the
    # single list query instead. Removing this line brings the N+1 back.
    list_select_related = ("project",)