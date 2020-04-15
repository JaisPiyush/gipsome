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
        model = DefaultItems
        fields = '__all__'

class DefaultItemsSelection(serializers.ModelSerializer):

    class Meta:
        model = DefaultItems
        fields = ('item_id', 'name')

class HeadCategorySerializer(serializers.ModelSerializer):

    class Meta:
        model = Category
        fields = ('name','cat_id','image')

class CategoryModel(object):

    def __init__(self, category):
        self.name = category.name
        self.cat_type = category.cat_type
        self.cat_id = category.cat_id
        self.prev_cat = category.prev_cat
        self.next_cat = category.next_cat [::1] if category.next_cat else []
        self.image = category.image
        self.required_desc = category.required_desc
        self.delivery_type = category.delivery_type
        self.radiod = category.radiod
        self.returnable = category.returnable
        self.default_items = category.default_items [::1] if category.default_items else []


class DefaultItemModel(object):

    def __init__(self,item):
        self.item_id = item.item_id
        self.name = item.name
        self.cat_id = item.cat_id
        self.unit = item.unit
        self.measure_param = item.measure_param
        self.pick_type = item.pick_type
        self.image = item.image
        self.delivery_type = item.delivery_type
        self.inspection = item.inspection
        self.description = item.description




class CategorySelectionSerializer:

    def __init__(self,query_set):
        self.query_set = query_set
        self.returnable = []
        print(self.query_set)
        for category in self.query_set:
            if isinstance(category,CategoryModel):
                self.returnable.append(self.category_serialize(category))
    
    def data(self):
        return self.returnable

    def category_serialize(self,category):
        data = {}
        print(type(category))
        if isinstance(category,str):
            print(category)
        data["name"] = category.name
        data["cat_type"] = category.cat_type
        data["cat_id"] = category.cat_id
        data["prev_cat"] = category.prev_cat
        if data["cat_type"] == "FC":
            data["next_cat"] = [self.category_serialize(nextcateg) for nextcateg in category.next_cat] if category.next_cat else []            
        data["image"] = category.image
        data["required_desc"] = category.required_desc
        data["delivery_type"] = category.delivery_type
        data["radiod"] = 1 if category.radiod else 0
        data["returnable"] = 1 if category.returnable else 0
        data["default_items"] = [self.default_item_serialize(defaultitem) for defaultitem in category.default_items] if category.default_items else []
        return data


    def default_item_serialize(self,defaultitem):
        return {
            "item_id":defaultitem.item_id,
            "name":defaultitem.name,
            "cat_id":defaultitem.cat_id,
            "unit":defaultitem.unit,
            "measure_param":defaultitem.measure_param,
            "image":defaultitem.image,
            "pick_type":defaultitem.pick_type,
            "delivery_type":defaultitem.delivery_type,
            "inspection":1 if defaultitem.inspection else 0,
            "description":defaultitem.description
        }


class MeasureParamSerializer(serializers.ModelSerializer):

    class Meta:
        model = MeasureParam
        fields = '__all__'


class RateSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Rate
        fields = '__all__'