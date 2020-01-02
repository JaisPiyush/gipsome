from django.shortcuts import render
from rest_framework.authentication import TokenAuthentication
from rest_framework.pagination import PageNumberPagination
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.views import APIView
from rest_framework.generics import GenericAPIView,ListAPIView
from rest_framework.views import Response
from rest_framework import status
from .serializers import AccountCreationSerializer
from .serializers import *
from .models import *
import datetime
from secrets import token_urlsafe
from .serverOps import storeKeyGenerator, item_id_generator, OtpHemdal, dtime_diff, coord_id_generator

# Create your views here.

# Account Creation

# Re construction required


class AccountAddmission(APIView):
    permission_classes = [AllowAny]

    def post(self, request, format=None):
        if (request.POST['phone_number'] != '' or request.POST['phone_number'] is not None) and (request.POST['phone_token'] != '' or request.POST['phone_token'] is not None) and (request.POST['password'] != '')and (request.POST['relation'] != ''):
            if PhoneToken.objects.get(token=request.POST['phone_token']):
                account = Account().pour(request.POST)
                token = Token.objects.create(user=account)
                serial = AccountCreationSerializer(account)
                return Response({'account': serial.data, 'token': token.key}, status=status.HTTP_201_CREATED)
            else:
                return Response({'error': 'Phone is not Authorised'}, status=status.HTTP_401_UNAUTHORIZED)
        else:
            return Response({'error', 'Un-Authorized'}, status=status.HTTP_401_UNAUTHORIZED)


# Customer Login
class CustomerLogin(ObtainAuthToken):
    def post(self, request, format=None):
        account = Account.objects.get(account_id=request.POST['account_id'])
        if account.check_password(request.POST['password']):
            token, created = Token.objects.get_or_create(user=account)
            return Response({'account_id': account.account_id, 'token': token.key}, status=status.HTTP_202_ACCEPTED)
        else:
            return Response({'error': 'Un-Authorised'}, status=status.HTTP_401_UNAUTHORIZED)


# Create Store View
class CreateStoreView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, format=None):
        if not Store.objects.get(store_key=storeKeyGenerator(request.POST['servei_id'])):
            # Servei
            servei = Servei.objects.get(servei_id=request.POST['servei_id'])
            # Store Does not Exist
            store = Store.objects.create(store_key=storeKeyGenerator(servei.servei_id),
                                         store_name=request.POST['store_name'], creators_profession=request.POST['creators_profession'],
                                         creator=servei.servei_id, owners=[
                                             servei.servei_id], official_support=request.POST['official_support'],
                                         store_category=request.POST['store_category'], father_categories=request.POST[
                                             'father_categories'], contacts=request.POST['contacts'],
                                         address=request.POST['address'], opening_time=request.POST['opening_time'], closing_time=request.POST['closing_time'], online=False, allowed=True,
                                         portfolio_updates=False, cityCode=servei.cityCode)

            servei.store_key = store.store_key
            servei.save()
            coords = Coordinates(unique_id=coord_id_generator(store.cityCode, store.store_key),
                                 relation='904', reference_id=store.store_key, cityCode=store.cityCode)
            store.coordinates = coords.unique_id
            store.save()
            store_serial = StoreSerializer(store)

            return Response(store_serial.data, status=status.HTTP_201_CREATED)
        else:
            return Response({'error': 'Store does exist'}, status=status.HTTP_400_BAD_REQUEST)


# Create Item
class ItemCreateView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, format=None):
        request.POST['item_id'] = item_id_generator(request.POST['servei_id'])
        item_serial = ItemSerializer(data=request.data)
        if item_serial.is_valid():
            item_serial.save()
            store = Store.objects.get(store_key=item_serial.data['store_key'])
            store.product_line.append(item_serial.data['item_id'])
            store.save()
            return Response(item_serial.data, status=status.HTTP_201_CREATED)
        else:
            return Response(item_serial.errors, status=status.HTTP_400_BAD_REQUEST)


