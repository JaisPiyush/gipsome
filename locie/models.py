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

    def _create_account(self, account_id, password, relation, phone_token, phone_number, is_superuser=False):
        print(account_id, password, phone_token, phone_number)
        if account_id and password and relation and phone_number and phone_token:
            account = Account(account_id=account_id, relation=relation,
                              phone_number=phone_number, phone_token=phone_token, is_superuser=is_superuser)
            account.set_password(password)
            account.save(using=self._db)
        else:
            raise ValueError('Details are incomplete!!')

    def create_account(self, account_id, password, relation, phone_token, phone_number):
        return self._create_account(account_id, password, relation, phone_token, phone_number)

    def create_super_account(self, account_id, password, relation, phone_token, phone_number):
        return self._create_account(account_id, password, relation, phone_token, phone_number, is_superuser=True)


class Account(AbstractBaseUser, PermissionsMixin):
    account_id = models.CharField(
        max_length=30, unique=True, default='account_id')
    data_joined = models.DateField(auto_now_add=True)
    phone_number = models.CharField(max_length=15, default='', db_index=True)
    phone_token = models.TextField(default='', db_index=True)
    is_superuser = models.BooleanField(default=False)
    # servei,de,customer
    # 001 : Servei, 002: DE, 009: customer, 100: Locie
    relation = models.CharField(max_length=20, default='', db_index=True)
    # FCM Token of device
    device_token = models.TextField(default='')

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
                                                  password=request['password'], relation=request['relation'], phone_token=request['phone_token'], phone_number=request['phone_number'])
        return account


# Items Model


