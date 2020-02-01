# Imports
from django.contrib.gis.db import models as gis_models
from django.db import models
from django.contrib.gis.geos.point import Point
from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin
from django.contrib.auth.base_user import BaseUserManager
from django.contrib.postgres.fields import ArrayField, JSONField
from .serverOps import servei_id_creatore, pilot_id_creatore
#from  .serializers import AccountCreationSerializer
import datetime

# Authentication Model


class AccountManager(BaseUserManager):

    use_in_migrations = True

    def _create_account(self, account_id, password, relation,phone_number, is_superuser=False):
        print(account_id, password,  phone_number)
        if account_id and password and relation and phone_number:
            account = Account(account_id=account_id, relation=relation,
                              phone_number=phone_number,  is_superuser=is_superuser)
            account.set_password(password)
            account.save(using=self._db)
        else:
            raise ValueError('Details are incomplete!!')

    def create_account(self, account_id, password, relation,  phone_number):
        return self._create_account(account_id, password, relation, phone_number)

    def create_super_account(self, account_id, password, relation,  phone_number):
        return self._create_account(account_id, password, relation,  phone_number, is_superuser=True)


class Account(AbstractBaseUser, PermissionsMixin):
    account_id = models.CharField(
        max_length=30, unique=True, default='account_id')
    data_joined = models.DateField(auto_now_add=True)
    phone_number = models.CharField(max_length=15, default='', db_index=True)
    # phone_token = models.TextField(default='', db_index=True)
    is_superuser = models.BooleanField(default=False)
    # servei,de,customer
    # 002 : Servei, 002: Pilot, 009: customer, 001: Locie
    relation = models.CharField(max_length=20, default='', db_index=True)
    # FCM Token of device
    # device_token = models.TextField(default='')

    objects = AccountManager()

    USERNAME_FIELD = 'account_id'
    REQUIRED_FIELDS = ('phone_number', 'relation', 'phone_token')

    class Meta:
        verbose_name = ('account')
        verbose_name_plural = ('accounts')

    def pour(self, request):
        # Customer 009
        if request['relation'] == '009':
            self.account_id = request['phone_number']
        # Servei 001
        elif request['relation'] == '001':
            self.account_id = servei_id_creatore(CityManager().get_code(
                request['pin_code']), request['aadhar'], request['phone_number'])
        # DE 002
        elif request['relation'] == '002':
            self.account_id = pilot_id_creatore(CityManager().get_code(
                request['pin_code']), request['aadhar'], request['phone_number'])
        print(self.account_id)
        account = AccountManager().create_account(account_id=self.account_id,
                                                  password=request['password'], relation=request['relation'],phone_number=request['phone_number'])
        return account


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
    #unit 0.5,1...
    unit = models.DecimalField(max_digits=6,decimal_places=2,default=0.00)
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

    # varinats -> JSON -> {'parameter','variants':[]}
    variants = JSONField(default=dict)
    required_desc = ArrayField(models.CharField(max_length=50),default=list)
    #postComplete = models.BooleanField(default=False)
    ratings = models.DecimalField(max_digits=3, decimal_places=2, default=0.00)



