from django.shortcuts import render, HttpResponse
from rest_framework.authentication import TokenAuthentication
from django.template import Context, Template
from rest_framework.pagination import PageNumberPagination
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.views import APIView
from rest_framework.generics import GenericAPIView, ListAPIView
from .paginate import StandardResultSetPagination
from rest_framework.views import Response
from rest_framework import status
from .serializers import AccountCreationSerializer
from .serializers import *
from .models import *
import datetime
from secrets import token_urlsafe
from .serverOps import storeKeyGenerator, item_id_generator, OtpHemdal, dtime_diff, coord_id_generator
import json

# Create your views here.

# Account Creation

def position(coordinates_id: str):
    return Coordinates.objects.get(coordinates_id = coordinates_id).position

def set_positon(coord_id,data:dict):
    coord = Coordinates.objects.get(coordinates_id = coord_id)
    coord.position = Point(float(data['lat']),float(data['long']))
    coord.save()


class CheckConnection(APIView):
    permission_classes = [AllowAny]

    def get(self, request, format=None):
        return Response({},status=status.HTTP_200_OK)

class AccountAddmission(APIView):
    permission_classes = [AllowAny]

    def post(self, request, format=None):
        try:
            servei = Servei.objects.get(aadhar = request.POST['aadhar'])
            if servei is not None:
                return Response({'message':'Account Already exist'},status=status.HTTP_403_FORBIDDEN)
        except:
            account,city_code = Account().pour(request.POST)
            if account == -1:
                return Response({},status= status.HTTP_406_NOT_ACCEPTABLE )
            else:
                return Response({'token':Token.objects.get(user = account).key,'cityCode':city_code,'account_id':account.account_id,'phone_number':account.phone_number,'relation':account.relation},status=status.HTTP_202_ACCEPTED)


class ServeiLogin(APIView):
    permission_classes = [AllowAny]

    def post(self, request, format=None):
        try:
            servei = None
            account = None
            if 'aadhar' in request.POST.keys():
                servei = Servei.objects.get(aadhar = request.POST['aadhar'])
            elif 'servei_id' in request.POST.keys():
                servei = Servei.objects.get(servei_id = request.POST['servei_id'])
                if servei:
                    account = Account.objects.get(account_id=servei.servei_id)
                else:
                    account = None
                if account:
                    if account.check_password(request.POST['password']):
                        servei.online = True
                        servei.save()
                        token = Token.objects.get(user=account)
                        return Response({'token': token.key}, status=status.HTTP_202_ACCEPTED)
                    else:
                        return Response({}, status=status.HTTP_401_UNAUTHORIZED)
                else:
                    return Response({}, status=status.HTTP_404_NOT_FOUND)
        except:
            return Response({},status=status.HTTP_404_NOT_FOUND)

class ServeiPasswordReset(APIView):
    permission_classes = [AllowAny]

    # Get Phone Number for OTP Verification
    def get(self, request, format=None):
        if 'aadhar' in request.GET.keys():
            try:
                servei = Servei.objects.get(aadhar = request.GET['aadhar'])
                account = Account.objects.get(account_id = servei.servei_id)
                return Response({'account_id':account.account_id,'phone_number':account.phone_number},status=status.HTTP_200_OK)
            except:
                return Response({},status=status.HTTP_404_NOT_FOUND)
        elif 'servei_id' in request.GET.keys():
            try:
                account = Account.objects.get(account_id = request.GET['servei_id'])
                return Response({'account_id':account.account_id,'phone_number':account.phone_number},status=status.HTTP_200_OK)
            except:
                return Response({},status=status.HTTP_404_NOT_FOUND)
    
    def post(self, requets, format=None):
        try:
            account = Account.objects.get(account_id = requets.POST['account_id'])
            account.set_password(requets.POST['password'])
            account.save()
            token = Token.objects.get(user=account)
            return Response({'token':token.key},status =status.HTTP_202_ACCEPTED )
        except:
            return Response({},status=status.HTTP_404_NOT_FOUND)

