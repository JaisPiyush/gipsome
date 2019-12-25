<Taxation Logic/>
  -- GST will be used as base for Tax for stores of Others professions.
  -- PAN will be used as replacement on single person store basis 
  -- All non-PAN holder will be managed by Aadhar Card
    
    PAN and Aadhar affilated Stores income Tax will be managed by us.
    

<Order Logic/>
  <Name: Tilak-Dhari-Mani-Order-System - [TDMOS]>
  
  -- Universal Constants
    <order_type: {67:/MultiPick , 77: /SinglePick }>
    waiting-time: 180sec
    <response = {103904:/Successful,
                 2090:/Order-Requested,
                 2002:/Order-Processing,
                 1990:/Delivery-Processing
                 9002:/Order-Completed
                [Failure]
                 404:/Servei-Declined(ALL-ORDER_CANCELLED),
                 408:/DE-Not-Found,
                 2801:/User-Cancelled,
                 0000:/Technical=Failure,
                 [SUCESS]
                 2705:/DE-Found,
                 2009:/Servei-Accepted and /Processing,
                [SSU-SP]
                 2708:/Order-Picked-by-DE
                 2711:/Order-Droped-by-DE
                [SSU-MP]
                 27081:/First-Order-Picked-by-DE
                 27082:/Last-Order-Picked-by-DE
                [SDU]
                 2808:/Servei-Picked-by-DE
                 2811:/Servei-Droped-by-DE
                 2008:/Servei-Picked-return-DE
                 2011:/Servei-Droped-return-DE
                [UDS]
                 0108:/Item-Picked-by-DE-from-User,
                 0111:/Item-Droped-by-DE-to-Servei,
                 0990:/Item-Picked-by-DE-from-Servei,
                 0904:/Item-Dropped-by-DE-to-User,
                [UDS-MP]
                 09901:/First-Item-Picked-from-First-Servei
                 09902:/Last-Item-Picked-from-Last-Servei
                 }/>


  -- Two base Category of Ordering System
    Single-Pick: When the relation of business is with one Servei body
      start TDMOS <status: Order-Requested> && <response: 2090>
      Drop-Notification
      Notification-Manager fetch Data and starts Order Manager
      Order Manager Creats Card and wait for <waiting-time/> 
      <if: Decline>:
             Notify the server
             Close the Order with status <staus: Cancelled> && <response: 404 (Servei-Declined)> && <TIME: LOG. response and time>
             Server Drop-Notification to User
             Notification-Manager fetch data and Notify User
      <elif: Accept>:
             Notify the server
             Update the Order with <status: Accepted and Processing> && <response: 2002> && <TIME: LOG. response and time>
             Notify Servei to Wait for 180sec to start Order-Processing
             Starts the <DE-Manager> ? 
                 --> (DE-Id) <status: Processing> &&<response: 2705 >&& <TIME: LOG.>: <staus: Cancelled>      && <response: 408(DE-Not-found)> && <TIME: LOG. response and time> [StartEmergencyDeliverySystem]
                 Notify Servei
             <SSU>:
                DE Picked the Order <status: Delivery-Processing> && <response: 2708>
                DE Drops the Order <status: Delivery-Droped> && <response: 2711> && <TIME: LOG.response and time>
                DE Mark Finish <status: Successful> && <response: 103904> &&<TIME: LOG. response and time>
             <UDS>:
                DE Picked the Item <status: Delivery-Processing> && <response: 0108> && <TIME: LOG.>
                DE Dropped the Item to Servei <status: Delivery-Completed> && <response: 0111> &&<TIME: LOG.>
                Servei Processing Order <status: Order-Processing> && <response: 2002> && <TIME: LOG.>
                Servei MArk Completed and Starts Delivery <status: Order-Completed>&&<response: 9002> &&<TIME: LOG.>
                Start <DE-Manager>
                          --> (DE-Id) <status: Delivery-Processing> && <response: 2705> && <TIME: LOG.>
                              : [StartEmergencyDeliverySystem]
                DE Picked the Item from Servei <status: Delivery-Processing> && <response: 0990> &&<TIME>
                DE Dropped the Item to User <status: Delivery-Completed> && <response: 0904> &&<TIME>
                DE Mark Finish <status: Successful> && <response: 103904> && <TIME>    
               

    Multi-Pick : When the relation of business is with Multiple Servei body
            starts TDMOS <status: Order-Requested> && <respone: 2090>

<Notification Service System>:
  <struct>:
     Notification:
        {
          to: ...
          notification: {
            body: ..
            title: ..
            icon: ..
          }
        },

      Message:
        {
          to: ...
          data: {
            Nick:...
            body: ..
            Room:...
            etc
          }
        },      
    <Working>:
      FCMDeviceModel:
         platform = ios/android
         token = token
         userId = userAccount can be null and blank
         serviceId = Account as de or servei
         serviceType = servei/de/null
       FCMDeviceCreate:
         if(token  not exist in FCMDeviceModel){
            if(request.serviceType == servei){
              serviceId = models.OneToOne(Servei,..)
              serviceType = 'servei'
            }else if(request.serviceType == de){
              serviceId = models.OneToOne(DE,..)
              serviceType = 'de'
            }else if(request.serviceType == '' or null){
              userId = oneToOne(Customer,...)
            }
         } else if(token exist in FCMDeviceModel){
           device  = FCMDeviceModel.objects.filter(token=request.token)
           FCMDeviceModel.update(
             if request.serviceType is not None or '' and device.serviceType is None:
               servieId = OneToOne(Servei if request.serviceType == 'servei' else DE if ...)
               serviceType = 'servei/de'
             if request.serviceType is None and device.serviceType is not None:
               userId = oneToOne(Customer)
               

           )
         }

        NotificationDataset(TimeStampedModel) :
          to = ...
          payloadType = 'notification/message'
          body = ..
          status = ..

        InAppMessage: #For Communication between Users
          sender =..
          to = ..
          content = ...
              



 <Returning/Replacing Order System>
     <RTDMOS>:
