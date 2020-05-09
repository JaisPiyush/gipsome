from ..models import Pilot,Account,Order,Token,MobileDevice,PickDropOrder,Servei,Store,Customer,CityCode
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny,IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from ..gadgets.serverOps import pilot_id_creatore
from django.db.models import Q
from ..customer.customer_serializer import PickDropOrderSerializer
from .pilot_manager import PilotManager
from ..serializers import PilotSerializer
from django.contrib.gis.geos.point import Point
from random import randint
from ..tdmos.tdmos import TDMOSystem,WORKING,CREATED,FINISHED,FAILED
from ..gadgets.rpmns import API_KEY
import json
import math
from .pilot_serializer import *



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
            cityCode = cityCode.first()
            pilot_id = pilot_id_creatore(cityCode.cityCode,data['aadhar'],data['phone_number'])
            account = account = Account.objects.filter(account_id=pilot_id)
            if not account :
                account = Account.objects.create_account(pilot_id,data['password'],'003',data['phone_number'])
            else:
                account = account.first()
            # Account does exist: time to create Pilot
            if not Pilot.objects.filter(pilot_id=pilot_id):
                # Pilot object with same pilot_id should not exist in the vicinity
                pilot = Pilot.objects.create(pilot_id=pilot_id,account = account,
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
          Possible actions are follow, pick, drop 

          If action is follow then send primary details and check len(pick_list) == len(senders_list)
           If True : len(droped_list) == len(receivers_list): False -> Then send receivers_list[len(droped_list)] data 
                     True: Order is Finished
           If False : send data of senders_list[len(picked_list)]
           Sent data will contain type:SERV/CUST, transaction : RECV/PAY items name id phon_number geolocation address
                                  action:PICK/DROP quantity net_price(amount to give or take)
            If SSU and data.type is CUST than RECV, If UDS and pilot.cluster.length ==1 then net_price = 0 else PAY and net_price is set

        """
        data = json.loads(request.body)
        order = Order.objects.get(order_id=data['order_id'])
        if data['action'] == 'FOLLOW':
            returning_data = PilotManager(order.order_id).next_task()
            return Response(returning_data,status=status.HTTP_200_OK)
        elif data['action'] == 'PICK':
            # sender_id is send with type CUST/SERV if uds and add id to picked_list, 
            # if second round than ender_id servei status to SERVED.
            # if SSU servei -> customer, add id to picked_list and if type is SERV set status to SERVED
            # pilot coordinates are updated every time
            pilot_id = data['pilot_id']
            pilot = Pilot.objects.get(pilot_id=pilot_id)
            pilot.coordinates = Point(data['coordinates']['lat'],data['coordinates']['long'])
            pilot.save()
            order.pilot_cluster[pilot_id]['coordinates'] = data['coordinates']
            order.save()
            if order.delivery_type == 'UDS' and len(order.picked_list) != len(order.sender_list):
                if len(order.pilot_cluster.keys()) == 1:
                    order.picked_list.append(data['sender_id'])
                    order.save()
                    returning_data = PilotManager(order.order_id).next_task()
                    return Response(returning_data,status=status.HTTP_200_OK)
                elif len(order.pilot_cluster.keys()) > 1:
                    order.picked_list.append(data['sender_id'])
                    order.final_servei_cluster[data['sender_id']]['status'] = SERVED
                    order.save()
                    returning_data = PilotManager(order.order_id).next_task()
                    return Response(returning_data,status=status.HTTP_200_OK)
            elif order.delivery_type == 'SSU' and len(order.picked_list) != len(order.sender_list):
                # Pick from servei and mark served
                order.picked_list.append(data['sender_id'])
                order.final_servei_cluster[data['servei_id']]['status'] = SERVED
                order.save()
                returning_data = PilotManager(order.order_id).next_task()
                return Response(returning_data,status=status.HTTP_200_OK)
            elif order.delivery_type == 'PAD' and len(order.picked_list) != len(order.sender_list):
                order.picked_list.append(data['sender_id'])
                order.save()
                returning_data = PilotManager(order.order_id).next_task()
                return Response(returning_data,status=status.HTTP_200_OK)
            else:
                returning_data = PilotManager(order.order_id).next_task()
                return Response(returning_data,status=status.HTTP_200_OK)

        elif data['action'] == 'DROP':
            # If Uds and pilotcluster == 1, then droping to servei setting their status to WORKING.
            # if len(droped_list) == len(receivers_list) after adding data then signof pilot, seting order status to WROKING else send next_task
            # elif pilotcluster >1 , then droping to customer.
            # add customer to droped_list and set order status to finished
            # if SSU , then add customer to dropped list and set Order status to finished
            pilot_id = data['pilot_id']
            pilot = Pilot.objects.get(pilot_id=pilot_id)
            pilot.coordinates = Point(data['coordinates']['lat'],data['coordinates']['long'])
            pilot.save()
            order.pilot_cluster[pilot_id]['coordinates'] = data['coordinates']
            order.save()
            if order.delivery_type == 'UDS':
                if len(order.pilot_cluster.keys()) == 1:
                    # Droping to servei's after which pilot's job will demise, but before that , we have to check that len of droped == receiver after drop 
                    # if yes than set pilot free and global status to WORKING 
                    order.droped_list.append(data['receiver_id'])
                    order.final_servei_cluster[data['receiver_id']]['status'] = WORKING
                    order.save()
                    if len(order.droped_list) == len(order.receivers_list):
                        TDMOSystem(order).status_setter(WORKING)
                        order.save()
                        return Response({"action":"finish","order_id":order.order_id},status=status.HTTP_204_NO_CONTENT)
                    else:
                        returning_data['secondary'] = PilotManager(order.order_id).next_task()
                        return Response(returning_data,status=status.HTTP_200_OK)
                elif len(order.pilot_cluster.dict_keys()) > 1:
                    # Droping back to customer 
                    order.droped_list.append(data['receiver_id'])
                    TDMOSystem(order).status_setter(FINISHED)
                    order.save()
                    return Response({"action":"finish","order_id":order.order_id},status=status.HTTP_204_NO_CONTENT)
            elif order.delivery_type == 'SSU' or order.delivery_type == 'PAD':
                # Droping back to Customer and finishing order
                order.droped_list.append(data['receiver_id'])
                TDMOSystem(order).status_setter(FINISHED)
                order.save()
                return Response({"action":"finish","order_id":order.order_id},status=status.HTTP_204_NO_CONTENT)
            


                    
class PilotNewOrder(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, format=None):
        data = request.GET 
        orders = Order.objects.filter(Q(pilot_cluster__has_key = data['pilot_id']) & Q(~Q(status = FINISHED) & ~Q(status = FAILED)))
        if orders:
            serialized = PilotOrderSerializer(orders)
            return Response({"orders":serialized.data()},status=status.HTTP_200_OK)
        else:
            return Response({"orders":[]},status=status.HTTP_200_OK)
                        

                


            

                
                    




      
