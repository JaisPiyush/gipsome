from django.urls import path, include
from .pilot import *

urlpatterns = [
    path('login/',PilotLogin.as_view()),
    path('create/',PilotCreate.as_view()),
    path('updates/',PilotOrderUpdate.as_view()),
    path('orders/',PilotNewOrder.as_view()),

]

