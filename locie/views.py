import datetime
import json
from secrets import token_urlsafe

from django.db.models import Q
from rest_framework import status
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.views import APIView
from rest_framework.views import Response
from .tdmos.tdmos import FINISHED, FAILED,WORKING,COMPLETED,PENDING
from .gadgets.serverOps import storeKeyGenerator, item_id_generator, ist_datetime
from .models import *
from .serializers import *
from .tdmos.tdmos import SERVED, FAILED


# Create your views here.

# Account Creation

def store_creation(servei: Servei, data):
    store = Store.objects.create(
        store_key = storeKeyGenerator(servei.servei_id),
        store_name=data['store_name'], creator=servei.servei_id,
        coordinates=Point(data['coordinates']['lat'], data['coordinates']['long']),
        contacts={"emails": [data['email']], "phone_numbers": [data['phone_number']]},
        address=data['address'], cityCode=data['cityCode'],
        opening_time=datetime.datetime.strptime(data['opening_time'], '%H:%M:%S'),
        closing_time=datetime.datetime.strptime(data['closing_time'], '%H:%M:%S'), online=True, allowed=True,
    )
    image = None
    description = None
    for key in data.keys():
        if key == "store_image":
            image = data['store_image']
            store.image = image
            if description and image:
                break
        elif key == "description":
            description = data['description']
            store.descriptions = description
            if description and image:
                break



    store.save()
    return store


def servei_creation(account:Account, data):
    servei = Servei.objects.create(
        servei_id=account.account_id, account=account, cityCode=data['cityCode'],
        first_name=data['first_name'], last_name=data['last_name'], phone_number=data['phone_number'],
        email=data['email'], gender=data['gender'], image=data['image'],
        coordinates=Point(data['coordinates']['lat'], data['coordinates']['long']),
        aadhar=data['aadhar'],allowed=True,
        online=True, address=data['address'], pin_code=data['pin_code']
    )
    return servei


class CheckConnection(APIView):
    permission_classes = [AllowAny]

    def get(self, request, format=None):
        return Response({}, status=status.HTTP_200_OK)


class AccountAdmission(APIView):
    permission_classes = [AllowAny]

    def post(self, request, format=None):
        data = json.loads(request.body)
        servei = Servei.objects.filter(aadhar=data['aadhar'])
        if servei:
            # Servei Exist Now Checking Store
            print('Trace When Servei Exist but not Store')
            servei = servei.first()
            account = Account.objects.get(account_id=servei.servei_id)
            store = Store.objects.filter(creator=servei.servei_id)
            token = Token.objects.get(user=account)
            if store:
                return Response({}, status=status.HTTP_400_BAD_REQUEST)
            elif account.check_password(data['password']):
                store = store_creation(servei, data)
                return Response({
                    "token": token.key,
                    "servei_id": servei.servei_id,
                    "cityCode": servei.cityCode,
                    "aadhar": servei.aadhar,
                    "store_key": store.store_key,
                    "phone_number": servei.phone_number,
                    "store_name": store.store_name
                }, status=status.HTTP_201_CREATED)
            else:
                return Response({}, status=status.HTTP_403_FORBIDDEN)
        else:
            account = Account.objects.filter(Q(relation='002') & Q(phone_number=data['phone_number']))
            if account:
                account = account.first()
                token = Token.objects.get(user=account)
                if account.check_password(data['password']):
                    print('Trace when account exist but n Servei n Store')
                    servei = servei_creation(account, data)
                    store = store_creation(servei, data)
                    return Response({
                        "token": token.key,
                        "servei_id": servei.servei_id,
                        "cityCode": servei.cityCode,
                        "aadhar": servei.aadhar,
                        "store_key": store.store_key,
                        "phone_number": servei.phone_number,
                        "store_name": store.store_name
                    }, status=status.HTTP_201_CREATED)
                else:
                    return Response({}, status=status.HTTP_403_FORBIDDEN)
            else:
                account = Account.objects.create_account(
                    servei_id_creatore(data['cityCode'], data['aadhar'], data['phone_number']), data['password'], '002',
                    data['phone_number'])
                token = Token.objects.get(user=account)
                print('Trace When none exist')
                servei = servei_creation(account, data)
                store = store_creation(servei, data)
                return Response({
                    "token": token.key,
                    "servei_id": servei.servei_id,
                    "cityCode": servei.cityCode,
                    "aadhar": servei.aadhar,
                    "store_key": store.store_key,
                    "phone_number": servei.phone_number,
                    "store_name": store.store_name
                }, status=status.HTTP_201_CREATED)


