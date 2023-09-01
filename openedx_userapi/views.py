import logging
import string
import random

from dateutil import parser

from django.core.exceptions import NON_FIELD_ERRORS, ValidationError
from django.contrib.auth.models import User
from django.db.models import Q
from django.core.validators import validate_email

from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response

from openedx.core.djangoapps.user_api.accounts.api import (
    get_username_existence_validation_error,
    get_email_existence_validation_error
)
from openedx.core.lib.api.authentication import (
    OAuth2AuthenticationAllowInactiveUser,
)
from openedx.core.lib.api.permissions import (
    IsStaffOrOwner,
)

from openedx.core.djangoapps.user_authn.views.registration_form import (
    get_registration_extension_form
)
from openedx.core.djangoapps.user_authn.views.register import create_account_with_params
from common.djangoapps.student.models import UserProfile

from .utils import auto_generate_username, send_activation_email

log = logging.getLogger(__name__)


def _check_account_exists(email, username):
    return get_email_existence_validation_error(email) or get_username_existence_validation_error(username)


class CreateUserAccountView(APIView):
    authentication_classes = (OAuth2AuthenticationAllowInactiveUser,)
    permission_classes = (IsStaffOrOwner,)

    def post(self, request):
        """
        Creates a new user account
        URL: /api/ps_user_api/v1/accounts/create
        Arguments:
            request (HttpRequest)
            JSON (application/json)
            {
                "username": "staff4",
                "password": "edx",
                "email": "staff4@example.com",
                "name": "stafftest"
            }
        Returns:
            HttpResponse: 200 on success, {"user_id ": 9, "success": true }
            HttpResponse: 400 if the request is not valid.
            HttpResponse: 409 if an account with the given username or email
                address already exists
        """
        data = request.data

        # set the honor_code and honor_code like checked,
        # so we can use the already defined methods for creating an user
        data["honor_code"] = "True"
        data["terms_of_service"] = "True"

        if "send_activation_email" in data and data["send_activation_email"] == "False":
            data["send_activation_email"] = False
        else:
            data["send_activation_email"] = True

        email = request.data.get("email")
        username = request.data.get("username")

        # Handle duplicate email/username
        conflicts = _check_account_exists(email=email, username=username)
        if conflicts:
            errors = {"user_message": "User already exists"}
            return Response(errors, status=409)

        try:
            user = create_account_with_params(request, data)
            # set the user as active
            user.is_active = True
            user.save()
            user_id = user.id
        except ValidationError as err:
            # Should only get non-field errors from this function
            assert NON_FIELD_ERRORS not in err.message_dict
            # Only return first error for each field
            errors = {"user_message": "Wrong parameters on user creation"}
            return Response(errors, status=400)

        response = Response({"user_id ": user_id}, status=200)
        return response


class CreateUserAccountWithoutPasswordView(APIView):
    authentication_classes = (OAuth2AuthenticationAllowInactiveUser,)
    permission_classes = (IsStaffOrOwner,)

    def post(self, request):
        """ """
        data = request.data

        # set the honor_code and honor_code like checked,
        # so we can use the already defined methods for creating an user
        data["honor_code"] = "True"
        data["terms_of_service"] = "True"

        email = request.data.get("email")

        # Handle duplicate email/username
        conflicts = _check_account_exists(email=email)
        if conflicts:
            errors = {"user_message": "User already exists"}
            return Response(errors, status=409)

        try:
            username = auto_generate_username(email)
            password = "".join(
                random.choice(
                    string.ascii_uppercase + string.ascii_lowercase + string.digits
                )
                for _ in range(32)
            )

            data["username"] = username
            data["password"] = password
            data["send_activation_email"] = False

            user = create_account_with_params(request, data)
            # set the user as inactive
            user.is_active = False
            user.save()
            user_id = user.id
            send_activation_email(request)
        except ValidationError as err:
            # Should only get non-field errors from this function
            assert NON_FIELD_ERRORS not in err.message_dict
            # Only return first error for each field
            errors = {"user_message": "Wrong parameters on user creation"}
            return Response(errors, status=400)
        except ValueError as err:
            errors = {"user_message": "Wrong email format"}
            return Response(errors, status=400)

        response = Response({"user_id": user_id, "username": username}, status=200)
        return response


class UserAccountConnect(APIView):
    authentication_classes = (OAuth2AuthenticationAllowInactiveUser,)
    permission_classes = (IsStaffOrOwner,)

    def post(self, request):
        """
        Connects an existing Open edX user account to one in an external system
        changing the user password, email or full name.

        URL: /appsembler_api/v0/accounts/connect
        Arguments:
            request (HttpRequest)
            JSON (application/json)
            {
                "username": "staff4@example.com", # mandatory, the lookup param
                "password": "edx",
                "email": staff@example.com,
                "name": "Staff edX"
            }
        Returns:
            HttpResponse: 200 on success, {"user_id ": 60}
            HttpResponse: 404 if the doesn't exists
            HttpResponse: 400 Incorrect parameters, basically if the password
                          is empty.
        """
        data = request.data

        username = data.get("username", "")
        new_email = data.get("email", "")
        new_password = data.get("password", "")
        new_name = data.get("name", "")

        try:
            user = User.objects.get(username=username)

            if new_password.strip() != "":
                user.set_password(new_password)

            if new_email.strip() != "" and new_email != user.email:
                try:
                    validate_email(new_email)

                    if _check_account_exists(email=new_email):
                        errors = {
                            "user_message": "The email %s is in use by another user"
                            % (new_email)
                        }
                        return Response(errors, status=409)

                    user.email = new_email
                except ValidationError:
                    errors = {"user_message": "Invalid email format"}
                    return Response(errors, status=409)

            if new_name.strip() != "":
                user.profile.name = new_name
                user.profile.save()

            user.save()

        except User.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        except ValidationError:
            errors = {"user_message": "Wrong parameters on user connection"}
            return Response(errors, status=400)

        response = Response({"user_id": user.id}, status=200)
        return response


