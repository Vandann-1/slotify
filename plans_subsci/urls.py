

from django.urls import path , include
from plans_subsci.views import *

urlpatterns =[
    
    path('list/', PlanListView.as_view(),name='plans-list'),
]