from django.shortcuts import render
from rest_framework.authentication import TokenAuthentication
from rest_framework.pagination import PageNumberPagination
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.views import APIView
from rest_framework.generics import GenericAPIView, ListAPIView
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
            coords = Coordinates.objects.create(unique_id=coord_id_generator(store.cityCode, store.store_key),
                                 relation='904', reference_id=store.store_key, cityCode=store.cityCode,position = Point(request.POST['address']['coordinates']['latitude'],request.POST['coordinates']['longitude']))
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


class CityCodeCreate(APIView):
    permission_classes = [AllowAny]
    """
      Mock Code Create untill th eabove class is rectified
      TODO: Add functionality to add multiple pin_codes at same time
    """

    def post(self, request, format=None):
        if request.POST['cityCode'] and request.POST['pin_code'] and not CityCode.objects.get(cityCode=request.POST['cityCode']):
            city = CityCode.objects.create(
                state=request.POST['state'], city=request.POST['city'], cityCode=request.POST['cityCode'], pin_code=[request.POST['pin_code']])
            return Response({'cityCode': city.cityCode}, status=status.HTTP_201_CREATED)
        elif request.POST['cityCode'] and request.POST['pin_code'] and CityCode.objects.get(cityCode=request.POST['cityCode']):
            city = CityCode.objects.get(cityCode=request.POST['cityCode'])
            if request.POST['pin_code'] not in city.pin_codes:
                city.pin_codes.append(request.POST['pin_code'])
                city.save()

            city_serial = CityCodeSerializer(city)
            return Response(city_serial.data, status=status.HTTP_400_BAD_REQUEST)


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
        queryset = Item.objects.filter(store_key=store_key)
        serialized = ItemSerializer(queryset, many=True)
        return Response(serialized.data, status=status.HTTP_200_OK)


class StoreTeamWindow(APIView):
    # authentication_classes = [TokenAuthentication]
    permission_classes = [AllowAny]

    def get(self, request, format=None):
        if Store.objects.get(store_key=request.GET['store_key']):
            store = Store.objects.get(store_key=request.GET['store_key'])
            team = []
            for servei in store.employees:
                team.append(StoreTeamSerializer(Servei.objects.get(servei_id=servei)))
            if team is not []:
                return Response(team, status=status.HTTP_200_OK)
            else:
                return Response({}, status=status.HTTP_404_NOT_FOUND)
        else:
            return Response({'error':"No Store Found"},status=status.HTTP_404_NOT_FOUND)


class CategorySelection(APIView):
    
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, format=None):
        categories = Category.objects.filter(city_site__contains = [request.GET['cityCode']])
        passed_categories = []
        for category in categories:
            if category.prev_cat == 'home' or category.radiod:
                passed_categories.append(category)
        category_serial = CategorySerializer(passed_categories,many=True)
        if category_serial.is_valid():
            return Response(category_serial.data,status=status.HTTP_200_OK)
        else:
            return Response(category_serial.errors,status=status.HTTP_400_BAD_REQUEST)


class DefaultItemsWindow(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self,request, format=None):
        item = DefaultItemSerializer(data=request.POST)
        item.data['item_id'] = item_id_generator(token_urlsafe(8))
        if item.is_valid():
            
            category = Category.objects.get(cat_id=request.POST['cat_id'])
            item.father_cat = category.father_cat
            item.save()
            category.default_items.append({'item_id':item.data['item_id'],'name':item.data['name']})
            category.save()
            return Response(item.data,status=status.HTTP_201_CREATED)
        else:
            return Response(item.errors,status=status.HTTP_400_BAD_REQUEST)
    
    def get(self, request ,format=None):
        item = DefaultItems.objects.get(item_id=request.GET['item_id'])
        item_serial = DefaultItemSerializer(item)
        if item_serial.is_valid():
            return Response(item_serial.data,status=status.HTTP_200_OK)
        else:
            return Response(item_serial.errors,status=status.HTTP_400_BAD_REQUEST)



class ItemCreateView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self,request, format=None):
        item = ItemSerializer(data=request.POST)
        item.data['item_id'] = item_id_generator(request.POST['servei_id'])
        category = Category.objects.get(cat_id=request.POST['prev_cat'])
        item.data['delivery_type'] = category.delivery_type
        item.data['city'] = CityCode.objects.filter(cityCode=request.POST['cityCode']).city
        item.data['father_cat'] = category.father_cat
        item.data['inspection'] = category.inspection
        item.data['allowed'] = True
        item.data['ratings'] = 0.0
        item.data['pick_type'] = category.pick_type
        if item.is_valid():
            item.save()
            return Response(item.data,status=status.HTTP_200_OK)
        else:
            return Response(item_serial.errors,status=status.HTTP_400_BAD_REQUEST)



class RateView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, format=None):
        rate = Rate.object.filter(city_site__contains = [request.GET['cityCode']],categories__contains=[request.GET['category']])
        if rate:
            return Response({'rate':rate.rate},status=status.HTTP_200_OK)
        else:
            return Response({'error':'Error In Rate View'},status=status.HTTP_400_BAD_REQUEST)

