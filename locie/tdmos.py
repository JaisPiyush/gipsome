from enum import Enum
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Order, Account, Servei, Item, Customer, Pilot, Store
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.authentication import TokenAuthentication
from rest_framework.views import Response
from .serializers import OrderSerialzer
from rest_framework import status
from datetime import datetime, timezone
from .serverOps import dtime_diff
from .rpmns import RPMNSystem
from django.contrib.gis.geos.point import Point
from .pilot import PilotManager
from random import randint
import time


class OtpPulse:

    def __init__(self):
       
        self.data = self.random_with_n_digits(7)

    def __str__(self):
        return repr(self.data)

    def random_with_n_digits(self, n):
        range_start = 10**(n-1)
        range_end = (10**n)-1
        return randint(range_start, range_end)


def order_id_generator(data):
    # UP53$8499ODRTIME
    customer = list(map(str, Customer.objects.filter(
        account_id=data['customer_id'])))
    customer = customer[6] + customer[7] + customer[8] + customer[9]
    time = datetime.now(timezone.utc).strftime('%d%m%y|%H%M%S')
    return 'UP53${c}ODR{t}'.format(c=customer, t=time)


class Vectus(Enum):

    START = 0000
    # Process
    MISSION_SUCCESSFUL = 103904  # SECOP
    MISSION_REQUESTED = 2090  # 20** + **90 # ORDER IS CREATED AND NOTIFICATIONS ARE SENT

    # Order in Processing
    MISSION_PROCESSING = 2002  # ORDER IS UNDER SERVEI's (GLOBAL STATUS)
    # Mission Procedded
    MISSION_SERVED = 2001  # ALL SERVEI COMPLETED JOB (GLOBAL STATUS)
    # Mission Failed
    MISSION_FAILED = 409301

    # Item Related
    AMMO_PACKED = 6392  # ITEM STATUS --> ACCEPTED
    AMMO_DROPED = 2936  # ITEM STATUS --> DECLINED
    AMMO_PICKED = 6492 # Pilto Picked Item
    JET_ON_THE_WAY = 1990  # DELIVERY FOUND
    # MARKED IN-CASE ORDER IS DROPED BUT CUSTOMER CLAIMED FOR REFUND-RETURN
    MISSION_ACCOMPLISHED = 9002

    # Failure
    SOLDIER_DECLINED = 404  # SERVEI DECLINED
    PILOT_NOT_FOUND = 408  # PILOT IS NOT FOUND
    VICTIM_REFUSED = 2801  # CUSTOMER CANCELED
    TECHNICAL_FAILURE = 7000  # TECHNICAL FAILURE

    # SERVEI ORIENTED
    SOLDIER_SERVED = 4037
    SOLDIER_COMPLETED = 8038
    # Sucess
    # PILOT_FOUND = 2705
    SOLDIER_ACCEPTED = 2009

    # SSU-SP
    PILOT_LOADED_AMMO = 2708  # SSU ITEMS ARE PICKED ALL
    PILOT_DROPED_AMMO = 2711  # SSU ITEMS ARE DROPED ALL

  
    PILOT_START_LOADING = 27081 # Pilot started loading used as action
    PILOT_FINISHED_LOADING = 27082 

    # SDU
    PILOT_BOARDED_SOLDIER = 2808
    PILOT_DROPED_SOLDIER = 2811
    PILOT_BOARDED_FALLBACK_SOLDIER = 2008
    PILOT_DROPED_FALLBACK_SOLDIER = 2011

    # UDS
    PILOT_TOOK_AMMO_VICTIM = 108  # SUBJECT PICKED FROM CUSTOMER
    PILOT_DROPED_AMMO_VICTIM = 904  # SUBJECT DROPED TO CUSTOMER





class Nectus(Enum):

    ORDER_CREATE = 1000  # CREATE ORDER
    ORDER_UPDATE = 1001  # UPDATE ORDER
    ORDER_CANCEL = 1002  # CANCEL ORDER
    ORDER_RETURN = 1003  # RETURN ORDER
    ORDER_SOLDIER_ACCEPT = 2019  # SERVEI ACCEPT ORDER
    ORDER_SOLDIER_DECLINE = 2020  # SERVEI DECLINE ORDER
    ORDER_CANCEL_PARTIAL = 125  # CUSTOMER CANCELLED FEW ITEMS
    ORDER_CANCEL_COMPLETE = 521  # CUSTOMER CANCELLED EVERYTHING
    ORDER_COMPLETE = 1235
    


