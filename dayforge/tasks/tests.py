from datetime import timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Task


class DayForgeTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="forge", password="strong-pass-123")
        self.other = User.objects.create_user(username="other", password="strong-pass-456")

    def login(self):
        self.client.login(username="forge", password="strong-pass-123")

    def test_signup_creates_authenticated_user(self):
        response = self.client.post(
            reverse("signup"),
            {"username": "newforge", "password1": "strong-pass-789", "password2": "strong-pass-789"},
        )
        self.assertRedirects(response, reverse("task_list"))
        self.assertTrue(User.objects.filter(username="newforge").exists())

    def test_login_is_required_for_dashboard(self):
        response = self.client.get(reverse("task_list"))
        self.assertRedirects(response, f'{reverse("login")}?next={reverse("task_list")}')

    def test_user_only_sees_and_edits_owned_tasks(self):
        own = Task.objects.create(owner=self.user, title="My task")
        foreign = Task.objects.create(owner=self.other, title="Private task")
        self.login()

        response = self.client.get(reverse("task_list"))
        self.assertContains(response, "My task")
        self.assertNotContains(response, "Private task")
        self.assertEqual(
            self.client.post(reverse("task_edit", args=[foreign.pk]), {"title": "Changed"}).status_code,
            404,
        )
        response = self.client.post(
            reverse("task_edit", args=[own.pk]),
            {"title": "Updated", "description": "Notes", "priority": "high", "due_date": ""},
        )
        self.assertRedirects(response, reverse("task_list"))
        own.refresh_from_db()
        self.assertEqual(own.title, "Updated")

    def test_create_toggle_and_delete_task(self):
        self.login()
        response = self.client.post(
            reverse("task_create"),
            {
                "title": "Plan sprint",
                "description": "Define the next milestone",
                "priority": "high",
                "due_date": timezone.localdate().isoformat(),
            },
        )
        self.assertRedirects(response, reverse("task_list"))
        task = Task.objects.get(title="Plan sprint")
        self.assertEqual(task.owner, self.user)

        self.client.post(reverse("task_toggle", args=[task.pk]))
        task.refresh_from_db()
        self.assertTrue(task.completed)

        self.client.post(reverse("task_delete", args=[task.pk]))
        self.assertFalse(Task.objects.filter(pk=task.pk).exists())

    def test_search_status_priority_and_overdue_stats(self):
        Task.objects.create(owner=self.user, title="Write brief", priority="high")
        Task.objects.create(
            owner=self.user,
            title="Old task",
            completed=True,
            priority="low",
            due_date=timezone.localdate() - timedelta(days=2),
        )
        Task.objects.create(
            owner=self.user,
            title="Late task",
            priority="medium",
            due_date=timezone.localdate() - timedelta(days=1),
        )
        self.login()

        response = self.client.get(reverse("task_list"), {"q": "brief", "status": "active", "priority": "high"})
        self.assertContains(response, "Write brief")
        self.assertNotContains(response, "Old task")

        response = self.client.get(reverse("task_list"))
        self.assertEqual(response.context["overdue"], 1)
        self.assertEqual(response.context["completed"], 1)

    def test_post_only_actions_reject_get(self):
        task = Task.objects.create(owner=self.user, title="Protected")
        self.login()
        self.assertEqual(self.client.get(reverse("task_toggle", args=[task.pk])).status_code, 405)
        self.assertEqual(self.client.get(reverse("task_delete", args=[task.pk])).status_code, 405)