class MeasureParamView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, format=None):
        measure_param = MeasureParam.objects.get(pk='krispiforever@103904tilltheendoftheinfinity')
        if measure_param:
            return Response({"measure_params":measure_param.measure_params,"units":measure_param.units},status=status.HTTP_200_OK)
        else:
            return Response({'error':'Error In Rate View'},status=status.HTTP_400_BAD_REQUEST)
    
    def post(self, request, format=None):
        if request.POST['unit'] != '' and request.POST['measure_param'] !='':
            measure_param = MeasureParam.objects.get_or_create(pk='krispiforever@103904tilltheendoftheinfinity')
            measure_param.units.append(request.POST['unit'])
            measure_param.measure_params.append(request.POST['measure_param'])
            measure_param.save()
            return Response({'message':"Done"},status=status.HTTP_201_CREATED)
        elif request.POST['unit'] == '' and request.POST['measure_param'] != '':
            measure_param = MeasureParam.objects.get_or_create(pk='krispiforever@103904tilltheendoftheinfinity')
            measure_param.measure_params.append(request.POST['measure_param'])
            measure_param.save()
            return Response({'message':"Done"},status=status.HTTP_201_CREATED)
        elif request.POST['unit'] != '' and request.POST['measure_param'] == '':
            measure_param = MeasureParam.objects.get_or_create(pk='krispiforever@103904tilltheendoftheinfinity')
            measure_param.units.append(request.POST['unit'])            
            measure_param.save()
            return Response({'message':"Done"},status=status.HTTP_201_CREATED)






# Future Production
# class HeadingView(APIView):
#     authentication_classes = [TokenAuthentication]
#     permission_classes = [IsAuthenticated]

#     def get(self, request, format=None):
#         store = Store.objects.filter(store_key = request.GET['store_key'])
#         headings = store.headings
#         return Response({'headings':headings},status=status.HTTP_200_OK)
    
#     def post(self, request, format=None):
#         store = Store.objects.filter(store_key=request.POST['store_key'])
#         store.headings.append(request.POST['heading'])
#         store.save()
#         return Response({'headings':store.heading},status=status.HTTP_200_OK)

class PortfolioManager(APIView):
    authentication_classes = [TokenAuthentication]
    parser_classes = [IsAuthenticated]

    def get(self, request, format=None):
        if request.GET['reference'] == 'servei':
            servei = Servei.objects.get(servei_id = request.GET['servei_id'])
            if servei:
                return Response({'email':servei.email,'phone_number':servei.phone_number,
                                 'address':[servei.address_line_1,servei.address_line_2,servei.city,servei.state,servei.pin_code,servei.country],
                                 'first_name':servei.first_name,'last_name':servei.last_name,'image':servei.image,
                                 'coordinates':servei.coordinates.position},status=status.HTTP_200_OK)
            else:
                return Response({'error':'Servei Does Not Exist'},status=status.HTTP_404_NOT_FOUND)
        elif request.GET['reference'] == 'store':
            store = Store.objects.get(store_key = request.GET['store_key'])
            if store:
                return Response({'name':store.name,'email':store.contacts['email'],'phone_number':store.contacts['phone_number'],
                                 'image':store.image,'address':store.address,'coordinates':store.coordinates.position})
            else:
                return Response({'error':'Store Does Not Exist'},status=status.HTTP_404_NOT_FOUND)
    
    def post(self, request, format=None):
        if request.POST['reference'] == 'servei':
            servei = Servei.objects.get(servei_id=request.POST['servei_id'])
            servei.first_name = request.POST['first_name']
            servei.last_name = request.POST['last_name']
            servei.email = request.POST['email']
            servei.phone_number = request.POST['phone_number']
            servei.address_line_1 = request.POST['address']['address_line_1']
            servei.address_line_2 = request.POST['address']['address_line_2']
            servei.city = request.POST['address']['city']
            servei.state = request.POST['address']['state']
            servei.pin_code = request.POST['address']['pin_code']
            servei.country = request.POST['address']['country']
            servei.image = request.POST['image']
            servei.coordinates.position = request.POST['coordinates']
            servei.save()
            return Response({'email':servei.email,'phone_number':servei.phone_number,
                                 'address':[servei.address_line_1,servei.address_line_2,servei.city,servei.state,servei.pin_code,servei.country,servei.country_code],
                                 'first_name':servei.first_name,'last_name':servei.last_name,'image':servei.image,
                                 'coordinates':{'lat':servei.coordinates.position.x,'long':servei.coordinates.position.y}},status=status.HTTP_200_OK)
        elif request.POST['reference'] == 'store':
            store = Store.objects.get(store_key=request.POST['store_key'])
            store.name = request.POST['name']
            store.contacts['email'] = request.POST['email']
            store.contacts['phone_number'] = request.POST['phone_number']
            store.address = request.POST['address']
            store.coordinates.position = request.POST['position']
            store.image = request.POST['image']
            return Response({'name':store.name,'email':store.contacts['email'],'phone_number':store.contacts['phone_number'],
                                     'image':store.image,'address':store.address,'coordinates':{'lat':servei.coordinates.position.x,'long':servei.coordinates.position.y}})



class HeadCategories(APIView):
    permission_classes = [AllowAny]

    def get(self, request, format=None):
        categories = Category.objects.filter(city_site__contains = [request.GET['cityCode']],prev_cat='home')
        serial = HeadCategorySerializer(categories,many=True)
        if serial:
            return Response(serial.data,status=status.HTTP_200_OK)
        else:
            return Response(serial.error_messages,status=status.HTTP_400_BAD_REQUEST)


