""" 'django.contrib.gis.db.models is models support for postgres with postgis extensions """

from django.contrib.gis.db import models as gis_models
from django.db import models
from django.contrib.gis.geos.point import Point


""" Below import are postgres specific fields required for various operatopns."""
from django.contrib.postgres.fields import ArrayField, JSONField

# Create your models here.

""""
 # Category Model -> Used as Linked list for creating Platform Category
 # if nextCat is 'items' --> then will dive into Items DB to search for items with prevCat == name
 # if prevCat is 'home' --> will be fathercats and the Categories to be shown on the home screen.
 # fatherCat will tell the Home Category of any Category or Item
 # nextcat will be used to locate the next categories using their name
 # on searching nextcat make sure each name has prevCat == CurrentCat
 """

class Category(models.Model):
    catId = models.CharField(max_length=30, db_index=True, default=True, unique=True)
    name = models.CharField(max_length=30, db_index=True, default='')
    prevCat = models.CharField(max_length=20, default='')
    image = models.TextField(default='')
    nextCat = ArrayField(models.CharField(max_length=30), default=list)
    fatherCat = models.CharField(max_length=30, default='')

    # Category type ---> FC(Father Category), SC (Sub- Category),MC (Micro Category) NC(Nano Category)
    catType = models.CharField(max_length=2, db_index=True, default='')

    #citySite --> Array Store cityCode which will have this category working
    # Servei won't be affected by this--> Servei will see all the options available
    # User screen will filter according to this
    # Upon adding first servei to any category--> server will automatically add the cityCode--> Check if cityCode is in citySite of category --> ifnot add the cityCode in the Array
    citySite = ArrayField(models.CharField(max_length=5, db_index=True), default=list)


    #Delivery Type --> SSU, SDU, UDS
    deliveryType = models.CharField(max_length=3, default='')

    #PickType --> OP (One Pick) , MP (Multi Pick)
    pickType= models.CharField(max_length=2, default='OP')

    #Post Complete Enabled
    # True will give Servei access to implement post-complete feature in item
    postCompleteEnable = models.BooleanField(default=False)



class Item(models.Model):
    name = models.CharField(max_length=70, db_index=True, default='')
    
    # itemId example --> UP536167!tem[time(till ms)]
    itemId = models.CharField(max_length=20, db_index=True, primary_key=True, default='')

    # use this locate all the items served by any servei    
    serveiId = models.CharField(max_length=20, db_index=True, default='')

    #Basic Location of Item 
    city = models.CharField(max_length=20,default='')
    cityCode = models.CharField(max_length=5, db_index=True, default='')

    allowed = models.BooleanField(default=True)
  

    price = models.DecimalField(max_digits=7, decimal_places=2, default=0.00)

    #effective price is the price after chopping the Locie's share amount --> amount the servei will get in hand
    effectivePrice = models.DecimalField(max_digits=7, decimal_places=2, default=0.00)
    images = ArrayField(models.CharField(max_length=255), size=4, default=list)
    description = models.TextField(default='')

    # Heading also Called NanoCat
    heading = models.CharField(max_length=30, default='None')
    
    """
    #Variant ---->
    # Will store JSON --> name,description,price,image

    """
    variant = JSONField(default=dict)
    #//TODO:  Variant Control 
    
    #MeasureParam ---> kg,sq.ft,gm,pck,pcs,etc
    measureParam = models.CharField(max_length=10, default='')

    # Inspection required
    inspection = models.BooleanField(default=False)

    #DeliveryType and PickType
    deliveryType = models.CharField(max_length=3, default='')
    pickType = models.CharField(max_length=2, default='OP')

    #Complete Time Complexity
    # On-Time Complete or Post time Complete
    completeType = models.CharField(max_length=2, default='OT')
    position = gis_models.PointField(srid=4326, default=Point(0.00,0.00, srid=4326))


    #Category Reference
    prevCat = models.CharField(max_length=30, default=True)
    fatherCat = models.CharField(max_length=30, default=True)

    postComplete = models.BooleanField(default=False)

    




# //TODO: We will add headings in servei which will be JSONField  and will contain itemId of every item falling insidde
# //TODO: A special view which will partial_update the headings json

class WebView(models.Model):
    webId = models.CharField(max_length=30,primary_key=True,db_index=True,default='',blank=False)
    serveiId = models.CharField(max_length=30,db_index=True,default='')
    templateId = models.CharField(max_length=30,default='')
    images = JSONField(default=dict)
    headings = JSONField(default=dict)
    contacts = JSONField(default=dict)
    #//TODO: Completion after template design

class Servei(models.Model):
    serveiId = models.CharField(max_length=30,db_index=True,primary_key=True,default='')
    cityCode = models.CharField(max_length=5,db_index=True,default='')

    #Coordinates
    position = gis_models.PointField(srid=4326, default=Point(0.00,0.00, srid=4326))

    #body_type --> I(Individual), O(Shop/Organisation/multi-body)
    body_type = models.CharField(max_length=2,db_index=True,default='I')

    #Proof Identifications According to India
    aadhar = models.CharField(max_length=20,unique=True,default='')
    pan = models.CharField(max_length=20,unique=True,default='')
    gstin = models.CharField(max_length=30,unique=True,default='')

    #Flush out if servei is marked not-allowed and will not be shown
    allowed = models.BooleanField(default=True)

    #Online---> feature to show availability --> True(Free and Open) False(Closed or Busy)(I)
    online = models.BooleanField(default=True)
    
    # WIll give sub-category functionality
    headings = ArrayField(models.CharField(max_length=40),default=list)

    #Will add itemId according to the headings
    headers = JSONField(default=dict)

    #address --> India
    address_line_1 = models.CharField(max_length=50,default='')
    address_line_2 = models.CharField(max_length=50,default='')
    city = models.CharField(max_length=30,default='')
    state = models.CharField(max_length=20,default='')
    pin_code = models.CharField(max_length=6,default='')
    country = models.CharField(max_length=20,default='INDIA')
    country_code = models.CharField(max_length=4,default='+91')




    



    

