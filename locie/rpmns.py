# # RPMNS Ram Pragat Mani Notification System
from .models import MobileDevice, CustomerDevice
from rest_framework.views import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.authentication import TokenAuthentication
from rest_framework.views import APIView
from rest_framework import status



API_KEY = 'AAAAV_Ah5fM:APA91bH2dMvLUYRTpcsY4irIzEk1gQzEDQdxY0DN01-MCb_HF2OE09jXpt7-RuFHxT-YEAZym83dvWUhyvQAkYiMz1_I1htdKHxrF1NFG-fwmCawpdpTSs7IwzRa0vCzftIWKzc7MkWv'

class RPMNSRegistartionUpdate(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, format=None):
        if 'locie_partner' in request.POST.keys():
            device = MobileDevice.objects.filter(
                locie_partner=request.POST['locie_partner'])
            if device:
                device.registration_id = request.POST['registration_id']
                device.save()
                return Response({'registration_id': device.registration_id}, status=status.HTTP_200_OK)
            else:
                return Response({'registration_id': device.registration_id}, status=status.HTTP_400_BAD_REQUEST)