class CustomerOrderInterface(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    """
    - View for Order and Customer Interaction
    - Creation action = 'create-order
    - customer - {clusters:[{'item_id','servei_id','store_key','quantity','price',effective_price','unit','measure','name','image'}],
                  'cityCode','customer_id','address','coords','pilot_charge,'name','total_price','order_type','delivery_type'}
    - Cancel - action -> cancel
               STATUS = CANCELLED
               NOTIFY ALL SERVEIS
               MARK EVERY SERVEI STATUS SOLDIER_DECLINED
                  

    """

    def post(self, request, format=None):
        data = request.POST
        if data['action'] == Nectus.ORDER_CREATE:
            order = Order.objects.create(
                order_id=order_id_generator(data['customer_id']))
            order.status = Vectus.START
            order.time_log[Vectus.START.name] = datetime.now(
                timezone.uts).strftime('%d-%m-%Y.%H:%M:%S')
            order.delivery_type = data['delivery_type']
            order.customer_id = data['customer_id']
            order.customer_address = data['address']
            order.customer_name = data['name']
            order.price = data['price']
            order.cityCode = data['cityCode']
            order.pilot_charge = data['pilot_charge']
            order.payment_method = data['payment_method']
            # json boolens are true/false whereas Python booleans are True/False
            order.payment_online = True if data['payment_online'] == 'true' or data['payment_online'] == 'True' else False
            order.customer_coords = Point(
                data['customer_coords']['lat'], data['customer_coords']['long'], srid=4326)
            for cluster in data['clusters']:
                if order.servei_cluster[cluster['servei_id']]:
                    order.servei_cluster[cluster['servei_id']
                                         ]['items'].append(cluster['items_id'])
                    order.servei_cluster[cluster['servei_id']
                                         ]['effective_price'] += cluster['effective_price']
                else:
                    clumps = {}
                    clumps['items'] = [cluster['items_id']]
                    clumps['store_key'] = cluster['store_key']
                    clumps['status'] = Vectus.START
                    clumps['effective_price'] = cluster['effective_price']
                    order.servei_cluster[cluster['servei_id']] = clumps

                if not order.items_cluster[cluster['item_id']]:
                    clumps = {}
                    clumps['servei_id'] = cluster['servei_id']
                    clumps['quantity'] = cluster['quantity']
                    clumps['price'] = cluster['price']
                    clumps['effective_price'] = cluster['effective_price']
                    clumps['unit'] = cluster['unit']
                    clumps['measure'] = cluster['measure']
                    clumps['name'] = cluster['name']
                    clumps['image'] = cluster['image']
                    order.items_cluster[cluster['item_id']] = clumps

                order.save()
                TDMOSystem(order).ignite()
                return Response({'order_id': order.order_id, 'status': order.status}, status=status.HTTP_201_CREATED)
        elif data['action'] == Nectus.ORDER_CANCEL:
            order = Order.objects.get(order_id=data['order_id'])
            # order.status = Vectus.MISSION_FAILED
            order.save()
            # TDMOSystem(order.order_id).kill()
            return Response({'order_id': order.order_id, 'status': order.status}, status=status.HTTP_200_OK)


class OrderServeiInterface(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, format=None):
        # Action Accept the order, decline the order, mark complete
        data = request.POST
        if data['action'] == Nectus.ORDER_SOLDIER_DECLINE:
            # Decline all
            order = Order.objects.get(order_id=data['order_id'])
            order.servei_cluster[data['servei_id']
                                 ]['status'] = Vectus.SOLDIER_DECLINED
            order.save()
            TDMOSystem(order.order_id).kill()
            return Response({'order_id': order.order_id, 'status': order.status}, status=status.HTTP_200_OK)
        
        elif data['action'] == Nectus.ORDER_SOLDIER_ACCEPT:
            # Servei wil send packets like {order_id,items} --> items will contain items accepted
            order = Order.objects.get(order_id=data['order_id'])
            order.servei_cluster[data['servei_id']
                                 ]['status'] = Vectus.SOLDIER_ACCEPTED
            servei_effective_price = 0.0
            total_quantity = 0
            servei_items = []
            for item_id in data['items']:
                order.items_cluster[item_id]['status'] = Vectus.AMMO_PACKED
                servei_effective_price += order.items_cluster[item_id]['effective_price']
                total_quantity += order.items_cluster[item_id]['quantity']
                servei_items.append(order.items_cluster[item_id])
            order.servei_cluster[data['servei_id']
                                 ]['quantity'] = total_quantity
            order.servei_cluster[data['servei_id']
                                 ]['effective_price'] = servei_effective_price
            if order.otp == '':
                order.otp = str(OtpPulse())
            order.save()
            # Starting TDMOS
            TDMOSystem(order.order_id).ignite()
            return Response({'order_id': order.order_id, 'status': order.status, 'clusters': servei_items, 'quantity': total_quantity, 'effective_price': servei_effective_price, 'otp': order.otp})

        elif data['action'] == Nectus.ORDER_COMPLETE:
            # FOR UDS //SDU IN FUTURE
            # WILL FIRE UDS_SERVICE IF ALL SERVEI COMPLETED
            # WILL ADD SDU IN FUTURE
            order = Order.objects.get(order_id=data['order_id'])
            order.final_servei_cluster[data['servei_id']
                                       ]['status'] = Vectus.SOLDIER_COMPLETED
            order.save()
            if all([servei['status'] == Vectus.SOLDIER_COMPLETED for servei in order.final_servei_cluster.values()]) and order.order_type == 'UDS':
                # Second Round Starts Here
                TDMOSystem(order.order_id).uds_service()
            return Response({'order_id': order.order_id, 'status': order.status, 'otp': order.orp}, status=status.HTTP_200_OK)





class OrderPilotInterface(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
#TODO:
    def post(self, requeset, format=None):
        data = requeset.POST
        # action item_picked, item_dropped
        if data['action'] == Vectus.PILOT_START_LOADING:
            
            order = Order.objects.get(order_id=data['order_id'])
           
            order.position = Point(data['coordinates']['lat'],data['coordinates']['long'])
            if order.order_type == 'SSU':
                
                order.final_servei_cluster[data['servei_id']]['status'] = Vectus.SOLDIER_SERVED
                for item_id in order.final_servei_cluster[data['servei_id']]['items']:
                    order.final_items[item_id]['status'] = Vectus.AMMO_PICKED
            elif order.order_type =='UDS':
                #pilot sends item_ids in a list as items
                for item_id in data['items']:
                    order.final_items[item_id]['status'] = Vectus.AMMO_PICKED
                    order.save()
            
            if all([servei['status']==Vectus.SOLDIER_SERVED for servei in order.final_servei_cluster.values()]):
                order.status = Vectus.PILOT_FINISHED_LOADING
                order.save()
                return Response({'order_id':order.order_id,'status':order.status,'collected':'all','order_type':order.order_type},status=status.HTTP_200_OK)
            return Response({'order_id':order.order_id,'status':order.status,'order_type':order.order_type,'collected':[item_id for item_id in order.final_items.keys() if order.final_items[item_id]['status']==Vectus.AMMO_PICKED]})

            
                
        

        # Pilot Dropped Subjects to Serveis
        if data['action'] == Vectus.PILOT_DROPED_AMMO:
            order = Order.objects.get(order_id=data['order_id'])
            for item_id in order.final_items.keys():
                order.final_items[item_id]['status'] = Vectus.AMMO_PACKED
            order.save()
            if all([item['status'] ==  Vectus.AMMO_PACKED for item in order.final_items.values() ]):
                RPMNSystem(order.customer_id,'009').telegram(title='Your Order is in Service',body='Orders have reached their destination, they will see you soon :)',data={'type':'order-update','order_id':order.order_id,'status':order.status})
                return Response({'order_id':order.order_id,'status':Vectus.MISSION_SUCCESSFUL},status=status.HTTP_200_OK)
            return Response({'order_id':order.order_id,'status':order.status},status=status.HTTP_200_OK)


                




        # Finally dropped Order to Customer
        if data['action'] == Vectus.PILOT_DROPED_AMMO_VICTIM:
            order = Order.objects.get(order_id=data['order_id'])
            
            if order.order_type == 'UDS':
                order.status = Vectus.MISSION_SUCCESSFUL
                RPMNSystem(order.customer_id,'009').telegram(title='Order Completed',body='Your Order has been delivered',data={'type':'order-complete','order_id':order.order_id})
                order.save()
                
            elif order.order_type == 'SSU':
                order.status = Vectus.MISSION_SUCCESSFUL
                RPMNSystem(order.customer_id,'009').telegram(title='Order Completed',body='Your Order has been delivered',data={'type':'order-complete','order_id':order.order_id})
                order.save()
            return Response({'order_id':order.order_id,'status':Vectus.MISSION_SUCCESSFUL},status=status.HTTP_200_OK)
            
# TODO: Pilot Charge Calculation View



class TDMOSystem:

    def __init__(self, order_id):
        self.order_id = order_id
        self.order = Order.objects.get(order_id=self.order_id)

    def ignite(self):
        # order = Order.objects.get(order_id=self.order_id)
        order = self.order
        for servei in order.servei_cluster.keys():
            servei_item_cluster = []
            total_quantity = 0
            servei_effective_price = 0.0
            for item_id in order.servei_cluster[servei]['items']:
                total_quantity += order.items_cluster[item_id]['quantity']
                servei_effective_price += order.items_cluster[item_id]['effective_price']
                # Setting all item_id into cluster
                servei_item_cluster.append(order.items_cluster[item_id])
            # Notifying Servei
            RPMNSystem(servei, '002').telegram(title='New Order', body='New Order has arrived for you', data={
                'type': 'new-order', 'order_id': order.order_id, 'cluster': servei_item_cluster, 'total_quantity': total_quantity, 'effective_price': servei_effective_price,'status':self.order.status})

        # Take pause for 3 minutes --> 180 seconds
        time.sleep(180)
        self.reactor()

    def reactor(self):
        final_servei_cluster = {}
        final_items = {}
        effective_price = 0.0
        price = 0.0
        for servei in self.order.servei_cluster.keys():
            if self.order.servei_cluster[servei]['status'] == Vectus.SOLDIER_ACCEPTED:
                final_servei_cluster[servei] = self.order.servei_cluster[servei]
                for item_id in self.order.servei_cluster[servei]['items']:
                    if self.order.items_cluster[item_id]['status'] == Vectus.AMMO_PACKED:
                        final_items[item_id] = self.order.items_cluster[item_id]
                        effective_price += final_items[item_id]['effective_price']
                        price += final_items[item_id]['price']

        self.order.update(final_items=final_items, final_servei_cluster=final_servei_cluster,
                          status=Vectus.MISSION_PROCESSING, effective_price=effective_price,price=price)
        self.order.save()
        if self.order.order_type == 'SSU':
            self.ssu_service()
        elif self.order.order_type == 'UDS':
            # First Round Starts Here
            self.uds_service()

    def kill(self):
        # Every servei declined
        if all([servei['status'] == Vectus.SOLDIER_DECLINED for servei in self.order.servei_cluster.values()]):
            self.order.status = Vectus.MISSION_FAILED
            self.order.save()
            for servei in self.order.servei_cluster.keys():
                RPMNSystem(servei, '002').telegram(title='Order has been Cancelled', body=f'{self.order.order_id} is Cancelled', data={
                    'type': 'order_update', 'order_id': self.order.order_id, 'status': self.order.status})
            RPMNSystem(self.order.customer_id, '009').telegram(title='Order has been Cancelled', body='Your Order is Cancelled', data={
                'type': 'order_update', 'order_id': self.order.order_id, 'status': self.order.status})
        # TODO: Cancellation On its way

    def ssu_service(self):
        PilotManager(self.order_id).pilot_compass()
        self.order.status = Vectus.MISSION_PROCESSING
        self.order.save()
        # Notify all the final serveis and pilot about otp and order update
        # pilot: [order_id, 'cluster, price, opt, effective_price, coordinates{servei_id,'customer'},address{servei_id,'customer'},customer_name]
        # servei : [pilot_id,otp,status,order_id,pilot_name,pilot_image]
        # customer: [order_id,pilot_id,pilot_name,pilot_image,status]
        #cluster : [{'servei_id','store_name',items= final_items[servei_id]}]
        cluster = []
        coordinates = {}
        address = {}
        for servei in self.order.final_servei_cluster.keys():
            store = Store.objects.get(store_key=self.order.final_servei_cluster[servei]['store_key'])
            coordinates[servei] = {'lat':store.coordinates.position.x,'long':store.coordinates.position.y}
            address[servei] = store.address 
            serial = self.order.final_servei_cluster[servei]
            serial['servei_id'] = servei
            serial['items'] = [self.order.final_items[item_id] for item_id in serial['items'] ]
            cluster.append(serial)
            RPMNSystem(servei,'002').telegram(title='Order Update',body='New Update on an Order',data={'type':'order-update','order_id':self.order.order_id,'otp':self.order.otp,
                                                                                                        'pilot_id':self.order.pilot_id_first,'pilot_name':self.order.pilot_name,'status':self.order.status})


        coordinates['customer'] = {'lat':self.order.customer_coords.x,'long':self.order.customer_coords.y}
        address['customer'] = self.order.customer_address
        RPMNSystem(self.order.pilot_id_first, '003').telegram(title='New Order',
                                                         body='New Order has Arrived for You', data={'type': 'new-order','order_id':self.order.order_id,'order_type':'SSU',
                                                         'cluster':cluster,'price':self.order.price,'otp':self.order.otp,'effective_price':self.order.effective_price,
                                                         'coordinates':coordinates,'address':address,'customer_name':self.order.customer_name})
        
        #TODO: Order Implementation on Customer
        RPMNSystem(self.order.customer_id,'009').telegram(title='Your Order has found it\'s Pilot',body=f'{self.order.pilot_name} is your order\'s pilot',icon=self.order.pilot_image,data={'type':'order-update','order_id':self.order_id,'status':self.order.status,'pilot_name':self.order.pilot_id_first,'pilot_name':self.order.pilot_name,'pilot_image':self.order.pilot_image})
        
    def uds_service(self):
        # First and then return
        if self.order.status == Vectus.MISSION_PROCESSING: 
            # First
            # No Money related details will be shared
            PilotManager(self.order_id).pilot_compass()
        elif self.order.status == Vectus.PILOT_FINISHED_LOADING:
            PilotManager(self.order_id).pilot_compass(first=False)
        cluster = []
        coordinates = {}
        address = {}
        for servei in self.order.final_servei_cluster.keys():
            store = Store.objects.get(store_key=self.order.final_servei_cluster[servei]['store_key'])
            coordinates[servei] = {'lat':store.coordinates.position.x,'long':store.coordinates.position.y}
            address[servei] = store.address 
            serial = self.order.final_servei_cluster[servei]
            serial['servei_id'] = servei
            serial['items'] = [self.order.final_items[item_id] for item_id in serial['items'] ]
            cluster.append(serial)
            RPMNSystem(servei,'002').telegram(title='Order Update',body='New Update on an Order',data={'type':'order-update','order_id':self.order.order_id,'otp':self.order.otp,
                                                                                                        'pilot_id':self.order.pilot_id_first,'pilot_name':self.order.pilot_name,'status':self.order.status})
        coordinates['customer'] = {'lat':self.order.customer_coords.x,'long':self.order.customer_coords.y}
        address['customer'] = self.order.customer_address
        
        if self.order.status == Vectus.MISSION_PROCESSING:
            RPMNSystem(self.order.pilot_id_first, '003').telegram(title='New Order',
                                                         body='New Order has Arrived for You', data={'type': 'new-order','order_id':self.order.order_id,'order_type':'UDS',
                                                         'cluster':cluster,'otp':self.order.otp,
                                                         'coordinates':coordinates,'address':address,'customer_name':self.order.customer_name})

        elif self.order.status == Vectus.PILOT_FINISHED_LOADING:
            RPMNSystem(self.order.pilot_id_first, '003').telegram(title='New Order',
                                                         body='New Order has Arrived for You', data={'type': 'new-order','order_id':self.order.order_id,'order_type':'UDS',
                                                         'cluster':cluster,'price':self.order.price,'otp':self.order.otp,'effective_price':self.order.effective_price,
                                                         'coordinates':coordinates,'address':address,'customer_name':self.order.customer_name})



        
