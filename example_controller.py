import json
import sys
import time as delay
import OpenOPC
import argparse



def write_status(status):
	""" 
	Writes the status of the simulation to the opc tag

	Arguments
		status -- the integer status to write. 0 is setup, 1 is simulating, 2 is simulation finished, 3 is resetting, 4 is closed

	"""
	opc.write((status_tag, status))

def read_status():
	""" 
	Reads the status of the simuation

	Returns
		status -- the integer status

	"""
	return int(opc.read(status_tag, timeout=1000)[0])


def get_ready_building(output_ready_pairs):
	""" 
	Determines which building is to be advanced next

	Arguments
		output_ready_pairs -- list of tuples of (building_name, opc_tag), where opc_tag is the output_ready tag of a building

	Returns
		building_name -- the name of the first ready building, or None if no buildings are ready
	"""
	tags = [pair[1] for pair in output_ready_pairs]
	values = []
	try:
		values = opc.read(tags, timeout=1000)
	except OpenOPC.TimeoutError as err:
		print("Caught Timeout Error, trying again")
		values = opc.read(tags, timeout=1000)

	for i, value in enumerate(values):
		if int(value[1]) is 1:
			return output_ready_pairs[i][0]
	return None



def get_input_group(building_name, mapping):
	"""
	Gets input tags for a specified building

	Arguments
		building_name -- the name of the building

	Returns
		input_group -- list of opc_tags, in the order specified by mapping.json, corresponding to the inputs of the specified building
	"""
	return mapping[building_name]["Inputs"]


def get_building_timestep(building_name, mapping):
	"""
	Gets the timestep tag for a specified building

	Arguments
		building_name -- the name of the building

	Returns
		timestep_tag -- the timestep_tag corresponding to the specified building
	"""
	controls = mapping[building_name]["Control"]
	for tag in controls:
		if "TimeStep" in tag:
			return tag

def write_inputs(input_group, setpoints, time_tag, time):
	"""
	Writes the new setpoints and simulation time to the corresponding opc tags

	Arguments
		input_group -- list of opc_tags, in the order specified by mapping.json, corresponding to the inputs of the specified building
		setpoints -- list of new setpoint values, in the order specified by mapping.json
		time_tag -- the timestep_tag
		time -- the new time to write, in seconds
	"""
	payload = zip(input_group, setpoints)
	payload.append((time_tag, time))
	opc.write(payload)

def toggle_ready(building_name, mapping):
	"""
	Marks new inputs are ready, and signifies that outputs are read.

	Arguments
		building_name -- the name of the building
	"""
	controls = mapping[building_name]["Control"]
	tags = [s for s in controls if "InputRdy" in s or "OutputRdy" in s]
	values = [1, 0]
	payload = zip(tags, values)
	opc.write(payload)


def get_output_group(building_name, mapping):
	"""
	Gets output tags for a specified building

	Arguments
		building_name -- the name of the building

	Returns
		output_group -- list of opc_tags, in the order specified by mapping.json, corresponding to the outputs of the specified building
	"""
	return mapping[building_name]["Outputs"]


def read_outputs(output_tags):
	"""
	Reads the new outputs from the specified opc tags

	Arguments
		output_tags -- list of output_tags to read

	Returns
		values -- list of float values, in order
	"""	
	values = []
	try:
		values = opc.read(output_tags, timeout=1000)
	except OpenOPC.TimeoutError as err:
		print("Caught Timeout Error, trying again")
		values = opc.read(output_tags, timeout=1000)
	
	return [float(value[1]) for value in values]



def time_synced(time_pairs):
	"""
	Determines if all buildings are at the same timestep

	Arguments
		time_pairs -- list of tuples of (building_name, timestep_tag)

	Returns
		synced -- True or False, if all buildings are at the same timestep
	"""
	tags = [pair[1] for pair in time_pairs]
	values = []
	try:
		values = opc.read(tags, timeout=1000)
	except OpenOPC.TimeoutError as err:
		print("Caught Timeout Error, trying again")
		values = opc.read(tags, timeout=1000)

	first = values[0][1]	
	for value in values:
		if value[1] is not first:
			return False
	return True


def get_output_ready_pairs(mapping):
	"""
	Gets a list of the output ready tags for all buildings

	Returns
		output_ready_pairs -- list of tuples (building_name, output_ready_tag) for each building, in the order specified by mapping.json

	"""
	output_group = []
	for building_name in mapping.keys():
		controls = mapping[building_name]["Control"]
		outputrdy = [s for s in controls if "OutputRdy" in s]
		output_group.append((building_name, outputrdy[0]))
	return output_group


def get_time_pairs(mapping):
	"""
	Gets a list of the timestep_tags for all buildings

	Returns
		time_pairs -- list of tuples of (building_name, timestep_tag), in the order specified by mapping.json
	"""
	ts_group = []
	for building_name in mapping.keys():
		controls = mapping[building_name]["Control"]
		print(controls)
		ts = [s for s in controls if "TimeStep" in s]
		print(ts)
		ts_group.append((building_name, ts[0]))
	return ts_group