class Item(models.Model):

    # TODO: Add Variant

    name = models.CharField(max_length=30, db_index=True, default='')
    # itemId example --> UP536167!tem[time(till ms)]
    item_id = models.CharField(
        max_length=20, db_index=True, primary_key=True, default='')
    # Store Key
    store_key = models.CharField(max_length=50, db_index=True, default='')
    # use this locate all the items served by any servei
    servei_id = models.CharField(max_length=20, db_index=True, default='')
    # Basic Location of Item
    city = models.CharField(max_length=20, default='')
    cityCode = models.CharField(max_length=5, db_index=True, default='')
    # allowed to be featured on locie
    allowed = models.BooleanField(default=True)

    price = models.DecimalField(max_digits=7, decimal_places=2, default=0.00)

    # effective price is the price after chopping the Locie's share amount
    # amount the servei will get in hand
    effectivePrice = models.DecimalField(
        max_digits=7, decimal_places=2, default=0.00)
    images = ArrayField(models.CharField(max_length=255), size=4, default=list)
    description = models.TextField(default='')

    # Heading also Called NanoCat
    heading = models.CharField(max_length=30, default='None')

    # MeasureParam ---> kg,sq.ft,gm,pck,pcs,etc
    measureParam = models.CharField(max_length=10, default='')

    # Inspection required
    inspection = models.BooleanField(default=False)

    # DeliveryType and PickType SSU.UDS.SDU
    deliveryType = models.CharField(max_length=3, default='')
    #SinglePick or MultiPick
    pickType = models.CharField(max_length=2, default='SP')

    # Complete Time Complexity
    # On-Time Complete or Post time Complete
    #completeType = models.CharField(max_length=2, default='OT')
    #position = gis_models.PointField(srid=4326, default=Point(0.00,0.00, srid=4326))

    # Category Reference
    prevCat = models.CharField(max_length=30, default=True)
    fatherCat = models.CharField(max_length=30, default=True)

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
        max_length=30, db_index=True, primary_key=True, default='')
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

    # Contacts Mobile Number and emails
    contacts = JSONField(default=dict)

    # Address first_line,secon_line,street,city,state,pin_code as key
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

    # allowed
    allowed = models.BooleanField(default=True)

    # Portfolio
    portfolio_updates = models.BooleanField(default=False)

    # Images
    thumbnail = models.TextField(default='')
    images = ArrayField(models.TextField(), default=list)
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
        max_length=30, default='', unique=True, primary_key=True, db_index=True)

    # Item Data
    # List with Item Id
    items = ArrayField(models.CharField(max_length=30), default=list)
    # Dict with ItemId as key and another Dict as value with serveiId,amount and price as another keys
    # 'item_id':['servei_id,price,eff_price,amount]
    items_data = JSONField(default=dict)
    # ServeiId list  Used for Notification Services
    serveis = ArrayField(models.CharField(max_length=30), default=list)
    # Dict of serveiId as key and List of Items as values
    servei_cluster = JSONField(default=dict)
    # Servei as key and total price Locie to pay as value
    # servei_id as key, effective_price servei will get is value --filled after acceptance motor will fill this
    servei_price_cluster = JSONField(default=dict)

    #stores cluster, store_keys as List
    store_cluster = ArrayField(models.CharField(max_length=50),default=dict)

    # final servei--> those accepted
    final_servei = ArrayField(models.CharField(max_length=30), default=list)
    # final items --> items got accepted
    final_items = ArrayField(models.CharField(max_length=30), default=list)
    # rejected _items
    rejected_items = ArrayField(models.CharField(max_length=30), default=list)
    # Key pait of servei: items for better consideration
    final_pair = JSONField(default=dict)

    # Amount Customer to pay
    customer_price = models.DecimalField(
        max_digits=7, decimal_places=2, default=0.00)
   
  

    # FOR ORder Status management
    # SEE  <TDMOS> in logic.md
    status = models.CharField(max_length=30, default='')
    response = models.IntegerField(default=0000)
    # Logs response as key and time as value
    time_log = JSONField(default=dict)

    # DE Data first way and return way
    pilot_id_first = models.CharField(max_length=30, default='')
    pilot_id_return = models.CharField(max_length=30, default='')
    # Updates de position after de picked up the order and before completion
    de_position = gis_models.PointField(
        srid=4326, default=Point(0.00, 0.00, srid=4326))
    
    # Customer Id
    customer_id = models.CharField(max_length=15,db_index=True,default='')
    #Customer address
    customer_address = models.TextField(default='')
    #customer_location
    customer_coords = models.TextField(default='')

    # Final response i.e Successfull or Cancelled
    final_response = models.IntegerField(default=0000)

    #Date of order creation
    date_of_creation = models.DateField(auto_now_add=True)
    # Time of order creation
    time_of_creation = models.TimeField(auto_now_add=True)

    # Time left for delivery
    # time(datetime.datetime.now().hour,datetime.datetime.now().minute,datetime.datetime.now().seconds))
    time_left = models.TimeField(default=datetime.datetime.now())

    # Order Type i.e MultiPick or Single Pick (67 or 77)
    order_type = models.IntegerField(default=00)

    # delivery_type i.e SSU, UDS or SDU
    delivery_type = models.CharField(max_length=3, default='')

    cityCode = models.CharField(max_length=8, default='')

    


# Category

class Category(models.Model):
    cat_id = models.CharField(
        max_length=30, db_index=True, default=True, unique=True)
    name = models.CharField(max_length=30, db_index=True, default='')
    prevCat = models.CharField(max_length=20, default='')
    image = models.TextField(default='')
    nextCat = ArrayField(models.CharField(max_length=30), default=list)
    fatherCat = models.CharField(max_length=30, default='')

    # Category type ---> FC(Father Category), SC (Sub- Category),MC (Micro Category) NC(Nano Category)

    catType = models.CharField(max_length=2, db_index=True, default='')

    # citySite --> Array Store cityCode which will have this category working
    # Servei won't be affected by this--> Servei will see all the options available
    # User screen will filter according to this
    # Upon adding first servei to any category--> server will automatically add the cityCode--> Check if cityCode is in citySite of category --> ifnot add the cityCode in the Array
    citySite = ArrayField(models.CharField(
        max_length=5, db_index=True), default=list)

    requiredDesc = ArrayField(models.CharField(
        max_length=50, db_index=True), default=list)

    # Delivery Type --> SSU, SDU, UDS
    deliveryType = models.CharField(max_length=3, default='')

    # PickType --> OP (One Pick) , MP (Multi Pick)
    pickType = models.CharField(max_length=2, default='OP')

    # Post Complete Enabled
    # True will give Servei access to implement post-complete feature in item
    #postCompleteEnable = models.BooleanField(default=False)

    # Radiod if true will tell to put radio button
    radiod = models.BooleanField(default=False)

    # Defaults items under this category
    default_items = ArrayField(models.CharField(max_length=50), default=list)


