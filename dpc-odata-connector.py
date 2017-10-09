import json
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

def to_odata_endpoint(tags):
	if tags is not list:
		tags = [tags]
	endpoints = ["http://localhost/ODataConnector/rest/RealtimeData?PointName=@Matrikon.OPC.Simulation.1\\" + tag for tag in tags]
	return endpoints

def build_payload_write(tags, values):
	payload = []
	for i in range(i, len(tags)):
		payload.append({"PointName" : "@Matrikon.OPC.Simulation.1\\" + tags[i], "Value" : values[i]})
	return payload

def build_payload_read(tags):
	full_point = ["@Matrikon.OPC.Simulation.1\\" + tag for tag in tags]
	payload = {"PointName" : full_point}

#TODO: Determine how to get all the outputrdy tags from building and determine the ready building namee
def output_ready_pairs():
	output_group = []
	for building_name in mapping.keys()	
		controls = mapping[building_name]["Control"]
		outputrdy = [s for s in controls if "OutputRdy" in s]
		output_group.append((building_name, outputrdy[0]))
	return output_group

def ready_building(pairs):
	payload = build_payload_read([point[1] for point in pairs])
	readys = write(payload)
	for i in range(0, len(readys)):
		if readys[i] is 1:
			return pairs[i][0]
	return None

def ts_synced_pairs():
	ts_group = []
	for building_name in mapping.keys()	
		controls = mapping[building_name]["Control"]
		ts = [s for s in controls if "TimeStep" in s]
		ts_group.append((building_name, ts[0]))
	return ts_group

def ts_synced(pairs):
	ts = pairs[0][1]
	for pair in pairs:
		if ts is not pair[1]:
			return False
	return True

def input_group(building_name):
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
	tags = [s for s in controls if "InputRdy" in s or "OutputRdy"]
	values = [1, 0]
	payload = build_payload_write(tags, values)
	write(payload)

def read_outputs_ready():
	for tag in output_group:
		r_get = requests.get(tag)
		data = json.loads(requests_get.text)
		print(data)
		tag_value = parseValue(data)
		if tag_value is 1:


def write_inputs(input_group, setpoints, time_tag, time):
	payload = build_payload_write(input_group + time_tag, setpoints + time)
	write(payload)

def read_outputs(output_tags):
	payload = build_payload_read(output_tags)
	return read(payload)	


#Initialize
output_ready_pairs = output_ready_pairs()
ts_pairs = ts_synced_pairs

output_history = {}
input_history = {}
for building_name in mapping.keys()
	input_history[building_name] = []
	output_history[building_name] = []

EPTimeStep = 4
SimDays = 5
kStep = 0
MAXSTEPS = SimDays*24*EPTimeStep
deltaT = (60/EPTimeStep)*60;

""" Simulation Loop """
#TODO: Buildings Loop and Overall TimeStep Changes, kStep, deltaT, etc
#INVARIANT: All energyplus buildings are on the same timestep, should have same timesteps per hour
while ts_synced(ts_pairs) and kStep < MAXSTEPS:

ready_building = ready_building(output_ready_pairs)
if ready_building is not None: 
	input_group = input_group(ready_building)

	#Whether or not setpoints will be determined by a strategy or default ones will be used
	use_default_setpoints = True

	if queryType is "Baseline"
		#TODO: Lagged Variables, and their relationship to mapping.json
		#Get Lagged Variables

		setpoints = strategies.baseline(ready_building, dayTime)
		use_default_setpoints = False

		#Build Array, pass to gp model for prediction
		#Write prediction to tag, or csv or somewhere
	elif queryType is "Strategy":
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
	write_inputs(input_group, setpoints, time_tag, time)

	toggle_ready(ready_building)

	output_tags = output_group(ready_building)
	output_values = read_outputs(output_tags)
	output_history[ready_building].appennd(output_values)
