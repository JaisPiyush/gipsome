# Imports
import datetime
import json

from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.contrib.gis.db import models as gis_models
from django.contrib.gis.geos.point import Point
from django.contrib.postgres.fields import ArrayField, JSONField
from django.db import models
from django.utils import timezone
from fcm_django.models import AbstractFCMDevice
from rest_framework.authtoken.models import Token

from .gadgets.serverOps import servei_id_creatore, pilot_id_creatore


# Authentication Model


    
    
class AccountManager(BaseUserManager):

    use_in_migrations = True

    def _create_account(self, account_id:str, password:str, relation:str, phone_number:str, is_superuser:bool=False,is_staff:bool=False):
        # print(account_id, password,  phone_number)
        if account_id and password and relation and phone_number:
            account = Account.objects.create(account_id=account_id, relation=relation,is_staff=is_staff,
                              phone_number=phone_number,  is_superuser=is_superuser)
            account.set_password(password)
            account.save(using=self._db)
            token = Token.objects.get_or_create(user = account)
            return account
        else:
            raise ValueError('Details are incomplete!!')

    def create_account(self, account_id:str, password:str, relation:str,  phone_number:str):
        return self._create_account(account_id, password, relation, phone_number)

    def create_super_account(self, account_id:str, password:str, relation:str,  phone_number:str):
        return self._create_account(account_id, password, relation,  phone_number, is_superuser=True,is_staff=True)


class Account(AbstractBaseUser, PermissionsMixin):
    account_id = models.CharField(
        max_length=30, unique=True, default='account_id')
    date_joined = models.DateField(default = timezone.now())
    phone_number = models.CharField(max_length=15, default='', db_index=True)
    is_staff = models.BooleanField(default=False)
    # phone_token = models.TextField(default='', db_index=True)
    is_superuser = models.BooleanField(default=False)
    # servei,de,customer
    # 002 : Servei, 003: Pilot, 009: customer, 001: Locie
    relation = models.CharField(max_length=4, default='', db_index=True)
    # FCM Token of device
    # device_token = models.TextField(default='')

    objects = AccountManager()

    USERNAME_FIELD = 'account_id'
    REQUIRED_FIELDS = ('phone_number', 'relation', 'phone_token')

    class Meta:
        verbose_name = ('account')
        verbose_name_plural = ('accounts')
    
    def pour(self,request):

        # Check city is available or not?
        city_code = CityCode.objects.filter(pin_codes__contains = [request['pin_code']])
        if not city_code:
            return -1,-1
        else:
            city_code = city_code.first().cityCode

        
        account = None
        # Check account exist or not ? 
        try:
            if request['relation'] == '002' or request['relation'] == '003':
                account = Account.objects.filter(relation = request['relation'],phone_number = request['phone_number']).first()
            if not account:
                account_id = None
                if request['relation'] == '002':
                    account_id = servei_id_creatore(city_code,request['aadhar'],request['phone_number'])
                elif request['relation'] == '003':
                    account_id = pilot_id_creatore(city_code,request['aadhar'],request['phone_number'])

                # Creating New Account    
                account = Account.objects.create_account(account_id,request['password'],request['relation'],request['phone_number'])
                # print(account)

        except:
            # print('in account except')
            account_id = None
            # print(f"Inside except {request['phone_number']} : {account_id}") 
            if request['relation'] == '002':
                account_id = servei_id_creatore(city_code,request['aadhar'],request['phone_number'])
            elif request['relation'] == '003':
                account_id = pilot_id_creatore(city_code,request['aadhar'],request['phone_number'])

            # Creating New Account   
            account = AccountManager().create_account(account_id,request['password'],request['relation'],request['phone_number'])
            # print(account)
            
        # print(account)
        keys = request.keys()
        if 'phone_token' in keys:
            device = MobileDevice.objects.get_or_create(locie_partner = account.account_id)[0]
            device.registration_id = request['phone_token']
            device.partnership = request['relation']
            device.save()
                                           
        partner = None
        
        #Servei
        if request['relation'] == '002':
            partner = Servei.objects.get_or_create(servei_id = account.account_id)[0]
            partner.phone_number = request['phone_number']
            partner.first_name = request['first_name']
            partner.last_name = request['last_name']
            partner.gender = request['gender']
            # partner.coordinates = coordinates
            partner.cityCode = city_code
            partner.account = account
            partner.aadhar = request['aadhar']
            partner.address = request['address'] if isinstance(request['address'],dict) else json.loads(request['address'])
            partner.pin_code = request['pin_code']           
            
            for key in keys:
                if 'image' == keys:
                    partner.image = request['image']
                elif 'aadhar_image' == key:
                    partner.aadhar_image = request['aadhar_image']
                elif 'pan'  == key:
                    partner.pan = request['pan']
                elif 'pan_image' == key:
                    partner.pan_image = request['pan_image']
                elif 'country' == key:
                    partner.country = request['country']
                elif 'country_code' == key:
                    partner.country_code = request['country_code']
                elif 'dob' == key:
                    partner.dob = datetime.datetime.strptime(request['dob'],'%d-%m-%Y')
                elif 'coordinates' == key:
                    partner.coordinates = Point(request['coordinates']['lat'],request['coordinates']['long'])
                    
            partner.save()       

        # Pilot
        elif request['relation'] == '003':
            partner = Pilot.objects.get_or_create(pilot_id = account.account_id)[0]
            partner.account = account
            partner.first_name = request['first_name']
            partner.last_name = request['last_name']
            partner.address = request['address']
            partner.cityCode = city_code
            partner.image = request['image']
            partner.phone_number = request['phone_number']
            partner.aadhar = request['aadhar']
            partner.aadhar_image = request['aadhar_image']
            partner.vehicle = request['vehicle']
            partner.vehicle_id = request['vehicle_id']
            partner.driving_license = request['driving_license']
            partner.dl_image = request['dl_image']
            

            if 'email' in keys:
                partner.email = request['email']
            partner.save()
        
        return account,city_code
        

