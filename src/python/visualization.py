import streamlit as st
# To make things easier later, we're also importing numpy and pandas for
# working with sample data.
import numpy as np
import pandas as pd
import pydeck as pdk
import math
import time
import json
import datetime, pytz
import utils
import eventGenerator
from StreamlitUtils import ScaledProgressBar

NUM_POINTS = 100
MAPBOX_TOKEN="pk.eyJ1IjoiZWJhc2FuZXoiLCJhIjoiY2thdmZqcnh3MWNwOTMxbXM3eDZncDlqeiJ9.BT3UQJ9yJ2eSiaSRu-RsJw"

st.title("SAMUR.AI\nSimulation Interactive Visualizaton Tool")
st.set_option('deprecation.showfileUploaderEncoding', False)

@st.cache
def getEmergenciesData():
	data = pd.DataFrame(np.random.randn(NUM_POINTS, 2) / [50, 50] + [utils.KM0_LATITUDE_DEGREES,utils.KM0_LONGITUDE_DEGREES],columns=['lat', 'lon'])
	return data

@st.cache
def getHospitalsData():
	data = pd.read_csv(utils.DATASETPATH_HOSPITALS, usecols=['latitude','longitude']).dropna()
	data.columns=['lat','lon']
	return data

@st.cache
def getEvents(string_io, hospitals_data):
	return eventGenerator.getEventsFromLogFile(string_io.getvalue(), hospitals_data)

def getSimulationStringIO():
	uploaded_string_io = st.sidebar.file_uploader("Choose a simulation log file", type = ['log'], encoding = "utf-8")
	if uploaded_string_io is not None:
		return uploaded_string_io


def applyEventToDeck(event, deck, mapToUpdate = None):
	layer = getLayerById(deck,event['layer'])
	if event['type'] == "ADD":
		layer.data.append(event['content'])
	if event['type'] == "REMOVE":	
		layer.data.remove(event['content'])
	if map:
		map.pydeck_chart(deck)
	

def getLayerById(dek, layer_id):
	for layer in deck.layers:
		if layer.id == layer_id:
			return layer

# Retrieve data:
emergencies_data 	= getEmergenciesData()
hospitals_data 		= getHospitalsData()
uploaded_string_io 	= getSimulationStringIO()
if uploaded_string_io is not None:
	
	events = getEvents(uploaded_string_io, hospitals_data)
	
	#Create map
	EMER_RGB = '[240, 100, 0, {}]'
	HOSP_RGB = '[0, 255, 0, {}]'
	map = st.empty()
	emer_layer  	= pdk.Layer('ScatterplotLayer', id='emer'     , data=[],get_position='[lon, lat]',get_color=EMER_RGB.format(160),get_radius=200,)
	hosp_layer  	= pdk.Layer('ScatterplotLayer', id='hosp'     , data=hospitals_data,get_position='[lon,lat]',get_color=HOSP_RGB.format(160),get_radius=200)		
	ambulance_layer = pdk.Layer("ArcLayer",         id='ambulance', data=[],get_height= .2, get_width=10.5, get_source_position=["lng_h", "lat_h"], get_target_position=["lng_w", "lat_w"],get_tilt=15, get_source_color=HOSP_RGB.format(50),get_target_color=EMER_RGB.format(50), pickable=True, auto_highlight=True,)

	deck = pdk.Deck(
		#map_style='mapbox://styles/ebasanez/ckavglgjf49dv1ipcmf3k81s5',
		map_style='mapbox://styles/mapbox/light-v9',
		initial_view_state=pdk.ViewState(
			latitude=utils.KM0_LATITUDE_DEGREES,
			longitude=utils.KM0_LONGITUDE_DEGREES,
			zoom=10.9,
			pitch=50
		),layers=[hosp_layer,emer_layer, ambulance_layer],
		tooltip=False
	)	
	map.pydeck_chart(deck)

	# Input widgets
	def getModeFromInput():
		return st.sidebar.selectbox('Select visualization mode',['Animation','Snapshot'])
	
	def getDateFromInput():
		return st.sidebar.date_input('Date',datetime.datetime.fromtimestamp(events[0]['epochMillis']/1000.0), min_value=datetime.datetime.fromtimestamp(events[0]['epochMillis']/1000.0), max_value=datetime.datetime.fromtimestamp(events[-1]['epochMillis']/1000.0))

	def getTimeFromInput():
		return st.sidebar.time_input('Hour')

	def getTimescaleFromInput():
		time_scale = st.sidebar.selectbox('Time scale',['1:10000','1:100000','1:1000000','1:10000000'],index = 1)
		return int(time_scale.split(':')[1])
		
	def calculateEventsAtTimestamp(date, hour, events):
		milliseconds = int(datetime.datetime.combine(date,hour).replace(tzinfo=pytz.utc).timestamp() * 1000)
		events = [e for e in events if e['epochMillis'] <= milliseconds] #Events previous to timestamp
		eventContentsToRemove = list([e['content'] for e in events if e['type'] == 'REMOVE'])
		events = list([e for e in events if e['type'] == 'ADD']) 
		events = [e for e in events if e['content'] not in eventContentsToRemove] #Events removing content in "REMOVE" events
		return events

	mode = getModeFromInput()

	# Mode 1: Snapshot visualization
	if mode == 'Snapshot':
		
		# Get subarray of events before selected timestamp
		date = getDateFromInput()
		hour = getTimeFromInput()
		events = calculateEventsAtTimestamp(date, hour, events)
		for e in events:
			applyEventToDeck(e, deck, map)
		
	# Mode 2: Simulation animation
	if mode == 'Animation':
		time_scale = getTimescaleFromInput()
		my_bar = ScaledProgressBar(events[0]['epochMillis'],events[-1]['epochMillis'])
		iterations = len(events)
		for i in range(iterations):
			event = events[i]
			applyEventToDeck(event, deck, map)
			my_bar.progress(event['epochMillis'])
			#sleep until new event:
			if i < iterations - 1:
				millis_diff = events[i+1]['epochMillis'] - event['epochMillis']
				if millis_diff > 0: 
					time.sleep(millis_diff/time_scale)	



