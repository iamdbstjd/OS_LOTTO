from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path

from lotto import views


urlpatterns = [
    path("admin/", admin.site.urls),
    path("signup/", views.SignupView.as_view(), name="signup"),
    path("login/", auth_views.LoginView.as_view(template_name="registration/login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("", include("lotto.urls")),
]
