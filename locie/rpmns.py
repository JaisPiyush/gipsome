# # RPMNS Ram Pragat Mani Notification System
from .models import MobileDevice, CustomerDevice,Account
from rest_framework.views import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.authentication import TokenAuthentication
from rest_framework.views import APIView
from rest_framework import status
import json
from django.db.models import Q


API_KEY = 'AAAAV_Ah5fM:APA91bH2dMvLUYRTpcsY4irIzEk1gQzEDQdxY0DN01-MCb_HF2OE09jXpt7-RuFHxT-YEAZym83dvWUhyvQAkYiMz1_I1htdKHxrF1NFG-fwmCawpdpTSs7IwzRa0vCzftIWKzc7MkWv'

class RPMNSRegistartionUpdate(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, format=None):
        body = json.loads(request.body)
        if 'locie_partner' in body.keys():
            device,created = MobileDevice.objects.get_or_create(locie_partner=body['locie_partner'])
            if device or created:
                mobile = device[0]
                mobile.registration_id = body['registration_id']
                mobile.save()
                return Response({'registration_id': mobile.registration_id}, status=status.HTTP_200_OK)
            else:
                account = Account.objects.filter(Q(account_id = body['locie_partner']) & Q(relation = body['partnership']))
                if account:
                    device = MobileDevice.objects.create(locie_partner = body['locie_partner'],
                                                           partnership = body['partnership'],
                                                        registration_id = body['registration_id'])
                    return  Response({'registration_id': device.registration_id}, status=status.HTTP_200_OK)
                else:
                    return  Response({}, status=status.HTTP_403_FORBIDDEN)






