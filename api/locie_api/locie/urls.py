from django.urls import path
from. import views
urlpatterns=[
     
     #---Category
    # LocieCatList View 
    path('api/croax/rosnops/eltit/lociecatlist',views.LocieCatList.as_view()),
    #LocieCatOps View
    path('api/croax/rosnops/eltit/lociecatops/<pk>',views.LocieCatOps.as_view()),
    
    #----Items
    #LocieItemsList View
    path('api/horcroax/etarbelec/locieitemslist', views.LocieItemsList.as_view()),
    #LocieItemsOps View
    path('api/horcroax/etarbelec/locieitemsops/<pk>', views.LocieItemsOps.as_view()),
    #ServeiItemsList View
    path('api/horcroax/yreve/evil/serveiitemslist/<str:serveiId>', views.ServeiItemsList.as_view()),
    #ServeiItemsOps View
    path('api/horcroax/yreve/evil/serveiitemsops/<pk>', views.ServeiItemsOps.as_view()),
]