class ServeiLogOut(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, format=None):
        servei = Servei.objects.get(servei_id = request.POST['servei_id'])
        servei.online = False
        servei.save()
        if 'store_key' in request.POST.keys():
            store = Store.objects.get(store_key = request.POST['store_key'])
            store.online = False
            store.save()
        return Response({},status=status.HTTP_200_OK)



# Servei Order History
class ServeiOrderHistory(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]    
    # permission_classes = [AllowAny]

    def get(self, request, format=None):
        try:
            orders = Order.objects.filter(servei_list__contains = request.GET['servei_id']).order_by('-date_of_creation','-time_of_creation')
             
            if len(orders) != 0:
                paginator = StandardResultSetPagination()
                data = []
                for order in paginator.paginate_queryset(order,request) :
                    servei_item_cluster = []
                    total_quantity = 0
                    servei_effective_price = 0.0
                    servei = order.servei_cluster[request.GET['servei_id']]
                    for item_id in servei['items']:
                        total_quantity += order.items_cluster[item_id]['quantity']
                        servei_effective_price += order.items_cluster[item_id]['effective_price']
                    data.append({'order_id': order.order_id, 'cluster': servei_item_cluster,
                                 'total_quantity': total_quantity, 'effective_price': servei_effective_price,'servei_status':servei['status'],
                                 'status':order.status,'order_type':order.order_type,'date_time':f"{datetime.date.strftime(order.date_of_creation)} {datetime.datetime.strftime(order.time_of_creation)}"})
                    if len(data) is not 0:
                        return Response({"orders":data},status=status.HTTP_200_OK)                    
                    else:
                        return Response({"orders":[]},status=status.HTTP_404_NOT_FOUND)
            else:
                return Response({"orders":[]},status=status.HTTP_404_NOT_FOUND)

        except:
            return Response({"orders":[]},status = status.HTTP_404_NOT_FOUND)
                




        
           


# Customer Login
class CustomerLogin(ObtainAuthToken):
    def post(self, request, format=None) -> Response:
        account = Account.objects.get(account_id=request.POST['account_id'])
        if account.check_password(request.POST['password']):
            token, created = Token.objects.get_or_create(user=account)[0]
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
                                         address=request.POST['address'], opening_time=datetime.datetime.strptime(request.POST['opening_time'],'%Y-%m-%d %H:%M:%S'),closing_time = datetime.datetime.strptime(request.POST['closing_time'],'%Y-%m-%d %H:%M:%S') , online=False, allowed=True,
                                         portfolio_updates=False, cityCode=servei.cityCode)

            servei.store_key = store.store_key
            servei.save()
            coords = Coordinates.objects.create(unique_id=coord_id_generator(store.cityCode, store.store_key),
                                 relation='904', reference_id=store.store_key, cityCode=store.cityCode, position=Point(request.POST['address']['coordinates']['latitude'], request.POST['coordinates']['longitude']))
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


# Item Alter 
class ItemAlterView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, format=None):
        item = Item.objects.get(item_id = request.POST['item_id'])
        if request.POST['action'] == 'del':
            item.delete()
            return Response({},status=status.HTTP_200_OK)
        else:
            if 'name' in request.POST.keys():
                item.name = request.POST['name']
            if 'price' in request.POST.keys():
                item.price = float(request.POST['price'])
            item.save()
            return Response({'item_id':item.item_id,'name':item.name,'price':item.price,'unit':item.unit,'measure':item.measure},status=status.HTTP_200_OK)
    
    
# CityCode Creator
# Need Fixing


