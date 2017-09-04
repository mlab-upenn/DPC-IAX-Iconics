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

# #GET request working
# print("-----------GET Request-----------")
# r_get = requests.Request('GET', "http://localhost/ODataConnector/rest/RealtimeData?PointName=svrsim:sine double med -100 100")
# prepared = r_get.prepare()
# s = requests.Session()
# res = s.send(prepared)
# print(res.text)

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
#POST request to get an example value, defined header
# r_post = requests.Request('POST', "http://localhost/ODataConnector/rest/RealtimeData", headers = headers, data=json.dumps(payload))
# prepared = r_post.prepare()
# pretty_print_POST(prepared)
# s = requests.Session()
# res = s.send(prepared)
# print(res.text)

def startSimulation(start):
	start = int(start)
	payload = [ { "PointName": "@Matrikon.OPC.Simulation.1\\EPSimServer.EnergyPlus.Control.Start.Value", "Value": start }]
	r = requests.post("http://localhost/ODataConnector/rest/RealtimeData/Write", headers=  headers, data = json.dumps(payload))

def control_bridge(value):
	payload = [ { "PointName": "@Matrikon.OPC.Simulation.1\\EPSimServer.EnergyPlus.Control.Status.Value", "Value": value }]
	r = requests.post("http://localhost/ODataConnector/rest/RealtimeData/Write", headers=  headers, data = json.dumps(payload))

def write_time(time):
	payload = [ { "PointName": "@Matrikon.OPC.Simulation.1\\EPSimServer.EnergyPlus.Control.TimeStep.Value", "Value": time }]
	r = requests.post("http://localhost/ODataConnector/rest/RealtimeData/Write", headers=  headers, data = json.dumps(payload))

def write_days(days):
	payload = [ { "PointName": "@Matrikon.OPC.Simulation.1\\EPSimServer.EnergyPlus.Control.SimDays.Value", "Value": days }]
	r = requests.post("http://localhost/ODataConnector/rest/RealtimeData/Write", headers=  headers, data = json.dumps(payload))


def write_cw_lil_clg(cw, lil, clg):
	payload = [ { "PointName": "@Matrikon.OPC.Simulation.1\\EPSimServer.EnergyPlus.Inputs.clgsetp.Value", "Value": clg }, 
	{ "PointName": "@Matrikon.OPC.Simulation.1\\EPSimServer.EnergyPlus.Inputs.lilsetp.Value", "Value": lil },
	{ "PointName": "@Matrikon.OPC.Simulation.1\\EPSimServer.EnergyPlus.Inputs.cwsetp.Value", "Value": cw }]
	r = requests.post("http://localhost/ODataConnector/rest/RealtimeData/Write", headers=  headers, data = json.dumps(payload))

def write_everything(cw, lil, clg, time):
	payload = [ { "PointName": "@Matrikon.OPC.Simulation.1\\EPSimServer.EnergyPlus.Inputs.clgsetp.Value", "Value": clg }, 
	{ "PointName": "@Matrikon.OPC.Simulation.1\\EPSimServer.EnergyPlus.Inputs.lilsetp.Value", "Value": lil },
	{ "PointName": "@Matrikon.OPC.Simulation.1\\EPSimServer.EnergyPlus.Inputs.cwsetp.Value", "Value": cw },
	{ "PointName": "@Matrikon.OPC.Simulation.1\\EPSimServer.EnergyPlus.Control.TimeStep.Value", "Value": time }]
	r = requests.post("http://localhost/ODataConnector/rest/RealtimeData/Write", headers=  headers, data = json.dumps(payload))

def write_hotel_inputs(clg, kclg, gclg, air, cw, time):
	payload = [ { "PointName": "@Matrikon.OPC.Simulation.1\\EPSimServer.EnergyPlus.Inputs.clgsetp.Value", "Value": clg }, 
	{ "PointName": "@Matrikon.OPC.Simulation.1\\EPSimServer.EnergyPlus.Inputs.kclgsetp.Value", "Value": kclg },
	{ "PointName": "@Matrikon.OPC.Simulation.1\\EPSimServer.EnergyPlus.Inputs.gclgsetp.Value", "Value": gclg },
	{ "PointName": "@Matrikon.OPC.Simulation.1\\EPSimServer.EnergyPlus.Inputs.airsetp.Value", "Value": air },
	{ "PointName": "@Matrikon.OPC.Simulation.1\\EPSimServer.EnergyPlus.Inputs.cwsetp.Value", "Value": cw },
	{ "PointName": "@Matrikon.OPC.Simulation.1\\EPSimServer.EnergyPlus.Control.TimeStep.Value", "Value": time }]
	r = requests.post("http://localhost/ODataConnector/rest/RealtimeData/Write", headers=  headers, data = json.dumps(payload))



