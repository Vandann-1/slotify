from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import PlanListViewSet, SubscriptionListViewSet


router = DefaultRouter()

router.register("plans", PlanListViewSet, basename="plans")

router.register("subscription", SubscriptionListViewSet, basename="subscription")


urlpatterns = [
    path("", include(router.urls)),
]