# Items Model


class Item(models.Model):

    name = models.CharField(max_length=30, db_index=True, default='')
    # itemId example --> UP536167!tem[time(till ms)]
    item_id = models.CharField(
        max_length=50, db_index=True, primary_key=True, default='')
    # Store Key
    store_key = models.CharField(max_length=50, db_index=True, default='')
    # use this locate all the items served by any servei
    servei_id = models.CharField(max_length=50, db_index=True, default='')
    # Basic Location of Item
    city = models.CharField(max_length=20, default='')
    cityCode = models.CharField(max_length=5, db_index=True, default='')
    # allowed to be featured on locie
    allowed = models.BooleanField(default=True)

    price = models.DecimalField(max_digits=7, decimal_places=2, default=0.00)

    # effective price is the price after chopping the Locie's share amount
    # amount the servei will get in hand
    effective_price = models.DecimalField(
        max_digits=7, decimal_places=2, default=0.00)
    images = ArrayField(models.CharField(max_length=255), size=4, default=list)
    description = models.TextField(default='')

    # Heading also Called NanoCat
    heading = models.CharField(max_length=30, default='None')

    # MeasureParam ---> kg,sq.ft,gm,pck,pcs,etc
    measure_param = models.CharField(max_length=10, default='')
    # unit 0.5,1...
    unit = models.DecimalField(max_digits=6, decimal_places=2, default=0.00)
    # Inspection required
    inspection = models.BooleanField(default=False)

    # DeliveryType SSU.UDS.SDU
    delivery_type = models.CharField(max_length=3, default='')
    # Category Reference
    prev_cat = models.CharField(max_length=30, default=True)
    father_cat = models.CharField(max_length=30, default=True)
    required_desc = ArrayField(models.CharField(max_length=80),default=list,blank=True)

    ratings = models.DecimalField(max_digits=3, decimal_places=2, default=0.00)

    # Id of default_item if associated with
    default_item_id = models.CharField(max_length=70,default='none')




