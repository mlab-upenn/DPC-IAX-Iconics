import requests
import json
import matplotlib.pyplot as plot
import time
import sys

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


def read_outputs():
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
    filename = ('models/gp-%s-numsamples-%s.pickle' %(building_type, n_samples))
    print('loading GP model...')
    with open(filename, 'rb') as f:
        (model, buildingType, features_c, features_d, output, 
         normalizer_c, normalizer_d, normalizer_y) = pickle.load(f)
    return model, normalizer_c, normalizer_d, normalizer_y

if len(sys.argv) > 1 :
	start = time.clock()
	status = int(get_status())
	end = time.clock()
	print(end-start)
	command = sys.argv[1]

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
    
	status = int(get_status())
	print(status)
	if status is not 0:
		print("Bridge is not Ready. Call setup first before running the simulation")
		sys.exit(0)
  
	control_bridge(1)
       
    query_type = "baseline"
    if query_type is "baseline":
        model, normalizer_c, normalizer_d, normalizer_y = load_baseline_model()    
     
    EPTimeStep = 4
    SimDays = 1
    kStep = 0
    MAXSTEPS = SimDays*24*EPTimeStep
    deltaT = (60/EPTimeStep)*60;
    outputs = []
    while kStep < MAXSTEPS:

        	hotel_outputs = get_hotel_outputs()
		TotalLoad = hotel_outputs[0]
		DOW = hotel_outputs[1]
		TOD = hotel_outputs[2]
		Ambient = hotel_outputs[3]
		Humidity = hotel_outputs[4]

            lagged_power = [outputs[8][kStep-2],outputs[8][kStep-3]]
            
            if query_type is "baseline":
                
                X_d = [Ambient, Humidity, TOD, DOW, HtgSP, KitchenHtgSP, TotalLoad]
                
                if dayTime <= 7*3600:
                    
                    clgstp = 30
                    htgstp = 16
                    kitclgstp = 30
                    kithtgstp = 16
                    guestclgstp = 24
                    guesthtgstp = 21
                    sat = 13
                    cwstp = 6.7
        
                    X_c = [clgstp, htgstp, kitclgstp, kithtgstp, guestclgstp, guesthtgstp, sat, cwstp]
                    
                else:
                    
                    clgstp = 24
                    htgstp = 21
                    kitclgstp = 26
                    kithtgstp = 19
                    guestclgstp = 24
                    guesthtgstp = 21
                    sat = 13
                    cwstp = 6.7
        
                    X_c = [clgstp, htgstp, kitclgstp, kithtgstp, guestclgstp, guesthtgstp, sat, cwstp]
                    
            X_d_norm = normalizer_d.transform(X_d)
            X_c_norm = normalizer_c.transform(X_c)
            X_norm = np.concatenate((Xd_test, Xc_test), axis=1)
            y_mean, y_std = model.predict(X_norm, return_std=True)   
            
            y_mean = normalizer_y.inverse_transform(y_mean)
            y_std = y_std*(normalizer_y.data_max_-normalizer_y.data_min_)/2

            time = (kStep-1)*deltaT
		write_hotel_inputs(clgstp, htgstp, kitclgstp, kithtgstp, guestclgstp, guesthtgstp, sat, cwstp, time)

		kStep = kStep + 1;

	control_bridge(2)


