from rest_framework.authentication import TokenAuthentication
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.views import APIView
from rest_framework.views import Response
from rest_framework import status
from .serializers import AccountCreationSerializer
from .serializers import *
from .models import *
import datetime
from .tdmos import CREATED,DECLINED,WORKING,FINISHED,PENDING,SERVED,CREATE,CANCEL,FAILED
import time
from secrets import token_urlsafe
from .serverOps import storeKeyGenerator, item_id_generator, OtpHemdal, dtime_diff, coord_id_generator
import json
from django.db.models import Q

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
        argument = json.loads(request.body)
        try:
            servei = Servei.objects.get(aadhar = argument['aadhar'],relation='002')
            if servei is not None:
                return Response({'message':'Account Already exist'},status=status.HTTP_403_FORBIDDEN)
        except:
            account,city_code = Account().pour(argument)
            if account == -1:
                return Response({},status= status.HTTP_406_NOT_ACCEPTABLE )
            else:
                return Response({'token':Token.objects.get(user = account).key,'cityCode':city_code,'account_id':account.account_id,
                'phone_number':account.phone_number,'relation':account.relation},status=status.HTTP_202_ACCEPTED)


class ServeiLogin(APIView):
    permission_classes = [AllowAny]

    def post(self, request, format=None):
        try:
            # request.POST = json.loads(request.body)
            servei = None
            account = None
            if 'aadhar' in request.POST.keys():
                servei = Servei.objects.filter(aadhar = request.POST['aadhar']).first()
            elif 'servei_id' in request.POST.keys():
                servei = Servei.objects.filter(servei_id = request.POST['servei_id']).first()
            if servei:
                account = Account.objects.get(account_id=servei.servei_id)
            else:
                account = None
            if account:
                if account.check_password(request.POST['password']):
                    servei.online = True
                    servei.save()
                    token = Token.objects.get(user=account)
                    if not servei.store:
                        return Response({'servei_id':servei.servei_id,'token': token.key,'aadhar':servei.aadhar,'phone_number':servei.phone_number,'cityCode':servei.cityCode}, status=status.HTTP_202_ACCEPTED)
                    else:
                        return Response({'servei_id':servei.servei_id,'token': token.key,'aadhar':servei.aadhar,'phone_number':servei.phone_number,'cityCode':servei.cityCode,'store_key':servei.store}, status=status.HTTP_202_ACCEPTED)
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
            body = json.loads(requets.body)
            account = Account.objects.get(account_id = body['account_id'])
            account.set_password(body['password'])
            account.save()
            token = Token.objects.get(user=account)
            return Response({'token':token.key},status =status.HTTP_202_ACCEPTED )
        except:
            return Response({},status=status.HTTP_404_NOT_FOUND)

class ServeiLogOut(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, format=None):
        body = json.loads(request.body)
        servei = Servei.objects.get(servei_id = body['servei_id'])
        servei.online = False
        servei.save()
        if 'store_key' in request.POST.keys():
            store = Store.objects.get(store_key = body['store_key'])
            store.online = False
            store.save()
        return Response({},status=status.HTTP_200_OK)



# Create Store View
class CreateStoreView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, format=None):
        data = json.loads(request.body)
        if not Store.objects.filter(creator = data['servei_id']):
            # Servei
            servei = Servei.objects.get(servei_id=data['servei_id'])
            # Store Does not Exist
            store = Store.objects.create(store_key=storeKeyGenerator(servei.servei_id),
                                         store_name=data['store_name'], creators_profession=data['creators_profession'],
                                         creator=servei.servei_id, owners=[
                                             servei.servei_id], official_support=data['official_support'],
                                         store_category=data['store_category'], father_categories=data[
                                             'store_category'], contacts=data['contacts'],
                                         address=data['address'],
                                         opening_time= datetime.datetime.strptime(str(data['opening_time']),'%H:%M:%S'),
                                         closing_time = datetime.datetime.strptime(str(data['closing_time']),'%H:%M:%S') ,
                                         online=False, allowed=True,descriptions=data['descriptions'],
                                         cityCode=servei.cityCode)

            servei.store_key = store.store_key
            servei.save()
            if 'coordinates' in data['address'].keys():
                coords = Coordinates.objects.create(coordinates_id=coord_id_generator(store.cityCode, store.store_key),
                                 relation='904',
                                 position=Point(float(data['address']['coordinates']['latitude']),float(data['address']['coordinates']['longitude'])))
                store.coordinates_id = coords.coordinates_id
            store.save()

            # Creating Publytics
            publytics = Publytics.objects.filter(reference_id=store.store_key)
            if not publytics:
                publytics = Publytics.objects.create(pub_id = f'pub-{token_urlsafe(6)}',reference_id=store.store_key)           

            return Response({'store_key':store.store_key}, status=status.HTTP_201_CREATED)
        else:
            return Response({'error': 'Store does exist'}, status=status.HTTP_400_BAD_REQUEST)