# Servei Model
class Servei(models.Model):
    servei_id = models.CharField(
        max_length=50, db_index=True, primary_key=True, default='')
    account = models.OneToOneField(
        Account, on_delete=models.CASCADE, null=True)
    cityCode = models.CharField(max_length=5, db_index=True, default='')

    # Details
    first_name = models.CharField(max_length=30, default='')
    last_name = models.CharField(max_length=30, default='')
    phone_number = models.CharField(max_length=10, default='', unique=True)
    email = models.EmailField(default='')
    gender = models.CharField(max_length=20, default='')
    profession = models.CharField(max_length=30, default='')
    image = models.TextField(default='')
    coordinates = gis_models.PointField(srid=4326, default=Point(0.00, 0.00, srid=4326))

    # Official Data
    aadhar = models.CharField(
        max_length=30, default='', unique=True, db_index=True)
    aadhar_image = models.TextField(default='')
    pan = models.CharField(max_length=30, default='',
                           unique=True, db_index=True)
    pan_image = models.TextField(default='')

    store = models.CharField(max_length=50, default='', db_index=True)
    # Date of joining and DOB
    date_join = models.DateField(default=timezone.now().date())

    # Flush out if servei is marked not-allowed and will not be shown
    allowed = models.BooleanField(default=True)

    # Online---> feature to show availability --> True(Free and Open) False(Closed or Busy)(I)
    online = models.BooleanField(default=True)

    # address --> {'address_line_1',address_line_2,city,state,country,pin_code}
    address = JSONField(default=dict)
    pin_code = models.CharField(max_length=6, default='')
    country = models.CharField(max_length=20, default='INDIA')
    country_code = models.CharField(max_length=4, default='+91')



# TODO:Fix Store
class Store(models.Model):

    store_name = models.CharField(max_length=50, default='')
    # creator
    creator = models.CharField(max_length=30, default=True, db_index=True)
    coordinates = gis_models.PointField(srid=4326, default=Point(0.00, 0.00, srid=4326))
    store_category = ArrayField(models.CharField(max_length=30), default=list)
    father_categories = ArrayField(
        models.CharField(max_length=30), default=list)

    # store Key
    store_key = models.CharField(
        max_length=50, db_index=True, default='', primary_key=True)
    owners = ArrayField(models.CharField(max_length=30), default=list)

    # Array of itemIds
    product_line = ArrayField(models.CharField(
        max_length=20, db_index=True), default=list)

    # When non-gst store is created
    creators_profession = models.CharField(max_length=30, default='')


    # aadhar and pan  of creator or pan_token of creator
    # if has gst ask for pan too
    official_support = JSONField(default=dict)

    # Contacts emails : [servei.email,...] and phone_numbers : [servei.phone_number,...]
    contacts = JSONField(default=dict)

    # Address address_line_1,address_line_2,street,city,state,pin_code as key
    address = JSONField(default=dict)
    # CityCode
    cityCode = models.CharField(max_length=6, db_index=True, default='')

    # Coordinates data
    coordinates = gis_models.PointField(srid=4326, default=Point(0.00, 0.00, srid=4326))
    # Use strftime to set this
    opening_time = models.TimeField(default = timezone.now().time())
    closing_time = models.TimeField(default = timezone.now().time())

    # Online for serving
    online = models.BooleanField(default=True)

    # headings for keeping all store related sub cats
    headings = ArrayField(models.CharField(max_length=70), default=list)

    # allowed
    allowed = models.BooleanField(default=True)

    store_link = models.CharField(max_length=255,default='')
    store_site_online = models.BooleanField(default=False)
    store_images = ArrayField(models.TextField(),default=list)
    store_unmae = models.CharField(max_length=70,default='',db_index=True)
    # coordinates = CoordinateManager(coordinates_id)

    # Images
    image = models.TextField(default='')
    descriptions = JSONField(default=dict)



