
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .forms import SignUpForm, TaskForm
from .models import Task


@login_required
def task_list(request):
    tasks = Task.objects.filter(owner=request.user)
    search = request.GET.get("q", "").strip()
    status = request.GET.get("status", "all")
    priority = request.GET.get("priority", "all")
    sort = request.GET.get("sort", "smart")

    if search:
        tasks = tasks.filter(Q(title__icontains=search) | Q(description__icontains=search))
    if status == "active":
        tasks = tasks.filter(completed=False)
    elif status == "completed":
        tasks = tasks.filter(completed=True)
    if priority in Task.Priority.values:
        tasks = tasks.filter(priority=priority)

    if sort == "due":
        tasks = tasks.order_by("completed", "due_date", "-created_at")
    elif sort == "newest":
        tasks = tasks.order_by("-created_at")
    elif sort == "title":
        tasks = tasks.order_by("title")
    else:
        tasks = tasks.order_by("completed", "-priority", "due_date", "-created_at")

    today = timezone.localdate()
    total = Task.objects.filter(owner=request.user).count()
    completed = Task.objects.filter(owner=request.user, completed=True).count()
    overdue = Task.objects.filter(
        owner=request.user,
        completed=False,
        due_date__lt=today,
    ).count()

    context = {
        "tasks": tasks,
        "search": search,
        "status": status,
        "priority": priority,
        "sort": sort,
        "total": total,
        "completed": completed,
        "active": total - completed,
        "overdue": overdue,
        "completion_percent": round((completed / total * 100) if total else 0),
        "today": today,
        "create_form": TaskForm(),
    }
    return render(request, "tasks/task_list.html", context)


@login_required
def task_create(request):
    if request.method == "POST":
        form = TaskForm(request.POST)
        if form.is_valid():
            task = form.save(commit=False)
            task.owner = request.user
            task.save()
            messages.success(request, "Task added successfully.")
            return redirect("task_list")
        messages.error(request, "Please correct the task details.")
    else:
        form = TaskForm()
    return render(request, "tasks/task_form.html", {"form": form, "mode": "Create"})


@login_required
def task_edit(request, task_id):
    task = get_object_or_404(Task, pk=task_id, owner=request.user)
    if request.method == "POST":
        form = TaskForm(request.POST, instance=task)
        if form.is_valid():
            form.save()
            messages.success(request, "Task updated.")
            return redirect("task_list")
    else:
        form = TaskForm(instance=task)
    return render(request, "tasks/task_form.html", {"form": form, "mode": "Edit", "task": task})


@login_required
@require_POST
def task_toggle(request, task_id):
    task = get_object_or_404(Task, pk=task_id, owner=request.user)
    task.completed = not task.completed
    task.save(update_fields=("completed", "updated_at"))
    messages.success(request, "Task marked complete." if task.completed else "Task reopened.")
    return redirect("task_list")


@login_required
@require_POST
def task_delete(request, task_id):
    task = get_object_or_404(Task, pk=task_id, owner=request.user)
    task.delete()
    messages.success(request, "Task deleted.")
    return redirect("task_list")


def signup(request):
    if request.user.is_authenticated:
        return redirect("task_list")
    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Welcome to DayForge.")
            return redirect("task_list")
    else:
        form = SignUpForm()
    return render(request, "tasks/signup.html", {"form": form})