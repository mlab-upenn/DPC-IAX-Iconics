import json
import strategies
import sys
import requests
import time as delay

with open("mapping.json", 'r') as f:
	s = f.read()
	mapping = json.loads(s)

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


def write(payload):
	requests.post("http://localhost/ODataConnector/rest/RealtimeData/Write", headers = headers, data = json.dumps(payload))

def read(payload):
	post_res = requests.post("http://localhost/ODataConnector/rest/RealtimeData", headers = headers, data = json.dumps(payload))
	data = json.loads(post_res.text)
	return [float(parseValue(point)) for point in data]

def parseValue(data):
	if data is None:
		print("Skipped")
	try:
		return data["Value"]
	except:
		print("Exception when parsing value")
		print("Bad Response")
		print("Complete Data:")
		print(data)	

def build_payload_write(tags, values):
	payload = []
	for i in range(0, len(tags)):
		payload.append({"PointName" : "@Matrikon.OPC.Simulation.1\\" + str(tags[i]) + ".Value", "Value" : values[i]})
	return payload

def build_payload_read(tags):
	full_point = ["@Matrikon.OPC.Simulation.1\\" + tag  + ".Value" for tag in tags]
	payload = {"PointName" : full_point}
	return payload

def get_output_ready_pairs():
	output_group = []
	for building_name in mapping.keys():
		controls = mapping[building_name]["Control"]
		outputrdy = [s for s in controls if "OutputRdy" in s]
		output_group.append((building_name, outputrdy[0]))
	return output_group

def get_ready_building(pairs):
	payload = build_payload_read([point[1] for point in pairs])
	readys = read(payload)
	for i in range(0, len(readys)):
		if int(readys[i]) is 1:
			return pairs[i][0]
	return None


def ts_synced_pairs():
	#Builds group of timestep points for each building to check if they are synced
	ts_group = []
	for building_name in mapping.keys():
		controls = mapping[building_name]["Control"]
		ts = [s for s in controls if "TimeStep" in s]
		ts_group.append((building_name, ts[0]))
	return ts_group

def ts_synced(pairs):
	#Read TimeSteps
	ts_tags = [pair[1] for pair in pairs]
	payload = build_payload_read(ts_tags)
	tss = read(payload)
	#Determine if they are all equal
	print(tss)
	first_ts = tss[0]
	for ts in tss:
		if not ts == first_ts:
			return False
	return True

def get_input_group(building_name):
	return mapping[building_name]["Inputs"]

def output_group(building_name):
	return mapping[building_name]["Outputs"]

def building_timestep(building_name):
	controls = mapping[building_name]["Control"]
	for tag in controls:
		if "TimeStep" in tag:
			return tag

def toggle_ready(building_name):
	controls = mapping[building_name]["Control"]
	tags = [s for s in controls if "InputRdy" in s or "OutputRdy" in s]
	values = [1, 0]
	payload = build_payload_write(tags, values)
	write(payload)

def write_inputs(input_group, setpoints, time_tag, time):
	payload = build_payload_write(input_group + [time_tag], setpoints + [time])
	write(payload)

def read_outputs(output_tags):
	payload = build_payload_read(output_tags)
	return read(payload)	

def read_status():
	payload = build_payload_read(["EPSimServer.EnergyPlus.Status"])
	res = read(payload)
	return res[0]

def write_status(value):
	payload = build_payload_write(["EPSimServer.EnergyPlus.Status"], [value])
	write(payload)

#Initialize
output_ready_pairs = get_output_ready_pairs() #[(building_name, endpoint)]
ts_pairs = ts_synced_pairs() #[(building_name, endpoint)]

output_history = {}
input_history = {}
for building_name in mapping.keys():
	input_history[building_name] = []
	output_history[building_name] = []

print(output_ready_pairs)
print(ts_pairs)

if len(sys.argv) < 2:
	sys.exit(0)

command = sys.argv[1]

delay.sleep(1)

status = int(read_status())
print(command)


if command == "setup":

	if status is 2 or status is 1:
		write_status(3)
		delay.sleep(2)
	write_status(0)
	print("Bridge is Ready")

elif command ==  "close":

	write_status(3)
	print("Bridge has been Closed")

elif command == "kill":

	write_status(4)
	print("Bridge has been Burned")
	delay.sleep(2)
	write_status(0)

elif command == "run":
	if status is not 0:
		print("Bridge is not Ready. Call setup first before running the simulation")
		sys.exit(0)
	supported_queries = ["baseline", "strategy"]
	query_type = None
	if len(sys.argv) > 2:
		query_type = sys.argv[2]

	if query_type not in supported_queries:
		query_type = supported_queries[0]

	write_status(1)

	""" Simulation Loop """
	#INVARIANT: All energyplus buildings are on the same timestep, should have same timesteps per hour
	print("Running Simulation")

	EPTimeStep = 4
	SimDays = 5
	kStep = 1
	MAXSTEPS = SimDays*24*EPTimeStep
	deltaT = (60/EPTimeStep)*60;

	num_buildings = len(mapping.keys())

	while kStep < MAXSTEPS:

		was_synced = True
		is_synced = True

		time = kStep * deltaT
		dayTime = time % 86400

		while not is_synced or was_synced:
			# print("Wating for Building")
			#Determine if a building has outputs that can be read
			ready_building = get_ready_building(output_ready_pairs)
			if ready_building is not None: 
				print(ready_building)
				input_group = get_input_group(ready_building)

				#Whether or not setpoints will be determined by a strategy or default ones will be used
				use_default_setpoints = True

				if query_type is "Baseline":
					#TODO: Lagged Variables, and their relationship to mapping.json
					#Get Lagged Variables

					setpoints = strategies.baseline(ready_building, dayTime)
					use_default_setpoints = False

					#Build Array, pass to gp model for prediction
					#Write prediction to tag, or csv or somewhere
				elif query_type is "Strategy":
					#Example of only using a strategy for a certain building type. Other types will use default instead
					if ready_building is "LargeOffice":
						setpoints = strategies.strategy1(ready_building, dayTime)
						use_default_setpoints = False
					
					#etc.

				#If setpoints have not been set by the queryType
				if use_default_setpoints:
					setpoints = strategies.default(ready_building, dayTime)

				time_tag = building_timestep(ready_building)
				#INVARIANT: setpoints are in the same order as specified by mapping.json
				# print(input_group)
				# print(time_tag)
				print(setpoints)
				print(time)
				write_inputs(input_group, setpoints, time_tag, time)

				toggle_ready(ready_building)

				output_tags = output_group(ready_building)
				output_values = read_outputs(output_tags)
				output_history[ready_building].append(output_values)


				#Edge case in which a single building is always in sync with itself, but kStep should increase
				if num_buildings == 1:
					break


			#Determine if all the buildings are on the same timestep

			was_synced = is_synced
			is_synced = ts_synced(ts_pairs)

		kStep = kStep + 1