class ServeiLogin(APIView):
    permission_classes = [AllowAny]

    def post(self, request, format=None):
        try:
            # request.POST = json.loads(request.body)
            servei = None
            account = None
            if 'aadhar' in request.POST.keys():
                servei = Servei.objects.filter(aadhar=request.POST['aadhar']).first()
            elif 'servei_id' in request.POST.keys():
                servei = Servei.objects.filter(servei_id=request.POST['servei_id']).first()
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
                        return Response({'servei_id': servei.servei_id, 'token': token.key, 'aadhar': servei.aadhar,
                                         'phone_number': servei.phone_number, 'cityCode': servei.cityCode,'online':1 if servei.online else 0},
                                        status=status.HTTP_202_ACCEPTED)
                    else:
                        return Response({'servei_id': servei.servei_id, 'token': token.key, 'aadhar': servei.aadhar,
                                         'phone_number': servei.phone_number, 'cityCode': servei.cityCode,
                                         'store_key': servei.store,'online':1 if servei.online else 0}, status=status.HTTP_202_ACCEPTED)
                else:
                    return Response({}, status=status.HTTP_401_UNAUTHORIZED)
            else:
                return Response({}, status=status.HTTP_404_NOT_FOUND)
        except:
            return Response({}, status=status.HTTP_404_NOT_FOUND)


class ServeiPasswordReset(APIView):
    permission_classes = [AllowAny]

    # Get Phone Number for OTP Verification
    def get(self, request, format=None):
        if 'aadhar' in request.GET.keys():
            try:
                servei = Servei.objects.get(aadhar=request.GET['aadhar'])
                account = Account.objects.get(account_id=servei.servei_id)
                return Response({'account_id': account.account_id, 'phone_number': account.phone_number},
                                status=status.HTTP_200_OK)
            except:
                return Response({}, status=status.HTTP_404_NOT_FOUND)
        elif 'servei_id' in request.GET.keys():
            try:
                account = Account.objects.get(account_id=request.GET['servei_id'])
                return Response({'account_id': account.account_id, 'phone_number': account.phone_number},
                                status=status.HTTP_200_OK)
            except:
                return Response({}, status=status.HTTP_404_NOT_FOUND)

    def post(self, requets, format=None):
        try:
            body = json.loads(requets.body)
            account = Account.objects.get(account_id=body['account_id'])
            account.set_password(body['password'])
            account.save()
            token = Token.objects.get(user=account)
            return Response({'token': token.key}, status=status.HTTP_202_ACCEPTED)
        except:
            return Response({}, status=status.HTTP_404_NOT_FOUND)


class ServeiLogOut(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, format=None):
        body = json.loads(request.body)
        servei = Servei.objects.get(servei_id=body['servei_id'])
        servei.online = False
        servei.save()
        if 'store_key' in request.POST.keys():
            store = Store.objects.get(store_key=body['store_key'])
            store.online = False
            store.save()
            return Response({}, status=status.HTTP_202_ACCEPTED)
        else:
            return Response({},status=status.HTTP_400_BAD_REQUEST)


