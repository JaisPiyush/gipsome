# Imports
from fcm_django.models import AbstractFCMDevice, FCMDeviceManager
from django.contrib.gis.db import models as gis_models
from django.db import models
from django.db.models.manager import BaseManager
from django.contrib.gis.geos.point import Point
from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin
from django.contrib.auth.base_user import BaseUserManager
from django.contrib.postgres.fields import ArrayField, JSONField
from .serverOps import servei_id_creatore, pilot_id_creatore
from rest_framework.authtoken.models import Token
import datetime
from django.utils import timezone
import json
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
    relation = models.CharField(max_length=20, default='', db_index=True)
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
        #TODO: Abandoned block needed to be removed
        try:
            # print('in account try')
            if request['relation'] == '009':
                account = Account.objects.get(account_id = request['phone_number'])
            elif request['relation'] == '002' or request['relation'] == '003':
                account = Account.objects.filter(relation = request['relation'],phone_number = request['phone_number']).first()
            if not account:
                account_id = None
                if request['relation'] == '009':
                    account_id = request['phone_number']
                elif request['relation'] == '002':
                    account_id = servei_id_creatore(city_code,request['aadhar'],request['phone_number'])
                elif request['relation'] == '003':
                    account_id = pilot_id_creatore(city_code,request['aadhar'],request['phone_number'])

                # Creating New Account    
                account = AccountManager().create_account(account_id,request['password'],request['relation'],request['phone_number'])
                # print(account)

        except:
            # print('in account except')
            account_id = None
            # print(f"Inside except {request['phone_number']} : {account_id}") 
            if request['relation'] == '009':
                account_id = request['phone_number']
            elif request['relation'] == '002':
                account_id = servei_id_creatore(city_code,request['aadhar'],request['phone_number'])
            elif request['relation'] == '003':
                account_id = pilot_id_creatore(city_code,request['aadhar'],request['phone_number'])

            # Creating New Account   
           
            account = AccountManager().create_account(account_id,request['password'],request['relation'],request['phone_number'])
            # print(account)
            
        # print(account)
        keys = request.keys()
        if 'phone_token' in keys:
            if request['relation'] == '009':
                device = CustomerDevice.objects.get_or_create(customer_id = account.account_id)[0]
                device.registration_id = request['phone_token']
                device.save()
            else:
                device = MobileDevice.objects.get_or_create(locie_partner = account.account_id)[0]
                device.registration_id = request['phone_token']
                device.partnership = request['relation']
                device.save()
            
        # Checking Coordinates exist or not
        coordinates = None
        coordinates = Coordinates.objects.get_or_create(coordinates_id = account.account_id)[0]
        # print(coordinates)
        
        coordinates.relation = request['relation']
        coordinates.position = Point(float(request['lat']),float(request['long']))
        coordinates.save()
                                           
        partner = None
        
        #Servei
        if request['relation'] == '002':
            partner = Servei.objects.get_or_create(servei_id = account.account_id)[0]
            partner.phone_number = request['phone_number']
            partner.first_name = request['first_name']
            partner.last_name = request['last_name']
            partner.gender = request['gender']
            # partner.profession = request['profession']
            # partner.coordinates = coordinates
            partner.coordinates_id = coordinates.coordinates_id
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
            partner.save()
        
        # Customer
        elif request['relation'] == '009':
            # print(account)
            print(account.account_id)
            partner = Customer.objects.get_or_create(customer_id = account.account_id,account=account)[0]
            partner.account = account
            partner.dob = datetime.datetime.strptime(request['dob'],'%d-%m-%Y')
            

            for key in keys:
                if key == 'gender':
                    partner.gender = request['gender']
                elif key == 'address':
                    partner.address = request['address']
                elif key == 'lat':
                    partner.coordinates_id = coordinates.coordinates_id
                elif key == 'extras':
                    partner.extras = request['extras']
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
            partner.coordinates_id = coordinates.coordinates_id

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

    # DeliveryType and PickType SSU.UDS.SDU
    delivery_type = models.CharField(max_length=3, default='')
    #SinglePick or MultiPick
    pick_type = models.CharField(max_length=2, default='SP')

    # Complete Time Complexity
    # On-Time Complete or Post time Complete
    #completeType = models.CharField(max_length=2, default='OT')
    #position = gis_models.PointField(srid=4326, default=Point(0.00,0.00, srid=4326))

    # Category Reference
    prev_cat = models.CharField(max_length=30, default=True)
    father_cat = models.CharField(max_length=30, default=True)

    # varinats -> JSON -> {'parameter','variant':[{value,price,image}]}
    variants = JSONField(default=dict)
    required_desc = ArrayField(models.CharField(max_length=80),default=list,blank=True)
    #postComplete = models.BooleanField(default=False)
    ratings = models.DecimalField(max_digits=3, decimal_places=2, default=0.00)

    # Id of default_item if associated with
    default_item_id = models.CharField(max_length=70,default='none')


