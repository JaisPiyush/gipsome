from django.urls import path, include
from .views import *
from .rpmns import *
from .tdmos import *
urlpatterns = [
    #Check Connetcion
    path('checkConn/',CheckConnection.as_view()),
    #account creation
    path('accountcreate/suit/', AccountAddmission.as_view()),

    # Servei Login
    path('accountlogin/servei',ServeiLogin.as_view()),

    #Servei LogOut
    path('accountlogout/servei',ServeiLogOut.as_view()),

    # Servei Password Reset
    path('accountPassworReset/servei/',ServeiPasswordReset.as_view()),

    #Servei Order History
    # path('orderHistory/servei/',ServeiOrderHistory.as_view()),

    #Item Alter
    path('serveiAlterItem/',ItemAlterView.as_view()),
    # one account
    # path('account/',CustomerLogin.as_view()), #--check
    path('cityCode/',CityCodeCreate.as_view()),
    #Analytics
    # path('analytics/',Analytics.as_view()),
    # Items Extractor
    path('items-extractor/',ItemExtractor.as_view()),

    #DefaultItems
    path('default-items/',DefaultItemsWindow.as_view()),
    # Item Creation
    path('item-creation/',ItemCreateView.as_view()),
    #Rate
    path('rate-list/',RateView.as_view()),
    #MeasureParam
    path('measure-parameters/',MeasureParamView.as_view()),
    #StoreCreate
    path('new-store/',CreateStoreView.as_view()),

    # registration_id  update
    path('fcm_key_update/',RPMNSRegistartionUpdate.as_view()), #-check
    # OrderServeiInterface
    path('order-interface-servei/',OrderServeiInterface.as_view()),

    #Customer Order Interface --check
    path('customer-order-interface/',CustomerOrderInterface.as_view()), # --check
    # Availablity
    path('available/',ServeiAvailablity.as_view()),

    #CheckUnmae
    path('checkuname/',CheckUname.as_view()),

    #CheckSite
    path('checkSite/',CheckSite.as_view()),

    #WebView
    path('webView/',WebView.as_view()),
   
   #Super User account
   path('superuser/',SuperUserAccount.as_view()),
   path('checkstore/',CheckStore.as_view()),

   #CategoryCreation
   path('categoryCreation/',CategoryCreation.as_view()),

  

]