# Create Store View
class CreateStoreView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, format=None):
        data = json.loads(request.body)
        if not Store.objects.filter(creator=data['servei_id']):
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
                                         opening_time=datetime.datetime.strptime(str(data['opening_time']), '%H:%M:%S'),
                                         closing_time=datetime.datetime.strptime(str(data['closing_time']), '%H:%M:%S'),
                                         online=False, allowed=True, descriptions=data['descriptions'],
                                         cityCode=servei.cityCode)

            servei.store_key = store.store_key
            servei.save()
            if 'coordinates' in data['address'].keys():
                store.coordinates = Point(data['address']['coordinates']['lat'], data['address']['coordinates']['long'])
            store.save()

            # Creating Publytics
            publytics = Publytics.objects.filter(reference_id=store.store_key)
            if not publytics:
                publytics = Publytics.objects.create(pub_id=f'pub-{token_urlsafe(6)}', reference_id=store.store_key)

            return Response({'store_key': store.store_key}, status=status.HTTP_201_CREATED)
        else:
            return Response({'error': 'Store does exist'}, status=status.HTTP_400_BAD_REQUEST)


# Item Alter
class ItemAlterView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, format=None):
        body = json.loads(request.body)
        item = Item.objects.get(item_id=body['item_id'])
        if body['action'] == 'del':
            item.delete()
            return Response({}, status=status.HTTP_200_OK)
        else:
            if 'name' in body.keys():
                item.name = body['name']
            if 'price' in body.keys():
                rate = Rate.objects.filter(categories__contains=[item.prev_cat])
                if rate:
                    rate = rate.rate
                    item.price = float((body['price']) + (body['price'] * rate / 100))
            item.save()
            serial = ItemSerializer(item)
            if serial and item:
                return Response(serial.data, status=status.HTTP_200_OK)
            else:
                return Response({}, status=status.HTTP_400_BAD_REQUEST)


# CityCode Creator
# Need Fixing


class CityCodeService(APIView):
    permission_classes = [AllowAny]
    """
      Mock Code Create untill th eabove class is rectified
      TODO: Add functionality to add multiple pin_codes at same time
    """

    def post(self, request, format=None):

        city = None
        # if Token.objects.filter(key=request.POST['token']):
        #     return Response({'error':'Un-authorised access'},status=status.HTTP_401_UNAUTHORIZED)
        try:
            city = CityCode.objects.get(cityCode=request.POST['cityCode'])
        except:
            city = CityCode.objects.create(cityCode=request.POST['cityCode'])
        if not ',' in request.POST['pin_code']:
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
            return Response({}, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request, format=None):
        if 'cityCode' in request.GET.keys():
            cityCode = CityCode.objects.get(cityCode=request.GET['cityCode'])
            serial = CityCodeSerializer(cityCode)
            if serial and cityCode:
                return Response({'cityCode': serial.data}, status=status.HTTP_200_OK)
            else:
                return Response({}, status=status.HTTP_400_BAD_REQUEST)
        else:
            cityCode = CityCode.objects.filter(pin_codes__contains=[request.GET['pin_code']]).first()
            serial = CityCodeSerializer(cityCode)
            if cityCode:
                if 'all' in request.GET.keys():

                    return Response({'cityCode': serial.data}, status=status.HTTP_200_OK)
                else:
                    return Response({'cityCode': serial.data['cityCode'], 'city': serial.data['city']},
                                    status=status.HTTP_200_OK)

            else:
                return Response({}, status=status.HTTP_400_BAD_REQUEST)


class ItemExtractor(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, format=None):
        items = Item.objects.filter(store_key=request.GET['store_key'])
        serialized = ItemSerializer(items, many=True)
        if serialized and items:
            return Response(serialized.data, status=status.HTTP_200_OK)
        else:
            return Response({}, status=status.HTTP_400_BAD_REQUEST)


class DefaultItemsWindow(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, format=None):
        item = DefaultItems.objects.get_or_create(item_id=request.POST['item_id'])[0]
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
            return Response(serail.data, status=status.HTTP_201_CREATED)
        else:
            return Response({}, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request, format=None):
        item = DefaultItems.objects.get(item_id=request.GET['item_id'])
        item_serial = DefaultItemSerializer(item)
        if item_serial and item:
            return Response(item_serial.data, status=status.HTTP_200_OK)
        else:
            return Response({}, status=status.HTTP_400_BAD_REQUEST)


