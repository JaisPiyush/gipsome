from enum import Enum
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Order, Account, Servei, Item, Customer, Pilot, Store,MobileDevice,CustomerDevice,Coordinates
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.authentication import TokenAuthentication
from rest_framework.views import Response
from .serializers import OrderSerialzer
from rest_framework import status
from datetime import datetime, timezone
from .serverOps import dtime_diff
from django.contrib.gis.geos.point import Point
from .pilot import PilotManager
from random import randint
from .rpmns import API_KEY
import time
from time import sleep
import json
# from .tasks import shared_task



def position(coordinates_id):
    return Coordinates.objects.get(coordinates_id = coordinates_id).position

def set_positon(coord_id,data:dict):
    coord = Coordinates.objects.get(coordinates_id = coord_id)
    coord.position = Point(float(data['lat']),float(data['long']))
    coord.save()


# Celery Async task to wait for 180s
# @shared_task
# def wait(order_id,time=180):
#     sleep(time)
#     print('Started Reactore')
#     TDMOSystem(order_id).reactor()

# Celery Task to start ignition
# @shared_task
# def trigger(order_id):
#     TDMOSystem(order_id).ignite()

# # Celery task to finish order
# @shared_task
# def kill_order(order_id):
#     print('Started Killing')
#     TDMOSystem(order_id).kill()

# @shared_task
# def ssu_start(order_id):
#     TDMOSystem(order_id).ssu_service()

# @shared_task
# def uds_start(order_id):
#     TDMOSystem(order_id).uds_service()


class OtpPulse:

    def __init__(self):
       
        self.data = self.random_with_n_digits(7)

    def __str__(self):
        return repr(self.data)

    def random_with_n_digits(self, n:int):
        range_start = 10**(n-1)
        range_end = (10**n)-1
        return randint(range_start, range_end)


def order_id_generator(data:str):
    # UP53$8499ODRTIME
    customer = [str(cusp) for cusp in data]
    print(customer)
    customer = customer[6] + customer[7] + customer[8] + customer[9]
    print(customer)
    time = datetime.now(timezone.utc).strftime('%d%m%y|%H%M%S')
    return 'UP53@{c}ODR{t}'.format(c=customer, t=time)




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

