import OpenOPC
import pyEp
import output_mapping


opc = OpenOPC.open_client()
opc.connect('Matrikon.OPC.Simulation.1')
print("Connected to Matrikon.Simulator")

class building:

	def __init__(name, ep, output, input, start_tag, end_tag, timestep):
		self.name = name
		self.ep = ep
		#OPC Tags
		self.input_group = input
		self.input_rdy = start_tag
		self.output_rdy = end_tag
		self.timestep = timestep






while True:
	if command is 0:
		#Setup
	elif command is 3:
		#Rest
	elif command is 4:
		#Kill
	elif:
		for building in buildings:
			building_name = building.name
			ep = building.ep
			input_group = building.input_group #OPC group for easy reading from tags
			end_tag = building.output_rdy
			input_rdy = building.input_rdy
			timestep_tag = building.timestep

			outputs = ep.decode_packet_simple(ep.read())

			output_mapping = mapping.map_outputs(building_name, outputs) # Mapping is in (k, v) of TagNames, Value
			for tag, value in output_mapping:
				opc.write(tag, value)

			#Notify controller that outputs are ready
			opc.write(end_tag, 1)


			#Wait for controller to write new inputs
			inputs_ready = opc.read(input_rdy)
			while inputs_ready is not 1:
				inputs_ready = opc.read(input_rdy)
				# Check for interrupts

			inputs = opc.read(input_group) # [(name, value, status, time)]
			input_mapping = mapping.map_inputs(building_name, inputs) #input_mapping is a list of the values of the tags, in order
			time, _, _ = opc.read(timestep_tag)

			ep.write(ep.encode_packet_simple(input_mapping, time))
			inputs_ready = opc.write((input_rdy, 0))