class Order(models.Model):
    """
      - Order Model for Backend System
      - servei cluster is a JSON with server_id as key, and cluster as value
      - servei list for containing all servei id only for query
      -  cluster is JSON inside contains items key with cluster of items 
      -     -items cluster contains item_id, item_name,item_image,price,quantity,unit,measure
      -  cluster also contains store_key,store_name,quantity(net),price,net_price and extra_charges,status =(DECLINE/WORKING/PENDING/SERVED/COMPLETED)
      - accepted items contains item_id of those items who are selected to be deliverd
      - picked items are item_id's who are picked by pilot, If all the items of a servei is picked than status of servei changes to SERVED
      - pick list contains item id's who are ready to be picked up, Usefull in UDS when servei MARKS Completd it actually push item to pick list
      - price the amount without any charges
      - net price is the price customer will pay , which includes price and all extra charges applicable
      - status defines current status of WORKING (CREATED/WORKING/FAILED/WAITING/FINISHED)
      - time log contains time of every status
      - pilot cluster contains pilot_id as key and details in json such as name,image, phone number as value
      - customer stack contains address, name, phone number, coordinates as key value pair IMP. coordinates contains json lat and long
      - payment id is the razorpay id
      - payment stack contians all other responses of razorpay as key value pair
      - route plan consist servei_id as key and and {lat,long} as values first is the farthest from customer and last is the nearest
      - biding bared signifies that acceptance of order hasbeen closed since 3min ha elapsed
    """

    order_id = models.CharField(
        max_length=50, default='', unique=True, primary_key=True, db_index=True)  
    servei_cluster = JSONField(default=dict)
    servei_list = ArrayField(models.CharField(max_length=70),default=list)
    route_plan = ArrayField(JSONField(),default=list)
    senders_list = ArrayField(models.CharField(max_length=70),default=list)
    receivers_list = ArrayField(models.CharField(max_length=70),default=list)
    picked_list = ArrayField(models.CharField(max_length=70),default=list)
    droped_list = ArrayField(models.CharField(max_length=70),default=list)
    final_servei_cluster = JSONField(default=dict)
    price = models.DecimalField(
        max_digits=7, decimal_places=2, default=0.00)
    locie_transfer = models.DecimalField(
        max_digits=7, decimal_places=2, default=0.00)
    locie_reversion = models.DecimalField(
        max_digits=7, decimal_places=2, default=0.00)
    net_price = models.DecimalField(
        max_digits=7, decimal_places=2, default=0.00)
    extra_charges = JSONField(default=dict)
    status = models.IntegerField(default=0000)
    time_log = JSONField(default=dict)
    pilot_cluster = JSONField(default=dict)
    position = gis_models.PointField(
        srid=4326, default=Point(0.00, 0.00, srid=4326))
    customer_id = models.CharField(max_length=15, db_index=True, default='')
    customer_stack = JSONField(default=dict)
    date_time_creation = models.DateTimeField(default=timezone.now())
    payment_complete = models.BooleanField(default=False)
    payment_COD = models.BooleanField(default=True)
    payment_id = models.TextField(default='')
    payment_stack = JSONField(default=dict)
    delivery_required = models.BooleanField(default=True)
    delivery_type = models.CharField(max_length=3, default='') # SSU,UDS and PAD
    cityCode = models.CharField(max_length=8, default='')
    otp = models.CharField(max_length=10, default='')
    biding_bared = models.BooleanField(default=False)


# Category
#TODO: MakeMigrations to show cat_id.default ='' not True
class Category(models.Model):
    cat_id = models.CharField(
        max_length=50, db_index=True, default='', unique=True)
    name = models.CharField(max_length=50, db_index=True, default='')
    prev_cat = models.CharField(max_length=50, default='',blank=True)
    image = models.TextField(default='',blank=True)
    next_cat = ArrayField(models.CharField(max_length=50), default=list,blank=True)
    father_cat = models.CharField(max_length=50, default='',blank=True)

    # Category type ---> FC(Father Category), SC (Sub- Category),MC (Micro Category) NC(Nano Category)

    cat_type = models.CharField(max_length=2, db_index=True, default='',blank=True)

    # citySite --> Array Store cityCode which will have this category working
    # Servei won't be affected by this--> Servei will see all the options available
    # User screen will filter according to this
    # Upon adding first servei to any category--> server will automatically add the cityCode--> Check if cityCode is in citySite of category --> ifnot add the cityCode in the Array
    city_site = ArrayField(models.CharField(
        max_length=5, db_index=True), default=list,blank=True)

    required_desc = ArrayField(models.CharField(
        max_length=50, db_index=True), default=list,blank=True)

    # Delivery Type --> SSU, SDU, UDS
    delivery_type = models.CharField(max_length=3, default='',blank=True)

    # PickType --> OP (One Pick) , MP (Multi Pick)
    pick_type = models.CharField(max_length=2, default='OP',blank=True)
    online = models.BooleanField(default=True)
    # Post Complete Enabled
    # True will give Servei access to implement post-complete feature in item
    #postCompleteEnable = models.BooleanField(default=False)

    # Radiod if true will tell to put radio button
    radiod = models.BooleanField(default=False,blank=True)

    # returnable if True than servei will accept the return and if false than servei wont take the return
    returnable = models.BooleanField(default=True,blank=True)
    inspection = models.BooleanField(default=False,blank=True)
    # Defaults items under this category
    # [{item_id,name},{item_id,name}]
    default_items = ArrayField(models.CharField(max_length=50), default=list,blank=True)


