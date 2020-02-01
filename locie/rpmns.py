# # RPMNS Ram Pragat Mani Notification System
from .models import OntoNotfication,MobileDevice,CustomerDevice


API_KEY = 'AAAAV_Ah5fM:APA91bH2dMvLUYRTpcsY4irIzEk1gQzEDQdxY0DN01-MCb_HF2OE09jXpt7-RuFHxT-YEAZym83dvWUhyvQAkYiMz1_I1htdKHxrF1NFG-fwmCawpdpTSs7IwzRa0vCzftIWKzc7MkWv'


class RPMNSystem:

    def __init__(self, receipient,partnership):
        self.receipient = receipient
        self.partnership = partnership

    def telegram(self, title=None, body=None,time_to_live=0, low_priority=False,icon=None, sound=None,badge=None,data=None):
        device = ''
        if self.partnership == '009':
            device = CustomerDevice.objects.filter(customer_id=self.receipient)
        elif self.partnership == '002' or self.partnership == '003':
            device = MobileDevice.objects.filter(locie_partner=self.receipient)
        # OntoNotfication.objects.create(receipient=device.customer_id,receipient_token=device.registration_id,content=locals())
        device.send_message(title,body,data=data,icon=icon,time_to_live=time_to_live,low_priority=low_priority,sound=sound,badge=badge,api_key=API_KEY)