# Position Database
class Coordinates(models.Model):
    #account_id
    coordinates_id = models.CharField(max_length=50, primary_key=True, default='')
    # 001 : Servei, 002: DE, 009: customer, 100: Locie , 904: Store
    relation = models.CharField(max_length=10, default='', db_index=True)
    position = gis_models.PointField(
        srid=4326, default=Point(0.00, 0.00, srid=4326))
    


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

    # Coordinate db ref
    # coordinates = models.ForeignKey(Coordinates, on_delete=models.CASCADE)
    coordinates_id = models.CharField(max_length=50,db_index=True,default='')

    # Official Data
    aadhar = models.CharField(
        max_length=30, default='', unique=True, db_index=True)
    aadhar_image = models.TextField(default='')
    pan = models.CharField(max_length=30, default='',
                           unique=True, db_index=True)
    pan_image = models.TextField(default='')

    store = models.CharField(max_length=50, default='', db_index=True)
    employer = models.CharField(max_length=50, default='')
    store_position = models.CharField(max_length=30, default='')

    # Date of joining and DOB
    date_join = models.DateField(default=timezone.now().date())
    dob = models.DateField(default= timezone.now().date())

    # Flush out if servei is marked not-allowed and will not be shown
    allowed = models.BooleanField(default=True)

    # Online---> feature to show availability --> True(Free and Open) False(Closed or Busy)(I)
    online = models.BooleanField(default=True)

    # address --> {'address_line_1',address_line_2,city,state,country,pin_code}
    address = JSONField(default=dict)
    pin_code = models.CharField(max_length=6, default='')
    country = models.CharField(max_length=20, default='INDIA')
    country_code = models.CharField(max_length=4, default='+91')

    # coordinates = CoordinateManager(coordinates_id)
    



# TODO:Fix Store
class Store(models.Model):

    store_name = models.CharField(max_length=50, default='')
    # creator
    creator = models.CharField(max_length=30, default=True, db_index=True)

    store_category = ArrayField(models.CharField(max_length=30), default=list)
    father_categories = ArrayField(
        models.CharField(max_length=30), default=list)

    # store Key
    store_key = models.CharField(
        max_length=50, db_index=True, default='', primary_key=True)
    employees = ArrayField(models.CharField(max_length=30), default=list)
    owners = ArrayField(models.CharField(max_length=30), default=list)

    # Array of itemIds
    product_line = ArrayField(models.CharField(
        max_length=20, db_index=True), default=list)

    # When non-gst store is created
    creators_profession = models.CharField(max_length=30, default='')
    creator_noob = models.BooleanField(default=False)

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
    coordinates_id = models.CharField(max_length=50,db_index=True,default='')

    seek_employee = models.BooleanField(default=False)
    seek_category = ArrayField(models.CharField(max_length=30), default=list)
    

    # Use strftime to set this
    opening_time = models.TimeField(default = timezone.now().time())
    closing_time = models.TimeField(default = timezone.now().time())
    twenty_four = models.BooleanField(default=False)

    # SingleBody Organisation--> gst not required
    store_type = models.CharField(max_length=2, default='SB')
    gst_requested = models.BooleanField(default=False)
    request_id = models.CharField(max_length=30, default='')
    gstin = models.CharField(max_length=30, default='', unique=True)

    # Online for serving
    online = models.BooleanField(default=True)

    # headings for keeping all store related sub cats
    headings = ArrayField(models.CharField(max_length=70), default=list)

    # allowed
    allowed = models.BooleanField(default=True)

    # Portfolio
    portfolio_updates = models.BooleanField(default=False)

    store_link = models.CharField(max_length=255,default='',db_index=True)
    store_template = models.TextField(default='')
    store_site_online = models.BooleanField(default=False)
    store_images = ArrayField(models.TextField(),default=list)

    # coordinates = CoordinateManager(coordinates_id)

    # Images
    image = models.TextField(default='')
    descriptions = JSONField(default=dict)

