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



def variant_describe(item):
    """
      * Return string or dict
      * check if item.variants !={}:
        True :- return {parameter,variants:[value,image,price]}
        False :- 'default'
    """
    if item.variants:
        return {"parameter":item.variants['parameter'],"variants":[{"value":variant['value'],"price":variant['price'],"image":variant['image']} for variant in item.variants['variants']]}
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
        # print(data.keys())
        prevCat = None
        if 'only-head' in data.keys():
            categories = Category.objects.filter(Q(city_site__contains=[data['cityCode']]) & Q(cat_type = 'FC'))
            categories = [{"cat_id":category.cat_id,"prev_cat":category.prev_cat,"name":category.name,"image":category.image,"cat_type":category.cat_type,"delivery_type":category.delivery_type}for category in categories]
            
        else:
            categories = Category.objects.filter(Q(city_site__contains=[data['cityCode']]) & Q(prev_cat = data['cat_id']))
            prevCat = Category.objects.get(cat_id=data['cat_id'])
            categories = [{"cat_id":category.cat_id,"prev_cat":category.prev_cat,"name":category.name,"image":category.image,"cat_type":category.cat_type,"delivery_type":category.delivery_type}for category in categories]
            items = Item.objects.filter(Q(prev_cat=data['cat_id']) & Q(cityCode = data['cityCode']))
            if items:
                items = [{"item_id":item.item_id,"prev_cat":item.prev_cat,"name":item.name,"images":item.images if hasattr(item,'images') else '',
                         "store_key":item.store_key,"servei_id":item.servei_id,"price":item.price,"effective_price":item.effective_price,
                         "unit":item.unit,"measure":item.measure_param,"store_name":Store.objects.get(store_key=item.store_key).store_name} for item in items]
        if categories or items:
            
            return Response({"categories":categories,"items":items,"prev_name":prevCat.name if prevCat is not None else ""},status=status.HTTP_200_OK)
        else:
            return Response({"prev_name":prevCat.name},status=status.HTTP_200_OK)




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
            return Response(serialized.data,status=status.HTTP_201_CREATED)
        else:
            return Response(serialized.error_messages,status=status.HTTP_400_BAD_REQUEST)
    

    def get(self, requests, format=None):
        cart = Cart.objects.get(cart_id=requests.GET['cart_id'])
        serialized = CartSerializer(cart)
        if serialized:
            return Response(serialized.data,status=status.HTTP_200_OK)
        else:
            return Response(serialized.error_messages,status=status.HTTP_400_BAD_REQUEST) #@return





class StoreView(APIView): #@class
    permission_classes = [AllowAny] #list:
    """
     *Send Store data to Customer upon clicking item in ItemView or directly calling the store
     @param store_key
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

    def get(self, requests, format = None): #@function
        data = requests.GET  #dict:
        store = Store.objects.get(store_key = data['store_key'])
        items = Item.objects.filter(store_key = data['store_key'])
        serialized = StoreViewSerializer(store,items).data()
        return Response(serialized,status=status.HTTP_200_OK) #@return




class CityCodeExtractor(APIView):
    permission_classes = [AllowAny]
    """
      Mock Code Create untill th eabove class is rectified
      TODO: Add functionality to add multiple pin_codes at same time
    """


    def get(self,request,format=None):
        if 'cityCode' in request.GET.keys():
            cityCode = CityCode.objects.get(cityCode = request.GET['cityCode'])
            serial = CityCodeSerializer(cityCode)
            if serial and cityCode:
                return Response({'cityCode':serial.data},status=status.HTTP_200_OK)
            else:
                return Response({},status=status.HTTP_400_BAD_REQUEST)
        else:
            cityCode = CityCode.objects.filter(pin_codes__contains = [request.GET['pin_code']]).first()
            serial = CityCodeSerializer(cityCode)
            if cityCode:
                if 'all' in request.GET.keys():
                    
                    return Response({'cityCode':serial.data},status=status.HTTP_200_OK)
                else:
                    return Response({'cityCode':serial.data['cityCode'],'city':serial.data['city']},status=status.HTTP_200_OK)

            else:
                return Response({},status=status.HTTP_400_BAD_REQUEST)





