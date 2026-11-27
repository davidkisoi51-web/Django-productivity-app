from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

urlpatterns = [
    path("", views.task_list, name="task_list"),
    path("new/", views.task_create, name="task_create"),
    path("<int:task_id>/edit/", views.task_edit, name="task_edit"),
    path("<int:task_id>/toggle/", views.task_toggle, name="task_toggle"),
    path("<int:task_id>/delete/", views.task_delete, name="task_delete"),
    path("signup/", views.signup, name="signup"),
    path(
        "login/",
        auth_views.LoginView.as_view(template_name="tasks/login.html"),
        name="login",
    ),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
]