# Position Database
class Coordinates(models.Model):
    unique_id = models.CharField(max_length=50, primary_key=True, default='')
    # 001 : Servei, 002: DE, 009: customer, 100: Locie , 904: Store
    relation = models.CharField(max_length=10,default='',db_index=True)
    reference_id = models.CharField(
        max_length=50, unique=True, db_index=True, default='')
    cityCode = models.CharField(max_length=6,db_index=True,default='')
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
    coordinates = models.OneToOneField(Coordinates,on_delete=models.CASCADE)


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
    date_join = models.DateField(default=datetime.datetime.today())
    dob = models.DateField(default=datetime.date.today())

    # Flush out if servei is marked not-allowed and will not be shown
    allowed = models.BooleanField(default=True)

    # Online---> feature to show availability --> True(Free and Open) False(Closed or Busy)(I)
    online = models.BooleanField(default=True)

   

    # address --> India
    address_line_1 = models.CharField(max_length=50, default='')
    address_line_2 = models.CharField(max_length=50, default='')
    city = models.CharField(max_length=30, default='')
    state = models.CharField(max_length=20, default='')
    pin_code = models.CharField(max_length=6, default='')
    country = models.CharField(max_length=20, default='INDIA')
    country_code = models.CharField(max_length=4, default='+91')


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
    cityCode = models.CharField(max_length=6,db_index=True,default='')

    # Coordinates data
    coordinates = models.OneToOneField(Coordinates,on_delete=models.CASCADE)

    seek_employee = models.BooleanField(default=False)
    seek_category = ArrayField(models.CharField(max_length=30), default=list)

    opening_time = models.TimeField()
    closing_time = models.TimeField()
    twenty_four = models.BooleanField(default=False)

    # SingleBody Organisation--> gst not required
    store_type = models.CharField(max_length=2, default='SB')
    gst_requested = models.BooleanField(default=False)
    request_id = models.CharField(max_length=30, default='')
    gstin = models.CharField(max_length=30, default='', unique=True)

    # Online for serving
    online = models.BooleanField(default=True)

    #headings for keeping all store related sub cats
    headings = ArrayField(models.CharField(max_length=70),default=list)

    # allowed
    allowed = models.BooleanField(default=True)

    # Portfolio
    portfolio_updates = models.BooleanField(default=False)

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

    date_requested = models.DateField(auto_now=True)
    date_applied = models.DateField(default=datetime.date.today())

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
    #    'servei_id':{
    #        'items':[...],
    #        'store_key':...,
    #        'status': ACCEPTED/DECLINED/START (accepted & processing/ canceled),
    #         'effective_price':...
    #         'store_name':...,                   
    #             
    # },
    #     ......
    #  }
    # """
    servei_cluster = JSONField(default=dict)

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
    pilot_id_first = models.CharField(max_length=50, default='',db_index=True)
    pilot_id_return = models.CharField(max_length=50, default='',db_index=True)

    # Pilot details Name, Image and Phone Number
    pilot_name = models.CharField(max_length=50, default='')
    plot_image = models.TextField(default='')
    pilot_number = models.CharField(max_length=15, default='')

    # Updates de position after de picked up the order and before completion
    position = gis_models.PointField(
        srid=4326, default=Point(0.00, 0.00, srid=4326))
    pilot_charge = models.DecimalField(max_digits=7, decimal_places=2, default=0.00)
    
    # Customer Id
    customer_id = models.CharField(max_length=15,db_index=True,default='')
    #Customer address
    customer_address = JSONField(default=dict)
    # customer_name
    customer_name = models.CharField(max_length=30,db_index=True,default='')
    #customer_location
    customer_coords = gis_models.PointField(srid=4326,default=Point(0.00,0.00,srid=4326))

   

    #Date of order creation
    date_of_creation = models.DateField(auto_now=True)
    # Time of order creation
    time_of_creation = models.TimeField(auto_now=True)

    # Time left for delivery
    # time(datetime.datetime.now().hour,datetime.datetime.now().minute,datetime.datetime.now().seconds))
    time_left = models.TimeField(default=datetime.datetime.now())

    #Payment Methods and details
    payment_method = models.CharField(max_length=30,default='',db_index=True)
    payment_online = models.BooleanField(default=False)

    # Order Type i.e MultiPick or Single Pick (67 or 77)
    delivery_type = models.IntegerField(default=00)

    # delivery_type i.e SSU, UDS or SDU
    order_type = models.CharField(max_length=3, default='')

    cityCode = models.CharField(max_length=8, default='')
    otp = models.CharField(max_length=10,default='')


    

    


# Category

