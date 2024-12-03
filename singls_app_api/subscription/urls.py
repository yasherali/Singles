from django.urls import path , include
from django.contrib import admin
from .views import *

urlpatterns = [
   
   path('get_plan/',GetPlan.as_view(),name='get_plan'),
   path('create_plan/',CreatePlan.as_view(),name='create_plan'),
   path('update_plan/<int:pk>/',UpdatePlan.as_view(),name='update_plan'),
   path('delete_plan/<int:pk>/',DeletePlan.as_view(),name='delete_plan'),
   

   path('create_upgrade_subscription/', CreateOrUpgradeSubscription.as_view(), name='create_upgrade_subscription'),
   path('get_packages/', GetPackages.as_view(), name='get_packages'),
   path('check_subscription/' , CheckSubscription.as_view(), name='check_subscription')
]
