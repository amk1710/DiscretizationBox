import json
import requests
import numpy as np
import urllib.parse
from itertools import tee
from geopandas import GeoDataFrame
import time

GH_KEY = "NOT SET"

def set_graphhopper_key(key):
	global GH_KEY
	GH_KEY = key

def base_url_gh(key):
	return "https://graphhopper.com/api/1/matrix?key={0}".format(key)

def make_req_gh(from_,to_):
	post_data = {}
	post_data["from_points"] = from_
	post_data["to_points"] = to_
	post_data["out_arrays"] = ["times"]
	post_data["vehicle"] = "car"
	post_data["fail_fast"] = False

	post_headers = {"Content-Type" : "application/json"}

	global GH_KEY

	r = requests.post(base_url_gh(GH_KEY), data=json.dumps(post_data), headers=post_headers)
	response_data = r.json()
	if "times" in response_data:
		times = response_data["times"]
		return times
	else:
		print(response_data)
		raise AssertionError("'times' key not in request response")
		return None

def chunks(coords, k=5):
	for i in range(0,len(coords),k):
		yield coords[i:i+k]



# Read a list of lat long, split the list and make multiple calls to the graphhopper API
def gen_distance_matrix_from_file(path):
	'''
		Reads a file in a specific format (list of lat long, split the list) and calculate the distance matrix from the coordinates in the file. 

		See graphhopper_getDistanceMatrix for further details

		Params:
			path - path of the file to be read

		Return:
			numpy.ndarray - distance matrix 

	'''
	coords = []
	arq = open(path,"r")
	n = int(arq.readline())
	for line in arq.readlines():
		lat, longi = [float(x) for x in line.split()]
		coords.append([longi,lat])

	return graphhopper_getDistanceMatrix(coords)
	
def gen_distance_matrix(coords : list, wait_time = True):
	'''
		Use graphhopper requests to fetch distance matrix between origin and destination (lists of lat-long). 
		The ndarray returned is such that [i,j] indicates the travel time from i to j. Notice that this matrix is *not* symmetric

		Params:
			coords : list - a list of [longi, lat] lists specifying the coordinates of each point. The retuned matrix follows the index of this list
			wait_time : bool - because of API limitation for non-paying users you might want to wait 1 second per request!
			return:
				numpy.ndarray - distance matrix 
	'''
	n = len(coords)
	times = np.zeros((n,n))
	c_size  = 39
	from_ = list(chunks(coords,c_size))
	to_ = list(chunks(coords, c_size))


	
	chunk_times = {}
	for i in range(len(from_)):
		for j in range(len(to_)):
			chunk_times[(i,j)] = make_req_gh(from_[i], to_[j])
			if wait_time:
				time.sleep(60) # wait a *minute*

	

	for i in range(len(from_)):
		for j in range(0,len(to_)):
			for a in range(i*c_size,min(i*c_size+c_size, n)):
				for b in range(j*c_size, min(j*c_size+c_size, n)):
					times[a,b] = chunk_times[(i,j)][a % c_size][b % c_size]

	return times

def distance_matrix_from_gdf(gdf : GeoDataFrame):
	'''
		Assuming a geodataframe in this project's usual format, calculate a distance matrix using graphhopper

		Params:
			gdf : GeoDataFrame - a geodataframe enriched with columns 'center_lat' and 'center_lon' indicating each geometries center coordinates.

		Return:
			numpy.ndarray - distance matrix, such that [i,j] indicates the travel time from i to j. Notice that this matrix is *not* symmetric
	'''
	coords = []
	for _t , row in gdf.iterrows():
		lat, longi = row['center_lat'], row['center_lon']
		coords.append([longi,lat])

	return gen_distance_matrix(coords)

