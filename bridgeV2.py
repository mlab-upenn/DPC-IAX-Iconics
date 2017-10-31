import OpenOPC
import pyEp
import tag_mapping
import json
import sys
import time as delay

with open("mapping.json", 'r') as f:
	s = f.read()
	mapping = json.loads(s)

def find_ts_tag(building_name):
	controls = mapping[building_name]["Control"]
	ts = [s for s in controls if "TimeStep" in s]
	return ts[0]

def find_input_group(building_name):
	return mapping[building_name]["Inputs"]
	
def find_output_group(building_name):
	return mapping[building_name]["Outputs"]

def find_input_rdy(building_name):
	controls = mapping[building_name]["Control"]
	inp = [s for s in controls if "InputRdy" in s]
	return inp[0]

def find_output_rdy(building_name):
	controls = mapping[building_name]["Control"]
	out = [s for s in controls if "OutputRdy" in s]
	return out[0]

class building:

	def __init__(self, name, ep, output, input, start_tag, end_tag, timestep):
		self.name = name
		self.ep = ep
		#OPC Tags
		self.input_group = input
		self.input_rdy = start_tag
		self.output_rdy = end_tag
		self.timestep = timestep



opc = OpenOPC.open_client()
opc.connect('Matrikon.OPC.Simulation.1')
print("Connected to Matrikon.Simulator")

print(pyEp.__file__)
pyEp.set_bcvtb_home('C:\Python27\Lib\site-packages\pyEp\\bcvtb')
#Set default EnergyPlus Version
pyEp.set_energy_plus_dir('C:\EnergyPlusV8-4-0\\')
path_to_buildings = 'C:\Users\Expresso Logic\Documents\GitHub\DPC-IAX-Iconics\ePlusBuildings'
weather_file = 'USA_IL_Chicago-OHare.Intl.AP.725300_TMY3'

buildings = []

command = ""
prev_command = ""
while True:
	command,_,_ = opc.read('EPSimServer.EnergyPlus.Status')
	command = int(command)

	if command is not prev_command:
		if command is 0: #setup
			print("Setup")
			builder = pyEp.socket_builder(path_to_buildings)
			configs = builder.build() #[(port, building_name, idf)]
			for config in configs:
				building_name = config[1]
				building_path = path_to_buildings + "\\" + building_name
				print(building_name)
				#Customize EnergyPlus Version or Weather file here
				if building_name in "LargeOffice":
					print("LargeOffice E+")
					ep = pyEp.ep_process('localhost', config[0], building_path, weather_file, True, 'C:\EnergyPlusV8-1-0\\')
				else:	
					ep = pyEp.ep_process('localhost', config[0], building_path, weather_file, True)

				output = find_output_group(building_name)
				output_rdy = find_output_rdy(building_name)
				input = find_input_group(building_name)
				input_rdy = find_input_rdy(building_name)
				ts = find_ts_tag(building_name)

				buildings.append(building(building_name, ep, output, input, input_rdy, output_rdy, ts))
				opc.write((ts, 0))
				opc.write((input_rdy, 0))
				opc.write((output_rdy, 0))

			print("E+ Iniitalized, Waiting for Start Signal")
		elif command is 2:
			print("EnergyPlus Simulation finished")
		elif command is 3: #reset
			print("Reset")
			for building in buildings:
				building.ep.close()
				delay.sleep(1)
			buildings = []
			delay.sleep(1)
		elif command is 4: #close
			print("Closing")
			for building in buildings:
				building.ep.close()	
			opc.remove(opc.groups())
			opc.close()
			break
			sys.exit(0)
	elif command is 1:
		for building in buildings:
			building_name = building.name
			ep = building.ep
			input_group = building.input_group #OPC group for easy reading from tags
			output_rdy = building.output_rdy
			input_rdy = building.input_rdy
			timestep_tag = building.timestep
			print(building_name)
			outputs = ep.decode_packet_simple(ep.read())
			print("Writing Outputs")
			output_mapping = tag_mapping.map_outputs(building_name, outputs) # Mapping is in (k, v) of TagNames, Value
			for tag, value in output_mapping:
				opc.write((tag, value))

			#Notify controller that outputs are ready
			opc.write((output_rdy, 1))

			print("Waiting for new inputs")
			#Wait for controller to write new inputs
			inputs_ready = int(opc.read(input_rdy)[0])
			while inputs_ready is not 1:
				inputs_ready = int(opc.read(input_rdy)[0])
				temp_command,_,_ = opc.read('EPSimServer.EnergyPlus.Status')
				temp_command = int(temp_command)
				if temp_command is not command:
					print("Got Interrupt")
					break

			print("Sending inputs to EnergyPlus")
			inputs = opc.read(input_group) # [(name, value, status, time)]
			#print(inputs)
			setpoints = [sp for (_, sp, _, _ ) in inputs]
			input_mapping = tag_mapping.map_inputs(building_name, inputs) #input_mapping is a list of the values of the tags, in order
			time, _, _ = opc.read(timestep_tag)
			encoded_packet = ep.encode_packet_simple(input_mapping, time)
			ep.write(encoded_packet)
			inputs_ready = opc.write((input_rdy, 0))

	prev_command = command

