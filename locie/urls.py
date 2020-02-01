from django.urls import path, include
from .views import *
from .rpmns import *
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
    path('items-extractor/<str:store_key>',ItemExtractor.as_view()),
    #Store Team
    path('store-team/',StoreTeamWindow.as_view()),
    #CategorySelection
    path('category-selection/',CategorySelection.as_view()),
    #DefaultItems
    path('default-items/',DefaultItemsWindow.as_view()),
    # Item Creation
    path('item-creation/',ItemCreateView.as_view()),
    #Rate
    path('rate-list/',RateView.as_view()),
    #MeasureParam
    path('measure-parameters/',MeasureParamView.as_view()),
    # portfolio
    path('portfolio/',PortfolioManager.as_view()),
    #StoreCreate
    path('new-store/',CreateStoreView.as_view()),
    #Head Categories
    path('head-categories/',HeadCategories.as_view()),
   
   

]
