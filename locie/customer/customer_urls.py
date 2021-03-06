from django.urls import path, include
from .customer_views import *
from ..tdmos.tdmos import CustomerOrderInterface

urlpatterns = [

    # @class Customer Category View
    path('customer_category_pull/',CustomerCategoryView.as_view()),

    # @class Cart Operations
    path('cart_operations/',CartOperation.as_view()),

    # @class StoreView
    path('store_view/',StoreView.as_view()),

    # @class CityCodeExtractor
    path('cityCode/',CityCodeExtractor.as_view()),

    # @class DefaultItemPull
    path('defItems/',DefaultItemPull.as_view()),

    path('login/',CustomerLogin.as_view()),

    path('register/',CustomerAddmission.as_view()), 

    path('pickdropOrder/',PickDropOrderView.as_view()),  

    path('order-making/',TemporaryOrderSystem.as_view()),

    path('interface/',CustomerOrderInterface.as_view()),
    
]