class ItemCreateView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, format=None):
        data = json.loads(request.body)
        item = Item.objects.get_or_create(item_id=item_id_generator(data['servei_id']))[0]
        item.name = data['name']
        item.store_key = data['store_key']
        item.servei_id = data['servei_id']
        item.allowed = True
        item.price = data['price']
        if "requirements" in data.keys():
            item.required_desc = data['requirements']
        if 'default_item_id' in data.keys():
            def_item = DefaultItems.objects.get(item_id=data['default_item_id'])
            item.images = [def_item.image]
            item.default_item_id = data['default_item_id']
            item.description = def_item.description
            item.delivery_type = def_item.delivery_type
            item.father_cat = def_item.father_cat
            item.prev_cat = def_item.cat_id
            item.inspection = def_item.inspection
            item.measure_param = def_item.measure_param
            item.unit = def_item.unit


        else:
            item.images = [image for image in data['images'] if image is not '@' and image is not '']
            item.measure_param = data['measureParam']
            item.unit = data['unit']
            category = Category.objects.get(cat_id=data['prev_cat'])
            # TODO: Item Inspection introduction in Category
            # item.inspection = False
            item.inspection = category.inspection
            item.delivery_type = category.delivery_type
            item.pick_type = category.pick_type
            item.prev_cat = data['prev_cat']
            item.father_cat = category.father_cat
            item.cityCode = data['cityCode']
            if 'description' in data.keys():
                item.description = data['description']
        item.city = CityCode.objects.get(cityCode=data['cityCode']).city
        item.save()
        serial = ItemSerializer(item)
        if serial and item:
            return Response(serial.data, status=status.HTTP_201_CREATED)
        else:
            return Response({}, status=status.HTTP_400_BAD_REQUEST)


class CategorySelection(APIView):
    permission_classes = [AllowAny]

    def get(self,request,format=None):
        data = request.GET
        father_categories = list(Category.objects.filter(Q(city_site__contains=[data['cityCode']]) & Q(cat_type='FC')))
        for father_category in father_categories:
            father_category.default_items = list(DefaultItems.objects.filter(cat_id=father_category.cat_id))
            categories = list(Category.objects.filter(Q(father_cat=father_category.cat_id) & Q(radiod=True)))
            for category in categories:
                category.default_items = list(DefaultItems.objects.filter(cat_id=category.cat_id))
            father_category.next_cat = categories

        serial = HeadCategorySerializer(father_categories).data()
        return Response({"categories":serial},status=status.HTTP_200_OK)

class ServeiAvailablity(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, format=None):
        body = json.loads(request.body)
        servei = Servei.objects.get(servei_id=body['servei_id'])
        if int(body['query']) == 1:
            return Response({'servei_id': servei.servei_id, 'available': 1 if servei.online else 0},
                            status=status.HTTP_200_OK)
        else:
            if servei:
                servei.online = True if int(body['available']) == 1 else False
                if 'coordinates' in body.keys():
                    servei.coordinates = Point(body['coordinates']['lat'], body['coordinates']['long'])
                servei.save()
                if servei.store:
                    store = Store.objects.get(store_key=servei.store)
                    if store:
                        store.online = True if int(body['available']) == 1 else False
                        store.save()
                return Response({'servei_id': servei.servei_id, 'available': 1 if servei.online else 0},
                                status=status.HTTP_200_OK)
            else:
                return Response({'servei_id': servei.servei_id, 'available': 1 if servei.online else 0},
                                status=status.HTTP_400_BAD_REQUEST)

    def get(self, request, format=None):

        servei = Servei.objects.get(servei_id=request.GET['servei_id'])
        if servei:
            return Response({'servei_id': servei.servei_id, 'available': 'true' if servei.online else 'false'},
                            status=status.HTTP_200_OK)
        else:
            return Response({}, status=status.HTTP_400_BAD_REQUEST)


class CheckUname(APIView):
    # authentication_classes = [TokenAuthentication]
    # permission_classes = [IsAuthenticated]
    permission_classes = [AllowAny]

    def get(self, request, format=None):
        store = Store.objects.filter(store_link=request.GET['uname'])
        if store:
            return Response({'allowed': '0'}, status=status.HTTP_200_OK)
        else:
            return Response({'allowed': '1'}, status=status.HTTP_200_OK)


