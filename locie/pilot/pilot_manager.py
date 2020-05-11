import math

from django.contrib.gis.geos.point import Point
from ..gadgets.rpmns import API_KEY
from ..models import Order, Pilot, Servei, Store, MobileDevice


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
            if self.order.delivery_type == 'SSU':
                self.order.locie_reversion = sum([value['net_price'] for value in self.order.final_servei_cluster.values()])
                self.order.locie_transfer = self.order.price
            elif self.order.delivery_type == 'UDS':
                if len(self.order.pilot_cluster.keys()) > 1:
                    self.order.locie_reversion = sum([value['net_price'] for value in self.order.final_servei_cluster.values()])
                    self.order.locie_transfer = self.order.price
                elif len(self.order.pilot_cluster.keys()) == 1:
                    self.order.locie_reversion = 0.0
                    self.order.locie_transfer = 0.0
            elif self.order.delivery_type == 'PAD':
                self.order.locie_transfer = self.order.price
                self.order.locie_reversion = self.order.extra_charges['delivery_charge'] * (0.375)


            self.order.save()
            device = MobileDevice.objects.get(locie_partner=final_pilot.pilot_id)
            device.send_message('New Order', f'New Order is assigned to you',
                                data={'click_action': 'FLUTTER_NOTIFICATION_CLICK', 'data': {
                                    'type': 'new-order', 'order_id': self.order_id}}, api_key=API_KEY)
            
            
        else:
            raise Exception()
    
    @staticmethod
    def fartest_point(servei_list,customer_coords):
        farthest_id = None
        distance = 0
        coords = Point(customer_coords['lat'],customer_coords['long'])
        for servei_id in servei_list:
           dis = coords.distance(Servei.objects.get(servei_id=servei_id).coordinates) * 100
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


    def route_planner(self,cust_to_servei=False):
        # Called only after servei's are finalised and Pilot is ready
        if not cust_to_servei:
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

        elif cust_to_servei:
            # first is customer and last is the farthest servei from customer
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
        price = 0.0
        if self.order.delivery_type == 'SSU':
            price = clust['net_price']
            returnable_dict['entity'] = 'SEND'
        elif self.order.delivery_type == 'UDS' and len(self.order.pilot_cluster.keys()) > 1:
            price = clust['net_price']
            returnable_dict['entity'] = 'SEND'
        elif self.order.delivery_type == 'UDS' and len(self.order.pilot_cluster.keys()) == 1:
            returnable_dict['entity'] = 'RECV'
            
        servei = Servei.objects.get(servei_id=servei_id)
        store = Store.objects.get(store_key=clust['store_key'])
        returnable_dict['id'] = servei_id
        returnable_dict['phone_number'] = servei.phone_number
        returnable_dict['address'] = servei.address
        returnable_dict['type'] = 'SERV'
        returnable_dict['transaction'] = 'PAY'
        returnable_dict['quantity'] = clust['quantity']
        returnable_dict['items'] = clust['items']
        returnable_dict['net_price'] = price
        returnable_dict['name'] = store.store_name
        returnable_dict['coordinates'] = {
            "lat":servei.coordinates[0],
            "long":servei.coordinates[-1]
        }
        return returnable_dict
    
    def sumarize_pad(self,sender=True):
        clust = self.order.final_servei_cluster[self.order.senders_list[0]] if sender else self.order.customer_stack
        returnable_dict = clust
        returnable_dict['type'] = 'CUST'
        returnable_dict['transaction'] = 'PAY'
        returnable_dict['net_price'] = self.order.net_price if sender else 0
        returnable_dict['entity'] = 'RECV' if not sender else 'SEND'
        return returnable_dict 

    def next_task(self):
        order = self.order
        returning_data = {}
        returning_data['primary'] = {
                "order_id": order.order_id,
                "locie_transfer": order.locie_transfer,
                "locie_reversion": order.locie_reversion,
                "otp": order.otp,
                "net_charge": math.ceil(order.extra_charge['delivery_charge']/2) if order.delivery_type == 'UDS' else order.extra_charges['delivery_charge'],
                "delivery_type": order.delivery_type,
                "payment_COD": 1 if order.payment_COD else 0,
                "payment_complete": 1 if order.payment_complete else 0
        }
        if len(order.picked_list) == len(order.senders_list):
            if len(order.droped_list) != len(order.receivers_list):
                if order.delivery_type == 'UDS' and len(order.pilot_cluster.keys()) == 1:
                    # Droping to Servei
                    returning_data['secondary'] = self.sumarize_servei(order.receivers_list[len(order.droped_list)])
                    return returning_data
                elif order.delivery_type == 'UDS' and len(order.pilot_cluster.keys()) > 1:
                    # Droping back to Customer
                    returning_data['secondary'] =  self.sumarize_customer(order.customer_id)
                    return returning_data
                elif order.delivery_type == 'SSU':
                    # Sending Customer details because dropping
                    returning_data['secondary'] = self.sumarize_customer(order.customer_id)
                    return returning_data
                elif order.delivery_type == 'PAD':
                    returning_data['secondary'] = self.sumarize_pad(sender=False)
                    return returning_data

                
            elif len(order.droped_list) == len(order.receivers_list):
                # Order is Complete
                pass
        elif len(order.picked_list) != len(order.senders_list):
            if order.delivery_type == 'UDS' and len(order.pilot_cluster.keys()) == 1:
                # Customer is pickup
                returning_data['secondary'] = self.sumarize_customer(order.customer_id)
                return returning_data
            elif order.delivery_type == 'UDS' and len(order.pilot_cluster.keys()) > 1:
                # Picking Up from servei
                returning_data['secondary'] = self.sumarize_servei(order.receivers_list[len(order.droped_list)])
                return returning_data
            elif order.delivery_type == 'SSU':
                returning_data['secondary'] = self.sumarize_servei(order.senders_list[len(order.droped_list)])
                return returning_data
            elif order.delivery_type == 'PAD':
                returning_data['secondary'] = self.sumarize_pad(sender=True)
                return returning_data


    
    def sumarize_customer(self,customer_id):
        returnable_dict ={
            "items":[]
        }
        price = 0.0
        returnable_dict['entity'] = 'RECV'
        if self.order.delivery_type == 'SSU':
            price = self.order.net_price
            for value in self.order.final_servei_cluster.values():
                returnable_dict['items'] += value['items']
        elif self.order.delivery_type == 'UDS' and len(self.order.pilot_cluster.keys()) == 1:
            price = math.ceil(self.order.extra_charges['delivery_charge']/2)
            returnable_dict['entity'] = 'SEND'
        elif self.order.delivery_type == 'UDS' and len(self.order.pilot_cluster.keys()) > 1:
            price = self.order.price + math.ceil(self.order.extra_charges['delivery_charge']/2)
            for value in self.order.final_servei_cluster.values():
                returnable_dict['items'] += value['items']
            returnable_dict['entity'] = 'RECV'
        returnable_dict['id'] = customer_id
        returnable_dict['phone_number'] = self.order.customer_stack['phone_number']
        returnable_dict['address'] = self.order.customer_stack['address']
        returnable_dict['type'] = 'CUST'
        returnable_dict['transaction'] = 'RECV'
        returnable_dict['net_price'] = price
        returnable_dict['coordinates']=self.order.customer_stack['coordinates']
        return returnable_dict


