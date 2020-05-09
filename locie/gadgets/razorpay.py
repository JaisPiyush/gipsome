import razorpay

client = razorpay.Client(auth=("rzp_test_P67ytGK6zecgQ9","AhBlgfthDyjHMEbfLHWUmFh2"))
client.set_app_details({"title":"Django"})


def create_order(amount,receipt,currency='INR',payment_capture=1,notes={}):
    razorpay_order_id = client.order.create(data={
        "amount":int(amount*100),
        "currency":currency,
        "receipt":receipt,
        "payment_capture":payment_capture,
        "notes":notes
    })
    return razorpay_order_id


def fetch_order(order_id):
    return client.order.fetch(order_id)


def refund(order_id,amount):
    client.payment.refund(order_id,f"{int(amount*100)}")
    