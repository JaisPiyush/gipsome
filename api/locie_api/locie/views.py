from django.shortcuts import render
from . import models as models                       
from . import serializers as serializers               
from rest_framework.mixins import ListModelMixin as List,CreateModelMixin as Create
from rest_framework.mixins import UpdateModelMixin as Update,RetrieveModelMixin as Retreieve
from rest_framework.mixins import DestroyModelMixin as Delete
from rest_framework.generics import GenericAPIView as Generic
from django_filters.rest_framework import DjangoFilterBackend
# Create your views here.



###########-------------------------Category Section----------------------------------############



class LocieCatList(List,Generic):

    """"
    # Checks for the presenc of citySite in url --> filter using raw
    #  otherwise presents all as queryset
    # Can only be handled by Locie or Servei
    # Url---> api/croax/rosnops/eltit/lociecatlist
    #    ---> api/croax/rosnops/eltit/lociecatlist?name=''&prevCat=''&fatherCat=''
    # """

    def get_queryset(self):
        if self.kwargs.get('citySite'):
            query = self.kwargs.get('citySite')
            #Below Postgres Query will return all the Categories as list with cityCode in citySite
            return models.Category.objects.raw('SELECT * FROM locie_category WHERE %s IN citySite ', [query])
        else:
            return models.Category.objects.all()

        
    
    serializer_class = serializers.CategorySerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['prevCat','fatherCat','name']

    def get(self,request,*args,**kwargs):
        return self.list(request,*args,**kwargs)




class LocieCatOps(Create,Retreieve,Update,Delete,Generic):

    """
    # Gives option to Create, Update partial update and delete
    # Category will be affected by this
    # Can only be handled by Locie
    # Url --> api/croax/rosnops/eltit/lociecatops
    #      ---> api/croax/rosnops/eltit/lociecatops
    #  """

   

    queryset = models.Category.objects.all() 
    serializer_class = serializers.CategorySerializer
    


    def get(self,request,*args,**kwargs):
        return self.retrieve(request,*args,**kwargs)
    
    
    def post(self,request,*args,**kwargs):
        return self.create(request,*args,**kwargs)

    def put(self,request,*args,**kwargs):
        return self.partial_update(request,*args,**kwargs)
    
    def delete(self,request,*args,**kwargs):
        return self.destroy(request,*args,**kwargs)
    


    
##############-----------------Category Section Ends --------------------------------#############


#############------------------Item Section -----------------------------------------############

class LocieItemsList(List,Generic):
    """
    # Show List of items of locie
    # Filters ---> name,cityCode,serveiId,prevCat,fatherCat,itemId,allowed 
    # Url --> api/horcroax/etarbelec/locieitemslist
    """

    queryset = models.Item.objects.all()
    serializer_class = serializers.ItemEnterpriseSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['name','cityCode','serveiId','prevCat','fatherCat','itemId','allowed']

    def get(self,request,*args,**kwargs):
        return self.list(request,*args,**kwargs)


class LocieItemsOps(Create,Retreieve,Update,Delete,Generic):
    """
    # Retreive, Update, Delete Item using ---> itemId
    # Url --> api/horcroax/eterbelec/locieitemops<pk>"""
    queryset = models.Item.objects.all()
    serializer_class = serializers.ItemEnterpriseSerializer

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)
    
    def put(self, request, *args, **kwargs):
        return self.partial_update(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)


class ServeiItemsList(List,Generic):
    """
    # List of Items ---> serveiId
    # Url --> api/horcroax/trams/lciuq/serveiitemslist/(?P<serveiId>)/$
    """

    def get_queryset(self):
        return models.Item.objects.filter(serveiId=self.kwargs.get('serveiId'))
    
    serializer_class = serializers.ItemServeiSerializer

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

class ServeiItemsOps(Create,Retreieve,Update,Delete,Generic):
    """ 
    # Retreive, Update, Delete ---> itemId
    # Create item
    # Url --> api/horcroax/trams/lciuq/serveiitemsops/<pk>
    """

    queryset= models.Item.objects.all()    
    serializer_class = serializers.ItemServeiSerializer

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)
    
    def put(self, request, *args, **kwargs):
        return self.partial_update(request, *args, **kwargs)
    
    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)
    
    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)