class Category(models.Model):
    cat_id = models.CharField(
        max_length=30, db_index=True, default=True, unique=True)
    name = models.CharField(max_length=50, db_index=True, default='')
    prev_cat = models.CharField(max_length=20, default='')
    image = models.TextField(default='')
    next_cat = ArrayField(models.CharField(max_length=30), default=list)
    father_cat = models.CharField(max_length=30, default='')

    # Category type ---> FC(Father Category), SC (Sub- Category),MC (Micro Category) NC(Nano Category)

    cat_type = models.CharField(max_length=2, db_index=True, default='')

    # citySite --> Array Store cityCode which will have this category working
    # Servei won't be affected by this--> Servei will see all the options available
    # User screen will filter according to this
    # Upon adding first servei to any category--> server will automatically add the cityCode--> Check if cityCode is in citySite of category --> ifnot add the cityCode in the Array
    city_site = ArrayField(models.CharField(
        max_length=5, db_index=True), default=list)

    required_desc = ArrayField(models.CharField(
        max_length=50, db_index=True), default=list)

    # Delivery Type --> SSU, SDU, UDS
    delivery_type = models.CharField(max_length=3, default='')

    # PickType --> OP (One Pick) , MP (Multi Pick)
    pick_type = models.CharField(max_length=2, default='OP')

    # Post Complete Enabled
    # True will give Servei access to implement post-complete feature in item
    #postCompleteEnable = models.BooleanField(default=False)

    # Radiod if true will tell to put radio button
    radiod = models.BooleanField(default=False)

    #returnable if True than servei will accept the return and if false than servei wont take the return
    returnable = models.BooleanField(default=True)

    # Defaults items under this category
    # [{item_id,name},{item_id,name}]
    default_items = ArrayField(models.CharField(max_length=50), default=list)


# Default Items class
class DefaultItems(models.Model):
    item_id = models.CharField(max_length=50, primary_key=True)
    cat_id = models.CharField(max_length=50, db_index=True, default='')
    measure_param = models.CharField(max_length=30, default='')
    unit = models.CharField(max_length=4,default='')
    image = models.TextField(default='')
    pick_type = models.CharField(max_length=2, default='SP')
    delivery_type = models.CharField(max_length=3, default='')
    father_cate = models.CharField(max_length=50,default='',db_index=True)
    name = models.CharField(max_length=50,default='')
    inspection = models.BooleanField(default=False)
    description = models.TextField(default='')


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


# class OTPLog(models.Model):
#     # otp_id = models.AutoField(primary_key=True,default=randint(0,100))
#     created = models.DateField(default = datetime.date.today)
#     data = models.CharField(max_length=8,default='',db_index=True)
#     # order_id = ArrayField(models.CharField(max_length=50))


class PhoneToken(models.Model):
    token = models.TextField(default='')
    created = models.DateTimeField(auto_now_add=True)
    phone_number = models.CharField(default='', max_length=12, db_index=True)

#--------------------------RPMNS----------------------------------------------------------#
#-----------------------------------------------------------------------------------------#
class InterCorse(models.Model):
    # device to device notification
    sender = models.CharField(max_length=30, db_index=True, default='')
    receipient = models.CharField(max_length=30, db_index=True)
    content = JSONField(default=dict)


class OntoNotfication(models.Model):
    #  server to device notification
    receipient = models.CharField(max_length=30, default='')
    receipient_token = models.TextField(default='')
    created_at = models.DateTimeField(auto_now_add=True)
    # notification or data =[fetch-order, update-order, etc]
    typo = models.CharField(max_length=10, default='')
    content = JSONField(default=dict)



from fcm_django.models import AbstractFCMDevice,FCMDeviceManager
# class MobileDeviceManager(FCMDeviceManager):
#     def create_device(self, registration_id, **extras):
#         # Checking if it exist
#         if MobileDevice.objects.filter(registration_id=registration_id):
#             device = MobileDevice.objects.filter(
#                 registration_id=registration_id)

#             # customer is applying for servei or de
#             if device.customer_id and device.partnership == '':
#                 device.update(locie_partner=extras['locie_partner'])
#                 device.update(partnership=extras['partnership'])
#                 device.save()
#             # servei/de is applying for customer
#             elif device.customer_id is None and device.partnership is not None:
#                 device.update(customer_id=extras['customer_id'])
#                 device.save()

#             # # customer and servei/de both already exist
#             # elif device.customer_id is not None and device.partnership is not None:
#             #     return -1

