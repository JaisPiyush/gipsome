from rest_framework import serializers
from rest_framework.authtoken.models import Token
from .models import Account, AccountManager
from .models import *
from .serverOps import servei_id_creatore, pilot_id_creatore


class AccountCreationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = '__all__'

class StoreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Store
        fields = '__all__'

class ItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = Item
        fields = '__all__'


    
class CityCodeSerializer(serializers.ModelSerializer):

    class Meta:
        model = CityCode
        fields= '__all__'

class OrderSerialzer(serializers.ModelSerializer):

    class Meta:
        model = Order
        fields= '__all__'

class PilotSerializer(serializers.ModelSerializer):
    class Meta:
        model= Pilot
        fields= '__all__'

class CoordinatesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Coordinates
        fields = '__all__'

class FetchedItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = Item
        fields = ('item_id', 'name', 'allowed', 'price', 'measure', 'ratings')

class StoreTeamSerializer(serializers.ModelSerializer):

    class Meta:
        model = Servei
        fields = ('first_name','last_name','phone_number','servei_id')

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'

class DefaultItemSerializer(serializers.ModelSerializer):
    class Meta:
        models = DefaultItems
        fields = '__all__'

class DefaultItemsSelection(serializers.ModelSerializer):

    class Meta:
        model = DefaultItems
        fields = ('item_id', 'name')

class HeadCategorySerializer(serializers.ModelSerializer):

    class Meta:
        model = Category
        fields = ('name','cat_id','image')

