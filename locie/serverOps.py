#from .models import CityCode
from datetime import datetime
from secrets import token_urlsafe 



def servei_id_creatore(cityCode, aadhar, phone_number):
    # city@aadhar[3:9]SERphone_number[6:]
    delimator = []
    delimator.append(cityCode)
    delimator.append([])
    delimator.append([])
    aadhar = list(map(str,aadhar))
    for index in range(3, 9):
        delimator[1].append(aadhar[index])
    phone_number = list(map(str,phone_number))
    for index in range(6):
        delimator[2].append(phone_number[index])

    return str(delimator[0] + '@' + str(''.join(delimator[1])) + 'SER' + str(''.join(delimator[2])))


def pilot_id_creatore(city_code, aadhar, phone_number):
    # city@aadhar[3:9]DEphone_number[6:]
    delimator = []
    delimator.append(city_code)
    delimator.append([])
    delimator.append([])
    aadhar = list(map(str,aadhar))
    for index in range(3, 9):
        delimator[1].append(aadhar[index])
    phone_number = list(map(str,phone_number))
    for index in range(6):
        delimator[2].append(phone_number[index])

    return str(delimator[0] + '@' + str(''.join(delimator[1])) + 'DE' + str(''.join(delimator[2])))




def storeKeyGenerator(servei_id):
    # UP53@572608-6167STR19122019-180640
    # cityCode@aadhar[3:9]-phone_number[6:]STRdate-time
    servei_id = servei_id.split('SER')
    delimatore = ['-'.join(servei_id), 'STR',
                  datetime.utcnow().strftime('%d%m%Y-%H%M%S')]
    return ''.join(delimatore)


def item_id_generator(servei_id):
    #UP53@57260SER6167ITMdate-time
    delimator = [servei_id,'ITM',datetime.utcnow().strftime('%d%m%Y-%H%M%S')]
    return ''.join(delimator)




# OTP
# randint(4)+time.sec(2)
from time import time
from random import randint, randrange


class OtpHemdal:
    def generate(self):
        key = str(randint(10**35, 10**68))
        keys = list(map(str, key))
        meteor = list(map(int, str(int(time()))))
        otpKey = []
        for index in range(0, 4):
             kemp = randrange(start=meteor[randint(1, len(meteor)-1)],stop=len(key), step=randint(len(meteor), int(len(key)/randint(1, 6))))
             otpKey.append(keys[kemp])
        otpKey.append(meteor[randrange(0, len(meteor))])
        otpKey.append(meteor[randrange(0, len(meteor))])
        otpKey = map(str,otpKey)
        return ''.join(otpKey)


def dtime_diff(time1:datetime,time2:datetime):
    #HH:MM::SS.MS
    delta= str(time1-time2).split(':')
    delta = float(delta[0])*60*60 + float(delta[1])*60 + float(delta[2])
    return delta

def coord_id_generator(cityCode,iden):
    token = token_urlsafe(5)
    return '{c}&{i}@{t}'.format(c=cityCode,i=iden,t=token)

# This function takes last element as pivot, places 
# the pivot element at its correct position in sorted 
# array, and places all smaller (smaller than pivot) 
# to left of pivot and all greater elements to right 
# of pivot 
def partition_pilot(arr,low,high): 
    i =  low-1         # index of smaller element 
    pivot = int(arr[high].weight)     # pivot 
  
    for j in range(low , high): 
  
        # If current element is smaller than the pivot 
        if   int(arr[j].weight) < pivot: 
          
            # increment index of smaller element 
            i = i+1 
            arr[i],arr[j] = arr[j],arr[i] 
  
    arr[i+1],arr[high] = arr[high],arr[i+1] 
    return  i+1 
  
# The main function that implements QuickSort 
# arr[] --> Array to be sorted, 
# low  --> Starting index, 
# high  --> Ending index 
  
# Function to do Quick sort 
def quickSort_pilot(arr,low,high): 
    if low < high: 
  
        # pi is partitioning index, arr[p] is now 
        # at right place 
        pi = partition_pilot(arr,low,high) 
  
        # Separately sort elements before 
        # partition and after partition 
        quickSort_pilot(arr, low, pi-1) 
        quickSort_pilot(arr, pi+1, high) 


