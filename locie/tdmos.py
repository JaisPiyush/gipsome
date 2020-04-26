from enum import Enum
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Order, Account, Servei, Item, Customer, Pilot, Store, MobileDevice, CustomerDevice, Coordinates, Cart, Rate,ExtraCharges
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
def kill_order(order_id,force=False,reason=None):
    print('Started Killing')
    TDMOSystem(Order.objects.get(order_id=order_id)).kill(force=force,reason=reason)


@shared_task
def ssu_start(order_id):
    TDMOSystem(Order.objects.get(order_id=order_id)).ssu_service()


@shared_task
def uds_start(order_id):
    TDMOSystem(Order.objects.get(order_id=order_id)).uds_service()


class OtpPulse:

    def __init__(self):

        self.data = self.random_with_n_digits(7)

    def __str__(self):
        return repr(self.data)

    def random_with_n_digits(self, n: int):
        range_start = 10**(n-1)
        range_end = (10**n)-1
        return randint(range_start, range_end)


def order_id_generator(data: str):
    # UP53$8499ODRTIME
    customer = [str(cusp) for cusp in data]
    print(customer)
    customer = customer[6] + customer[7] + customer[8] + customer[9]
    print(customer)
    time = datetime.now(timezone.utc).strftime('%d%m%y|%H%M%S')
    return 'UP53@{c}ODR{t}'.format(c=customer, t=time)


