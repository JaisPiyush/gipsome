from .models import Coordinates,Pilot,Account,Order,Token,MobileDevice,PickDropOrder,Servei,Store,Customer,CityCode
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny,IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from .serverOps import pilot_id_creatore
from django.db.models import Q
from .customer_serializer import PickDropOrderSerializer
from django.contrib.gis.geos.point import Point
from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.measure import D
from .serializers import PilotSerializer,CoordinatesSerializer
from random import randint
from .tdmos import WORKING,SERVED,TDMOSystem,FINISHED
import json
import math

class OtpPulse:
    
    def __init__(self):
       
        self.data = self.random_with_n_digits(7)

    def __str__(self):
        return repr(self.data)

    def random_with_n_digits(self, n):
        range_start = 10**(n-1)
        range_end = (10**n)-1
        return randint(range_start, range_end)







class PilotCreate(APIView):
    """
     First Step is Account creation <param>aadhar,city,phone</param> => token + pilot_id + cityCode
     Second Step is PilotCreation using pilot_id to register rest of the details
     
    """
    permission_classes = [AllowAny]

    def post(self, request, format=None):
        data = json.loads(request.body)
        cityCode = CityCode.objects.filter(pin_codes__contains=[data['pin_code']])
        if cityCode:
            pilot_id = pilot_id_creatore(cityCode.cityCode,data['aadhar'],data)
            account = account = Account.objects.filter(account_id=data['pilot_id'])
            if not account :
                account = Account.objects.create_account(pilot_id,data['password'],'003',data['phone_number'])
            else:
                account = account.first()
            # Account does exist: time to create Pilot
            if not Pilot.objects.filter(pilot_id=pilot_id):
                # Pilot object with same pilot_id should not exist in the vicinity
                pilot = Pilot.objects.create(pilot_id=data['pilot_id'],account = account,
                                             first_name=data['first_name'],last_name=data['last_name'],phone_number=data['phone_number'],
                                             address = data['address'],cityCode=cityCode.cityCode,image = data['image'],weight=0,
                                             aadhar = data['aadhar'])
                for key in data.keys():
                    if key == 'aadhar_image':
                        pilot.aadhar_image=data['aadhar_image']
                    elif key == 'vehicle':
                        pilot.vehicle=data['vehicle']
                    elif key == 'vehicle_id':
                        pilot.vehicle_id = data['vehicle_id']
                    elif key == 'driving_license':
                        pilot.driving_license=data['driving_license']
                    elif key == 'vehicle_id':
                        pilot.vehicle_id = data['vehicle_id']
                    elif key == 'dl_image':
                        dl_image = data['dl_image']
                    elif key == 'email':
                        pilot.email = data['email']
                    elif key == 'coordinates':
                        pilot.coordinates = Point(data['coordinates']['lat'],data['coordinates']['long'])
                pilot.rating = 0.00
                pilot.save()
                token = Token.objects.get(user=account)
                return Response({"token":token.key,"pilot_id":pilot.pilot_id},status=status.HTTP_201_CREATED)
            
            else:
                # Pilot exist
                return Response({'error':'Pilot Already Exist'},status=status.HTTP_406_NOT_ACCEPTABLE)
        else:
            # Account Does not Exist
            return Response({'error':'City Not Servicable'},status=status.HTTP_404_NOT_FOUND)


        
