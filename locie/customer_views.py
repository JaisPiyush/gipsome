# from django.shortcuts import render, HttpResponse
from rest_framework.authentication import TokenAuthentication
# from django.template import Context, Template
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.views import APIView
from rest_framework.views import Response
from rest_framework import status
# from .serializers import AccountCreationSerializer
from .customer_serializer import *
from .models import *
import datetime
import time
from secrets import token_urlsafe
# from .serverOps import storeKeyGenerator, item_id_generator, OtpHemdal, dtime_diff, coord_id_generator
import json
from django.db.models import Q
from .serializers import CityCodeSerializer
from .tdmos import order_id_generator


def variant_describe(item):
    """
      * Return string or dict
      * check if item.variants !={}:
        True :- return {parameter,variants:[value,image,price]}
        False :- 'default'
    """
    if item.variants:
        return {"parameter": item.variants['parameter'], "variants": [{"value": variant['value'], "price":variant['price'], "image":variant['image']} for variant in item.variants['variants']]}
    else:
        return 'default'


"""
  * Return categories and items of respective category
  * If only-head is int the key then only return {cat_id,name,image} of father_cat of that cityCode
  * Filter the next categories using prev_cat and cityCode 
  * Filter items of that category using prev_cat
  * Category Data Packet : {cat_id,prev_cat,name,image}
  * Item Data Packet: {item_id,prev_cat,name,image,store_key,servei_id,price,effective_price,unit,measure,variants}
  * Item variants list packet : {parameter,variants:[{value,image,price}]}
"""


class CustomerCategoryView(APIView):
    permission_classes = [AllowAny]

    def get(self, requests, format=None):
        data = requests.GET
        categories = []
        items = []
        default_items = []
        # print(data.keys())
        prevCat = None
        if 'only-head' in data.keys():
            categories = Category.objects.filter(
                Q(city_site__contains=[data['cityCode']]) & Q(cat_type='FC'))
            categories = [{"cat_id": category.cat_id, "prev_cat": category.prev_cat, "name": category.name, "image": category.image,
                           "cat_type": category.cat_type, "delivery_type": category.delivery_type}for category in categories]

        else:
            categories = Category.objects.filter(
                Q(city_site__contains=[data['cityCode']]) & Q(prev_cat=data['cat_id']))
            prevCat = Category.objects.get(cat_id=data['cat_id'])
            categories = [{"cat_id": category.cat_id, "prev_cat": category.prev_cat, "name": category.name, "image": category.image,
                           "cat_type": category.cat_type, "delivery_type": category.delivery_type}for category in categories]
            items = Item.objects.filter(Q(prev_cat=data['cat_id']) & Q(
                cityCode=data['cityCode']) & Q(default_item_id='none'))
            default_items = [{"item_id": item.item_id, "cat_id": item.cat_id, "measure": item.measure_param, "image": item.image,
                              "unit": item.unit, "name": item.name} for item in DefaultItems.objects.filter(cat_id=data['cat_id'])]

            if items:
                items = [{"item_id": item.item_id, "prev_cat": item.prev_cat, "name": item.name, "images": item.images if hasattr(item, 'images') else '',
                          "store_key": item.store_key, "servei_id": item.servei_id, "price": item.price, "effective_price": item.effective_price,
                          "unit": item.unit, "measure": item.measure_param, "store_name": Store.objects.get(store_key=item.store_key).store_name} for item in items]
        if len(categories) > 0 or len(items) > 0 or len(default_items) > 0:
            del data
            return Response({"categories": categories, "items": items, "prev_name": prevCat.name if prevCat is not None else "", "default_items": default_items}, status=status.HTTP_200_OK)
        else:
            return Response({"prev_name": prevCat.name}, status=status.HTTP_200_OK)


class CartOperation(APIView):
    permission_classes = [AllowAny]

    """
      *  Handling Carts when Customer add item in cart from website or app.
      *  Orders will be added globally.
      *  Operations include post,get,update,delete
      *  Clusters [{item_id,name,image,quantity,servei_id,store_key,unit,measure,price,effective_price}]
    """

    def post(self, requests, format=None):
        data = json.loads(requests.body)
        cart = None
        serialized = None
        if data['action'] == 'create':
            cart = Cart.objects.create(cart_id=token_urlsafe(16))
            cart.customer_id = data['customer_id']
            price = 0.0
            effective_price = 0.0
            total_quantity = 0
            cart.clusters = data['clusters']
            for cluster in cart.clusters:
                price += float(str(cluster['price']))
                effective_price += float(str(cluster['effective_price']))
                total_quantity += float(str(cluster['quantity']))
            cart.price = price
            cart.effective_price = effective_price
            cart.total_quantity = total_quantity
            cart.save()
            serialized = CartSerializer(cart)
        elif data['action'] == 'update':
            cart = Cart.objects.get(cart_id=data['cart_id'])
            price = 0.0
            effective_price = 0.0
            total_quantity = 0
            cart.clusters = data['clusters']
            for cluster in cart.clusters:
                price += float(str(cluster['price']))
                effective_price += float(str(cluster['effective_price']))
                total_quantity += float(str(cluster['quantity']))
            cart.price = price
            cart.effective_price = effective_price
            cart.total_quantity = total_quantity
            cart.save()
            serialized = CartSerializer(cart)
        if serialized:
            return Response(serialized.data, status=status.HTTP_201_CREATED)
        else:
            return Response(serialized.error_messages, status=status.HTTP_400_BAD_REQUEST)

    def get(self, requests, format=None):
        cart = Cart.objects.get(cart_id=requests.GET['cart_id'])
        serialized = CartSerializer(cart)
        if serialized:
            return Response(serialized.data, status=status.HTTP_200_OK)
        else:
            # @return
            return Response(serialized.error_messages, status=status.HTTP_400_BAD_REQUEST)


