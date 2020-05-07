from enum import Enum
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Order, Account, Servei, Item, Customer, Pilot, Store, MobileDevice, CustomerDevice, Coordinates, Cart, Rate, ExtraCharges
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
from .tasks import shared_task
from secrets import token_urlsafe
import math


def position(coordinates_id):
    return Coordinates.objects.get(coordinates_id=coordinates_id).position


def set_positon(coord_id, data: dict):
    coord = Coordinates.objects.get(coordinates_id=coord_id)
    coord.position = Point(float(data['lat']), float(data['long']))
    coord.save()


# Celery Async task to wait for 180s
@shared_task
def wait(order_id, time=180):
    sleep(time)
    print('Started Reactore')
    TDMOSystem(Order.objects.get(order_id=order_id)).reactor()

# Celery Task to start ignition
@shared_task
def trigger(order_id):
    TDMOSystem(Order.objects.get(order_id=order_id)).ignite()

# Celery task to finish order
@shared_task
def kill_order(order_id, force=False, reason=None):
    print('Started Killing')
    TDMOSystem(Order.objects.get(order_id=order_id)
               ).kill(force=force, reason=reason)


@shared_task
def ssu_start(order_id):
    TDMOSystem(Order.objects.get(order_id=order_id)).ssu_service()


@shared_task
def uds_start(order_id):
    TDMOSystem(Order.objects.get(order_id=order_id)).uds_service()

@shared_task
def padding(order_id):
    TDMOSystem(Order.objects.get(order_id=order_id)).pad_service()


class OtpPulse:

    def __init__(self):

        self.data = self.random_with_n_digits(7)

    def __str__(self):
        return repr(self.data)

    @staticmethod
    def random_with_n_digits(n: int):
        range_start = 10**(n-1)
        range_end = (10**n)-1
        return randint(range_start, range_end)


def order_id_generator(data: str):
    # UP53$8499ODRTIME
    customer = data
    customer = customer[6] + customer[7] + customer[8] + customer[9]
    return '{c}_{t}'.format(c=customer, t=OtpPulse.random_with_n_digits(4))


CREATED = 0
WORKING = 7
FAILED = 9
WORKING = 5
ACCEPTED = 12
FINISHED = 1
DECLINED = 13
PENDING = 11
SERVED = 10
CREATE = 39
CANCEL = 69
COMPLETED = 49


def cartilage(cart, cluster):
    if cluster['item_id'] in cart.clusters.keys():
        cart.clusters.pop(cluster['item_id'])
        cart.quanity -= cluster['quantity']
        cart.price -= cluster['price']
        if len(cart.clusters.keys()) == 0:
            cart.delete()


