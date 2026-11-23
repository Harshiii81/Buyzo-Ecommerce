from django.urls import path
from . import views

app_name = "userauths"

urlpatterns = [
    path("signup/", views.signup_view, name="signup"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("account/", views.account_view, name="account"),
    path("save-address/", views.save_address_view, name="save_address"),
    path("update-profile/", views.update_profile_view, name="update_profile"),
    path(
    "cancel-order/<int:order_id>/",
    views.cancel_order_view,
    name="cancel_order"
),
]