from rest_framework import serializers
from .models import *

class CartSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cart
        fields = '__all__'

class StoreViewSerializer:

    def __init__(self,store,items):
        self.store = store
        self.items = items    
    def data(self):
        return {
            "store_key":self.store.store_key,
            "servei_id":self.store.creator,
            "name": self.store.store_name,
            "link": self.store.store_link,
            "image":self.store.image,
            "items": [SingelItemSerializer(item).data() for item in self.items]
        }

class SingelItemSerializer:

    def __init__(self,item):
        self.item = item
    
    def data(self):
        print(self.item.variants)
        return {
            "item_id":self.item.item_id,
            "name":self.item.name,
            "measure":self.item.measure_param,
            "unit":self.item.unit,
            "price": self.item.price,
            "effective_price": self.item.effective_price,
            "image": self.item.images[0],
            "variants": {"parameter":self.item.variants['parameter'],"variant": [ {"value":variant['value'],"price":variant['price'],"image":variant['image']} for variant in self.item.variants['variant']]} if self.item.variants else 'default'         
        }