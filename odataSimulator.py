import requests
import json
import matplotlib.pyplot as plot
import time
import sys
import cPickle as pickle
import copy_reg, copy
import numpy as np
import warnings
import strategies as strategies
from plot_data import plot_gp


def pretty_print_POST(req):
	print('{}\n{}\n{}\n\n{}'.format(
		'-----------POST Request-----------',
		req.method + ' ' + req.url,
		'\n'.join('{}: {}'.format(k, v) for k, v in req.headers.items()),
		req.body,
	))

def parseValue(data):
	for res in data:
		if res is None:
			print("Skipped")
			continue
		try:
			return res["Value"]
		except:
			print("Exception when parsing value")
			print("Bad Response:")
			print(res)
			print("Complete Data:")
			print(data)	


headers = {
'Content-Type': 'application/json',
'Host' : 'localhost',
'Connection' : 'keep-alive',
'Cache-Control' : 'no-cache',
'Accept' : '*/*',
'Accept-Encoding' : 'gzip, deflate, bar',
'Accept-Language' : 'en-US,en;q=0.8',
'User-Agent' : 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.115 Safari/537.36'
}

def get_status():
	r_get = requests.get("http://localhost/ODataConnector/rest/RealtimeData?PointName=@Matrikon.OPC.Simulation.1\\EPSimServer.EnergyPlus.Control.Status.Value")
	data = json.loads(r_get.text)
	return parseValue(data)
 
def start_simulation(start):
	start = int(start)
	payload = [ { "PointName": "@Matrikon.OPC.Simulation.1\\EPSimServer.EnergyPlus.Control.Start.Value", "Value": start }]
	requests.post("http://localhost/ODataConnector/rest/RealtimeData/Write", headers=  headers, data = json.dumps(payload))


def control_bridge(value):
	payload = [ { "PointName": "@Matrikon.OPC.Simulation.1\\EPSimServer.EnergyPlus.Control.Status.Value", "Value": value }]
	requests.post("http://localhost/ODataConnector/rest/RealtimeData/Write", headers=  headers, data = json.dumps(payload))


def write_inputs(clgstp, htgstp, kitclgstp, kithtgstp, guestclgstp, guesthtgstp, sat, cwstp, time):
	payload = [ { "PointName": "@Matrikon.OPC.Simulation.1\\EPSimServer.EnergyPlus.Inputs.clgsetp.Value", "Value": clgstp }, 
	{ "PointName": "@Matrikon.OPC.Simulation.1\\EPSimServer.EnergyPlus.Inputs.htsetp.Value", "Value": htgstp },
	{ "PointName": "@Matrikon.OPC.Simulation.1\\EPSimServer.EnergyPlus.Inputs.kclgsetp.Value", "Value": kitclgstp },
	{ "PointName": "@Matrikon.OPC.Simulation.1\\EPSimServer.EnergyPlus.Inputs.khtsetp.Value", "Value": kithtgstp },
	{ "PointName": "@Matrikon.OPC.Simulation.1\\EPSimServer.EnergyPlus.Inputs.gclgsetp.Value", "Value": guestclgstp },
	{ "PointName": "@Matrikon.OPC.Simulation.1\\EPSimServer.EnergyPlus.Inputs.ghtsetp.Value", "Value": guesthtgstp },
	{ "PointName": "@Matrikon.OPC.Simulation.1\\EPSimServer.EnergyPlus.Inputs.airsetp.Value", "Value": sat },
	{ "PointName": "@Matrikon.OPC.Simulation.1\\EPSimServer.EnergyPlus.Inputs.cwsetp.Value", "Value": cwstp },
	{ "PointName": "@Matrikon.OPC.Simulation.1\\EPSimServer.EnergyPlus.Control.TimeStep.Value", "Value": time }]
	requests.post("http://localhost/ODataConnector/rest/RealtimeData/Write", headers=  headers, data = json.dumps(payload))

def write_prediction(predict, lower, upper):
	payload = [ { "PointName": "@Matrikon.OPC.Simulation.1\\EPSimServer.EnergyPlus.DPC.PowerPredict.Value", "Value": predict },
	{ "PointName": "@Matrikon.OPC.Simulation.1\\EPSimServer.EnergyPlus.DPC.PowerLowerConfidence.Value", "Value": lower },
	{ "PointName": "@Matrikon.OPC.Simulation.1\\EPSimServer.EnergyPlus.DPC.PowerUpperConfidence.Value", "Value": upper }]
	requests.post("http://localhost/ODataConnector/rest/RealtimeData/Write", headers=  headers, data = json.dumps(payload))