def get_power():
	r_get = requests.get("http://localhost/ODataConnector/rest/RealtimeData?PointName=@Matrikon.OPC.Simulation.1\\EPSimServer.EnergyPlus.Outputs.WholeBuilding.FacilityTotalElectricDemandPower.Value")
	data = json.loads(r_get.text)
	return parseValue(data)

def get_hotel_outputs():
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


def get_status():
	r_get = requests.get("http://localhost/ODataConnector/rest/RealtimeData?PointName=@Matrikon.OPC.Simulation.1\\EPSimServer.EnergyPlus.Control.Status.Value")
	data = json.loads(r_get.text)
	return parseValue(data)


def get_sim_time():
	r_get = requests.get("http://localhost/ODataConnector/rest/RealtimeData?PointName=@Matrikon.OPC.Simulation.1\\EPSimServer.EnergyPlus.Outputs.EMS.TimeOfDay.Value")
	data = json.loads(r_get.text)
	return parseValue(data) 


def get_sim_day():
	r_get = requests.get("http://localhost/ODataConnector/rest/RealtimeData?PointName=@Matrikon.OPC.Simulation.1\\EPSimServer.EnergyPlus.Outputs.EMS.DayOfWeek.Value")
	data = json.loads(r_get.text)
	return parseValue(data)

def sim_total_days():
	r_get = requests.get("http://localhost/ODataConnector/rest/RealtimeData?PointName=@Matrikon.OPC.Simulation.1\\EPSimServer.EnergyPlus.Control.SimDays.Value")
	data = json.loads(r_get.text)
	return parseValue(data)


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
	elif command == "days":
		num_days = int(sys.argv[2])
		write_days(num_days)
		print("Number of Simulation Days: " + str(num_days))


else:
	status = int(get_status())
	print(status)
	if status is not 0:
		print("Bridge is not Ready. Call setup first before running the simulation")
		sys.exit(0)
	control_bridge(1)
	timeSteps = 0
	write_time(timeSteps)
	outputs = []
	times = []
	day = 0
	i = 0
	sum_write_time = 0.0
	sum_read_time = 0.0	
	sum_time_time = 0.0

	start_sim_time = time.clock()
	days = int(sim_total_days())

	timeSteps = 0
	while timeSteps < 288 * days:
		if timeSteps % 12 == 0:
			print(timeSteps)


		# print("Grabbing Time")
		# sim_day = get_sim_day()
		# sim_time = get_sim_time()
		# if sim_day is not None or sim_time is not None:
		# 	sim_day = int(sim_day)
		# 	if day is not sim_day:
		# 		print("New Day: " + str(sim_day) + " " + str(timeSteps))
		# 		day = sim_day

		# 	times.append(sim_time)
		# 	if sim_time.is_integer():
		# 		print("Hour: " + str(sim_time) + " " + str(timeSteps))

		hotel_outputs = get_hotel_outputs()
		total_load = hotel_outputs[0]
		dow = hotel_outputs[1]
		tod = hotel_outputs[2]
		ambient = hotel_outputs[3]
		humidity = hotel_outputs[4]

		#write_hotel_inputs(clg, kclg, clg, air, cw, time)


		if timeSteps % 288 < 12 * 14:
			write_everything(6.3, 0.8, 26, timeSteps)
		elif timeSteps % 288 < 12 * 16:
			write_everything(8, 0.8, 28, timeSteps)
		else:
			write_everything(6.3, 0.8, 26, timeSteps)
		

		i = i+1

		# start_t = time.clock()
		# write_time(timeSteps)
		# end_t = time.clock()
		# sum_time_time = sum_time_time + (end_t - start_t)		
		times.append(timeSteps)
		timeSteps = timeSteps + 1

	end_sim_time = time.clock()
	control_bridge(2)
	plot.plot(outputs)
	plot.show()

	print("AVERAGE Write Time: " + str(sum_write_time/float(i)))
	print("AVERAGE Read Time: " + str(sum_read_time/float(i)))	
	print("AVERAGE Time Time: " + str(sum_time_time/float(i)))
	print("Total Simulation Time: " + str(end_sim_time-start_sim_time))


#POST request to write 2 values, to a different URL
# r_post = requests.Request('POST', "http://localhost/ODataConnector/rest/RealtimeData/Write HTTP/1.1", headers = headers, data=json.dumps(payload))
# pretty_print_POST(prepared)
# s = requests.Session()
# res = s.send(prepared)
# print(res.text)