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
	payload = [ { "PointName": "@ICONICS.Simulator.1\\EnergyPlus.Control.Start.Value", "Value": start }]
	r = requests.post("http://localhost/ODataConnector/rest/RealtimeData/Write", headers=  headers, data = json.dumps(payload))

def control_bridge(value):
	payload = [ { "PointName": "@ICONICS.Simulator.1\\EnergyPlus.Control.Status.Value", "Value": value }]
	r = requests.post("http://localhost/ODataConnector/rest/RealtimeData/Write", headers=  headers, data = json.dumps(payload))

def write_time(time):
	payload = [ { "PointName": "@ICONICS.Simulator.1\\EnergyPlus.Control.TimeStep.Value", "Value": time }]
	r = requests.post("http://localhost/ODataConnector/rest/RealtimeData/Write", headers=  headers, data = json.dumps(payload))


def write_cw_lil_clg(cw, lil, clg):
	payload = [ { "PointName": "@ICONICS.Simulator.1\\EnergyPlus.Inputs.clgsetp.Value", "Value": clg }, 
	{ "PointName": "@ICONICS.Simulator.1\\EnergyPlus.Inputs.lilsetp.Value", "Value": lil },
	{ "PointName": "@ICONICS.Simulator.1\\EnergyPlus.Inputs.cwsetp.Value", "Value": cw }]
	r = requests.post("http://localhost/ODataConnector/rest/RealtimeData/Write", headers=  headers, data = json.dumps(payload))

def write_everything(cw, lil, clg, time):
	payload = [ { "PointName": "@ICONICS.Simulator.1\\EnergyPlus.Inputs.clgsetp.Value", "Value": clg }, 
	{ "PointName": "@ICONICS.Simulator.1\\EnergyPlus.Inputs.lilsetp.Value", "Value": lil },
	{ "PointName": "@ICONICS.Simulator.1\\EnergyPlus.Inputs.cwsetp.Value", "Value": cw },
	{ "PointName": "@ICONICS.Simulator.1\\EnergyPlus.Control.TimeStep.Value", "Value": time }]
	r = requests.post("http://localhost/ODataConnector/rest/RealtimeData/Write", headers=  headers, data = json.dumps(payload))


def get_power():
	r_get = requests.get("http://localhost/ODataConnector/rest/RealtimeData?PointName=@ICONICS.Simulator.1\\EnergyPlus.Outputs.WholeBuilding.FacilityTotalElectricDemandPower.Value")
	data = json.loads(r_get.text)
	return data[0]["Value"]

def get_status():
	r_get = requests.get("http://localhost/ODataConnector/rest/RealtimeData?PointName=@ICONICS.Simulator.1\\EnergyPlus.Control.Status.Value")
	data = json.loads(r_get.text)
	return data[0]["Value"]


if len(sys.argv) > 1 :
	start = time.clock()
	status = get_status()
	end = time.clock()
	print(end-start)
	command = sys.argv[1]

	if command == "setup":
		if status is 2:
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
	status = get_status()
	if status is not 0:
		print("Bridge is not Ready. Call setup first before running the simulation")
		sys.exit(0)
	control_bridge(1)
	timeSteps = 0
	write_time(timeSteps)
	outputs = []
	i = 0
	sum_write_time = 0.0
	sum_read_time = 0.0	
	sum_time_time = 0.0
	start_sim_time = time.clock()
	while timeSteps < 288:
		if timeSteps % 12 == 0:
			print(timeSteps)
		start_w = time.clock()


		if timeSteps < 144:
			write_everything(6.3, 0.8, 26, timeSteps)
		elif timeSteps < 200:
			write_everything(8, 0.8, 28, timeSteps)
		else:
			write_everything(6.3, 0.8, 27, timeSteps)
		




		end_w = time.clock()
		sum_write_time = sum_write_time + (end_w-start_w)
		i = i+1

		# start_t = time.clock()
		# write_time(timeSteps)
		# end_t = time.clock()
		# sum_time_time = sum_time_time + (end_t - start_t)		
		timeSteps = timeSteps + 1


		start_r = time.clock()
		


		power = get_power()




		end_r = time.clock()		
		sum_read_time = sum_read_time + (end_r - start_r)
		outputs.append(power)


	end_sim_time = time.clock()
	control_bridge(2)
	print("AVERAGE Write Time: " + str(sum_write_time/float(i)))
	print("AVERAGE Read Time: " + str(sum_read_time/float(i)))	
	print("AVERAGE Time Time: " + str(sum_time_time/float(i)))
	print("Total Simulation Time: " + str(end_sim_time-start_sim_time))
	plot.plot(outputs)
	plot.show()

#POST request to write 2 values, to a different URL
# r_post = requests.Request('POST', "http://localhost/ODataConnector/rest/RealtimeData/Write HTTP/1.1", headers = headers, data=json.dumps(payload))
# pretty_print_POST(prepared)
# s = requests.Session()
# res = s.send(prepared)
# print(res.text)