from django.apps import AppConfig


class PlansSubsciConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'plans_subsci'


def ready(self):
    import plans_subsci.signals