# Item Alter 
class ItemAlterView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, format=None):
        body = json.loads(request.body)
        item = Item.objects.get(item_id = body['item_id'])
        if body['action'] == 'del':
            item.delete()
            return Response({},status=status.HTTP_200_OK)
        else:
            if 'name' in body.keys():
                item.name = body['name']
            if 'price' in body.keys():
                rate  = Rate.objects.filter(categories__contains = [item.prev_cat])
                if rate:
                    rate = rate.rate
                    item.price = float((body['price']) + (body['price'] * rate/100))
            item.save()
            serial = ItemSerializer(item)
            if serial and item:
                return Response(serial.data,status=status.HTTP_200_OK)
            else:
                return Response({},status=status.HTTP_400_BAD_REQUEST)
    
    
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
        # if Token.objects.filter(key=request.POST['token']):
        #     return Response({'error':'Un-authorised access'},status=status.HTTP_401_UNAUTHORIZED)
        try:
            city = CityCode.objects.get(cityCode = request.POST['cityCode'])
        except:
            city = CityCode.objects.create(cityCode = request.POST['cityCode'])
        if  not ',' in request.POST['pin_code']:
            if request.POST['pin_code'] not in city.pin_codes:
                city.pin_codes.append(request.POST['pin_code'])
                
        else:
            city.pin_codes = list(set(city.pin_codes + request.POST['pin_code'].split(',')))

        if 'state' in request.POST.keys():
                city.state = request.POST['state']
        if 'city' in request.POST.keys():
                city.city = request.POST['city']
        city.save()
        serial = CityCodeSerializer(city)
        if serial and city:
            return Response(serial.data, status=status.HTTP_200_OK)
        else:
            return Response({},status=status.HTTP_400_BAD_REQUEST)

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



class ItemExtractor(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, format=None):
        items = Item.objects.filter(store_key=request.GET['store_key'])
        serialized = ItemSerializer(items,many=True)
        if serialized and items:
            return Response(serialized.data,status=status.HTTP_200_OK)
        else:
            return Response({},status=status.HTTP_400_BAD_REQUEST)
    


class DefaultItemsWindow(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self,request, format=None):
        item = DefaultItems.objects.get_or_create(item_id = request.POST['item_id'])[0]
        isCatId = False
        isName = False
        isMeasureParam = False
        isUnit = False
        isPT = False
        isDT = False
        isImage = False
        isInsp = False
        isDes = False
        for key in request.POST.keys():
            if key == 'cat_id':
                isCatId = True
            elif key == 'name':
                isName = True
            elif key == 'measure_param':
                isMeasureParam = True
            elif key == 'unit':
                isUnit = True
            elif key == 'pick_type':
                isPT = True
            elif key == 'delivery_type':
                isDT = True
            elif key == 'image':
                isImage = True
            elif key == 'inspection':
                isInsp = True
            elif key == 'description':
                isDes = True
        if isCatId:
            item.cat_id = request.POST['cat_id']
        if isName:
            item.name = request.POST['name']
        if isMeasureParam:
            item.measure_param = request.POST['measure_param']
        if isUnit:
            item.unit = request.POST['unit']
        if isPT:
            item.pick_type = request.POST['pick_type']
        if isDT:
            item.delivery_type = request.POST['delivery_type']
        if isDes:
            item.description = request.POST['description']
        if isImage:
            item.image = request.POST['image']
        if isInsp:
            item.inspection = True if request.POST['inspection'] == '1' else False
        item.save()
        category = Category.objects.get(cat_id=request.POST['cat_id'])
        item.father_cat = category.father_cat
        item.save()
        category.default_items.append(item.item_id)
        category.save()
        serail = DefaultItemSerializer(item)

        if serail and item:         
            return Response(serail.data,status=status.HTTP_201_CREATED)
        else:
            return Response({},status=status.HTTP_400_BAD_REQUEST)
    
    def get(self, request ,format=None):
        item = DefaultItems.objects.get(item_id=request.GET['item_id'])
        item_serial = DefaultItemSerializer(item)
        if item_serial and item:
            return Response(item_serial.data,status=status.HTTP_200_OK)
        else:
            return Response({},status=status.HTTP_400_BAD_REQUEST)



