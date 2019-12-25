# RPMNS Ram Pragat Mani Notification System
from django.db import models
from rest_framework.views import APIView
from .models import OntoNotfication,InterCorse,MobileDevice






# When order is created every servei_id plugged-in will be notified about the order
# selected de will be notified about the order 
"""
- to:
- data:{
    'typo': 'order':
    'order_id': order_id
}"""

class OrderFleet:
    # Used for servei and de conversation

    def telegram(self,receipient,data,typo):
        device = MobileDevice.objects.filter(locie_partner=receipient)
        noti = OntoNotfication.objects.create(receipient=receipient,receipient_token=device.registration_id,type=typo,content=data)
        device.send_message(data = {'content':noti.content,'type':noti.type})
    
    # Used for customer conversation
    def telephone(self,recepient,data,typo):
        device = MobileDevice.objects.filter(customer_id=recepient)
        noti = OntoNotfication.objects.create(recepient=recepient,recepient_token=device.registration_id,type=typo,content=data)
        device.send_message(data={'content':noti.content,'type':noti.type})

        