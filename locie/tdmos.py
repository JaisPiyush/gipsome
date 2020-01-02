"""
   Takes in order_id
   get all the servei_ids
   notify them servei_id , item_id, price  and effective  price
   notif_time = datetime.datetime.now(datetime.timezone.utc)
   Signals for any injection related to order_id
   after 180
   get final servei_id and items and mark else as cancelled
   send notification to users
   DE Manager -> pilot generatesOTP
   Signals update of order pickup | order cancelled --> notif to servei and  user
   mark finish -> Update DB

   1. Signals (Order Acceptance):
       notify when order.final_servei added something new server
   2. Signals (Order Update): after de
       notify 

 
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Order, Account, Servei, Item
from rpmns import OrderFleet
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.authentication import TokenAuthentication
from rest_framework.views import Response
from .serializers import OrderSerialzer
from rest_framework import status
from datetime import datetime, timezone
from .serverOps import dtime_diff
import asyncio


class OrderCreate(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    """
      Client will push
      customer_id, items_data,serveis,items,customer_price,order_type,customer_address,customer_coords,delivery_type,cityCode
      Needed to add servei_cluster,store_cluster
    """

    def post(self, request, format=None):

        order = OrderSerialzer(data=request.POST)
        if order.is_valid():
            order.data['order_id'] = TDMOS().order_id_generator(request.POST)
            for item in order.data['items']:
                order.data['servei_cluster'][order.data['items_data'][item][0]] = order.data['servei_cluster'][order.data['items_data'][item][0]].append(item) if order.data['servei_cluster'][order.data['items_data'][item][0]] is not None else [item]
            for servei in order.data['serveis']:
                servei_object = Servei.objects.get(servei_id=servei)
                if not servei_object.store in order.data['store_cluster']:
                    order.data['store_cluster'].append(servei_object.store)
                
            order.save()
            TDMOS().ignite(order.data['order_id'])
            return Response(order.data, status=status.HTTP_201_CREATED)
        else:
            return Response(order.errors, status=status.HTTP_400_BAD_REQUEST)

# will do non-blocking sleep
# so that api remains un-affected
async def sleepershell(seconds, order_id, now):
    await asyncio.sleep(seconds)
    TDMOS().motor(order_id, now)


#enum class for status and response
from enum import Enum
class Vectus(Enum):
    #Process
    MISSION_SUCCESSFUL = 103904 #SECOP
    MISSION_REQUESTED = 2090 #20** + **90
    MISSION_PROCESSING = 2002 # order accepted
    JET_ON_THE_WAY = 1990 # delivery started
    MISSION_ACCOMPLISHED = 9002 # MARKED IN-CASE ORDER IS DROPED BUT CUSTOMER CLAIMED FOR REFUND-RETURN

    #Failure
    SOLDIER_DECLINED = 404
    PILOT_NOT_FOUND = 408
    VICTIM_REFUSED = 2801
    TECHNICAL_FAILURE = 0000

    #Sucess
    PILOT_FOUND = 2705
    SOLDIER_ACCEPTED = 2009

    #SSU-SP
    PILOT_LOADED_AMMO_SSU_SP = 2708
    PILOT_DROPED_AMMO_SSU_SP = 2711

    #SSU-MP
    PILOT_START_LOADING_SSU_MP = 27081
    PILOT_FINISHED_LOADING_SSU_MP = 27082

    #SDU
    PILOT_BOARDED_SOLDIER = 2808
    PILOT_DROPED_SOLDIER = 2811
    PILOT_BOARDED_FALLBACK_SOLDIER = 2008
    PILOT_DROPED_FALLBACK_SOLDIER = 2011

    #UDS
    PILOT_TOOK_AMMO_VICTIM = 108
    PILOT_DROPED_AMMO_VICTIM = 904

    #SP
    PILOT_DROPED_AMMO_SOLDIER = 111
    PILOT_TOOK_AMMO_SOLDIER = 990
    
    #MP
    PILOT_START_FETCH_AMMO_SOLDIER = 9901
    PILOT_FINISHED_FECTH_AMMO_SOLDIER = 9902



class TDMOS:

    def logger(self,vectus):
        order = Order.objects.get(order_id = self.order_id)
        order.response = vectus
        order.status = str(vectus.name)
        order.time_log[datetime.now(timezone.uts).strftime('%d-%m-%Y.%H:%M:%S')] = (vectus.name,vectus)


    def order_id_generator(self, data):
        # UP53$8499ODRTIME
        customer = list(map(str, Account.objects.filter(
            account_id=data['customer_id'])))
        customer = customer[6] + customer[7] + customer[8] + customer[9]
        time = datetime.now(timezone.utc).strftime('%d%m%y|%H%M%S')
        return 'UP53${c}ODR{t}'.format(c=customer, t=time)

    def ignite(self, order_id):
        # Called after to start order is created in the system
        order = Order.objects.get(order_id=order_id)
        self.order_id = order_id
        self.customer_id = order.customer_id
        self.logger(vectus=Vectus.MISSION_REQUESTED)
        # List of serveis
        servei_list = order.serveis
        # List of Items
        item_list = order.items
        # Dict of items as key and servei_id price and quantity as sub dict
        items_data = order.items_data
        # Dict as servei_id as key and list of items as value
        servei_cluster = order.servei_cluster
        now = datetime.now(timezone.utc)
        for servei in servei_list:
            items = servei_cluster[servei]
            OrderFleet().telegram(receipient=servei, typo='fetch-order',
                                  data={'items': items, 'order_id': self.order_id})
        # Goes async for 180sec sleep then starts Motor
        sleepershell(180, self.order_id, now)

    def motor(self, order_id, now):
        # Motor wil take after 180s halt
        # getting final list and then satrting DE Manager
        order = Order.objects.get(order_id=order_id)
        self.order_id  = order_id
        # if final item is not empty then update status and time log
        if order.final_items is not None or order.final_items != []:
            # order accepted
            self.logger(vectus= Vectus.MISSION_PROCESSING)
            # Sending Notification to User
            OrderFleet().telephone(recepient=self.customer_id,data={'order_id':self.order_id,'response':Vectus.MISSION_PROCESSING},typo='update-order')
            #start DE Manger

        else:
            #If no Item is accepted for service
            self.logger(vectus = Vectus.SOLDIER_DECLINED)
            OrderFleet().telephone(recepient=self.customer_id,data={'order_id':self.order_id,'response':Vectus.SOLDIER_DECLINED},typo = 'update-order')




        
       
