from  django.urls import path
from  .lociestore import *

urlpatterns = [
    path('',LocieStoreHomeView.as_view()),
    path('<str:obees>',LocieStorePageView.as_view()),
]