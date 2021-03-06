# # RPMNS Ram Pragat Mani Notification System
from ..models import MobileDevice, CustomerDevice,Account
from rest_framework.views import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.authentication import TokenAuthentication
from rest_framework.views import APIView
from rest_framework import status
import json
from ..tasks import shared_task
from django.db.models import Q


API_KEY = 'AAAAV_Ah5fM:APA91bH2dMvLUYRTpcsY4irIzEk1gQzEDQdxY0DN01-MCb_HF2OE09jXpt7-RuFHxT-YEAZym83dvWUhyvQAkYiMz1_I1htdKHxrF1NFG-fwmCawpdpTSs7IwzRa0vCzftIWKzc7MkWv'

class RPMNSRegistartionUpdate(APIView):
    permission_classes = [AllowAny]

    def post(self, request, format=None):
        body = json.loads(request.body)
        if 'locie_partner' in body.keys():
            device,created = MobileDevice.objects.get_or_create(locie_partner=body['locie_partner'])
            if device or created:
                if 'web' in body.keys():
                    device.type = 'web'
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



@shared_task
def send_notification_to_partner(partner_id,title=None,body=None,data={}):
    device = MobileDevice.objects.filter(locie_partner=partner_id)
    if device:
        device = device.first()
        device.send_message(title=title,body=body,data={
            'click_action':'FLUTTER_NOTIFICATION_CLICK',
            'data':data,

        },api_key=API_KEY)

@shared_task
def send_notification_to_customer(customer_id,title=None,body=None,data={}):
    device = CustomerDevice.objects.filter(customer_id=customer_id)
    if device:
        device = device.first()
        device.send_message(title=title,body=body,data={
            'click_action':'FLUTTER_NOTIFICATION_CLICK',
            'data':data
        },api_key=API_KEY)

