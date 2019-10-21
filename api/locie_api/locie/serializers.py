from rest_framework import serializers
# VSCODE is presenting pylint error on importing rest_framework
# STACKOVERFLOW suggests ---> due to virtual enviroment settings error


from .models import Category,Item


class CategorySerializer(serializers.ModelSerializer):
    """
    # Show required data --> name, image,nextCat,fatherCat
    """
    class Meta:
        model = Category
        fields = '__all__'

class ItemEnterpriseSerializer(serializers.ModelSerializer):
    """
    # This Serializer will show data to locie and Servei
    # Data --> name,itemId, sereviId,cityCode,position,price,effectiveprice,image,measureParam
    #//TODO: Add Variant features
    """
    class Meta:
        model = Item
        fields = '__all__'


class ItemServeiSerializer(serializers.ModelSerializer):
    """
    # This Serializer will show data to Servei
    # Data --> name, itemId,serveiId,cityCode,city,position,price,image,measureParam,
    # image,inspection,deliveryType,pickType,postComplete,varaiant,allowed,prevCat,fatherCat
    # //TODO: Add Variant fetaure
    """

    class Meta:
        model = Item
        fields = ['name','itemId','serveiId','variant','allowed','cityCode','city','position','price','images','measureParam','inspection','deliveryType','pickType','postComplete']






