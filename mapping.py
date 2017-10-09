import json
with open("mapping.json", 'r') as f:
	s = f.read()
	mapping = json.loads(s)

def map_output(building_name, outputs):

	"""
	Maps outputs from EnergyPlus to OPC tags
	
	Inputs:
	building_name- The name of the building
	outputs- List of values from EnergyPlus
	Outputs:
	[(OPC_tag, value)]- List of tuples of tags and values
	"""
	output_tags = mapping[building_name]["Outputs"]
	ret = []
	for tag, value in zip(output_tags, outputs):
		ret.append((tag, value))

	return ret

def map_input(building_name, inputs):
	"""
	Maps inputs from OPC server to EnergyPlus

	Inputs:
	building_name- The name of the building
	inputs- [(name, value, status, timestamp)] from opc
	Outputs:
	[value]- List of values, in the order specified by E+
	"""
	input_tags = mapping[building_name]["Inputs"]
	ret = []
	for tag in input_tags:
		matching_input = next(t for t in inputs if t[0] == tag)
		ret.append(matching_input[2])

	return ret