# Default Items class
class DefaultItems(models.Model):
    item_id = models.CharField(max_length=50, primary_key=True)
    cat_id = models.CharField(max_length=50, db_index=True, default='')
    measure_pram = models.CharField(max_length=30, default='')
    image = models.TextField(default='')
    pick_type = models.CharField(max_length=2, default='SP')
    delivery_type = models.CharField(max_length=3, default='')

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


class OTPLog(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    data = models.CharField(max_length=6, default='')
    # Phone Number
    phone_number = models.CharField(max_length=12, default='', db_index=True)
    otp_cred = models.CharField(max_length=40, default='', primary_key=True)
    closed = models.BooleanField(default=False)
    closing = models.DateTimeField(null=True, blank=True)


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
    type = models.CharField(max_length=10, default='')
    content = JSONField(default=dict)



from fcm_django.models import AbstractFCMDevice,FCMDeviceManager
class MobileDeviceManager(FCMDeviceManager):
    def create_device(self, registration_id, type, **extras):
        # Checking if it exist
        if MobileDevice.objects.filter(registration_id=registration_id):
            device = MobileDevice.objects.filter(
                registration_id=registration_id)

            # customer is applying for servei or de
            if device.customer_id and device.partnership == '':
                device.update(locie_partner=extras['locie_partner'])
                device.update(partnership=extras['partnership'])
                device.save()
            # servei/de is applying for customer
            elif device.customer_id is None and device.partnership is not None:
                device.update(customer_id=extras['customer_id'])
                device.save()

            # customer and servei/de both already exist
            elif device.customer_id is not None and device.partnership is not None:
                return -1

        else:
            #  customer is creating a device
            if extras['customer_id'] is not None and extras['locie_partner'] is None:
                device = MobileDevice(
                    registration_id=registration_id, type=type, customer_id=extras['customer_id'])
                device.save()
            # servei/de is creating a device
            elif extras['locie_partner'] is not None and extras['customer_id'] is None:
                device = MobileDevice(registration_id=registration_id, type=type,
                                      locie_partner=extras['locie_partner'], partnership=extras['partnership'])
                device.save()
            # applied for both at same time
            # theoretical
            elif extras['locie_partner'] is not None and extras['customer'] is not None:
                device = MobileDevice(registration_id=registration_id, type=type,
                                      customer_id=extras['customer_id'], locie_partner=extras['locie_partner'], partnership=extras['partnership'])
                device.save()


class MobileDevice(AbstractFCMDevice):

    # Id of receipient servei_id,pilot_id,customer_id
    customer_id = models.CharField(max_length=30, default='', db_index=True)
    # receipient 'servei/customer/de
    # if receipient is customer then locie_partner will have servei_id or pilot_id
    locie_partner = models.CharField(max_length=30, default='', db_index=True)
    # de or servei
    partnership = models.CharField(max_length=10, default='', db_index=True)

    object = MobileDeviceManager()

    class Meta:
        verbose_name = ('FCM device')
        verbose_name_plural = ('FCM devices')

#----------------------------------RPMNS---------------------------------------------------#
#------------------------------------------------------------------------------------------#

class Customer(models.Model):
    customer_id = models.CharField(max_length=20,primary_key=True,default='')
    gender = models.CharField(max_length=10,default='')
    address = JSONField(default=dict)
    coord = models.OneToOneField(Coordinates,on_delete=models.CASCADE)
    account = models.OneToOneField(Account,on_delete=models.CASCADE)
    dob = models.DateField(auto_now_add=False)


#------------------DeliverExecutive-------------------------------------------------------------
class Pilot(models.Model):
    pilot_id = models.CharField(max_length=30,primary_key=True,default='')
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
    

    