# Default Items class
class DefaultItems(models.Model):
    item_id = models.CharField(max_length=50, primary_key=True)
    cat_id = models.CharField(max_length=50, db_index=True, default='')
    measure_param = models.CharField(max_length=30, default='')
    unit = models.CharField(max_length=4, default='')
    image = models.TextField(default='',blank=True)
    pick_type = models.CharField(max_length=2, default='SP')
    delivery_type = models.CharField(max_length=3, default='')
    father_cat = models.CharField(max_length=50, default='', db_index=True)
    name = models.CharField(max_length=50, default='')
    inspection = models.BooleanField(default=False)
    description = models.TextField(default='',blank=True)
    required_desc = ArrayField(models.CharField(max_length=70),default=list,blank=True)


# # Checking
class CityManager(models.Manager):
    def get_code(self, pin_code):
        city = CityCode.objects.filter(pin_codes__contains=[pin_code])
        return city


class CityCode(models.Model):
    city = models.CharField(max_length=40, default='', db_index=True)
    cityCode = models.CharField(max_length=10, primary_key=True)
    state = models.CharField(max_length=20, db_index=True, default='')
    pin_codes = ArrayField(models.CharField(max_length=10), default=list)


class MobileDevice(AbstractFCMDevice):

    # receipient 'servei/customer/de
    # if receipient is customer then locie_partner will have servei_id or pilot_id
    locie_partner = models.CharField(max_length=50, default='', db_index=True)
    # 001 : Locie, 002:Servei, 003:Pilot, 009:Customer
    partnership = models.CharField(max_length=10, default='', db_index=True)



    class Meta:
        verbose_name = ('FCM device')
        verbose_name_plural = ('FCM devices')


class CustomerDevice(AbstractFCMDevice):
    customer_id = models.CharField(max_length=50, default='', db_index=True)



#----------------------------------RPMNS---------------------------------------------------#
#------------------------------------------------------------------------------------------#

class Customer(models.Model):
    customer_id = models.CharField(max_length=50, primary_key=True, default='')
    gender = models.CharField(max_length=10, default='')
    name = models.CharField(max_length=120,default='')
    address = JSONField(default=dict)
    coordinates = gis_models.PointField(srid=4326, default=Point(0.00, 0.00, srid=4326))
    # coordinates_id = models.CharField(max_length=50,db_index=True,default='')
    dob = models.DateField(default = timezone.now())
    extras = JSONField(default=dict)


# ------------------DeliverExecutive-------------------------------------------------------------
class Pilot(models.Model):
    pilot_id = models.CharField(max_length=50, primary_key=True, default='')
    account = models.OneToOneField(Account, on_delete=models.CASCADE)

    # Personal Details
    first_name = models.CharField(max_length=30, default='')
    last_name = models.CharField(max_length=30, default='')
    address = JSONField(default=dict)
    cityCode = models.CharField(max_length=6, default='', db_index=True)
    image = models.TextField(default='')

    # Phone Number and Email
    phone_number = models.CharField(max_length=12, db_index=True, default='')
    email = models.EmailField(db_index=True, null=True, blank=True)

    # Vehicle and official data
    aadhar = models.CharField(
        max_length=30, unique=True, db_index=True, default='')
    aadhar_image = models.TextField(default='')
    # Vehicle type BIK:BIKE/SCOOTY, CYC:CYCLE, TRICYC:TriCycle = Rickshaw,cart
    vehicle = models.CharField(max_length=10, default='')
    # BIKE/SCOOTY Licence Plate
    vehicle_id = models.CharField(
        max_length=20, db_index=True, unique=True, default='')
    # Driving License Bike and Scooty
    driving_license = models.CharField(
        max_length=30, db_index=True, default='')
    dl_image = models.TextField(default='')

    # Rating of Pilot
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.00)

    # Coords id
    # coordinates_id = models.CharField(max_length=50,db_index=True,default='')
    coordinates = gis_models.PointField(srid=4326, default=Point(0.00, 0.00, srid=4326))
    # coordinates = CoordinateManager(coordinates_id)
    # No. of order on time
    weight = models.IntegerField(default=0, db_index=True)