class ItemCreateView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self,request, format=None):
        data = json.loads(request.body)
        item = Item.objects.get_or_create(item_id = item_id_generator(data['servei_id']))[0]
        item.name = data['name']
        item.store_key = data['store_key']
        item.servei_id = data['servei_id']
        item.allowed = True
        item.price = data['price']
        item.effective_price = data['effective_price']
        item.images = [image for image in data['images'] if image is not '@']
        item.description = data['description']
        item.measure_param = data['measureParam']
        item.unit = data['unit']
        category = Category.objects.get(cat_id=data['prev_cat'])
        #TODO: Item Inspection introduction in Category
        # item.inspection = False
        item.inspection = category.inspection
        item.delivery_type = category.delivery_type
        item.pick_type = category.pick_type
        item.prev_cat = data['prev_cat']
        item.father_cat = category.father_cat
        item.variants = data['variants']
        item.required_desc = data['requirments']
        item.cityCode = data['cityCode']
        if 'default_item_id' in data.keys():
            item.default_item_id = data['default_item_id']
        item.city = CityCode.objects.get(cityCode=data['cityCode']).city
        item.save()
        serial = ItemSerializer(item)
        if serial and item:
            return Response(serial.data,status=status.HTTP_200_OK)
        else:
            return Response({},status=status.HTTP_400_BAD_REQUEST)



class RateView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, format=None):
        rate = Rate.objects.filter(city_site__contains = [request.GET['cityCode']],categories__contains=[request.GET['category']])
        if rate:
            rate = rate.first()
            return Response({'rate':rate.rate},status=status.HTTP_200_OK)
        else:
            return Response({'error':'Error In Rate View'},status=status.HTTP_400_BAD_REQUEST)
    def post(self, requests, format=None):
        rate = None
        if 'categories' in requests.POST.keys():
            categories = requests.POST['categories'].split(',')
            rate = Rate.objects.get_or_create(categories = categories)[0]
        elif 'category' in requests.POST.keys():
            rate = Rate.objects.get_or_create(categories__contains = [requests.POST['category']])[0]
            if requests.POST['category'] not in rate.categories:
                rate.categories.append(requests.POST['category'])
            
        
        if 'city_site' in requests.POST.keys():
            city_site = [cityCode for cityCode in requests.POST['city_site'].split(',') if CityCode not in rate.city_site]
            rate.city_site = rate.city_site + city_site
        elif 'cityCode' in requests.POST.keys():
            rate.city_site.append(requests.POST['cityCode'])
        if 'rate' in requests.POST.keys():
            rate.rate = requests.POST['rate']
        rate.save()
        serial = RateSerializer(rate)
        if serial and rate:
            return Response(serial.data,status=status.HTTP_201_CREATED)
        else:
            return Response({},status=status.HTTP_404_NOT_FOUND)




class MeasureParamView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, format=None):
        measure_param = MeasureParam.objects.filter(pk='krispiforever@103904tilltheendoftheinfinity')
        if measure_param:
            measure_param = measure_param.first()
            return Response({"measure_params":measure_param.measure_params,"units":measure_param.units},status=status.HTTP_200_OK)
        else:
            return Response({'error':'Error In Rate View'},status=status.HTTP_400_BAD_REQUEST)
    
    def post(self, request, format=None):
        measure_param = MeasureParam.objects.get_or_create(pk='krispiforever@103904tilltheendoftheinfinity')[0]
        if 'unit' in request.POST.keys():
            measure_param.units.append(float(request.POST['unit']))
        elif 'units' in request.POST.keys():
            units = [float(unit) for unit in request.POST['units'].split(',') if float(unit) not in measure_param.units]

            measure_param.units = measure_param.units + units

        if 'measure_param' in request.POST.keys():
            measure_param.measure_params.append(request.POST['measure_param'])
        elif 'measure_params' in request.POST.keys():
            measureParams = [param for param in request.POST['measure_params'].split(',') if param not in measure_param.measure_params ]
            measure_param.measure_params = measure_param.measure_params + measureParams
        measure_param.save()
        serial = MeasureParamSerializer(measure_param)
        if serial and measure_param:
            return Response(serial.data,status=status.HTTP_201_CREATED)
        else:
            return Response({},status=status.HTTP_400_BAD_REQUEST)