class StoreView(APIView):  # @class
    permission_classes = [AllowAny]  # list:
    """
     *Send Store data to Customer upon clicking item in ItemView or directly calling the store
     @param store_key,item_id
     @steps :: store-execution  
        @function ::: Store.objects.get(store_key) 
        @function ::: Item.objects.filter(Q(store_key))
        @return StoreSerializer ::dict
            {
            str: servei_id,store_key,name,link,image
            list: items [
                dict: item_packet {
                    str: item_id,name,measure,image
                    float: unit, price, effective_price,
                        dict: or str: variants 
                            str: parameter
                            list: variants[
                                str: value, image
                                float: price]
                }]}                     
    """

    def get(self, requests, format=None):  # @function
        data = requests.GET  # dict:
        store = Store.objects.get(store_key=data['store_key'])
        items = Item.objects.filter(store_key=data['store_key'])
        serialized = StoreViewSerializer(store, items).data()
        return Response(serialized, status=status.HTTP_200_OK)  # @return


class CityCodeExtractor(APIView):
    permission_classes = [AllowAny]
    """
      Mock Code Create untill th eabove class is rectified
      TODO: Add functionality to add multiple pin_codes at same time
    """

    def get(self, request, format=None):
        if 'cityCode' in request.GET.keys():
            cityCode = CityCode.objects.get(cityCode=request.GET['cityCode'])
            serial = CityCodeSerializer(cityCode)
            if serial and cityCode:
                return Response({'cityCode': serial.data}, status=status.HTTP_200_OK)
            else:
                return Response({}, status=status.HTTP_400_BAD_REQUEST)
        else:
            cityCode = CityCode.objects.filter(
                pin_codes__contains=[request.GET['pin_code']]).first()
            if cityCode:
                if 'all' in request.GET.keys():

                    return Response({'cityCode': {
                        "cityCode":cityCode.cityCode,
                        "city":cityCode.city,
                        "state":cityCode.state,
                        "pin_codes":cityCode.pin_codes
                    }}, status=status.HTTP_200_OK)
                else:
                    return Response({'cityCode': cityCode.cityCode, 'city': cityCode.city}, status=status.HTTP_200_OK)

            else:
                return Response({}, status=status.HTTP_400_BAD_REQUEST)


class DefaultItemPull(APIView):
    permission_classes = [AllowAny]

    def get(self, request, format=None):
        data = request.GET
        default_item = DefaultItems.objects.get(item_id=data['item_id'])
        prev_cat = Category.objects.get(cat_id=default_item.cat_id)
        items = [{"item_id": item.item_id, "prev_cat": item.prev_cat, "name": item.name, "images": item.images if hasattr(item, 'images') else '',
                  "store_key": item.store_key, "servei_id": item.servei_id, "price": item.price, "effective_price": item.effective_price,
                  "unit": item.unit, "measure": item.measure_param, "store_name": Store.objects.get(store_key=item.store_key).store_name} for item in Item.objects.filter(Q(cityCode=data['cityCode']) & Q(default_item_id=default_item.item_id))]
        if len(items) > 0:
            return Response({"items": items, "prev_name": default_item.name, "prev_image": default_item.image}, status=status.HTTP_200_OK)


class TemporaryOrderSystem(APIView):
    permission_classes = [AllowAny]
    """
     takes cart as dictionary which hve item_id as key and others such as {item_id, name, price, unit, quantity, measureParam, servei_id, store_key} as values
     customer_name,phone number and adddress is sent with subtotal, delivery and grandTotal
     Take the sequence and create order, notify my device
    """
    def post(self, request, format=None):
        data = json.loads(request.body)
        servei_cluster = {}
        servei_list =[]
        for value in data['cart'].values():
            if value['servei_id'] in servei_cluster.keys():
                servei_cluster[value['servei_id']]['items'].append(value)
                servei_cluster[value['servei_id']]['net_price'] += value['price']
                servei_cluster[value['servei_id']]['quantity'] += value['quantity']
            else:
                servei_list.append(value['servei_id'])
                servei_cluster[value['servei_id']] = {}
                servei_cluster[value['servei_id']]['items'] = [value]
                servei_cluster[value['servei_id']]['net_price'] = value['price']
                servei_cluster[value['servei_id']]['quantity'] = value['quantity']
        phone = data['customer_phone_number']
        if len(phone) > 10:
            size = len(phone) - 10
            phone = phone[size::1]

        order = Order.objects.create(order_id = order_id_generator(phone),servei_list = servei_list,
                                     servei_cluster = servei_cluster, customer_id=phone,
                                     customer_stack={"phone_number":phone,"name":data['customer_name'],"address":data['customer_address']},
                                     cityCode = 'UP53',net_price = data['grandTotal'],price=data['subTotal'],extra_charges={"delivery":25.0},

                                     )
        if order:
            return Response({"order_id":order.order_id},status=status.HTTP_201_CREATED)
        else:
            return Response({},status=status.HTTP_200_OK)
        




