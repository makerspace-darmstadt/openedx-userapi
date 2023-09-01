"""
openedx_userapi Django application initialization.
"""

from django.apps import AppConfig


class OpenedxUserapiConfig(AppConfig):
    """
    Configuration for the openedx_userapi Django application.
    """

    name = "openedx_userapi"
    plugin_app = {
        "url_config": {
            "lms.djangoapp": {
                "namespace": "openedx_userapi",
                "regex": r"^userapi/",
                "relative_path": "urls",
            },
        },
    }
