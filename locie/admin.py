from django.contrib import admin
from .models import Account,MobileDevice,Category,DefaultItems,Rate,Order,Customer
from .models import MeasureParam,Store,Item,Pilot,Servei
from .models import CustomerDevice,Coordinates,PickDropOrder

# Register your models here.

admin.site.register(MobileDevice)
admin.site.register(Category)
admin.site.register(DefaultItems)
admin.site.register(Rate)
admin.site.register(MeasureParam)
admin.site.register(Store)
admin.site.register(Item)
admin.site.register(Order)
admin.site.register(Customer)
admin.site.register(Pilot)
admin.site.register(Account)
admin.site.register(Servei)
admin.site.register(CustomerDevice)
admin.site.register(Coordinates)
admin.site.register(PickDropOrder)