#         else:
#             #  customer is creating a device
#             if 'customer_id' in extras.keys()and 'locie_partner' not in extras.keys():
#                 device = MobileDevice(
#                     registration_id=registration_id,  customer_id=extras['customer_id'],type=extras['type'])
#                 device.save()
#             # servei/de is creating a device
#             elif 'locie_partner' in extras.keys() and 'customer_id' not in extras.keys():
#                 device = MobileDevice(registration_id=registration_id,type=extras['type'],
#                                       locie_partner=extras['locie_partner'], partnership=extras['partnership'])
#                 device.save()
#             # applied for both at same time
#             # theoretical
#             elif 'locie_partner' in extras.keys() and 'customer_id'  in extras.keys():
#                 device = MobileDevice(registration_id=registration_id,type=extras['type'],
#                                       customer_id=extras['customer_id'], locie_partner=extras['locie_partner'], partnership=extras['partnership'])
#                 device.save()


class MobileDevice(AbstractFCMDevice):

    # Id of receipient servei_id,pilot_id,customer_id
    # customer_id = models.CharField(max_length=50, default='', db_index=True)
    # receipient 'servei/customer/de
    # if receipient is customer then locie_partner will have servei_id or pilot_id
    locie_partner = models.CharField(max_length=50, default='', db_index=True)
    # 001 : Locie, 002:Servei, 003:Pilot, 009:Customer
    partnership = models.CharField(max_length=10, default='', db_index=True)

    # object = MobileDeviceManager()

    class Meta:
        verbose_name = ('FCM device')
        verbose_name_plural = ('FCM devices')

class CustomerDevice(AbstractFCMDevice):
    customer_id = models.CharField(max_length=50, default='', db_index=True)

    # object = MobileDeviceManager()











#----------------------------------RPMNS---------------------------------------------------#
#------------------------------------------------------------------------------------------#

class Customer(models.Model):
    customer_id = models.CharField(max_length=50,primary_key=True,default='')
    gender = models.CharField(max_length=10,default='')
    address = JSONField(default=dict)
    coord = models.OneToOneField(Coordinates,on_delete=models.CASCADE)
    account = models.OneToOneField(Account,on_delete=models.CASCADE)
    dob = models.DateField(auto_now_add=False)


#------------------DeliverExecutive-------------------------------------------------------------
class Pilot(models.Model):
    pilot_id = models.CharField(max_length=50,primary_key=True,default='')
    account = models.OneToOneField(Account,on_delete = models.CASCADE)

    # Personal Details
    first_name = models.CharField(max_length=30,default='')
    last_name = models.CharField(max_length=30,default='')
    address = JSONField(default=dict)
    cityCode = models.CharField(max_length=6,default='',db_index=True)
    image = models.TextField(default='')

    #Phone Number and Email
    phone_number = models.CharField(max_length=12,db_index=True,default='')
    email = models.EmailField(db_index=True,null=True,blank=True)

    # Vehicle and official data
    aadhar = models.CharField(max_length=30,unique=True,db_index=True,default='')
    aadhar_image = models.TextField(default='')
    #Vehicle type BIK:BIKE/SCOOTY, CYC:CYCLE, TRICYC:TriCycle = Rickshaw,cart
    vehicle = models.CharField(max_length=10,default='')
    # BIKE/SCOOTY Licence Plate
    vehicle_id = models.CharField(max_length=20,db_index=True,unique=True,default='')
    # Driving License Bike and Scooty
    driving_license = models.CharField(max_length=30,db_index=True,default='')
    dl_image = models.TextField(default='')
    
    # Rating of Pilot
    rating = models.DecimalField(max_digits=3,decimal_places=2,default=0.00)

    #Coords id
    coordinates = models.OneToOneField(Coordinates,on_delete=models.CASCADE)
    #No. of order on time
    weight = models.IntegerField(default=0,db_index=True)
    

    
class Rate(models.Model):
    rate = models.DecimalField(max_digits=4,decimal_places=2,default=00.00,db_index=True)
    categories = ArrayField(models.CharField(max_length=30),default=list)
    city_site = ArrayField(models.CharField(max_length=5),default=list)


class MeasureParam(models.Model):
    measure_id = models.CharField(max_length=30,primary_key=True,default='krispiforever@103904tilltheendoftheinfinity')
    # 0.5,1,10,25,50,100,150,200,500,
    units = ArrayField(models.IntegerField(),default=list)
    # kg,gm,sqrft,pkt.,..etc
    measure_params = ArrayField(models.CharField(max_length=30),default=list)
