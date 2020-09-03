import json
import datetime
import pandas as pd
import time
import numpy as np

LATITUDE_1DEG_KM = 110.574
LONGITUDE_KM_PER_DEG = 111.320
KM0_LATITUDE = 40.4146500
KM0_LONGITUDE = -3.7004000

AM_LINE_EM_ID_INDEX = -1


def coordinatesToKm0(latitude, longitude):		
	x = np.round(np.cos(KM0_LATITUDE/180 * np.pi) * (longitude - KM0_LONGITUDE) * LONGITUDE_KM_PER_DEG, 9)
	y = np.round((latitude - KM0_LATITUDE) * LATITUDE_1DEG_KM, 9)
	return (y,x)

def latTransform(kim_lat):    
    return np.round(kim_lat/(LATITUDE_1DEG_KM) + KM0_LATITUDE,9)


def lonTransform(kim_lon):
    return np.round(kim_lon/(np.cos(KM0_LATITUDE/180 * np.pi)*LONGITUDE_KM_PER_DEG) + KM0_LONGITUDE,9)


def coordinateTransform(tuple):
    return (latTransform(tuple[0]), lonTransform(tuple[1]))


def getHospitalCoordinates(hospitals_data, value):
    return (hospitals_data.iloc[int(value)].lat, hospitals_data.iloc[int(value)].lon)


def ambulanceEvent(epochMillism, action, severity, accident_id, lat_h, lng_h, lat_w, lng_w):
    return {'epochMillis': epochMillism, 'id': '', 'type': action, 'layer': 'ambulance', 'content': {'lat_h': lat_h, 'lng_h': lng_h, 'lat_w': lat_w, 'lng_w': lng_w, 'id': severity + '_' + accident_id}}


def emergencyEvent(epochMillism, action, severity, accident_id, lat, lon):
    return {'epochMillis': epochMillism, 'id': '', 'type': action, 'layer': 'emer', 'content': {'lat': lat, 'lon': lon, 'id': severity + '_' + accident_id}}


def getAmbulanceEvents(items,emergency_dict, hospital_data):
    amb_otime = datetime.datetime.strptime(
        items[1], '%Y-%m-%dT%H:%M:%S').timestamp() * 1000
    amb_toobtime = datetime.datetime.strptime(
        items[5], '%Y-%m-%dT%H:%M:%S.%f').timestamp() * 1000
    amb_tohostime = datetime.datetime.strptime(
        items[6], '%Y-%m-%dT%H:%M:%S.%f').timestamp() * 1000
    coord_tuple = coordinateTransform(emergency_dict[int(items[2])][int(items[AM_LINE_EM_ID_INDEX])])
    origin_hosp_coord = getHospitalCoordinates(hospital_data,items[3])
    dest_hosp_coord = getHospitalCoordinates(hospital_data,items[4])
    temp = []
    temp.append(ambulanceEvent(amb_otime, 'ADD',
                               items[2], items[AM_LINE_EM_ID_INDEX], origin_hosp_coord[0], origin_hosp_coord[1], coord_tuple[0], coord_tuple[1]))
    temp.append(ambulanceEvent(amb_toobtime, 'REMOVE',
                               items[2], items[AM_LINE_EM_ID_INDEX], origin_hosp_coord[0], origin_hosp_coord[1], coord_tuple[0], coord_tuple[1]))
    temp.append(emergencyEvent(amb_toobtime, 'REMOVE',
                               items[2], items[AM_LINE_EM_ID_INDEX], coord_tuple[0], coord_tuple[1]))
    temp.append(ambulanceEvent(amb_toobtime, 'ADD',
                               items[2], items[AM_LINE_EM_ID_INDEX], coord_tuple[0], coord_tuple[1], dest_hosp_coord[0], dest_hosp_coord[1]))
    temp.append(ambulanceEvent(amb_tohostime, 'REMOVE',
                               items[2], items[AM_LINE_EM_ID_INDEX], coord_tuple[0], coord_tuple[1], dest_hosp_coord[0], dest_hosp_coord[1]))
    return temp


def getEmergencyEvent(items,emergency_dict):
    coord_tuple = coordinateTransform((float(items[3]), float(items[4])))
    emergency_dict[int(items[2])][int(items[6])] = (
        float(items[3]), float(items[4]))
    emergency_millis = datetime.datetime.strptime(
        items[1], '%Y-%m-%dT%H:%M:%S').timestamp() * 1000
    return emergencyEvent(emergency_millis, 'ADD', items[2], items[6], coord_tuple[0], coord_tuple[1])


def getMoveEvents(items, hospitals_data):
    amb_otime = datetime.datetime.strptime(
        items[1], '%Y-%m-%dT%H:%M:%S').timestamp() * 1000
    amb_tohostime = datetime.datetime.strptime(
        items[6], '%Y-%m-%dT%H:%M:%S.%f').timestamp() * 1000
    origin_hosp_coord = getHospitalCoordinates(hospitals_data, items[3])
    dest_hosp_coord = getHospitalCoordinates(hospitals_data, items[4])
    temp = []
    temp.append(ambulanceEvent(amb_otime, 'ADD',
                               items[2], items[AM_LINE_EM_ID_INDEX], origin_hosp_coord[0], origin_hosp_coord[1], dest_hosp_coord[0], dest_hosp_coord[1]))
    temp.append(ambulanceEvent(amb_tohostime, 'REMOVE',
                               items[2], items[AM_LINE_EM_ID_INDEX], origin_hosp_coord[0], origin_hosp_coord[1], dest_hosp_coord[0], dest_hosp_coord[1]))
    return temp
#AM [timeISO] [severity] [hosp_origin] [hosp_destination] [tobjective] [thospital] [reward] [em_identifier]


def getEventsFromLogFile(file_text, hospitals_data):

    output = []
    emergency_dict = {1: {}, 2:   {}, 3: {}, 4: {}, 5: {}}
    lines = file_text.splitlines()

    for line in lines:
        items = line.split()
        if items[0] == 'EM':
            output.append(getEmergencyEvent(items,emergency_dict))

        elif (items[0] == 'AM') & (items[2] != '0'):
            events = getAmbulanceEvents(items, emergency_dict, hospitals_data)
            for x in events:
                output.append(x)

        elif (items[0] == 'AM') & (items[2] == '0'):
            if(items[1] != items[6]):
                events = getMoveEvents(items,hospitals_data)
                for x in events:
                    output.append(x)

    output = sorted(output, key=lambda i: i['epochMillis'])

    return output