class CustomerLogin(APIView):
    permission_classes = [AllowAny]

    def get(self, request, format=None):
        customer = Customer.objects.filter(
            customer_id=request.GET['customer_id']).first()
        if customer:
            account = Account.objects.get(account_id=customer.customer_id)
            if account.check_password(request.GET['password']):
                token = Token.objects.get(user=account)
                return Response({'token': token.key}, status=status.HTTP_202_ACCEPTED)
            else:
                return Response({}, status=status.HTTP_401_UNAUTHORIZED)
        else:
            return Response({}, status=status.HTTP_403_FORBIDDEN)


class CustomerAddmission(APIView):
    permission_classes = [AllowAny]

    def post(self, request, format=None):
        data = request.POST
        customer = None
        created = False
        try:
            customer = Customer.objects.get(customer_id=data['customer_id'])
            return Response({'msg': 'Account Already exist'}, status=status.HTTP_403_FORBIDDEN)
        except:
            created = True
        if created:
            cityCode = CityCode.objects.filter(pin_codes__contains= [data['pin_code']])
            if cityCode:
                cityCode = cityCode.first()
                account = Account.objects.create(
                    account_id=data['customer_id'],
                    relation='009',
                    phone_number=data['customer_id'],
                    is_staff=False, is_superuser=False
                )
                account.set_password(data['password'])
                account.save()
                print(account.account_id)
                
                if account:
                    token = Token.objects.create(user=account)
                    customer = Customer.objects.create(customer_id=data['customer_id'])
                    coordinates = Coordinates.objects.get_or_create(
                        coordinates_id=account.account_id)[0]
                    for key in data.keys():
                        if key == 'gender':
                            customer.gender = request['gender']
                        elif key == 'address':
                            customer.address = request['address']
                        elif key == 'lat':
                            customer.coordinates_id = coordinates.coordinates_id
                        elif key == 'extras':
                            customer.extras = request['extras']
                        elif key == 'dob':
                            customer.dob = datetime.datetime.strptime(
                                request['dob'], '%d-%m-%Y')
                    customer.save()

                    return Response({'token': token.key, }, status=status.HTTP_202_ACCEPTED)
            else:
                return Response({}, status=status.HTTP_406_NOT_ACCEPTABLE)


class PickDropOrderView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, format=None):

        data = json.loads(request.body)
        phone = ''
        if len(data['sender_phone_number']) > 10:
            phone = data['sender_phone_number'][-1:-11:-1][::-1]
        elif len(data['sender_phone_number']) < 10 :
            return Response({},status=status.HTTP_206_PARTIAL_CONTENT)
        else:
            phone = data['sender_phone_number']


        order = PickDropOrder.objects.create(
            sender_phone_number=phone,
            sender_address = data['sender_address'],
            sender_name = data['sender_name'],
            receivers_stack = {
            "name":data['rec_name'],
            "phone_number":data['rec_phone_number'],
            "address":data['rec_address']
             },
             payee = data['payee']


            )
  
        if 'distance' in data.keys():
            order.distance = data['distance']
            order.cost = order.distance*40.0/2
        else:
            order.cost = 40.0
        order.save()
        return Response({'cost':order.cost,'rec_address':order.receivers_stack['address'],"rec_name":order.receivers_stack['name'],'rec_phone_number':order.receivers_stack['phone_number']},status=status.HTTP_201_CREATED)
    
    def get(self, request, format=None):
        data = request.GET
        if 'order_id' in data.keys():
            order = Order.objects.filter(order_id = data['order_id'])
            if order:
                order = order.first()
                serial = OrderItemSerializer(order)
                return Response({"items":serial.serialize(),
                                 "subTotal":order.price,
                                 "grandTotal":order.net_price,
                                 "delivery":25.0
                },status=status.HTTP_200_OK)
        else:
            porders = PickDropOrder.objects.filter(sender_phone_number=data['phone_number'])
            orders = Order.objects.filter(customer_id = data['phone_number'])
            if orders or porders:
                serial = PickDropOrderSerializer(porders,many=True)
                oerial = OrderCustomerSerializer(orders,many=True)            
                return Response({"p_orders":serial.data,"orders":oerial.data},status=status.HTTP_200_OK)
            else:
                return Response({"orders":[],"p_orders":[]},status=status.HTTP_200_OK)

