from django.urls import path, include
from .views import *

urlpatterns = [
    #account creation
    path('accountcreate/suit/', AccountAddmission.as_view()),
    #otpMectus
    path('otpMectus/exposure/',OtpCreator.as_view()),
    #all accounts
    #path('all/accounts/',AccountBase.as_view()),
    # one account
    path('account/',CustomerLogin.as_view()),
    path('cityCode/',CityCodeCreate.as_view()),
    #Analytics
    path('analytics/',Analytics.as_view()),
    # Items Extractor
    path('items-extractor/<str:store_key>',ItemExtractor.as_view())

]
