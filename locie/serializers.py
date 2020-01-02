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

class OtpLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = OTPLog
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

# class FetchedItemSerializer(serializers.ModelSerializer):
#     """
#       sends item_id,name,allowed,price,measure,ratings
#     """
#     class Meta:
#         model = Item
#         fields = ('item_id','name','allowed','price','measure','ratings')