# OTp Creator
class OtpCreator(APIView):
    permission_classes = [AllowAny]

    def get(self, request, format=None):
        if request.GET['phone_number'] is not None and request.GET['otp_cred'] == '' and request.GET['data'] == '':
            # send sms structure
            data = OtpHemdal().generate()
            log = OTPLog.objects.create(
                otp_cred=request.GET['phone_number'] + data, data=data, phone_number=request.GET['phone_number'])
            return Response({'data': log.data, 'otp_cred': log.otp_cred, 'created': log.created, 'closed': log.closed}, status=status.HTTP_201_CREATED)
        elif request.GET['otp_cred'] != '' and request.GET['data'] == '':
            log = OTPLog.objects.get(otp_cred=request.GET['otp_cred'])
            return Response({'data': log.data, 'otp_cred': log.otp_cred, 'created': log.created, 'closed': log.closed}, status=status.HTTP_302_FOUND)
        elif request.GET['otp_cred'] != '' and request.GET['data'] != '':
            log = OTPLog.objects.get(otp_cred=request.GET['otp_cred'])
            # 6 minutes for verification
            now = datetime.datetime.now(datetime.timezone.utc)
            if dtime_diff(now, log.created) <= 6*60:
                log.closed = True
                log.closing = datetime.datetime.now(datetime.timezone.utc)
                log.save()
                token = PhoneToken.objects.create(
                    token=token_urlsafe(16), phone_number=log.phone_number)
                return Response({'phone_number': log.phone_number, 'token': token.token}, status=status.HTTP_202_ACCEPTED)
            elif dtime_diff(now, log.created) > 6*60:
                return Response({"phone_number": log.phone_number, 'error': 'TimeOut'}, status=status.HTTP_408_REQUEST_TIMEOUT)

# CityCode Creator
# Need Fixing


class CityCodeCreator(APIView):
    permission_classes = [AllowAny]

    def post(self, request, format=None):
        if not CityCode.objects.get(cityCode=request.POST['cityCode']):
            city = CityCode.objects.create(
                city=request.POST['city'], state=request.POST['state'], cityCode=request.POST['cityCode'], pin_codes=[request.POST['pin_code']])
            serial_code = CityCodeSerializer()
            if serial_code.is_valid():
                serial_code.save()
                return Response(serial_code.data, status=status.HTTP_201_CREATED)
        elif CityCode.objects.get(cityCode=CityManager().get_code(pin_code=request.POST['pin_code'])):
            city = CityCode.objects.get(cityCode=request.POST['cityCode'])
            city.pin_codes = city.pin_codes.append(request.POST['pin_code'])
            city.save()
            return Response({'cityCode': city.cityCode, 'pin_codes': city.pin_codes})


# Portfolio Import
# Only Name and phone_number and address
class ServeiPortifolio(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, format=None):
        servei = Servei.objets.get(servei_id=request.POST['servei_id'])
        if servei:
            return Response({'servei_id': servei.servei_id, 'name': servei.first_name + ' '+servei.last_name, 'image': servei.image}, status=status.HTTP_302_FOUND)
        else:
            return Response({'error': 'Does not exist'})


# Analytics
"""
  Return total order, total cash, net income
  Now, yesterday, last week(last 7 days),untill (uptil now),all means fetch all
  #remand now,yest,week,month
"""


class Analytics(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, format=None):
        if request.GET['remand']:
            if request.GET['remand'] == 'now':
                orders = Order.objects.filter(serveis__contains=[
                    request.GET['servei_id']], store_cluster__contains=[request.GET['store_key']], date_of_creation=datetime.date.today()).order_by('-time_of_creation')

            elif request.GET['remand'] == 'yest':
                orders = Order.objects.filter(serveis__contains=[request.GET['servei_id']], store_cluster__contains=[
                                              request.GET['store_key']], date_of_creation=datetime.date.today()-datetime.timedelta(days=1)).order_by('-time_of_creation')
            elif request.GET['remand'] == 'week':
                orders = Order.objects.filter(serveis__contains=[request.GET['servei_id']], store_cluster__contains=[request.GET['store_key']], date_of_creation__gte=datetime.date.today(
                                              )-datetime.timedelta(days=7), date_of_creation__lte=datetime.datetime.today()).order_by('-date_of_creation')
            elif request.GET['remand'] == 'untill':
                orders = Order.objects.filter(serveis__contains=[request.GET['servei_id']], store_cluster__contains=[request.GET['store_key']],
                                              date_of_creation__lte=datetime.datetime.today()).order_by('-date_of_creation')
            sell = 0
            cash = 0.0
            for order in orders:
                # extract all final items sold by servei
                servei_sellout = order.final_pair[request.GET['servei_id']]
                for item in servei_sellout:
                    # Returns [servei_id,price,eff_price,amount]
                    packet = order.items_data[item]
                    cash += packet[-2] * packet[1]
                    sell += packet[-1]
        
            return Response({'servei_id': request.GET['servei_id'], 'cashin': cash, 'sell': sell, 'remand': request.GET['remand']}, status=status.HTTP_200_OK)
        else:
            return Response({}, status=status.HTTP_400_BAD_REQUEST)


class ItemExtractor(GenericAPIView):
    permission_classes = [PageNumberPagination]
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = ItemSerializer
    queryset = Item.objects.all()

    def list(self, request, store_key):
        queryset = Item.objects.filter(store_key = store_key)
        serialized = ItemSerializer(queryset,many=True)
        return Response(serialized.data,status=status.HTTP_200_OK)
    