def write_strategy(predict, strategy_name):
	payload = [ { "PointName": "@Matrikon.OPC.Simulation.1\\EPSimServer.EnergyPlus.DPC.%s.Value" % strategy_name, "Value": predict }]
	requests.post("http://localhost/ODataConnector/rest/RealtimeData/Write", headers=  headers, data = json.dumps(payload))


def  read_outputs():
	output_tags = ["http://localhost/ODataConnector/rest/RealtimeData?PointName=@Matrikon.OPC.Simulation.1\\EPSimServer.EnergyPlus.Outputs.WholeBuilding.FacilityTotalElectricDemandPower.Value",
	"http://localhost/ODataConnector/rest/RealtimeData?PointName=@Matrikon.OPC.Simulation.1\\EPSimServer.EnergyPlus.Outputs.EMS.DayOfWeek.Value",
	"http://localhost/ODataConnector/rest/RealtimeData?PointName=@Matrikon.OPC.Simulation.1\\EPSimServer.EnergyPlus.Outputs.EMS.TimeOfDay.Value",
	"http://localhost/ODataConnector/rest/RealtimeData?PointName=@Matrikon.OPC.Simulation.1\\EPSimServer.EnergyPlus.Outputs.Environment.Drybulb.Value",
	"http://localhost/ODataConnector/rest/RealtimeData?PointName=@Matrikon.OPC.Simulation.1\\EPSimServer.EnergyPlus.Outputs.Environment.Humidity.Value"]
	outputs = []
	for tag in output_tags:
		r_get = requests.get(tag)
		data = json.loads(r_get.text)
		outputs.append(parseValue(data))

	return outputs

def load_baseline_model(building_type, n_samples):
	if 'copy_reg' not in sys.modules:
		print("COPY REG Not Imported")
	else:
		print("Copy_reg imported")
	filename = ('dpc/models/gp-%s-numsamples-%s.pickle' %(building_type, n_samples))
	print('loading GP model...')
	with open(filename, 'rb') as f:
		(model, buildingType, features_c, features_d, output, 
		 normalizer_c, normalizer_d, normalizer_y) = pickle.load(f)
	return model, normalizer_c, normalizer_d, normalizer_y

def gp_predict(kStep, X_c, X_d):
	if kStep > 2:
		with warnings.catch_warnings():
			warnings.simplefilter("ignore")
			X_d_norm = normalizer_d.transform(X_d)
			X_c_norm = normalizer_c.transform(X_c)	

		X_norm = np.concatenate((X_d_norm, X_c_norm), axis=0)
		if kStep == 3:
			print(X_norm)

		with warnings.catch_warnings():
			warnings.simplefilter("ignore")	
			y_mean, y_std = model.predict(X_norm, return_std=True)   
			y_mean = normalizer_y.inverse_transform(y_mean)

		y_std = y_std*(normalizer_y.data_max_-normalizer_y.data_min_)/2
		y_mean = y_mean.tolist()
		y_std = y_std.tolist()
	elif kStep == 0:
		y_mean = [[0]]
		y_std = [0]
	else:
		y_mean = [[outputs[kStep-1][0]]]
		y_std = [0]

	return y_mean[0][0], y_std[0]


if len(sys.argv) == 2:
	start = time.clock()
	status = int(get_status())
	end = time.clock()
	print(end-start)
	command = sys.argv[1]
	#python odataSimulator.py control setup
	if command == "setup":
		if status is 2 or status is 1:
			control_bridge(3)
			time.sleep(2)
		control_bridge(0)
		print("Bridge is Ready")
	elif command ==  "close":
		control_bridge(3)
		print("Bridge has been Closed")
	elif command == "kill":
		control_bridge(4)
		print("Bridge has been Burned")
		time.sleep(2)
		control_bridge(0)