class CityCodeCreate(APIView):
    permission_classes = [AllowAny]
    """
      Mock Code Create untill th eabove class is rectified
      TODO: Add functionality to add multiple pin_codes at same time
    """

    def post(self, request, format=None) :

        city = None
        try:
            city = CityCode.objects.get(cityCode = request.POST['cityCode'])
        except:
            city = CityCode.objects.create(cityCode = request.POST['cityCode'])
        if  not ',' in request.POST['pin_code']:
            if request.POST['pin_code'] not in city.pin_codes:
                city.pin_codes.append(request.POST['pin_code'])
                city.save()
        else:
            city.pin_codes = list(set(city.pin_codes + request.POST['pin_code'].split(',')))
            city.save()
        keys = request.POST.keys()
        for key in keys:
            if 'state' == key:
                city.state = request.POST['state']
            elif 'city' == key:
                city.city = request.POST['city']
        serial = CityCodeSerializer(city)
        if serial:
            return Response(serial.data, status=status.HTTP_200_OK)
        else:
            return Response(serial.errors,status=status.HTTP_404_NOT_FOUND)

    def get(self,request,format=None):
        if 'cityCode' in request.GET:
            cityCode = CityCode.objects.get(cityCode = request.GET['cityCode'])
            serial = CityCodeSerializer(cityCode)
            if serial:
                return Response({'cityCode':serial.data},status=status.HTTP_200_OK)
            else:
                return Response(serial.errors,status=status.HTTP_404_NOT_FOUND)
        else:
            cityCode = CityCode.objects.filter(pin_codes__contains = [request.GET['pin_code']]).first()
            serial = CityCodeSerializer(cityCode)
            if serial:
                if 'all' in request.GET.keys():
                    
                    return Response({'cityCode':serial.data},status=status.HTTP_200_OK)
                else:
                    return Response({'cityCode':serial.data['cityCode']},status=status.HTTP_200_OK)

            else:
                return Response(serial.errors,status=status.HTTP_404_NOT_FOUND)




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
  # remand now,yest,week,month
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


class ItemExtractor(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, format=None):
        items = Item.objects.filter(store_key=request.GET['store_key'])
        serialized = ItemSerializer(items,many=True)
        if serialized:
            return Response(serialized.data,status=status.HTTP_200_OK)
        else:
            return Response(serialized.errors)
    

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
        item.data['city'] = CityCode.objects.filter(cityCode=request.POST['cityCode']).first().city
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
            measure_param = MeasureParam.objects.get_or_create(pk='krispiforever@103904tilltheendoftheinfinity')[0]
            measure_param.units.append(request.POST['unit'])
            measure_param.measure_params.append(request.POST['measure_param'])
            measure_param.save()
            return Response({'message':"Done"},status=status.HTTP_201_CREATED)
        elif request.POST['unit'] == '' and request.POST['measure_param'] != '':
            measure_param = MeasureParam.objects.get_or_create(pk='krispiforever@103904tilltheendoftheinfinity')[0]
            measure_param.measure_params.append(request.POST['measure_param'])
            measure_param.save()
            return Response({'message':"Done"},status=status.HTTP_201_CREATED)
        elif request.POST['unit'] != '' and request.POST['measure_param'] == '':
            measure_param = MeasureParam.objects.get_or_create(pk='krispiforever@103904tilltheendoftheinfinity')[0]
            measure_param.units.append(request.POST['unit'])            
            measure_param.save()
            return Response({'message':"Done"},status=status.HTTP_201_CREATED)








