import xml.etree.ElementTree as ET
import os

var_config_path = 'C:\Users\Expresso Logic\Documents\GitHub\DPC-IAX-Iconics\ePlusBuildings' 

with cd(var_config_path):
	buildings = next(os.walk('.'))[1]
	configs = {}
	for building in buildings:
		print(building)
		with cd(self.path + "/" + building):
			tree = ET.parse('variables.cfg')
			root = tree.getroot()
			inputs = []
			outputs = {}
			unknowns = []
			for bcvtb_var in root:
				input_type = bcvtb_var.attrib
				if input_type == "Ptolemy":
					setpoint_name = bcvtb_var[0].attrib.schedule
					inputs.append(setpoint_name)
				else:
					var_name, var_type = bcvtb_var[0].attrib.name, bcvtb_var[0].attrib.type
					if var_name == "EMS":
						outputs["EMS"].append(var_type)
					elif var_name == "Environment":
						outputs["Environment"].append(var_type)
					elif var_name == "Whole Building":
						outputs["WholeBuilding"].append(var_type)
					elif var_type == "Zone Air Temperature":
						ouputs["ZoneAirTemp"].append(var_name)
					else
						unknowns.append(var_name + var_type)
			configs[building]["Inputs"] = inputs
			configs[building]["Outputs"] = outputs
			configs[building]["Unknown"] = unknowns
			print(configs)




class cd:
	"""Context manager for changing the current working directory"""
	def __init__(self, newPath):
		self.newPath = os.path.expanduser(newPath)

	def __enter__(self):
		self.savedPath = os.getcwd()
		os.chdir(self.newPath)

	def __exit__(self, etype, value, traceback):
		os.chdir(self.savedPath)