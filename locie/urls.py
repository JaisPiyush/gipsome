from django.urls import path, include
from .views import *
from .gadgets.rpmns import *
from .tdmos.tdmos import OrderServeiInterface
urlpatterns = [
    #Check Connetcion
    path('checkConn/',CheckConnection.as_view()),
    #account creation
    path('accountcreate/suit/', AccountAdmission.as_view()),

    # Servei Login
    path('accountlogin/servei',ServeiLogin.as_view()),

    #Servei LogOut
    path('accountlogout/servei',ServeiLogOut.as_view()),

    # Servei Password Reset
    path('accountPassworReset/servei/',ServeiPasswordReset.as_view()),

    #Servei Order History
    path('orderHistory/servei/',OrderHistory.as_view()),

    #Item Alter
    path('serveiAlterItem/',ItemAlterView.as_view()),
    # one account
    # path('account/',CustomerLogin.as_view()), #--check
    path('cityCode/',CityCodeService.as_view()),
    #Analytics
    path('analytics/',Analytics.as_view()),
    # Items Extractor
    path('items-extractor/',ItemExtractor.as_view()),

    #DefaultItems
    path('default-items/',DefaultItemsWindow.as_view()),
    # Item Creation
    path('item-creation/',ItemCreateView.as_view()),
    #MeasureParam

    #StoreCreate
    path('new-store/',CreateStoreView.as_view()),

    # registration_id  update
    path('fcm_key_update/',RPMNSRegistartionUpdate.as_view()), #-check
    # OrderServeiInterface
    path('order-interface-servei/',OrderServeiInterface.as_view()),

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

   # Verify Token
   path('verifyToken/',VerifyToken.as_view()),

   #Get Orders
   path('ordersView/',OrderView.as_view()),

   path('category-selection/',CategorySelection.as_view()),

  

]
