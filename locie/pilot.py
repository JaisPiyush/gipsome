from .models import Coordinates,Pilot,Account,Order
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny,IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from .serverOps import coord_id_generator,quickSort_pilot
from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.geos import fromstr
from django.contrib.gis.measure import D
from .serializers import PilotSerializer,CoordinatesSerializer
from random import randint


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
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, format=None):
        account = Account.objects.get(account_id=request.POST['pilot_id'])
        if account :
            # Account does exist: time to create Pilot
            if not Pilot.objects.get(pilot_id=request.POST['pilot_id']):
                # Pilot object with same pilot_id should not exist in the vicinity
                pilot = Pilot.objects.create(pilot_id=request.POST['pilot_id'],account = account,
                                             first_name=request.POST['first_name'],last_name=request.POST['last_name'],
                                             address = request.POST['address'],cityCode=request.POST['cityCode'],image = request.POST['image'],
                                             aadhar = request.POST['aadhar'],aadhar_image=request.POST['aadhar_image'],vehicle=request.POST['vehicle'],
                                             vehicle_id = request.POST['vehicle_id'],driving_license=request.POST['driving_license'],weight=0,
                                             dl_image = request.POST['dl_image'],rating = 0.00,phone_number=request.POST['phone_number'],email = request.POST['email'])
                #Create a coordinate
                if not Coordinates.objects.filter(reference_id=pilot.pilot_id):
                    coords = Coordinates.objects.create(unique_id=coord_id_generator(pilot.cityCode,pilot.pilot_id),
                                                        relation='002',reference_id=pilot.pilot_id,cityCode=pilot.cityCode)
                    pilot.coordinates = coords.unique_id
                    pilot.save()
                return Response({'pilot':PilotSerializer(pilot).data,'pilot_id':pilot.pilot_id,'coordinates':CoordinatesSerializer(coords).data},status=status.HTTP_201_CREATED)
            
            else:
                # Pilot exist
                return Response({'error':'Pilot Already Exist'},status=status.HTTP_406_NOT_ACCEPTABLE)
        else:
            # Account Does not Exist
            return Response({'error':'Account Does not Exist'},status=status.HTTP_404_NOT_FOUND)



# class PilotManager:

#     def locator(self,centre_id,cityCode,radius=3):
#         """
#          centre_id is the id of centre position.
#          reference_id is triggered using centre_id
#          redius = 3 where 3 is in km
#          locates all the Pilot present in the radius of 3km around the centre
#         """
#         # Filter all points within range
#         centre = Coordinates.objects.filter(reference_id=centre_id)
#         rangers = Coordinates.objects.filter(position__distance_lte=(centre,D(m=radius*1000)))
#         pilots = []
#         for ranger in rangers:
#             if ranger.cityCode == cityCode and ranger.relation == '002':
#                 pilots.append(ranger)
#         if pilots == []:
#             return ['list of deafult DE']
#         else:
#             return pilots
    
#     def procsecutor(self,pilots):
#         #pilots list will be sorted on the basis of weight they are loading
#         quickSort_pilot(pilots,0,len(pilots))
#         # We Will sort pilots according to distance
        
class PilotManager:

    def __init__(self,order_id):
        self.order_id = order_id
        self.order = Order.objects.get(order_id=self.order_id)

    
    def pilot_compass(self,first=True):
        # Find Pilot
        #TODO: Not Implemented real pilot base
        pilots  = Pilot.objects.all()
        final_pilot = pilots[0]
        for pilot in pilots:
            if pilot.weight == 0:
                final_pilot = pilot
                break
            elif final_pilot.weight > pilot.weight:
                final_pilot = pilot
        # order = Order.objects.get(order_id=self.order_id)
        if first:
            self.order.pilot_id_first = final_pilot.pilot_id
            self.order.pilot_name = final_pilot.first_name + final_pilot.last_name
            self.order.pilot_image = final_pilot.image
            self.order.pilot_number = final_pilot.phone_number
            self.order.position = final_pilot.coordinates.position
            self.order.save()
        else:
            self.order.otp = str(OtpPulse())
            self.order.pilot_id_return = final_pilot.pilot_id
            self.order.pilot_name = final_pilot.first_name + final_pilot.last_name
            self.order.pilot_image = final_pilot.image
            self.order.pilot_number = final_pilot.phone_number
            self.order.position = final_pilot.coordinates.position
            self.order.save()
            
    
    
        



    



                



                                             