else:
	#python odataSimulator.py setup
	status = int(get_status())
	print(status)
	if status is not 0:
		print("Bridge is not Ready. Call setup first before running the simulation")
		sys.exit(0)
  
	control_bridge(1)
	supported_queries = ["baseline", "strategy"]

	query_type = "strategy"
	if len(sys.argv) > 2 and sys.argv[1] == "sim":
		query_type = sys.argv[2]

	if query_type not in supported_queries:
		query_type = supported_queries[0]

	print(query_type)
	if query_type is "baseline" or query_type is "strategy":
		model, normalizer_c, normalizer_d, normalizer_y = load_baseline_model("LargeHotel", 1000)    
	 
	EPTimeStep = 4
	SimDays = 5
	kStep = 0
	MAXSTEPS = SimDays*24*EPTimeStep
	deltaT = (60/EPTimeStep)*60;
	outputs = []
	predictions = []
	input_history = []

	time = 0
	dayTime = 0
	while kStep < MAXSTEPS:

		dayTime = time % 86400


		if kStep > 2:

			lagged_ambient = [outputs[kStep-1][3], outputs[kStep-2][3], outputs[kStep-3][3]]
			lagged_humidity = [outputs[kStep-1][4], outputs[kStep-2][4], outputs[kStep-3][4]]
			lagged_power = [outputs[kStep-2][0], outputs[kStep-3][0]]
			if kStep == 3:
				print("Lagged Variables:")
				print(lagged_ambient)
				print(lagged_humidity)
				print(lagged_power)

		if query_type is "baseline":

			clgstp, kitclgstp, guestclgstp, sat, cwstp, htgstp, kithtgstp, guesthtgstp = strategies.baseline(dayTime)
			X_c = np.array([clgstp, kitclgstp, guestclgstp, sat, cwstp])


			if kStep > 2:								
				X_d = lagged_ambient + lagged_humidity + [TOD, DOW, HtgSP, KitchenHtgSP] + lagged_power
				X_d = np.array(X_d)
			else:
				X_d = np.array([])			

			y_mean, y_std = gp_predict(kStep, X_c, X_d)
			
			# if kStep == 3:
			# 	print("X variables")				
			# 	print(X_d)
			# 	print(X_c)

			# if kStep > 95 and kStep < 102:
			# 	print("KStep : %s" % (kStep))
			# 	print("Prediction, Std", (y_mean, y_std))
			# 	print("Day Time", dayTime)
			# 	print("Time", time)
			# 	print("Actual", outputs[kStep-1][0])
			# 	print("X_d:")
			# 	print(X_d)
			# 	print("X_c:")
			# 	print(X_c)

			write_prediction(y_mean, y_mean-2*y_std, y_mean+2*y_std)
			predictions.append([y_mean, y_std])
			
			HtgSP = htgstp
			KitchenHtgSP = kithtgstp


		elif query_type == "strategy":
			#Strategy 1
			clgstp, kitclgstp, guestclgstp, sat, cwstp, htgstp, kithtgstp, guesthtgstp = strategies.strategy1(dayTime)
			X_c = np.array([clgstp, kitclgstp, guestclgstp, sat, cwstp])

			if kStep > 2:								
				X_d = lagged_ambient + lagged_humidity + [TOD, DOW, HtgSP, KitchenHtgSP] + lagged_power
				X_d = np.array(X_d)
			else:
				X_d = np.array([])			

			y_mean, y_std = gp_predict(kStep, X_c, X_d)
			write_strategy(y_mean, "Strategy1")

			#Baseline
			clgstp, kitclgstp, guestclgstp, sat, cwstp, htgstp, kithtgstp, guesthtgstp = strategies.baseline(dayTime)
			X_c = np.array([clgstp, kitclgstp, guestclgstp, sat, cwstp])
			
			if kStep > 2:								
				X_d = lagged_ambient + lagged_humidity + [TOD, DOW, HtgSP, KitchenHtgSP] + lagged_power
				X_d = np.array(X_d)
			else:
				X_d = np.array([])			
			y_mean, y_std = gp_predict(kStep, X_c, X_d)

			# if y_std > 30000 or kStep > 95 and kStep < 102:
			# 	print("KStep : %s" % (kStep))
			# 	print("Prediction, Std", (y_mean, y_std))
			# 	print("Day Time", dayTime)
			# 	print("Time", time)
			# 	print("Actual", outputs[kStep-1][0])
			# 	print("X_d:")
			# 	print(X_d)
			# 	print("X_c:")
			# 	print(X_c)

			write_prediction(y_mean, y_mean-2*y_std, y_mean+2*y_std)
			predictions.append([y_mean, y_std])


			HtgSP = htgstp
			KitchenHtgSP = kithtgstp

		time = (kStep)*deltaT
		write_inputs(clgstp, htgstp, kitclgstp, kithtgstp, guestclgstp, guesthtgstp, sat, cwstp, time)


		hotel_outputs = read_outputs()
		hotel_outputs = [float(output) for output in hotel_outputs]
		TotalLoad = hotel_outputs[0]
		DOW = hotel_outputs[1]
		TOD = hotel_outputs[2]
		Ambient = hotel_outputs[3]
		Humidity = hotel_outputs[4]
		if kStep < 4:
			print("Outputs")
			print("kStep: ", kStep)
			print(hotel_outputs)

		outputs.append(hotel_outputs)

		kStep = kStep + 1;

	control_bridge(2)

	actual = [row[0] for row in outputs]
	predict = [row[0] for row in predictions]
	std = [row[1] for row in predictions]
	print(actual)
	print(predict)
	print(std)

	plot.figure(1)
	plot.subplot(211)
	plot.plot(predict)
	plot.subplot(212)
	plot.plot(actual)
	plot.show()