class Rate(models.Model):
    rate = models.DecimalField(
        max_digits=4, decimal_places=2, default=00.00, db_index=True)
    categories = ArrayField(models.CharField(max_length=30), default=list)
    city_site = ArrayField(models.CharField(max_length=5), default=list)

class ExtraCharges(models.Model):
    #relation : 001 Locie 002 Servei 003 Pilot 009 Customer
    relation = models.CharField(max_length=4,default='009')
    categories = ArrayField(models.CharField(max_length=70),default=list)
    extra_charges = JSONField(default=dict)


class MeasureParam(models.Model):
    measure_id = models.CharField(
        max_length=50, primary_key=True, default='krispiforever@103904tilltheendoftheinfinity')
    # 0.5,1,10,25,50,100,150,200,500,
    units = ArrayField(models.DecimalField(max_digits=4, decimal_places=2, default=00.00), default=list)
    # kg,gm,sqrft,pkt.,..etc
    measure_params = ArrayField(models.CharField(max_length=30), default=list)


class Cart(models.Model):
    cart_id = models.CharField(max_length=75,default='',primary_key=True)
    clusters = JSONField(default=dict)
    price = models.DecimalField(max_digits=7,decimal_places=2,default=00.00)
    net_price = models.DecimalField(max_digits=7,decimal_places=2,default=00.00)
    quantity = models.DecimalField(max_digits=5,decimal_places=2,default=00.00)
    customer_id = models.CharField(max_length=70,db_index=True,default='')


class LocieStoreSite(models.Model):
    uname = models.CharField(max_length=120,primary_key=True,default='')
    # Complete link uname.locie.co.in
    store_link = models.CharField(max_length=255,db_index=True,default='')
    # {"page_name":{"tag":"html","childrens":[]}}
    site = JSONField(default=dict)
    # {"page_name":{}}
    site_context = JSONField(default=dict)
    monetized = models.BooleanField(default=True)
    online = models.BooleanField(default=True)
    date_of_creation = models.DateField(default=timezone.now())


class PickDropOrder(models.Model):
    sender_phone_number = models.CharField(max_length=13,db_index=True,default='')
    sender_address = JSONField(default=dict)
    sender_name = models.CharField(max_length=70,default='')
    receivers_stack = JSONField(default=dict)
    # who will pay SEN -> sender REC -> receiver
    payee = models.CharField(max_length=3,default='SEN')
    distance = models.DecimalField(max_digits=7,decimal_places=4,default=0.00)
    cost = models.DecimalField(max_digits=7,decimal_places=4,default=40.0)
    pilot_id = models.CharField(max_length=70,default='')
    droped = models.BooleanField(default=False)
    picked = models.BooleanField(default=False)

    
class Publytics(models.Model):
    pub_id = models.CharField(max_length=50,primary_key=True,default='')
    reference_id = models.CharField(max_length=70,default='')
    site_uname = models.CharField(max_length=70,default='')
    views_log = JSONField(default=dict)
    revenue_log = JSONField(default=dict)
    start_dates = models.DateField(default=timezone.now())

class CustomerReviewModel(models.Model):
    customer_id = models.CharField(max_length=50,default='')
    rating = models.DecimalField(max_digits=3,decimal_places=2,default=0.00)
    servei_ids = ArrayField(models.CharField(max_length=70),default=list)
    store_keys = ArrayField(models.CharField(max_length=70),default=list)
    item_ids = ArrayField(models.CharField(max_length=70),default=list)
    order_ids = ArrayField(models.CharField(max_length=70),default=list)
    pilot_ids = ArrayField(models.CharField(max_length=70),default=list)
    review_type = models.CharField(max_length=15,default='COMMENT')
    date_time = models.DateTimeField(default=timezone.now())