class PilotManager:
    """
      Pilot Manager is responsible to find and dispatch order to pilot for an order.
      The basic algorithm for finding a Pilot.
      __future__

      shipment function calculates the distance between sender and receiver and create's pick and Drop
      order with all the details.
    """

    def __init__(self,order_id):
        self.order_id = order_id
        self.order = Order.objects.get(order_id=self.order_id)

    
    def pilot_compass(self,first=True):
        # Find Pilot
        #TODO: Not Implemented real pilot base
        pilots  = Pilot.objects.filter(cityCode=self.order.cityCode)
        final_pilot = pilots[0]
        for pilot in pilots:
            if pilot.weight == 0:
                final_pilot = pilot
                break
            elif final_pilot.weight > pilot.weight:
                final_pilot = pilot
        # order = Order.objects.get(order_id=self.order_id)
        if final_pilot:
            self.order.pilot_cluster[final_pilot.pilot_id] = {
                "pilot_name":final_pilot.first_name +" " + final_pilot.last_name,
                "pilot_phone_number":final_pilot.phone_number,
                "image":final_pilot.image,
                "coordinates":{"lat":final_pilot.coordinates[0],"long":final_pilot.coordinates[1]}
            }
            self.order.save()
            
        else:
            raise Exception()
    
    @staticmethod
    def fartest_point(servei_list,customer_coords):
        farthest_id = None
        distance = 0
        coords = Point(customer_coords['lat'],customer_coords['long'])
        for servei_id in servei_list:
           dis = coords.distance(Servei.objects.get(servei_id=servei_id)) * 100
           if dis > distance:
               distance = dis
               farthest_id = servei_id
        return [farthest_id,distance]
    
    @staticmethod
    def pilot_charge(distance,uds=False):
        if not uds:
            if distance <= 3:
                return 25
            elif distance >3:
                return math.floor((3*distance)+16)                
        else:
            if distance <= 3:
                return 40
            elif distance > 3:
                return math.ceil(2*distance + 34)


    def route_planner(self,returning=False):
        # Called only after servei's are finalised and Pilot is ready
        if not returning:
            servei_list = self.order.final_servei_cluster.keys()
            customer_coords = self.order.customer_stack['coordinates']
            pilot_coords = self.order.pilot_stack[-1]['coordinates']
            pilot_coord = Point(pilot_coords['lat'],pilot_coords['long'])
            customer_coord = Point(customer_coords['lat'],customer_coords['long'])
            del pilot_coords
            del customer_coords
            pointers =[]
            for serveiId in servei_list:
                serve_coordinates = Servei.objects.get(servei_id=serveiId).coordinates
                pointers.append({
                    "servei_id":serveiId,
                    "index":float(customer_coord.distance(serve_coordinates)/pilot_coord.distance(serve_coordinates))
                })
                param = lambda point: point['index']
                pointers.sort(reverse=True,key=param)
                self.order.route_planner = pointers 
        elif returning:
            # first is customer and last is the farthes servei from customer
            # origin is customer and destin is farthest servei
            # Pick or drop updates coordinates of pilot  every time
            servei_list = self.final_servei_cluster.keys()
            farthest_servei,distance = self.fartest_point(servei_list,self.order.customer_stack['coordinates'])
            farthest_coods = Servei.objects.get(servei_id=farthest_servei).coordinates
            customer_coord = Point(self.order.customer_stack['coordinates']['lat'],self.order.customer_stack['coordinates']['long'])
            pointers = []
            for serveiId in servei_list:
                if serveiId is not farthest_servei:
                    servei = Servei.objects.get(servei_id=serveiId).coordinates
                    pointers.append({
                        "servei_id":serveiId,
                        "index":float(farthest_coods.distance(servei)/customer_coord.distance(servei))
                    })
            param = lambda point: point['index']
            pointers.sort(reverse=True,key=param)
            pointers.append({
                "servei_id":farthest_servei
            })
            self.order.route_planner = pointers
        self.order.save()
           
    def sumarize_servei(self,servei_id):
        returnable_dict ={}
        clust = self.order.final_servei_cluster[servei_id]
        servei = Servei.objects.get(servei_id=servei_id)
        store = Store.objects.get(store_key=clust['store_key'])
        returnable_dict['id'] = servei_id
        returnable_dict['phone_number'] = servei.phone_number
        returnable_dict['address'] = servei.address
        returnable_dict['type'] = 'SERV'
        returnable_dict['transaction'] = 'PAY'
        returnable_dict['quantity'] = clust['quantity']
        returnable_dict['items'] = clust['items']
        returnable_dict['net_price'] = clust['net_price']
        returnable_dict['name'] = store.store_name
        return returnable_dict
    
    def sumarize_customer(self,customer_id):
        returnable_dict ={}
        returnable_dict['id'] = customer_id
        returnable_dict['phone_number'] = self.order.customer_stack['phone_number']
        returnable_dict['address'] = self.order.customer_stack['address']
        returnable_dict['type'] = 'CUST'
        returnable_dict['transaction'] = 'RECV'
        returnable_dict['net_price'] = self.order.price
        return returnable_dict
        

        
            
    

class PilotLogin(APIView):
    permission_classes = [AllowAny]

    def post(self, request, format=None):
        data = json.loads(request.body)
        account = Account.objects.filter(aadhar=data['aadhar'])
        if account:
            account = account.first()
            if account.check_password(data['password']):
                device = MobileDevice.objects.get_or_create(locie_partner=account.account_id,partnership='003')[0]
                device.registration_id = data['phone_token']
                token = Token.objects.get(user=account)
                return Response({'token':token.key,"pilot_id":account.account_id},status=status.HTTP_200_OK)
            else:
                return Response({},status=status.HTTP_401_UNAUTHORIZED)
        else:
            return Response({},status=status.HTTP_404_NOT_FOUND)


class PilotPickOrders(APIView):
    permission_classes = [AllowAny]

    def get(self,request,format=None):
        data = request.GET 
        pick_orders = PickDropOrder.objects.filter(Q(pilot_id=data['pilot_id'] & Q(picked=False)))
        picked_orders = PickDropOrder.objects.filter(Q(pilot_id=data['pilot_id'] & Q(picked=True)))
        if pick_orders or picked_orders:
            pick_serial = PickDropOrderSerializer(pick_orders,many=True)
            picked_serial = PickDropOrderSerializer(picked_orders,many=True)
            if pick_serial or picked_serial:
                return Response({"pick_orders":pick_serial.data,"picked_orders":picked_serial.data},status=status.HTTP_200_OK)
            else:
                return Response({"pick_orders":[],"picked_orders":[]},status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({"pick_orders":[],"picked_orders":[]},status=status.HTTP_400_BAD_REQUEST)



class PilotOrderUpdate(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self,request,format=None):
        """
          Possible actions are follow, pick drop

        """
        pass