# Official Request Model


class OfficialRequest(models.Model):
    reference_id = models.CharField(
        max_length=30, default='', unique=True, primary_key=True)
    # Reference Type servei,de,store,customer
    reference_type = models.CharField(max_length=30, default='')

    phone_number = models.CharField(max_length=30, default='')
    permanent_address = models.TextField()
    status = models.CharField(max_length=10, default='')
    # gst or pan
    request_type = models.CharField(max_length=30, default='')

    # token of application
    token = models.TextField(default='')

    date_requested = models.DateField(default = timezone.now())
    date_applied = models.DateField(default= timezone.now())

    # applied or not
    applied = models.BooleanField(default=False)
    # dispatched requestee got or not
    dispatched = models.BooleanField(default=False)


class Order(models.Model):

    order_id = models.CharField(
        max_length=50, default='', unique=True, primary_key=True, db_index=True)

    # Dict with ItemId as key and another Dict as value with serveiId,amount and price as another keys
    # {'item_id':{'name':..,'servei_id':..,'quantity':...,'price':...,'effective_price':..,status:START/AMMO_PICKED/AMMO_DROPED,'unit':..,'measure:...}}
    items_cluster = JSONField(default=dict)
    # Servei as key and total price Locie to pay as value
    # servei_id as key, effective_price servei will get is value --filled after acceptance motor will fill this
    servei_price_cluster = JSONField(default=dict)

    """
    # servei_cluster: {
    # 'servei_id':{
    # 'items':[...],
    # 'store_key':...,
    # 'status': ACCEPTED/DECLINED/START (accepted & processing/ canceled),
    # 'effective_price':...
    # 'store_name':...,                                
    # },
    #  ......
    #  }
    # """
    servei_cluster = JSONField(default=dict)

    # For easing search of Orders asked to servei
    servei_list = ArrayField(models.CharField(max_length=50), default=list)

    # final servei--> those accepted
    # {'serveri_id':{'items':[...],'store_key':...}...}
    final_servei_cluster = JSONField(default=dict)

    # final items --> items got accepted
    #  {'item_id':{'quantity':...,'price':...,'effective_price':....,}}
    final_items = JSONField(default=dict)

    # rejected _items
    rejected_items = ArrayField(models.CharField(max_length=30), default=list)

    # Amount Customer to pay
    price = models.DecimalField(
        max_digits=7, decimal_places=2, default=0.00)
    effective_price = models.DecimalField(
        max_digits=7, decimal_places=2, default=0.00)

    # FOR ORder Status management
    # SEE  <TDMOS> in logic.md
    #  -- global status
    status = models.IntegerField(default=0000)

    # {'status.name':time,....}
    time_log = JSONField(default=dict)

    # DE Data first way and return way
    pilot_id_first = models.CharField(max_length=50, default='', db_index=True)
    pilot_id_return = models.CharField(
        max_length=50, default='', db_index=True)

    # Pilot details Name, Image and Phone Number
    pilot_name = models.CharField(max_length=50, default='')
    pilot_image = models.TextField(default='')
    pilot_number = models.CharField(max_length=15, default='')

    # Updates de position after de picked up the order and before completion
    position = gis_models.PointField(
        srid=4326, default=Point(0.00, 0.00, srid=4326))
    pilot_charge = models.DecimalField(
        max_digits=7, decimal_places=2, default=0.00)

    # Customer Id
    customer_id = models.CharField(max_length=15, db_index=True, default='')
    # Customer address
    customer_address = JSONField(default=dict)
    # customer_name
    customer_name = models.CharField(max_length=30, db_index=True, default='')
    # customer_location
    customer_coords = gis_models.PointField(
        srid=4326, default=Point(0.00, 0.00, srid=4326))

    # Date of order creation
    date_of_creation = models.DateField(default = timezone.now())
    # Time of order creation
    time_of_creation = models.TimeField(default = timezone.now())

    # creation = models.DateTimeField(auto_now=True)

    # Time left for delivery
    # time(datetime.datetime.now().hour,datetime.datetime.now().minute,datetime.datetime.now().seconds))
    time_left = models.TimeField(default= timezone.now().time())

    # Payment Methods and details
    payment_method = models.CharField(max_length=30, default='', db_index=True)
    payment_online = models.BooleanField(default=False)

    # delivery_type i.e SSU, UDS or SDU
    delivery_type = models.CharField(max_length=3, default='')

    
    # Order Type i.e MultiPick or Single Pick (67 or 77)
    order_type = models.IntegerField(default=00)
    cityCode = models.CharField(max_length=8, default='')
    otp = models.CharField(max_length=10, default='')


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
    address = JSONField(default=dict)
    coordinates_id = models.CharField(max_length=50,db_index=True,default='')
    account = models.OneToOneField(Account, on_delete=models.CASCADE)
    dob = models.DateField(default = timezone.now())
    extras = JSONField(default=dict)
    # coordinates = CoordinateManager(coordinates_id)


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
    coordinates_id = models.CharField(max_length=50,db_index=True,default='')
    # coordinates = CoordinateManager(coordinates_id)
    # No. of order on time
    weight = models.IntegerField(default=0, db_index=True)


