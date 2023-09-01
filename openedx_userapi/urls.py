"""
URLs for openedx_userapi.
"""
from django.urls import re_path

from openedx_userapi import views


urlpatterns = [
    re_path(
        r"^accounts/user_without_password",
        views.CreateUserAccountWithoutPasswordView.as_view(),
        name="create_user_account_without_password_api",
    ),
    re_path(
        r"^accounts/create",
        views.CreateUserAccountView.as_view(),
        name="create_user_account_api",
    ),
    re_path(
        r"^accounts/connect",
        views.UserAccountConnect.as_view(),
        name="user_account_connect_api",
    ),
    re_path(
        r"^accounts/update_user",
        views.UpdateUserAccount.as_view(),
        name="user_account_update_user",
    ),
    re_path(
        r"^accounts/get-user/(?P<username>[\w.+-]+)",
        views.GetUserAccountView.as_view(),
        name="get_user_account_api",
    ),
]
