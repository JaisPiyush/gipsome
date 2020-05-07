from django.urls import path, include
from .pilot import *

urlpatterns = [
    path('login/',PilotLogin.as_view()),
    path('create/',PilotCreate.as_view()),
    path('sender/',PilotUpdateSender.as_view()),
    path('reciever/',PilotUpdateReciever.as_view()),
]