class Rate(models.Model):
    rate = models.DecimalField(
        max_digits=4, decimal_places=2, default=00.00, db_index=True)
    categories = ArrayField(models.CharField(max_length=30), default=list)
    city_site = ArrayField(models.CharField(max_length=5), default=list)


class MeasureParam(models.Model):
    measure_id = models.CharField(
        max_length=50, primary_key=True, default='krispiforever@103904tilltheendoftheinfinity')
    # 0.5,1,10,25,50,100,150,200,500,
    units = ArrayField(models.DecimalField(max_digits=4, decimal_places=2, default=00.00), default=list)
    # kg,gm,sqrft,pkt.,..etc
    measure_params = ArrayField(models.CharField(max_length=30), default=list)


class Cart(models.Model):
    cart_id = models.CharField(max_length=75,default='',primary_key=True)
    clusters = ArrayField(JSONField(),default=list)
    price = models.DecimalField(max_digits=7,decimal_places=2,default=00.00)
    effective_price = models.DecimalField(max_digits=7,decimal_places=2,default=00.00)
    total_quantity = models.DecimalField(max_digits=5,decimal_places=2,default=00.00)
    customer_id = models.CharField(max_length=70,db_index=True,default='')


class LocieStoreSite(models.Model):
    uname = models.CharField(max_length=120,primary_key=True,default='')
    # Complete link uname.locie.co.in
    store_link = models.CharField(max_length=255,db_index=True,default='')
    # {"page_name":{"tag":"html","childrens":[]}}
    site = JSONField(default=dict)
    # {"page_name":{}}
    site_context = JSONField(default=dict)