CREATED = 0
WORKING = 7
FAILED = 9
WORKING = 5
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
    - Customers Item View will add variant it's price and effective price of variant directly
    - View for Order and Customer Interaction
    - Creation action = 'create-order
    - Data packet contains clusters,customer_stack,cityCode,payment_stack,cart_id,delivery_type,action,price,extra_charges
    - clusters is a JSON with item_id of cluster as key and cluster as value
    - cluster contains item_id,name,image,price,quantity,unit,measure,servei_id,store_key,store_name,prev_cat,cityCode
    - simultaneously delete item from cart if cart key is given
    - check every time if cluster length gets 0, then delete the cart
    """

    def post(self, request, format=None):
        data = json.loads(request.body)
        if(data['action'] == CREATE):
            order = Order.objects.create(order_id=order_id_generator(
                data['customer_stack']['customer_id']))
            order.delivery_type = data['delivery_type']
            cart = None
            if 'cart' in data.keys():
                cart = Cart.objects.get(cart_id=data['cart_id'])
            quantity = 0.0
            price = 0.0
            net_price = 0.0
            clusters = data['clusters']
            tdmos = TDMOSystem(order)
            for item_id in clusters.keys():
                servei_id = clusters[item_id]['servei_id']
                if servei_id in order.servei_cluster.keys():
                    order.servei_cluster[servei_id]['price'] += clusters[item_id]['price']
                    order.servei_cluster[servei_id]['quantity'] += clusters[item_id]['quanity']
                    order.servei_cluster[servei_id]['items'].append(
                        clusters[item_id])
                    tdmos.charge_calculator(clusters[item_id],servei_id,final=False)
                    if cart:
                        cartilage(cart, clusters[item_id])
                else:
                    order.servei_list.append(servei_id)
                    order.servei_cluster[servei_id] = {"items": [clusters[item_id]], "price": clusters[item_id]['price'], "quantity": clusters[item_id]['quantity'],
                                                       "store_key": clusters[item_id]['store_key'], "store_name": clusters[item_id]['store_name'],
                                                       "net_price": 0.0, "extra_charges": {'platform_delivery':0.0}, "status": PENDING}
                    tdmos.charge_calculator(clusters[item_id],servei_id,final=False)
                    if cart:
                        cartilage(cart, clusters[item_id])
            order.customer_stack = data['customer_stack']
            order.payment_stack = data['payment_stack']
            if data['payment_stack']['method'] != 'COD':
                order.payment_COD = True
            else:
                order.payment_COD = False
            if 'payment_id' in data['payment_stack'].keys():
                order.payment_id = data['payment_stack']['payment_id']
            if 'cityCode' in data.keys():
                order.cityCode = data['cityCode']
            order.price = data['price']
            order.extra_cahrges = data['extra_charges']
            order.net_price = data['price'] + \
                sum(data['extra_charges'].values())
            tdmos.status_setter(CREATED)
            order.save()
            trigger.delay(order.order_id)
            return Response({'order_id': order.order_id, 'status': order.status}, status=status.HTTP_201_CREATED)
        elif int(data['action']) == CANCEL:
            order = Order.objects.get(order_id=data['order_id'])
            if order.delivery_type == 'SSU':
                kill_order.delay(order.order_id)
                return Response({'order_id': order.order_id, 'status': FAILED}, status=status.HTTP_200_OK)
            elif order.delivery_type == 'UDS':
                return Response({'order_id': order.order_id, 'status': order.status,'error':'Un killable'}, status=status.HTTP_200_OK)                
        else:
            return Response({}, status=status.HTTP_400_BAD_REQUEST)


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

        elif int(data['action']) == WORKING:
            # Servei wil send packets like {order_id,items:[item_id]} --> items will contain items accepted
            order = Order.objects.get(order_id=data['order_id'])
            order.servei_cluster[data['servei_id']
                                 ]['status'] = WORKING
            servei_price = 0.0
            total_quantity = 0.0
            order.servei_cluster[data['servei_id']]['status'] = WORKING
            order.final_servei_cluster[data['servei_id']] = order.servei_cluster[data['servei_id']]
            final_items = []
            tdmos = TDMOSystem(order)
            for item in order.servei_cluster[data['servei_id']]['items']:
                if item['item_id'] in data['items']:
                    final_items.append(item)
                    servei_price += item['price']
                    total_quantity += item['quantity']
                    tdmos.charge_calculator(item,data['servei_id'],final=True)
            order.final_servei_cluster[data['servei_id']]['items'] = final_items
            del final_items
            order.final_servei_cluster[data['servei_id']]['price'] = servei_price
            order.final_servei_cluster[data['servei_id']]['quantity'] = total_quantity

            # TDMOSystem(order).charge_calculator(order.servei_cluster[data['servei_id']])
            if order.otp == '':
                order.otp = str(OtpPulse())
            order.save()
            trigger.delay(order.order_id)
            return Response({'order_id': order.order_id, 'status': order.status, 'servei_status': WORKING,
                             'cluster': order.final_servei_cluster[data['servei_id']]['items'], 'quantity': total_quantity,
                             'effective_price': servei_price, 'otp': order.otp,
                             "extra_charges": order.final_servei_cluster[data['servei_id']]['extra_charges'],
                             "net_price": order.final_servei_cluster[data['servei_id']]['net_price']}, status=status.HTTP_200_OK)

        elif int(data['action']) == COMPLETED:
            order = Order.objects.get(order_id=data['order_id'])
            order.final_servei_cluster[data['servei_id']
                                       ]['status'] = COMPLETED
            order.pick_list = [cluster['item_id'] for cluster in order.final_servei_cluster[data['servei_id']]['items']]
            order.save()
            if len(order.pick_list) == len([servei['items'] for servei in order.final_servei_cluster.values()]):
                # Second Round Starts Here
                uds_start.delay(order.order_id)
                
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

    def charge_calculator(self, cluster,servei_id,final=False):
        # TODO: Implementation takes in icluster 
        # Takes out the rate and extra_charges applicable per_item, and set the extra_charges using servei_id from item and self.order
        # Takes rate of each item, price*rate*quantity/100 value of item in order per servei
        # principal_portion = value/price(Total)*100
        # if final: order.final_servei_cluster[servei_id]['extra_charges']['value'] += principal_protion
        # else order.servei_cluster[servei_id]['extra_charges']['value'] += principal_protion
        # net_price = price + sum([price*value/100 for value in servei_cluster[extra_charges].values()])
        # extra_charges = {}
        servei_cluster = None
        if final:
            servei_cluster = self.order.final_servei_cluster[servei_id]
        else:
            servei_cluster = self.order.servei_cluster[servei_id]
        item = Item.objects.get(item_id=cluster['item_id'])
        rate = Rate.object.filter(categories__contains = [item.prev_cat])
        servei_cluster['extra_charges']['platform_delivery'] += (item.price * rate.rate * cluster['quantity'] /100)* 100 /servei_cluster['price']
        servei_cluster['net_price'] = servei_cluster['price'] + sum([servei_cluster['price'] * value/100 for value in servei_cluster['extra_charges'].values()])
        self.order.save()

    def ignite(self):
        """
         - Ignition starts just after the creation
         - It will call all the servei's and notify them about their order
         - Then start reactore through celery
        """
        if self.order.status == CREATED:
            for servei_id in self.order.servei_cluster.keys():
                device = MobileDevice.objects.get(locie_partner=servei_id)
                device.send_message('New Order', 'New Order has arrived for you', data={'click_action': 'FLUTTER_NOTIFICATION_CLICK',
                                                                                    'data': {'type': 'new-order', 'order_id': self.order.order_id, 
                                                                                    'cluster': [item['item_id'] for item in self.order.servei_cluster[servei_id]['items']],
                                                                                    'total_quantity':self.order.servei_cluster[servei_id]['quantity'], 'net_price': self.order.servei_cluster['net_price'],
                                                                                    'status': self.order.status, 'delivery_type': self.order.delivery_type}}, api_key=API_KEY)            
            wait.delay(self.order.order_id, time=180)        

    def reactor(self):
        """
          -- Check Count in final servei clusters
          -- Check Delivery Type and Start respective service or kill if final_servei_cluster is empty
          -- Notify Customer about next step
        """
        if self.order.status == CREATED:
            self.status_setter(WORKING)
            if self.order.final_servei_cluster == {}:
                kill_order.delay(self.order.order_id)
            else:
                accepted_items = [servei['items'] for servei in self.order.final_servei_cluster.values()]
                device = CustomerDevice.objects.get(
                    customer_id=self.order.customer_id)
                device.send_message('Order Cancelled', f'Order has been Accepted.',
                                    data={'click_action': 'FLUTTER_NOTIFICATION_CLICK', 'data': {'cluster':accepted_items,
                                        'type': 'order_accepted', 'order_id': self.order.order_id, 'status': self.order.status}}, api_key=API_KEY)
                
                if self.order.delivery_type == 'SSU':
                    ssu_start.delay(self.order.order_id)
                elif self.order.delivery_type == 'UDS':
                    uds_start.delay(self.order.order_id)

    def kill(self,force=False,reason=None):
        """
          - Cancellation works in these ways
          - No Servei Accepted Order/ Customer Cancelled/ No Pilot Found
          - Customer can cancel order in these ways before pickup, before service, on service, on the way
          - Tell Customer, Servei and Pilot
          - if delivery_type == UDS :: un-killable
          - else kill
          - At last set status to Failed
        """
        if self.order.status != FAILED and self.order.delivery_type == 'SSU' and force ==  False:
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
            kill_order.delay(self.order.order_id,force=True,reason='We couldn\'t find any Pilot')
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

            device = CustomerDevice.objects.get(customer_id=self.order.customer_id)
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
                    PilotManager(self.order.order_id).pilot_compass(first=False)
                except:
                    # Emergency Pilot
                    pass
            else:
                try:
                    PilotManager(self.order.order_id).pilot_compass(first=True)
                except:
                    kill_order.delay(self.order.order_id,force=True,reason='Couldn\'t find any Pilot near you.' )