class PortfolioManager(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, format=None):
        if request.GET['reference'] == 'servei':
            servei = Servei.objects.get(servei_id = request.GET['servei_id'])
            if servei:
                return Response({'email':servei.email,'phone_number':servei.phone_number,
                                 'address':[servei.address_line_1,servei.address_line_2,servei.city,servei.state,servei.pin_code,servei.country],
                                 'first_name':servei.first_name,'last_name':servei.last_name,'image':servei.image,
                                 'coordinates':{'lat':position(servei.coordinates_id)[0],'long':position(servei.coordinates_id)[1]}},status=status.HTTP_200_OK)
            else:
                return Response({'error':'Servei Does Not Exist'},status=status.HTTP_404_NOT_FOUND)
        elif request.GET['reference'] == 'store':
            store = Store.objects.get(store_key = request.GET['store_key'])
            if store:
                return Response({'name':store.name,'email':store.contacts['email'],'phone_number':store.contacts['phone_number'],
                                 'image':store.image,'address':store.address,'coordinates':{'lat':position(store.coordinates_id)[0],'long':position(store.coordinates_id)[1]}})
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
            set_positon(servei.coord_id,request.POST['coordinates'])
            servei.save()
            return Response({'email':servei.email,'phone_number':servei.phone_number,
                                 'address':[servei.address_line_1,servei.address_line_2,servei.city,servei.state,servei.pin_code,servei.country,servei.country_code],
                                 'first_name':servei.first_name,'last_name':servei.last_name,'image':servei.image,
                                 'coordinates':{'lat':position(servei.coordinates_id)[0],'long':position(servei.coordinates_id)[1]}},status=status.HTTP_200_OK)
        elif request.POST['reference'] == 'store':
            store = Store.objects.get(store_key=request.POST['store_key'])
            store.name = request.POST['name']
            store.contacts['email'] = request.POST['email']
            store.contacts['phone_number'] = request.POST['phone_number']
            store.address = request.POST['address']
            set_position(servei.coordinates_id,request.POST['position'])
            store.image = request.POST['image']
            return Response({'name':store.name,'email':store.contacts['email'],'phone_number':store.contacts['phone_number'],
                                     'image':store.image,'address':store.address,'coordinates':{'lat':position(store.coordinates_id)[0],'long':position(store.coordinates_id)[1]}})



class HeadCategories(APIView):
    permission_classes = [AllowAny]

    def get(self, request, format=None):
        categories = Category.objects.filter(city_site__contains = [request.GET['cityCode']],prev_cat='home')
        serial = HeadCategorySerializer(categories,many=True)
        if serial:
            return Response(serial.data,status=status.HTTP_200_OK)
        else:
            return Response(serial.error_messages,status=status.HTTP_400_BAD_REQUEST)



class ServeiAvailablity(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self,request, format=None):
        servei = Servei.objects.get(servei_id=request.POST['servei_id'])
        if int(request.POST['query']) == 1:
            return Response({'servei_id':servei.servei_id,'available': 1 if servei.online else 0},status=status.HTTP_200_OK)
        else:
            if servei:
                servei.online = True if int(request.POST['available']) == 1 else False
                servei.save()
                if servei.store != '':
                    store = Store.objects.get(store_key=servei.store)
                    if store:
                        store.online = True if int(request.POST['available']) == 1 else False
                        store.save()
                return Response({'servei_id':servei.servei_id,'available': 1 if servei.online else 0},status=status.HTTP_200_OK)
            else:
                return Response({'servei_id':servei.servei_id,'available':1 if servei.online else 0},status=status.HTTP_400_BAD_REQUEST)

    
    def get(self,request, format=None):
        servei = Servei.objects.get(servei_id=request.POST['servei_id'])
        if servei:
            return Response({'servei_id':servei.servei_id,'available':'true' if servei.online else 'false'},status=status.HTTP_200_OK)
        else:
            return Response({},status=status.HTTP_400_BAD_REQUEST)


class CheckUname(APIView):
    # authentication_classes = [TokenAuthentication]
    # permission_classes = [IsAuthenticated]
    permission_classes = [AllowAny]



    def get(self, request, format=None):
        store = Store.objects.filter(store_link = request.GET['uname'])
        if store:
            return Response({'allowed':'0'},status=status.HTTP_200_OK)
        else:
            return Response({'allowed':'1'},status=status.HTTP_200_OK)

class CheckSite(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self,request, format=None):
        stores = Store.objects.filter(store_key=request.GET['store_key'])
        if stores:
            store = stores[0]
            return Response({'uname':store.store_link,'online':'1' if store.store_site_online else '0','allowed':'0'},status=status.HTTP_200_OK)
        else:
            return Response({'allowed':'1','uname':'null','online':'null'},status=status.HTTP_200_OK)




class WebView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, requests, format=None):
        store = Store.objects.get(store_key = requests.POST['store_key'])
        store.store_link = requests.POST['uname']
        if requests.POST['images'] != '':
            store.store_images = requests.POST['images'].split('^')
        store.save()
        return Response({'uname':store.store_link},status=status.HTTP_200_OK)