MISSION_CANCELLED = 4091990 # User Cancelled the order

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
    - Customers Item View will add variant it's price and effective price of variant directly
    - View for Order and Customer Interaction
    - Creation action = 'create-order
    - customer - {cart_id,clusters:[{'item_id','servei_id','store_key','quantity','price',effective_price','unit','measure','name','image','variant':'default'}],
                  cityCode','customer_id','address','customer_coords','pilot_charge,'name','delivery_type','delivery_type'}
    - Cancel - action -> cancel
               STATUS = CANCELLED
               NOTIFY ALL SERVEIS
               MARK EVERY SERVEI STATUS SOLDIER_DECLINED
                  

    """

    def post(self, request, format=None):
        data = json.loads(request.body)
        print(ORDER_CREATE)
        if int(str(data['action'])) == ORDER_CREATE:
            order = Order.objects.create(
                order_id=order_id_generator(data['customer_id']))
            order.status = START
            order.time_log[START] = datetime.now(
                timezone.utc).strftime('%d-%m-%Y.%H:%M:%S')
            order.delivery_type = data['delivery_type']
            order.customer_id = data['customer_id']
            order.customer_address = data['address']
            # order.customer_coords = Point(data['coordinates']['lat'],data['coordinates']['long'])
            order.customer_name = data['name']
            order.price = data['price']
            order.cityCode = data['cityCode']
            order.pilot_charge = data['pilot_charge']
            order.payment_method = data['payment_method']
            # json boolens are true/false whereas Python booleans are True/False
            order.payment_online = True if data['payment_online'] == 1 else False
            order.customer_coords = Point(
                data['customer_coords']['lat'], data['customer_coords']['long'], srid=4326)
            for cluster in data['clusters']:
                if cluster['servei_id'] in order.servei_cluster.keys():
                    order.servei_cluster[cluster['servei_id']
                                         ]['items'].append(cluster['items_id'])
                    order.servei_cluster[cluster['servei_id']
                                         ]['effective_price'] += cluster['effective_price']
                else:
                    clumps = {}
                    clumps['items'] = [cluster['item_id']]
                    clumps['store_key'] = cluster['store_key']
                    clumps['status'] = START
                    clumps['effective_price'] = cluster['effective_price']
                    order.servei_cluster[cluster['servei_id']] = clumps
                    order.servei_list.append(cluster['servei_id'])

                if not cluster['item_id'] in  order.items_cluster.keys():
                    clumps = {}
                    clumps['servei_id'] = cluster['servei_id']
                    clumps['quantity'] = cluster['quantity']
                    clumps['effective_price'] = cluster['effective_price']
                    clumps['price'] = cluster['price']
                    # clumps['effective_price'] = cluster['effective_price']
                    clumps['unit'] = cluster['unit']
                    clumps['measure'] = cluster['measure']
                    clumps['name'] = cluster['name']
                    clumps['image'] = cluster['image']
                    if 'variant' in cluster.keys() and cluster['variant'] is not 'default':
                        clumps['variant'] = cluster['variant']
                    order.items_cluster[cluster['item_id']] = clumps

            order.save()
            #TODO: Clear Cart Database with cart_id
            # trigger.delay(order.order_id)
            
            return Response({'order_id': order.order_id, 'status': order.status}, status=status.HTTP_201_CREATED)
        elif int(data['action']) == ORDER_CANCEL:
            order = Order.objects.get(order_id=data['order_id'])
            order.status = MISSION_FAILED
            order.save()
            # kill_order.delay(order.order_id)
            # TDMOSystem(order.order_id).kill()
            return Response({'order_id': order.order_id, 'status': order.status}, status=status.HTTP_200_OK)
        else:
            print(data['action'])
            return Response({}, status=status.HTTP_400_BAD_REQUEST)




class OrderServeiInterface(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, format=None):
        # Action Accept the order, decline the order, mark complete
        data = json.loads(request.body)
        if int(data['action']) == ORDER_SOLDIER_DECLINE:
            # Decline all
            order = Order.objects.get(order_id=data['order_id'])
            order.servei_cluster[data['servei_id']
                                 ]['status'] = SOLDIER_DECLINED
            order.save()
            # kill_order.delay(order.order_id)
            return Response({'order_id': order.order_id, 'status': order.status,'servei_status':SOLDIER_DECLINED}, status=status.HTTP_200_OK)
        
        elif int(data['action']) == ORDER_SOLDIER_ACCEPT:
            # Servei wil send packets like {order_id,items} --> items will contain items accepted
            order = Order.objects.get(order_id=data['order_id'])
            order.servei_cluster[data['servei_id']
                                 ]['status'] = SOLDIER_ACCEPTED
            servei_effective_price = 0.0
            total_quantity = 0
            servei_items = []
            for item_id in data['items']:
                order.items_cluster[item_id]['status'] = AMMO_PACKED
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
            # trigger.delay(order.order_id)
            # TDMOSystem(order.order_id).ignite()
            return Response({'order_id': order.order_id, 'status': MISSION_PROCESSING, 'servei_status':SOLDIER_ACCEPTED,'cluster': servei_items, 'quantity': total_quantity, 'effective_price': servei_effective_price, 'otp': order.otp},status=status.HTTP_200_OK)

        elif int(data['action']) == ORDER_COMPLETE:
            # FOR UDS //SDU IN FUTURE
            # WILL FIRE UDS_SERVICE IF ALL SERVEI COMPLETED
            # WILL ADD SDU IN FUTURE
            order = Order.objects.get(order_id=data['order_id'])
            order.final_servei_cluster[data['servei_id']
                                       ]['status'] = SOLDIER_COMPLETED
            order.save()
            if all([servei['status'] == SOLDIER_COMPLETED for servei in order.final_servei_cluster.values()]) and order.delivery_type == 'UDS':
                # Second Round Starts Here
                # uds_start.delay(order.order_id)
                ...
                # TDMOSystem(order.order_id).uds_service()
            return Response({'order_id': order.order_id, 'servei_status': SOLDIER_COMPLETED, 'otp': order.otp,'status':order.status}, status=status.HTTP_200_OK)
        
        





class OrderPilotInterface(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
#TODO:
    def post(self, requeset, format=None):
        data = json.loads(requeset.body)
        # action item_picked, item_dropped
        if int(data['action']) == PILOT_START_LOADING:
            
            order = Order.objects.get(order_id=data['order_id'])
           
            order.position = Point(data['coordinates']['lat'],data['coordinates']['long'])
            if order.delivery_type == 'SSU':
                
                order.final_servei_cluster[data['servei_id']]['status'] = SOLDIER_SERVED
                for item_id in order.final_servei_cluster[data['servei_id']]['items']:
                    order.final_items[item_id]['status'] = AMMO_PICKED
            elif order.delivery_type =='UDS':
                #pilot sends item_ids in a list as items
                for item_id in data['items']:
                    order.final_items[item_id]['status'] = AMMO_PICKED
                    order.save()
            
            if all([servei['status']==SOLDIER_SERVED for servei in order.final_servei_cluster.values()]):
                order.status = PILOT_FINISHED_LOADING
                order.save()
                return Response({'order_id':order.order_id,'status':order.status,'collected':'all','delivery_type':order.delivery_type},status=status.HTTP_200_OK)
            return Response({'order_id':order.order_id,'status':order.status,'delivery_type':order.delivery_type,'collected':[item_id for item_id in order.final_items.keys() if order.final_items[item_id]['status']==AMMO_PICKED]})

            
                
        

        # Pilot Dropped Subjects to Serveis
        elif int(data['action']) == PILOT_DROPED_AMMO:
            order = Order.objects.get(order_id=data['order_id'])
            for item_id in order.final_items.keys():
                order.final_items[item_id]['status'] = AMMO_PACKED
            order.save()
            if all([item['status'] ==  AMMO_PACKED for item in order.final_items.values() ]):
                device = CustomerDevice.objects.get(customer_id = order.customer_id)

                device.send_message('Your Order is in Service','You Orders have reached their destinations',
                data= {'click_action':'FLUTTER_NOTIFICATION_CLICK','data':{'type':'order-update','order_id':order.order_id,
                'status':order.status}},api_key=API_KEY)
                # RPMNSystem(order.customer_id,'009').telegram(title='Your Order is in Service',body='Orders have reached their destination, they will see you soon :)',data={'type':'order-update','order_id':order.order_id,'status':order.status})
                return Response({'order_id':order.order_id,'status':MISSION_SUCCESSFUL},status=status.HTTP_200_OK)
            return Response({'order_id':order.order_id,'status':order.status},status=status.HTTP_200_OK)


                




        # Finally dropped Order to Customer
        elif int(data['action']) == PILOT_DROPED_AMMO_VICTIM:
            order = Order.objects.get(order_id=data['order_id'])
            
            if order.delivery_type == 'UDS':
                order.status = MISSION_SUCCESSFUL
                device = CustomerDevice.objects.get(customer_id=order.customer_id)

                device.send_message('Order Completed','Your Order has been delivered',
                                    data={'click_action':'FLUTTER_NOTIFICATION_CLICK',
                                    'data':{'type':'order-complete','order_id':order.order_id}},api_key=API_KEY)
                
                # RPMNSystem(order.customer_id,'009').telegram(title='Order Completed',body='Your Order has been delivered',data={'type':'order-complete','order_id':order.order_id})
                order.save()
                
            elif order.delivery_type == 'SSU':
                order.status = MISSION_SUCCESSFUL
                device = CustomerDevice.objects.get(customer_id=order.customer_id)

                device.send_message('Order Completed','Your Order has been Delivered',data={'click_action':'FLUTTER_NOTIFICATION_CLICK',
                                    'data':{'type':'order-complete','order_id':order.order_id}},api_key=API_KEY)

                # RPMNSystem(order.customer_id,'009').telegram(title='Order Completed',body='Your Order has been delivered',data={'type':'order-complete','order_id':order.order_id})
                order.save()
            return Response({'order_id':order.order_id,'status':MISSION_SUCCESSFUL},status=status.HTTP_200_OK)
            
# TODO: Pilot Charge Calculation View



class TDMOSystem:

    def __init__(self, order_id:str):
        self.order_id = order_id
        self.order = Order.objects.get(order_id=self.order_id)

    def ignite(self):
        print("trigger")
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
            device = MobileDevice.objects.get(locie_partner = servei)
            device.send_message('New Order','New Order has arrived for you',data = {'click_action': 'FLUTTER_NOTIFICATION_CLICK',
                                'data':{'type': 'new-order', 'order_id': order.order_id, 'cluster': servei_item_cluster,
                                 'total_quantity': total_quantity, 'effective_price': servei_effective_price,
                                 'status':self.order.status,'delivery_type':self.order.delivery_type}},api_key=API_KEY)
            # RPMNSystem(servei, '002').telegram(title='New Order', body='New Order has arrived for you', data={
            #     'type': 'new-order', 'order_id': order.order_id, 'cluster': servei_item_cluster, 'total_quantity': total_quantity, 'effective_price': servei_effective_price,'status':self.order.status,'delivery_type':self.order.delivery_type})

        # Take pause for 3 minutes --> 180 seconds Celery to schedule to execute this task 3 minutes later
        # time.sleep(180)
        # self.reactor()
        wait.delay(self.order_id,time=180)
        


    def reactor(self):
        print('tri')
        self.order = Order.objects.get(order_id=self.order_id)
        final_servei_cluster = {}
        final_items = {}
        effective_price = 0.0
        price = 0.0
        for servei in self.order.servei_cluster.keys():
            if self.order.servei_cluster[servei]['status'] == SOLDIER_ACCEPTED:
                final_servei_cluster[servei] = self.order.servei_cluster[servei]
                for item_id in self.order.servei_cluster[servei]['items']:
                    if self.order.items_cluster[item_id]['status'] == AMMO_PACKED:
                        final_items[item_id] = self.order.items_cluster[item_id]
                        effective_price += final_items[item_id]['effective_price']
                        price += final_items[item_id]['price']

        # self.order.update(final_items=final_items, final_servei_cluster=final_servei_cluster,
        #                   status=MISSION_PROCESSING, effective_price=effective_price,price=price)
        print(final_items)
        if not final_items:
            print('Trying to kill')
            for servei in self.order.servei_cluster.keys():
                self.order.servei_cluster[servei]['status'] = SOLDIER_DECLINED
            self.order.status = MISSION_FAILED
            self.order.save()
            # kill_order.delay(self.order_id)
        else:
            self.order.final_items = final_items
            self.order.final_servei_cluster = final_servei_cluster
            self.order.status = MISSION_PROCESSING
            self.order.effective_price = effective_price
            self.order.price = price
            self.order.save()
            # self.order.save()
            if self.order.delivery_type == 'SSU':
                # ssu_start.delay(self.order_id)
                pass
                # self.ssu_service()
            elif self.order.delivery_type == 'UDS':
                # First Round Starts Here
                pass
                # uds_start.delay(self.order_id)
                # self.uds_service()

    def kill(self):
        # Every servei declined
        print('Killing it')
        self.order = Order.objects.get(order_id = self.order_id)
        if self.order.status == MISSION_CANCELLED or all([servei['status'] == SOLDIER_DECLINED for servei in self.order.servei_cluster.values()]) or self.order.status == MISSION_FAILED:
            print('Kill dil')
            self.order.status = MISSION_FAILED
            self.order.save()
            for servei in self.order.servei_cluster.keys():
                print(servei)
                device = MobileDevice.objects.get(locie_partner = servei)

                device.send_message('Order Cancelled',f'Order has been Cancelled!. Order ID:{self.order.order_id}',
                                    data = {'click_action': 'FLUTTER_NOTIFICATION_CLICK','data':{
                    'type': 'order_cancel', 'order_id': self.order.order_id, 'status': self.order.status}},api_key=API_KEY)

                # RPMNSystem(servei, '002').telegram(title='Order has been Cancelled', body=f'{self.order.order_id} is Cancelled', data={
                #     'type': 'order_update', 'order_id': self.order.order_id, 'status': self.order.status})
            
            device = CustomerDevice.objects.get(customer_id = self.order.customer_id)
            
            device.send_message('Order Cancelled',f'Your Order with Order Id - {self.order.order_id} has been Cancelled',
                                data= {'click_action': 'FLUTTER_NOTIFICATION_CLICK','data':{
                'type': 'order_update', 'order_id': self.order.order_id, 'status': self.order.status}},api_key = API_KEY)
            
            # RPMNSystem(self.order.customer_id, '009').telegram(title='Order has been Cancelled', body='Your Order is Cancelled', data={
            #     'type': 'order_update', 'order_id': self.order.order_id, 'status': self.order.status})
        else:
            print('Un-killable')
        # TODO: Cancellation On its way

    def ssu_service(self):
        PilotManager(self.order_id).pilot_compass()
        self.order.status = MISSION_PROCESSING
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
            coordinates[servei] = {'lat':position(store.coordinates_id)[0],'long':position(store.coordinates_id)[1]}
            address[servei] = store.address 
            serial = self.order.final_servei_cluster[servei]
            serial['servei_id'] = servei
            serial['items'] = [self.order.final_items[item_id] for item_id in serial['items'] ]
            cluster.append(serial)
            device = MobileDevice.objects.get(locie_partner = servei)

            device.send_message('Order Update','New Update on Order',data = {
                'click_action': 'FLUTTER_NOTIFICATION_CLICK','data':{'type':'order-update','action':'pilot_attach',
                'order_id':self.order.order_id,'otp':self.order.otp,'pilot_id':self.order.pilot_id_first,
                'pilot_name':self.order.pilot_name,'status':self.order.status}},api_key=API_KEY)

            # RPMNSystem(servei,'002').telegram(title='Order Update',body='New Update on an Order',data={'type':'order-update','order_id':self.order.order_id,'otp':self.order.otp,
            #                                                                                             'pilot_id':self.order.pilot_id_first,'pilot_name':self.order.pilot_name,'status':self.order.status})


        coordinates['customer'] = {'lat':self.order.customer_coords[0],'long':self.order.customer_coords[1]}
        address['customer'] = self.order.customer_address

        device  = MobileDevice.objects.get(locie_partner = self.order.pilot_id_first)

        device.send_message('New Order','New Order has Arrived for You',data={'click_action': 'FLUTTER_NOTIFICATION_CLICK',
                            'data':{'type': 'new-order','order_id':self.order.order_id,'delivery_type':'SSU',
                            'cluster':cluster,'price':self.order.price,'otp':self.order.otp,'effective_price':self.order.effective_price,
                            'coordinates':coordinates,'address':address,'customer_name':self.order.customer_name}},api_key=API_KEY)

        # RPMNSystem(self.order.pilot_id_first, '003').telegram(title='New Order',
        #                                                  body='New Order has Arrived for You', data={'type': 'new-order','order_id':self.order.order_id,'delivery_type':'SSU',
        #                                                  'cluster':cluster,'price':self.order.price,'otp':self.order.otp,'effective_price':self.order.effective_price,
        #                                                  'coordinates':coordinates,'address':address,'customer_name':self.order.customer_name})
        
        #TODO: Order Implementation on Customer
        device = CustomerDevice.objects.get(customer_id = self.order.customer_id)

        device.send_message('Pilot Assigned',f"Your Order's Pilot is {self.order.pilot_name}",data={
            'click_action': 'FLUTTER_NOTIFICATION_CLICK','data': {'type':'order-update','order_id':self.order_id,'status':self.order.status,
            'pilot_name':self.order.pilot_id_first,'pilot_name':self.order.pilot_name,'pilot_image':self.order.pilot_image}},api_key=API_KEY)

        # RPMNSystem(self.order.customer_id,'009').telegram(title='Your Order has found it\'s Pilot',body=f'{self.order.pilot_name} is your order\'s pilot',icon=self.order.pilot_image,data={'type':'order-update','order_id':self.order_id,'status':self.order.status,'pilot_name':self.order.pilot_id_first,'pilot_name':self.order.pilot_name,'pilot_image':self.order.pilot_image})
        
    def uds_service(self):
        ############################################### Look Required
        # First and then return
        if self.order.status == MISSION_PROCESSING: 
            # First
            # No Money related details will be shared
            PilotManager(self.order_id).pilot_compass()
        elif self.order.status == PILOT_FINISHED_LOADING:
            PilotManager(self.order_id).pilot_compass(first=False)

        cluster = []
        coordinates = {}
        address = {}
        for servei in self.order.final_servei_cluster.keys():
            store = Store.objects.get(store_key=self.order.final_servei_cluster[servei]['store_key'])
            coordinates[servei] = {'lat':position(store.coordinates_id)[0],'long':position(store.coordinates_id)[1]}
            address[servei] = store.address 
            serial = self.order.final_servei_cluster[servei]
            serial['servei_id'] = servei
            serial['items'] = [self.order.final_items[item_id] for item_id in serial['items'] ]
            cluster.append(serial)

            device = MobileDevice.objects.get(locie_partner = servei)

            device.send_message('Order Update','New Update on an Order',data={'click_action': 'FLUTTER_NOTIFICATION_CLICK',
              'data':{'type':'order-update','action':'pilot_attach','order_id':self.order.order_id,'otp':self.order.otp,
                      'pilot_id':self.order.pilot_id_first,'pilot_name':self.order.pilot_name,'status':self.order.status}},api_key=API_KEY)

            # RPMNSystem(servei,'002').telegram(title='Order Update',body='New Update on an Order',data={'type':'order-update','order_id':self.order.order_id,'otp':self.order.otp,
            #                                                                                             'pilot_id':self.order.pilot_id_first,'pilot_name':self.order.pilot_name,'status':self.order.status})

        coordinates['customer'] = {'lat':self.order.customer_coords[0],'long':self.order.customer_coords[1]}
        address['customer'] = self.order.customer_address
        
        ########################################################
        if self.order.status == MISSION_PROCESSING:
            device = MobileDevice.objects.get(locie_partner = self.order.pilot_id_first)

            device.send_message('New Order','New Order has Arrived for You',data={'click_action': 'FLUTTER_NOTIFICATION_CLICK',
            'data':{'type': 'new-order','order_id':self.order.order_id,'delivery_type':'UDS',
                    'cluster':cluster,'otp':self.order.otp,'coordinates':coordinates,'address':address,
                    'customer_name':self.order.customer_name}},api_key=API_KEY)

            # RPMNSystem(self.order.pilot_id_first, '003').telegram(title='New Order',
            #                                              body='New Order has Arrived for You', data={'type': 'new-order','order_id':self.order.order_id,'delivery_type':'UDS',
            #                                              'cluster':cluster,'otp':self.order.otp,
            #                                              'coordinates':coordinates,'address':address,'customer_name':self.order.customer_name})

        elif self.order.status == PILOT_FINISHED_LOADING:
            device = MobileDevice.objects.get(locie_partner = self.order.pilot_id_return)
            device.send_message('New Order','New Order has Arrived for You',data={'click_action': 'FLUTTER_NOTIFICATION_CLICK',
             'data':{'type': 'new-order','order_id':self.order.order_id,'delivery_type':'UDS','cluster':cluster,'price':self.order.price,
             'otp':self.order.otp,'effective_price':self.order.effective_price,'coordinates':coordinates,'address':address,
             'customer_name':self.order.customer_name}},api_key=API_KEY)

            # RPMNSystem(self.order.pilot_id_first, '003').telegram(title='New Order',
            #                                              body='New Order has Arrived for You', data={'type': 'new-order','order_id':self.order.order_id,'delivery_type':'UDS',
            #                                              'cluster':cluster,'price':self.order.price,'otp':self.order.otp,'effective_price':self.order.effective_price,
            #                                              'coordinates':coordinates,'address':address,'customer_name':self.order.customer_name})



        
