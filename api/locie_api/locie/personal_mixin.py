"""
+--------------------------------------------------------------------------------+
| Bulding personal Mixins for minimizing the operations                          |
| Mixins Will take filters to perform querysets and can present data accordingly |
| Using normal Generic views                                                     |
+--------------------------------------------------------------------------------+
"""

from rest_framework import status
from rest_framework.response import responses
from rest_framework.settings import settings
from rest_framework.generics import GenericAPIView

"""
+==============================================================================================+
| Edit Required ---->  :                                                                       |                                 
| CreateModelMixin ---> nothing                                                                |                                 
| LocieCatMixin ---> Will give feature to perform Create, Update, Retreive, Delete and List    |
|                    with multiple lookup fields                                               |
|               --> Will look in the url for 'all'-> list,                                     |
+==============================================================================================+
"""

class LocieCatMixin(GenericAPIView):
    pass
    