class UpdateUserAccount(APIView):
    """HTTP endpoint for updating and user account"""

    authentication_classes = (OAuth2AuthenticationAllowInactiveUser,)
    permission_classes = (IsStaffOrOwner,)

    def post(self, request):
        """
        This endpoint allows to change user attributes including email, profile
        attributes and extended profile fields. Receives one mandatory param
        user_lookup that can be an email or username to lookup the user to
        update and the rest of parameters are option. Any attribute to update
        must be sent in key:val JSON format.

        URL: /appsembler_api/v0/accounts/update_user
        Arguments:
            request (HttpRequest)
            JSON (application/json)
            {
                "user_lookup": email or username to lookup the user to update,
                # mandatory ex: "staff4@example.com" or "staff4"

                "email": "staff@example.com",
                "bio": "this is my bio",
                "country": "BR"
            }
        Returns:
            HttpResponse: 200 on success, {"success ": "list of updated params"}
            HttpResponse: 404 if the doesn't exists
            HttpResponse: 400 Incorrect parameters, basically if username or
            email parameter is not sent
        """
        data = request.data

        if data["user_lookup"].strip() == "":
            errors = {"lookup_error": "No user lookup has been provided"}
            return Response(errors, status=400)

        user = User.objects.filter(
            Q(username=data["user_lookup"]) | Q(email=data["user_lookup"])
        )

        if user:
            user = user[0]
        else:
            errors = {
                "user_not_found": "The user for the Given username or email doesn't exists"
            }
            return Response(errors, status=404)

        updated_fields = {}

        # update email
        if "email" in data and data["email"] != user.email:
            user_exists = _check_account_exists(email=data["email"])
            if user_exists:
                errors = {
                    "integrity_error": "the user email you're trying to set already belongs to another user"
                }
                return Response(errors, status=400)

            user.email = data["email"]
            user.save()
            updated_fields.update({"email": data["email"]})

        # update profile fields
        profile_fields = [
            "name",
            "level_of_education",
            "gender",
            "mailing_address",
            "city",
            "country",
            "goals",
            "bio",
            "year_of_birth",
            "language",
        ]

        profile_fields_to_update = {}
        for field in profile_fields:
            if field in data:
                profile_fields_to_update[field] = data[field]

        if len(profile_fields_to_update):
            UserProfile.objects.filter(user=user).update(**profile_fields_to_update)
            updated_fields.update(profile_fields_to_update)

        # If there is an exension form fields installed update them too
        custom_profile_fields_to_update = {}
        custom_form = get_registration_extension_form()

        if custom_form is not None:
            for custom_field in custom_form.fields:
                if custom_field in data:
                    custom_profile_fields_to_update[custom_field] = data[custom_field]
                    updated_fields.update(custom_profile_fields_to_update)

            if len(custom_profile_fields_to_update):
                custom_form.Meta.model.objects.filter(user=user).update(
                    **custom_profile_fields_to_update
                )

        return Response(
            {
                "success": "The following fields has been updated: {}".format(
                    ", ".join("{}={}".format(f, v) for f, v in updated_fields.items())
                )
            },
            status=200,
        )


class GetUserAccountView(APIView):
    authentication_classes = (OAuth2AuthenticationAllowInactiveUser,)
    permission_classes = (IsStaffOrOwner,)

    def get(self, request, username):
        """
        check if a user exists based in the username

        URL: /api/ps_user_api/v1/accounts/{username}
        Args:
            username: the username you are looking for

        Returns:
            200 OK and the user id
            404 NOT_FOUND if the user doesn't exists

        """
        try:
            account_settings = User.objects.select_related("profile").get(
                username=username
            )
        except User.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        return Response({"user_id": account_settings.username}, status=200)


class GetBatchUserDataView(APIView):
    authentication_classes = (OAuth2AuthenticationAllowInactiveUser,)
    permission_classes = (IsStaffOrOwner,)

    def get(self, request):
        """
        /appsembler_api/v0/analytics/accounts/batch[?time-parameter]

        time-parameter is an optional query parameter of:
            ?updated_min=yyyy-mm-ddThh:mm:ss
            ?updated_max=yyyy-mm-ddThh:mm:ss
            ?updated_min=yyyy-mm-ddThh:mm:ss&updated_max=yyyy-mm-ddThh:mm:ss

        """
        updated_min = request.GET.get("updated_min", "")
        updated_max = request.GET.get("updated_max", "")

        users = User.objects.all()
        if updated_min:
            min_date = parser.parse(updated_min)
            users = users.filter(date_joined__gt=min_date)

        if updated_max:
            max_date = parser.parse(updated_max)
            users = users.filter(date_joined__lt=max_date)

        user_list = []
        for user in users:
            user_data = {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "is_active": user.is_active,
                "date_joined": user.date_joined,
            }
            user_list.append(user_data)

        return Response(user_list, status=200)
