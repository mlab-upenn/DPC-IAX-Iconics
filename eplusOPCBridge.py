import OpenOPC
import pyEp
import time

opc = OpenOPC.open_client()
opc.connect('ICONICS.Simulator')
print("Connected to ICONICS.Simulator")

input_tags = opc.list('EnergyPlus.Inputs.*')
output_tags = opc.list('EnergyPlus.Outputs.*.*', recursive=True)
opc.read(input_tags, group = 'inputs')


pyEp.set_bcvtb_home('C:\Python27\Lib\site-packages\pyEp\\bcvtb')
pyEp.set_energy_plus_dir('C:\EnergyPlusV8-1-0\\')
path_to_buildings = 'C:\Users\ICONICS_USER\Documents\EplusBuildings'
eps = []
timesteps = []

sim_total_time = 0.0
wait_total_time = 0.0
i = 0

command = ""
prev_command = ""
while True:
	command,_,_ = opc.read('EnergyPlus.Control.Status')
	if command is not prev_command:
		if command is 0: #setup
			print("Setup")
			builder = pyEp.socket_builder(path_to_buildings)
			configs = builder.build()
			for config in configs:
				building_path = path_to_buildings + "\\" + config[1]
				print(building_path)
				eps.append(pyEp.ep_process('localhost', config[0], building_path, True))
				timesteps.append(0)
			print("E+ Iniitalized")
		elif command is 2:
			print("Simulation Total Time:" + str(sim_total_time))
			print("Simulation Timestep Average: " + str(sim_total_time/i))
			print("Simulation Wait Average: " + str(wait_total_time/i))					
		elif command is 3: #reset
			print("Reset")
			for ep in eps:
				ep.close()
			eps = []
		elif command is 4: #close
			print("Closing")
			for ep in eps:
				ep.close()		
			opc.remove(opc.groups())
			opc.close()
			break
	elif command is 1: #Simulation
		for idx, ep in enumerate(eps):
			start = time.clock()
			#Get output from EnergyPlus and write to OPC Server
			#TODO: Update so everything is more automatic, when changing how the OPC Simulated Server is configurated
			if timesteps[idx] % 12 == 0:
				print(timesteps[idx])
			output = ep.decode_packet_simple(ep.read())
			power = output[0]
			opc.write(('EnergyPlus.Outputs.WholeBuilding.FacilityTotalElectricDemandPower', power))
			#Wait for controller to update to next time step
			new_time_step, status, _ = opc.read('EnergyPlus.Control.TimeStep')		
			if status is 'Error':
				print("Error Reading TimeStep")
				continue
			# print(type(timesteps[idx]))
			# print(int(timesteps[idx]))
			# print(type(new_time_step))
			# print(int(new_time_step))
			start_w = time.clock()
			while int(timesteps[idx]) == int(new_time_step):
				new_time_step, status, _ = opc.read('EnergyPlus.Control.TimeStep')
				temp_command,_,_ = opc.read('EnergyPlus.Control.Status')
				if temp_command is not command:
					print("Got Interrupt")
					break
			end_w = time.clock()
			wait_total_time = wait_total_time + (end_w - start_w)
			#Read new inputs from the controller and give them to EnergyPlus
			
			cw,_,_ = opc.read('EnergyPlus.Inputs.cwsetp')
			lil,_,_ = opc.read('EnergyPlus.Inputs.lilsetp')
			clg,_,_ = opc.read('EnergyPlus.Inputs.clgsetp')
			ep.write(ep.encode_packet_simple([clg, cw, lil], new_time_step))
			timesteps[idx] = new_time_step
			end = time.clock()
			sim_total_time = sim_total_time + (end-start)
			i = i+ 1
	prev_command = command

print("BRIDGE COLLAPSED")