class CheckSite(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, format=None):
        stores = Store.objects.filter(store_key=request.GET['store_key'])
        if stores:
            store = stores[0]
            return Response(
                {'uname': store.store_link, 'online': '1' if store.store_site_online else '0', 'allowed': '0'},
                status=status.HTTP_200_OK)
        else:
            return Response({'allowed': '1', 'uname': 'null', 'online': 'null'}, status=status.HTTP_200_OK)


class WebView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, requests, format=None):
        body = json.loads(requests.body)
        store = Store.objects.get(store_key=body['store_key'])
        store.store_link = body['uname']
        if body['images'] is not '':
            store.store_images = body['images'].split('^')
        store.save()
        return Response({'uname': store.store_link}, status=status.HTTP_200_OK)


class SuperUserAccount(APIView):
    permission_classes = [AllowAny]

    def post(self, requests, format=None):
        account = Account.objects.create_super_account(requests.POST['account_id'], requests.POST['password'], '001',
                                                       requests.POST['phone_number'], )
        return Response({'account_id': account.account_id, "token": Token.objects.get(user=account).key},
                        status=status.HTTP_200_OK)


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

        category, created = Category.objects.get_or_create(
            cat_id=''.join([token_urlsafe(4), '_CAT_', datetime.datetime.utcnow().strftime('%d%m%Y-%H%M%S')]))

        category.name = data['name']
        category.prev_cat = data['prev_cat']
        prev_cat = Category.objects.get(cat_id=data['prev_cat'])
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
        return Response({'cat_id': category.cat_id, 'city_site': category.city_site, 'father_cat': category.father_cat,
                         'prev_cat': category.prev_cat}, status=status.HTTP_200_OK)


class CheckStore(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, requests, format=None):
        store = Store.objects.filter(creator=requests.GET['servei_id'])
        if store:
            return Response({'store_key': store.first().store_key}, status=status.HTTP_200_OK)
        else:
            return Response({}, status=status.HTTP_400_BAD_REQUEST)


class VerifyToken(APIView):
    permission_classes = [AllowAny]

    def post(self, request, format=None):
        """
        Only for Pilot or Servei
          To check if token exist or not
          if exist then return true and false if doesn't
        """
        data = json.loads(request.body)
        token = Token.objects.filter(key=data['token'])
        if token:
            token = token.first()
            if 'phone_token' in data.keys():
                device = MobileDevice.objects.get_or_create(locie_partner=token.user.account_id,
                                                             partnership=token.user.relation)
                device.registration_id = data['phone_token']
                device.save()

            return Response({"exist": 1}, status=status.HTTP_200_OK)
        else:
            return Response({"exist": 0}, status=status.HTTP_403_FORBIDDEN)


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
        order_month = orders.filter(
            Q(date_time_creation__month=timezone.now().month) & Q(date_time_creation__year=timezone.now().year))
        price_month = 0.0
        price_total = 0.0
        for order in orders:
            if order.final_servei_cluster[servei_id]['status'] == SERVED:
                price_month += order.final_servei_cluster[servei_id]['price']
        for order in order_month:
            if order.final_servei_cluster[servei_id]['status'] == SERVED:
                price_month += order.final_servei_cluster[servei_id]['price']
        failed_orders = orders.filter(
            ~Q(final_servei_cluster__has_key=servei_id) | Q(final_servei_cluster__contains={f'{servei_id}': {
                "status": FAILED
            }}))
        success_orders = orders.filter(Q(final_servei_cluster__contains={f'{servei_id}': {
            "status": SERVED
        }}))
        all_views = sum(publytics.views_log.values())
        this_month_order = len(orders)
        if all_views > 1000 and this_month_order >= 2:
            widthrawl = True
        if publytics:
            publytics = publytics.first()
            return Response({
                "store_key": data['store_key'],
                "withdrawl": 1 if widthrawl else 0,
                "views": {
                    "this_month": list(publytics.views_log.values())[-1],
                    "total_views": all_views
                },
                "orders": {
                    "total_orders": this_month_order,
                    "this_month": len(order_month),
                    "failed_orders": len(failed_orders),
                    "success_orders": len(success_orders)
                },
                "revenue": {
                    "total": price_total,
                    "this_month": price_month
                }
            }, status=status.HTTP_200_OK)
        else:
            print(data['store_key'])
            return Response({
                "store_key": data['store_key'],
                "withdrawl": 1 if widthrawl else 0,
                "views": {
                    "this_month": 0,
                    "total_views": 0.0
                },
                "orders": {
                    "total_orders": 0,
                    "this_month": 0,
                    "failed_orders": 0,
                    "success_orders": 0
                },
                "revenue": {
                    "total": 0,
                    "this_month": 0
                }
            }, status=status.HTTP_200_OK)