class ServeiAvailablity(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self,request, format=None):
        body = json.loads(request.body)
        servei = Servei.objects.get(servei_id=body['servei_id'])
        if int(body['query']) == 1:
            return Response({'servei_id':servei.servei_id,'available': 1 if servei.online else 0},status=status.HTTP_200_OK)
        else:
            if servei:
                servei.online = True if int(body['available']) == 1 else False
                servei.save()
                if servei.store:
                    store = Store.objects.get(store_key=servei.store)
                    if store:
                        store.online = True if int(body['available']) == 1 else False
                        store.save()
                return Response({'servei_id':servei.servei_id,'available': 1 if servei.online else 0},status=status.HTTP_200_OK)
            else:
                return Response({'servei_id':servei.servei_id,'available':1 if servei.online else 0},status=status.HTTP_400_BAD_REQUEST)

    
    def get(self,request, format=None):

        servei = Servei.objects.get(servei_id=request.GET['servei_id'])
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
        body = json.loads(requests.body)
        store = Store.objects.get(store_key = body['store_key'])
        store.store_link = body['uname']
        if body['images'] is not '':
            store.store_images = body['images'].split('^')
        store.save()
        return Response({'uname':store.store_link},status=status.HTTP_200_OK)


class SuperUserAccount(APIView):
    permission_classes = [AllowAny]

    def post(self, requests, format=None):
        account = Account.objects.create_super_account(requests.POST['account_id'],requests.POST['password'],'001',requests.POST['phone_number'],)
        return Response({'account_id':account.account_id,"token":Token.objects.get(user=account).key},status=status.HTTP_200_OK)


class CategoryCreation(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, requests, format=None):
        data = requests.POST
        isFatherCat = False
        isCitySite = False
        isRequiredDesc = False
        isDeliveryType = False
        isPickType = False
        isRadiod = False
        isReturnable = False
        isImage = False
        isCatType = False

        for key in data.keys():
            if key == 'image':
                isImage = True
            elif key == 'father_cat':
                isFatherCat = True
            elif key == 'cat_type':
                isCatType = True
            elif key == 'city_site':
                isCitySite = True
            elif key == 'required_desc':
                isRequiredDesc = True
            elif key == 'delivery_type':
                isDeliveryType = True
            elif key == 'pick_type':
                isPickType = True
            elif key == 'radiod':
                isRadiod = True
            elif key == 'returnable':
                isReturnable = True

        category,created = Category.objects.get_or_create(cat_id = ''.join([token_urlsafe(4),'_CAT_',datetime.datetime.utcnow().strftime('%d%m%Y-%H%M%S')]))

        category.name = data['name']
        category.prev_cat = data['prev_cat']
        prev_cat = Category.objects.get(cat_id = data['prev_cat'])
        if isImage:
            category.image = data['image']
        if isFatherCat:
            category.father_cat = data['father_cat']
        else:
            category.father_cat = prev_cat.father_cat
        if isCatType:
            category.cat_type = data['cat_type']
        if isCitySite:
            if ',' in data['city_site']:
                category.city_site = category.city_site + data['city_site'].split(',')
            else:
                category.city_site.append(data['city_site'])
        if isRequiredDesc:
            if ',' in data['required_desc']:
                category.required_desc = category.required_desc + data['required_desc'].split(',')
            else:
                category.required_desc.append(data['required_desc'])
        if isDeliveryType:
            category.delivery_type = data['delivery_type']
        if isPickType:
            category.pick_type = data['pick_type']
        if isRadiod:
            category.radiod = True if data['radiod'] == '1' else False
        if isReturnable:
            category.returnable = True if data['radiod'] == '1' else False
        category.save()
        prev_cat.next_cat.append(category.cat_id)
        prev_cat.save()
        return Response({'cat_id':category.cat_id,'city_site':category.city_site,'father_cat':category.father_cat,'prev_cat':category.prev_cat},status=status.HTTP_200_OK)

        


class CheckStore(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, requests,format=None):
        store = Store.objects.filter(creator = requests.GET['servei_id'])
        if store:
            return Response({'store_key':store.first().store_key},status=status.HTTP_200_OK)
        else:
            return Response({},status=status.HTTP_400_BAD_REQUEST)

