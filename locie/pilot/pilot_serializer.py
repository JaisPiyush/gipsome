from math import ceil

class PilotOrderSerializer:
    def __init__(self,orders):
        self.orders = orders
    
    def serialize(self,order):
        return {
            "order_id":order.order_id,
            "otp":order.otp,
           
            "payment_COD": 1 if order.payment_COD else 0 ,
            "payment_complete": 1 if order.payment_complete else 0,
            "locie_transfer":order.locie_transfer,
            "locie_reversion":order.locie_reversion,
            "net_charge":ceil(order.extra_charges['delivery_charge']/2) if order.delivery_type == 'UDS' else order.extra_charges['delivery_charge']
        }
    
    def data(self):
        appendix = []
        for order in self.orders:
            appendix.append(self.serialize(order))
        return appendix