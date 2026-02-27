
from django.urls import path
# from tenants.views.tenants_views import *
from accounts.views import RegisterView, LoginView, LogoutView , ProfessionalProfileView , AdminProfessionalDetailView


urlpatterns = [

    path("register/", RegisterView.as_view(), name="register"),
    path("login/", LoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
# ------------------------------------------------------------------------
# -   # Additional account-related endpoints can be added here
# ------------------------------------------------------------------------
    path("professional/me/", ProfessionalProfileView.as_view(), name="profile"),
    path(
    "admin/professionals/<int:user_id>/",
    AdminProfessionalDetailView.as_view(),
),
    
]