def setup():
	if status is 2 or status is 1:
		write_status(3)
		delay.sleep(2)
	write_status(0)
	print("Bridge is Ready")

#TODO: Redefine Reset
def reset():
	write_status(3)
	print("Reseting Bridge")
	delay.sleep(2)
	write_status(0)

def kill():
	write_status(4)
	print("Bridge has been Burned")


def run(mapping_path, output):
	if status is not 0:
		print("Bridge is not Ready. Call setup first before running the simulation")
		sys.exit(0)

	with open(mapping_path, 'r') as f:
		s = f.read()
		mapping = json.loads(s)

	#Initialize
	print(mapping)
	print(mapping.keys())

	output_ready_pairs = get_output_ready_pairs(mapping) #[(building_name, endpoint)]
	ts_pairs = get_time_pairs(mapping) #[(building_name, endpoint)]

	print(ts_pairs)

	output_history = {}
	input_history = {}
	power_history = {}
	for building_name in mapping.keys():
		input_history[building_name] = []
		output_history[building_name] = []
		power_history[building_name] = []

	write_status(1)

	""" Simulation Loop """	
	#INVARIANT: All energyplus buildings are on the same timestep, should have same timesteps per hour
	print("Running Simulation")

	EPTimeStep = 4
	SimDays = 1
	kStep = 1
	MAXSTEPS = SimDays*24*EPTimeStep
	deltaT = (60/EPTimeStep)*60;

	num_buildings = len(mapping.keys())
	print("Number of buildings: %d" % num_buildings)
	print("Number of Timesteps: %d" % MAXSTEPS)

	while kStep < MAXSTEPS:

		was_synced = True
		is_synced = True

		time = kStep * deltaT
		dayTime = time % 86400

		print(kStep)
		while not is_synced or was_synced:

			#Determine if a building has outputs that can be read
			ready_building = get_ready_building(output_ready_pairs)
			if ready_building is not None: 
				print(ready_building)

				#Determine setpoints for each building
				setpoints = []
				if "LargeHotel" in building_name: 
					if time <= 7*3600:
						clgstp = 30
						htgstp = 16
						kitclgstp = 30
						kithtgstp = 16
						guestclgstp = 24
						guesthtgstp = 21
						sat = 13
						cwstp = 6.7
					else:
						clgstp = 24
						htgstp = 21
						kitclgstp = 26
						kithtgstp = 19
						guestclgstp = 24
						guesthtgstp = 21
						sat = 13
						cwstp = 6.7

					#NOTE: Must matching ordering specified in variables.cfg/mapping.json
					setpoints = [clgstp, htgstp, kitclgstp, kithtgstp, guestclgstp, guesthtgstp, sat, cwstp]

				if "LargeOffice" in building_name:
					clg = 26.7
					cw = 6.7
					lil = 0.7
					setpoints = [clg, cw, lil]

				#Lookup input tags and write to them				
				time_tag = get_building_timestep(ready_building, mapping)
				input_group = get_input_group(ready_building, mapping)
				write_inputs(input_group, setpoints, time_tag, time)

				#Notify bridge that new inputs have been written
				toggle_ready(ready_building, mapping)

				#Lookup output tags and read from them. Store them for final output
				output_tags = get_output_group(ready_building, mapping)
				output_values = read_outputs(output_tags)
				output_history[ready_building].append(output_values)
				power_history[ready_building].append(output_values[8])

				#Edge case in which a single building is always in sync with itself, but kStep should increase
				if num_buildings == 1:
					break

			#Determine if all the buildings are on the same timestep
			was_synced = is_synced
			is_synced = time_synced(ts_pairs)

		kStep = kStep + 1

	print("Simulation Finished")

	if output is not None:
		with open(output, 'w') as f:
			#TODO: Determine output writing code
			pass

if __name__ == "__main__":

	parser = argparse.ArgumentParser(description="Example Controller for Communicating with EnergyPlus over OPC")
	parser.add_argument('--command', '-c', help="Command for Controller: setup, run, reset, kill. See documentation for details") #Command Argument
	parser.add_argument('--mapping', '-m', help="Path to mapping.json file", default="mapping.json") #Path to mapping.json
	parser.add_argument('--output', '-o', help="Enables output saving, in specified file") #Path to output.txt
	parser.add_argument('--server', '-s', help="Name of OPC Server", default="Matrikon.OPC.Simulation.1") #OPC Server Name

	args = parser.parse_args()

	if args.command is None:
		print("Command for Controller not specified")
		sys.exit(0)

	# Create OpenOPC client and connect to Matrikon OPC server	
	opc = OpenOPC.open_client()
	opc.connect(args.server)
	print("Connected to " + args.server)
	status_tag = "EPSimServer.EnergyPlus.Status"
	status = int(read_status())

	print(args.mapping)
	if args.command == "setup":
		setup()
	elif args.command == "run":
		mapping = {}
		run(args.mapping, args.output)
	elif args.command == "reset":
		reset()
	elif args.command == "kill":
		kill()
	else:
		print("Command for Controller unknown. Must be setup, run, reset, or kill")
		sys.exit(0)	