class CustomerOrderInterface(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    """
    - delivery required starts delivery other wise instore falicitation
    - If delivery type is PAD, then just add into senders_list and recievers list 
    -   using pad_route planner and then calculate the cost. After which Pilot is called to start following as planned
    -   data send will be sender{} reciever{} delivery_type,cityCode
    - Customers Item View will add variant it's price and effective price of variant directly
    - View for Order and Customer Interaction
    - Creation action = 'create-order
    - Delviery required True means home dilvery is required and PickAndOrder will be fired
    - else in-store checkout which will send servei asking accept and decline after accept card will directly transfer to completed section after which servei can mark complete
    - Data packet contains clusters,customer_stack,cityCode,payment_stack,cart_id,delivery_type,action,price,extra_charges
    - clusters is a JSON with item_id of cluster as key and cluster as value
    - cluster contains item_id,name,image,price,quantity,unit,measure,servei_id,store_key,store_name,prev_cat,cityCode
    - simultaneously delete item from cart if cart key is given
    - check every time if cluster length gets 0, then delete the cart
    """

    def post(self, request, format=None):
        data = json.loads(request.body)
        if data['action'] == CREATE and data['delivery_required'] == 1:
            if data['delivery_type'] == 'PAD':

                sender = {
                    "id": data['sender']['id'],
                    "name": data['sender']['name'],
                    "item_description": data['sender']['item_description'],
                    "address": data['sender']['address'],
                    "phone_number": data['sender']['phone_number'],
                }

                receiver = {
                    "id": data['receiver']['id'],
                    "name": data['receiver']['name'],
                    "address": data['receiver']['address'],
                }
                otp = OtpPulse().random_with_n_digits(6)
                order = Order.objects.create(order_id=order_id_generator(receiver['id']),
                                             senders_list=[sender['id']], receivers_list=[
                                                 receiver['id']], delivery_type='PAD',
                                             cityCode=data['cityCode'], otp=str(otp), customer_id=receiver['id'], customer_stack=receiver,
                                             final_servei_cluster={sender['id']: sender}, price=0, extra_charges={"delivery_charge": 40.0}, net_price=40.0,
                                             payment_COD=True, payment_complete=False, delivery_required=True,
                                             )
                tdmos = TDMOSystem(order).status_setter(CREATED)
                # TODO: Required area based sarching of pilot
                padding.delay(order.order_id)
                return Response({"order_id": order.order_id, "price": order.price,
                                 "extra_charges": order.extra_charges, "net_price": order.net_price,
                                 "delivery_type": order.delivery_type, "otp": order.otp,
                                 }, status=status.HTTP_201_CREATED)
            elif data['delivery_type'] == 'UDS' or data['delivery_type'] == 'SSU':
                order = Order.objetcs.create(
                    order_id=order_id_generator(data['customer_phone_number']), delivery_type=data['delivery_type'], cityCode=data['cityCode'],
                    delivery_required=True, customer_id=data['customer_phone_number'], customer_stack=data['customer_stack'])
                if not 'payment_stack' in data.keys():
                    order.payment_COD = True
                    order.payment_complete = False
                total_price = 0.0
                for value in data['clusters'].values():
                    if value['servei_id'] in order.server_cluster.keys():
                        order.servei_cluster[value['servei_id']
                                             ]['items'][value['item_id']] = value
                        order.servei_cluster[value['servei_id']
                                             ]['items']['quantity'] += value['quantity']
                        order.servei_cluster[value['servei_id']
                                             ]['items']['price'] += value['price']
                        total_price += value-['price']
                    else:
                        order.servei_cluster[value['servei_id']] = {
                            "items": {value['item_id']: value},
                            "servei_id": value['servei_id'],
                            "quantity": value["quanity"],
                            "store_key": value['store_key'],
                            "store_name": value['store_name'],
                            "platform_charge": 0.0,
                            "net_price": 0.0,
                            "extra_charges": {},
                            "status": PENDING
                        }
                        total_price += value-['price']
                order.price = total_price
                order.save()
                pilot_manager = PilotManager(order.order_id)
                farthest_point, distance = pilot_manager.fartest_point(
                    order.servei_cluster.keys(), order.customer_stack['coordinates'])
                pilot_charge = pilot_manager.pilot_charge(
                    distance, uds=True if order.delivery_type == 'UDS' else False)
                if order.delivery_type == 'UDS':
                    order.extra_charges = {
                        "pick_up_charges": math.ceil(pilot_charge/2),
                        "drop_charges": pilot_charge
                    }
                else:
                    order.extra_charges = {
                        "delivery_charge": pilot_charge
                    }
                order.net_price = order.price + pilot_charge
                order.save()
                tdmos = TDMOSystem(order)
                tdmos.status_setter(CREATED)
                trigger.delay(order.order_id)
                return Response({'order_id': order.order_id, 'status': order.status}, status=status.HTTP_201_CREATED)
        elif int(data['action']) == CANCEL:
            # TODO: Cancellation Required
            order = Order.objects.get(order_id=data['order_id'])
            if order.delivery_type == 'SSU':
                kill_order.delay(order.order_id)
                return Response({'order_id': order.order_id, 'status': FAILED}, status=status.HTTP_200_OK)
            elif order.delivery_type == 'UDS':
                return Response({'order_id': order.order_id, 'status': order.status, 'error': 'Un killable'}, status=status.HTTP_400_BAD_REQUEST)

        elif data['action'] == CREATE and data['delivery_required'] == 0:
            # In-Store Checkout
            # Only one store will be entertained
            # data sent will containe {"servi_id":{"items","quanity","price",,"net_price","store_key","store_name","servei_id",}"extra_charges" = {"Service Charge":2%}}}
            order = Order.objects.create(
                order_id=order_id_generator(data['customer_phone_number']), delivery_required=False, servei_cluster=data['cluster'],
                price=data['price'], extra_charges=data['extra_charges'], net_price=data['net_price'], otp=OtpPulse().random_with_n_digits(6), cityCode=data['cityCode']
            )
            if 'payment_stack' in data.keys():
                # TODO:Online Payment procedure
                pass
            else:
                order.payment_COD = True,
                order.payment_complete = False
            tdmos = TDMOSystem(order).status_setter(CREATED)
            trigger.delay(order.order_id)
            return Response({"order_id": order.order_id, "otp": order.otp, "price": order.price, "net_price": order.net_price, "extra_charges": order.extra_charges, "cluster": data['cluster']}, status=status.HTTP_201_CREATED)


class OrderServeiInterface(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, format=None):
        # Action Accept the order, decline the order, mark complete
        data = json.loads(request.body)
        if int(data['action']) == DECLINED:
            # Decline all
            order = Order.objects.get(order_id=data['order_id'])
            order.servei_cluster[data['servei_id']
                                 ]['status'] = DECLINED
            order.save()
            kill_order.delay(order.order_id)
            return Response({'order_id': order.order_id, 'status': order.status, 'servei_status': DECLINED}, status=status.HTTP_200_OK)

        elif int(data['action']) == ACCEPTED:
            # Servei wil send packets like {order_id,items:[item_id],servei_id} --> items will contain items accepted
            order = Order.objects.get(order_id=data['order_id'])
            order.servei_cluster[data['servei_id']
                                 ]['status'] = ACCEPTED
            servei_price = 0.0
            total_quantity = 0.0
            order.servei_cluster[data['servei_id']]['status'] = WORKING
            order.final_servei_cluster[data['servei_id']
                                       ] = {
                                           "items": {},
                                           "store_key": order.servei_cluster[data['servei_id']]["store_key"],
                                           "store_name": order.servei_cluster[data['servei_id']]["store_name"],
                                           "quantity": 0.0,
                                           "platform_charge": order.servei_cluster[data['servei_id']]['platform_charge'],
                                           "net_price": 0.0,
                                           "servei_id": data['servei_id']
            }
            final_items = {}
            tdmos = TDMOSystem(order)
            quantity = 0.0
            price = 0.0
            servei = order.servei_cluster[data['servei_id']]
            for item_id in data['items']:
                order.final_servei_cluster[data['servei_id']
                                           ]['items'][item_id] = servei['items'][item_id]
                order.final_servei_cluster[data['servei_id']
                                           ]['quantity'] += servei['items'][item_id]['quantity']
                order.final_servei_cluster[data['servei_id']
                                           ]['price'] += servei['items'][item_id]['price']
            # TDMOSystem(order).charge_calculator(order.servei_cluster[data['servei_id']])
            order.final_servei_cluster[data['servei_id']]['net_price'] = order.final_servei_cluster[data['servei_id']
                                                                                                    ]['price'] - order.final_servei_cluster[data['servei_id']]['platform_charge']
            if order.otp == '':
                order.otp = str(OtpPulse().random_with_n_digits(6))
            order.save()
            return Response({'order_id': order.order_id, 'status': order.status, 'servei_status': ACCEPTED,
                             'cluster': order.final_servei_cluster[data['servei_id']]['items'],
                             'quantity': order.final_servei_cluster[data['servei_id']]['quantity'],
                             'price': order.final_servei_cluster[data['servei_id']]['price'], 'otp': order.otp,
                             "platform_charge": order.final_servei_cluster[data['servei_id']]['platform_charge'],
                             "net_price": order.final_servei_cluster[data['servei_id']]['net_price']
                             }, status=status.HTTP_200_OK)

        elif int(data['action']) == COMPLETED:
            order = Order.objects.get(order_id=data['order_id'])
            if order.delivery_type == 'UDS' and not order.delivery_required:
                order.final_servei_cluster[data['servei_id']]['status'] = COMPLETED 
                order.save()
                uds_start.delay(order.order_id)            
            elif order.delivery_type == 'SSU' and not order.delivery_required:
                order.final_servei_cluster[data['servei_id']]['status'] = COMPLETED
                order.save()
            elif order.delivery_required:
                order.final_servei_cluster[data['sevei_id']]['status'] = SERVED
                TDMOSystem(order).status_setter(FINISHED) 
                order.save()              
            # TDMOSystem(order.order_id).uds_service()
            return Response({'order_id': order.order_id, 'servei_status': COMPLETED, 'otp': order.otp, 'status': order.status}, status=status.HTTP_200_OK)


class TDMOSystem:

    def __init__(self, order):
        self.order = Order.objects.get(order_id=self.order_id)

    def status_setter(self, status):
        self.order.status = status
        self.order.time_log[status] = timezone.now()
        self.order.save()

    def platform_formula(self, number, factor):
        fx = math.ceil(((-0.1*number)+1.1)*factor)
        if fx < 20.0:
            return (factor * 0.5)
        else:
            return fx

    def charge_calculator(self, final=False, real=False):
        # Called once before reactore and jsut after reactore
        number_servei = len(self.order.servei_cluster.keys())
        factor = 40
        if number_servei > 1:
            number = 0
            if real:
                eligible = [value for value in self.order.final_servei_cluster.values(
                ) if value['price'] > 80]
                number = math.floor(eligible/2)
            else:
                eligible = [
                    value for value in self.order.servei_cluster.values() if value['price'] > 80]
                number = eligible
            cluster = None
            if not real:
                cluster = self.order.servei_cluster.values()
            else:
                cluster = self.order.final_servei_cluster.values()

            for servei in self.cluster:
                if servei['price'] <= 80:
                    servei['platform_charge'] = 0
                elif servei['price'] > 80:
                    servei['platform_charge'] = self.platform_formula(
                        number, factor)
                elif servei['price'] > 2100:
                    servei['platform_charge'] = math.ceil(
                        servei['price'] * 2/100)
                servei['net_price'] = servei['price'] - \
                    servei['platform_charge']
            self.order.save()
        elif number_servei == 1:
            multiple = 6.5
            cluster = None
            if real:
                cluster = self.order.final_servei_cluster.values()
            else:
                cluster = self.order.servei_cluster.values()
            for servei in cluster:
                if servei['price'] < 80:
                    servei['platform_charge'] = 0
                elif servei['price'] >= 80 and servei['price'] < 150:
                    servei['platform_charge'] = 25
                elif servei['price'] >= 150 and servei['price'] < 250:
                    servei['platform_charge'] = 35
                elif servei['price'] >= 250 and servei['price'] < 700:
                    servei['platform_charge'] = 40
                elif servei['price'] >= 700 and servei['price'] < 2100:
                    servei['platform_charge'] = math.ceil(
                        servei['price'] * multiple/100)
                elif servei['price'] >= 2100:
                    EXCESS_MULTIPLE = 2.8
                    servei['platform_charge'] = math.ceil(
                        servei['price'] * EXCESS_MULTIPLE/100)
                servei['net_price'] = servei['price'] - \
                    servei['platform_charge']
            self.order.save()

    def ignite(self):
        """
          Notify every servei about orders and start reactore only if delivery required
        """
        for servei_id in self.order.servei_cluster.keys():
            device.send_message('New Order', 'New Order has arrived for you', data={'click_action': 'FLUTTER_NOTIFICATION_CLICK',
                                                                                        'data': {'type': 'new-order', 'order_id': self.order.order_id,
                                                                                                 'cluster': [item['item_id'] for item in self.order.servei_cluster[servei_id]['items']],
                                                                                                 'total_quantity': self.order.servei_cluster[servei_id]['quantity'], 'net_price': self.order.servei_cluster['net_price'],
                                                                                                 'status': self.order.status, 'delivery_type': self.order.delivery_type}}, api_key=API_KEY)
        if self.order.delivery_required:
            wait.delay(self.order.order_id, time=180)

    def reactor(self):
        """
          - Goal of this Function is to create senders, receivers list , 
          - calculate real platform charges and set locie values. Assign Pilot to order
          - First thing is to check whether the len of final servei_cluster
        """





    def kill(self, force=False, reason=None):
        """
          - Cancellation works in these ways
          - No Servei Accepted Order/ Customer Cancelled/ No Pilot Found
          - Customer can cancel order in these ways before pickup, before service, on service, on the way
          - Tell Customer, Servei and Pilot
          - if delivery_type == UDS :: un-killable
          - else kill
          - At last set status to Failed
        """
        if self.order.status != FAILED and self.order.delivery_type == 'SSU' and force == False:
            self.status_setter(FAILED)
            for servei in self.order.final_servei_cluster.keys():
                device = MobileDevice.objects.get(locie_partner=servei)
                device.send_message('Order Cancelled', f'Order has been Cancelled!. Order ID:{self.order.order_id}',
                                    data={'click_action': 'FLUTTER_NOTIFICATION_CLICK', 'data': {
                                        'type': 'order_cancel', 'order_id': self.order.order_id, 'status': self.order.status}}, api_key=API_KEY)
            device = CustomerDevice.objects.get(
                customer_id=self.order.customer_id)
            device.send_message('Order Cancelled', f'Your Order with Order Id - {self.order.order_id} has been Cancelled',
                                data={'click_action': 'FLUTTER_NOTIFICATION_CLICK', 'data': {
                                    'type': 'order_update', 'order_id': self.order.order_id, 'status': self.order.status}}, api_key=API_KEY)

            if self.order.pilot_cluster:
                pilot_id = self.order.pilot_cluster.keys()[-1]
                device = MobileDevice.objects.get(locie_partner=pilot_id)
                device.send_message('Order Cancelled', f'Order has been Cancelled!. Order ID:{self.order.order_id}',
                                    data={'click_action': 'FLUTTER_NOTIFICATION_CLICK', 'data': {
                                        'type': 'order_cancel', 'order_id': self.order.order_id, 'status': self.order.status}}, api_key=API_KEY)
        elif force and reason:
            self.status_setter(FAILED)
            for servei in self.order.final_servei_cluster.keys():
                device = MobileDevice.objects.get(locie_partner=servei)
                device.send_message('Order Cancelled', f'Order has been Cancelled!. Order ID:{self.order.order_id} because {reason}',
                                    data={'click_action': 'FLUTTER_NOTIFICATION_CLICK', 'data': {
                                        'type': 'order_cancel', 'order_id': self.order.order_id, 'status': self.order.status}}, api_key=API_KEY)
            device = CustomerDevice.objects.get(
                customer_id=self.order.customer_id)
            device.send_message('Order Cancelled', f'Your Order with Order Id - {self.order.order_id} has been Cancelled, because {reason}',
                                data={'click_action': 'FLUTTER_NOTIFICATION_CLICK', 'data': {
                                    'type': 'order_update', 'order_id': self.order.order_id, 'status': self.order.status}}, api_key=API_KEY)

            if self.order.pilot_cluster:
                pilot_id = self.order.pilot_cluster.keys()[-1]
                device = MobileDevice.objects.get(locie_partner=pilot_id)
                device.send_message('Order Cancelled', f'Order has been Cancelled!. Order ID:{self.order.order_id}, because {reason}',
                                    data={'click_action': 'FLUTTER_NOTIFICATION_CLICK', 'data': {
                                        'type': 'order_cancel', 'order_id': self.order.order_id, 'status': self.order.status}}, api_key=API_KEY)
    
    def pad_service(self):
        pass
    
    def ssu_service(self):
        """
         - Check cityCode of all item with order.cityCode
         - if any found not matching with cityCode put that into ship list 
         - Servei will be notified about delivery Details For now only hyperlocal is working
         - For now just find some pilot and send data to both of them
        """
        try:
            PilotManager(self.order.order_id).pilot_compass()
        except:
            kill_order.delay(self.order.order_id, force=True,
                             reason='We couldn\'t find any Pilot')
        self.order.save()
        for servei_id in self.order.final_servei_cluster.keys():
            device = MobileDevice.objects.get(locie_partner=servei_id)
            device.send_message('Order Update', 'New Update on Order', data={
                'click_action': 'FLUTTER_NOTIFICATION_CLICK', 'data': {'type': 'order-update', 'action': 'pilot_attach',
                                                                       'order_id': self.order.order_id, 'otp': self.order.otp, 'pilot_id': self.order.pilot_id_first,
                                                                       'pilot_name': self.order.pilot_name, 'status': self.order.status}}, api_key=API_KEY)

        if self.order.pilot_cluster:
            pilot_id = list(self.order.pilot_cluster.keys())[-1]
            device = MobileDevice.objects.get(locie_partner=pilot_id)
            device.send_message('Order Cancelled', f'New Order has arrivedOrder ID:{self.order.order_id}, because',
                                data={'click_action': 'FLUTTER_NOTIFICATION_CLICK', 'data': {
                                    'type': 'new_order', 'order_id': self.order.order_id, 'status': self.order.status}}, api_key=API_KEY)

            device = CustomerDevice.objects.get(
                customer_id=self.order.customer_id)
            device.send_message('Order Cancelled', f'{list(self.order.pilot_cluster.values())[-1]["name"]} is assigned as your Pilot',
                                data={'click_action': 'FLUTTER_NOTIFICATION_CLICK', 'data': {
                                    'type': 'order_update', 'order_id': self.order.order_id, 'status': self.order.status}}, api_key=API_KEY)

    def uds_service(self):
        """
          - Call pilot compass and assign pilot to order, if city Code matches
          - else kill it forcefully
        """
        if self.order.pilot_cluster:
            if len(self.order.pilot_cluster.keys()) == 1:
                try:
                    PilotManager(self.order.order_id).pilot_compass(
                        first=False)
                except:
                    # Emergency Pilot
                    pass
            else:
                try:
                    PilotManager(self.order.order_id).pilot_compass(first=True)
                except:
                    kill_order.delay(self.order.order_id, force=True,
                                     reason='Couldn\'t find any Pilot near you.')