class OrderHistory(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, format=None):
        data = request.GET
        orders = Order.objects.filter(servei_list__contains=[data['servei_id']] & Q(Q(status=FINISHED) | Q(status = FAILED))).order_by('-date_time_creation')
        if orders:
            returning_order = []
            for order in orders:
                cluster = order.final_servei_cluster[data['servei_id']] if data['servei_id'] in order.final_servei_cluster.keys() else order.servei_cluster[data['servei_id']]
                returning_order.append({
                    "order_id": order.order_id,
                    "payment_COD": order.payment_COD,
                    "payment_complete": order.payment_complete,
                    "price":cluster['price'],
                    "net_price":cluster['net_price'],
                    "quantity":cluster['quantity'],
                    "platform_charge":cluster['platform_charge'],
                    "items":cluster['items'],
                    "status":cluster['status'],
                    "delivery_required": 1 if order.delivery_required else 0,
                }),
            return Response({"orders": returning_order}, status=status.HTTP_200_OK)
        else:
            return Response({"orders": []}, status=status.HTTP_200_OK)


class CustomerReview(APIView):
    permission_classes = [AllowAny]

    def post(self, request, format=None):
        data = json.loads(request.body)
        reviews = CustomerReviewModel.objects.filter(servei_id__contains=[data['servei_id']]).order_by('-date_time')
        if reviews:
            comments = CustomerReviewSerializer(reviews.filter(Q(review_type='COMMENT')), many=True)
            complaints = CustomerReviewSerializer(reviews.filter(Q(review_type='COMPLAINT')), many=True)
            reviews = CustomerReviewSerializer(reviews.filter(Q(review_type='REVIEW')), many=True)
            if comments and complaints and reviews:
                return Response({
                    "comments": comments,
                    "complaints": complaints,
                    "reviews": reviews
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    "comments": [],
                    "complaints": [],
                    "reviews": []
                }, status=status.HTTP_200_OK)


class OrderView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, format=None):
        data = request.GET
        orders = Order.objects.filter(
            Q(servei_list__contains=[data['servei_id']]) & Q(~Q(status=FINISHED) & ~Q(status=FAILED)))
        pending_orders = orders.filter(~Q(final_servei_cluster__has_key=data['servei_id'])).order_by(
            '-date_time_creation')
        non_pending_orders = orders.filter(Q(final_servei_cluster__has_key=data['servei_id'])).order_by(
            '-date_time_creation')
        working_orders =[]
        completed_orders =[]
        for order in non_pending_orders:
            if order.final_servei_cluster[data['servei_id']]['status'] == WORKING:
                working_orders.append(order)
            elif order.final_servei_cluster[data['servei_id']]['status'] == COMPLETED:
                completed_orders.append(order)

        return Response({
            "pending_orders": OrderServeiSerializer(pending_orders, data['servei_id'], final=False),
            "working_order": OrderServeiSerializer(working_orders, data['servei_id'], final=True),
            "completed_orders":OrderServeiSerializer(completed_orders, data['servei_id'], final=True),
        }, status=status.HTTP_200_OK)