class VerifyToken(APIView):
    permission_classes = [AllowAny]

    def post(self,request, format=None):
        """
          To check if token exist or not
          if exist then return true and false if doesn't
        """
        data = json.loads(request.body)
        token = Token.objects.filter(key=data['token'])
        if token:
            return Response({"exist":1},status=status.HTTP_200_OK)
        else:
            return Response({"exist":0},status=status.HTTP_200_OK)

class Analytics(APIView):
    """
      Send View On Site this month, Total Views 
      Orders this month
      Revenue will pe paid after every month completion and revenue will be update then
    """
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, format=None):
        data = request.GET
        publytics = Publytics.objects.filter(reference_id=data['store_key'])
        widthrawl = False
        servei_id = data['servei_id']
        orders = Order.objects.filter(servei_list__contains=[servei_id])
        order_month = orders.filter(Q(date_time_creation__month = timezone.now().month) & Q(date_time_creation__year = timezone.now().year))
        price_month = 0.0
        price_total = 0.0
        for order in orders:
            if order.final_servei_cluster[servei_id]['status'] == SERVED:
                price_month += order.final_servei_cluster[servei_id]['price']
        for order in order_month:
            if order.final_servei_cluster[servei_id]['status'] == SERVED:
                price_month += order.final_servei_cluster[servei_id]['price']
        failed_orders = orders.filter(~Q(final_servei_cluster__has_key=servei_id) | Q(final_servei_cluster__contains = {f'{servei_id}':{
            "status":FAILED
        }}))
        success_orders = orders.filter(Q(final_servei_cluster__contains={f'{servei_id}':{
           "status":SERVED
        }}))
        all_views = sum(publytics.views_log.values())
        this_month_order = len(orders)
        if all_views > 1000 and this_month_order >= 2:
            widthrawl = True
        if publytics:
            publytics = publytics.first()
            return Response({
                "store_key":data['store_key'],
                "withdrawl":1 if widthrawl else 0,
                "views":{
                    "this_month":list(publytics.views_log.values())[-1],
                    "total_views":all_views
                },
                "orders":{
                    "total_orders":this_month_order,
                    "this_month":len(order_month),
                    "failed_orders":len(failed_orders),
                    "success_orders":len(success_orders)
                },
                "revenue":{
                    "total":price_total,
                    "this_month":price_month
                }
            },status=status.HTTP_200_OK)
        else:
            print(data['store_key'])
            return Response({
                "store_key":data['store_key'],
                "withdrawl":1 if widthrawl else 0,
                "views":{
                    "this_month":0,
                    "total_views":0.0
                },
                "orders":{
                    "total_orders":0,
                    "this_month":0,
                    "failed_orders":0,
                    "success_orders":0
                },
                "revenue":{
                    "total":0,
                    "this_month":0
                }
            },status=status.HTTP_200_OK)
            
class OrderHistory(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, format=None):
        data = request.GET 
        orders = Order.objects.filter(servei_list__contains = [data['servei_id']]).order_by('-date_time_creation')
        if orders:
            returning_order = []
            for order in orders:
                returning_order.append({
                    "order_id":order.order_id,
                    "payment_COD":order.payment_COD,
                    "payment_complete":order.payment_complete,
                    "clusters":order.final_servei_cluster[data['servei_id']] if data['servei_id'] in order.final_servei_cluster.keys() else order.servei_cluster[data['servei_id']],
                    "delivery_required":1 if order.delivery_required else 0,
                }),
            return Response({"orders":returning_order},status=status.HTTP_200_OK)
        else:
            return Response({"orders":[]},status=status.HTTP_200_OK)


class CustomerReview(APIView):
    permission_classes = [AllowAny]

    def post(self, request, format=None):
        data = json.loads(request.body)
        reviews = CustomerReviewModel.objects.filter(servei_id__contains = [data['servei_id']]).order_by('-date_time')
        if reviews:
            comments = CustomerReviewSerializer(reviews.filter(Q(review_type = 'COMMENT')),many=True)
            complaints = CustomerReviewSerializer(reviews.filter(Q(review_type = 'COMPLAINT')),many=True)
            reviews = CustomerReviewSerializer(reviews.filter(Q(review_type = 'REVIEW')),many=True)
            if comments and complaints and reviews:
                return Response({
                    "comments":comments,
                    "complaints":complaints,
                    "reviews":reviews
                },status=status.HTTP_200_OK)
            else:
                return Response({
                    "comments":[],
                    "complaints":[],
                    "reviews":[]
                },status=status.HTTP_200_OK)

