#from .models import CityCode
from datetime import datetime

import pytz


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
    return (''.join(delimatore)).replace("-","_")


def item_id_generator(servei_id):
    #UP53@57260SER6167ITMdate-time
    delimator = [servei_id,'ITM',datetime.utcnow().strftime('%d%m%Y-%H%M%S')]
    return (''.join(delimator)).replace("-","_")






def dtime_diff(time1:datetime,time2:datetime):
    #HH:MM::SS.MS
    delta= str(time1-time2).split(':')
    delta = float(delta[0])*60*60 + float(delta[1])*60 + float(delta[2])
    return delta


def ist_datetime(time:datetime):
    asia = pytz.timezone("Asia/Kolkata")
    return time.astimezone(asia)


