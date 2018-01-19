import pyEp
import matplotlib.pyplot as plt
import time as delay

pyEp.set_bcvtb_home('C:\Python27\Lib\site-packages\pyEp\\bcvtb')
#Set default EnergyPlus Version
pyEp.set_energy_plus_dir('C:\EnergyPlusV8-1-0\\')
path_to_buildings = 'C:\Users\Expresso Logic\Documents\GitHub\DPC-IAX-Iconics\ePlusBuildingsTest'
weather_file = 'USA_NY_New.York-Central.Park.725033_TMY3'

builder = pyEp.socket_builder(path_to_buildings)
configs = builder.build() #[(port, building_name, idf)]
building_path = path_to_buildings + "\\" + configs[0][1]

ep = pyEp.ep_process('localhost', configs[0][0], building_path, weather_file, True)

outputs = []

EPTimeStep = 12
SimDays = 365
kStep = 1
MAXSTEPS = SimDays*24*EPTimeStep
deltaT = (60/EPTimeStep)*60;
print("Total Steps", MAXSTEPS)

while kStep < MAXSTEPS:
		
		time = (kStep-1) * deltaT
		
		dayTime = time % 86400

		if dayTime == 0:
			print(kStep)

		output = ep.decode_packet_simple(ep.read())
		outputs.append(output)

		setpoints = [24, 6.7, 0.7]

		if(dayTime < 5 * 3600):
			setpoints = [27, 6.7, 0.05]
		elif(dayTime < 6 * 3600):
			setpoints = [27, 6.7, 0.01]
		elif(dayTime < 7 * 3600):
			setpoints = [24, 6.7, 0.1]
		elif(dayTime < 8 * 3600):
			setpoints = [24, 6.7, 0.3]
		elif(dayTime < 17 * 3600):
			setpoints = [24, 6.7, 0.9]
		elif(dayTime < 18 * 3600):
			setpoints = [24, 6.7, 0.7]
		elif(dayTime < 20 * 3600):
			setpoints = [24, 6.7, 0.5]
		elif(dayTime < 22 * 3600):
			setpoints = [24, 6.7, 0.4]
		elif(dayTime < 23 * 3600):
			setpoints = [24, 6.7, 0.1]
		elif(dayTime < 24 * 3600):
			setpoints = [24, 6.7, 0.05]

		ep.write(ep.encode_packet_simple(setpoints, (kStep-1) * deltaT))
		
		kStep = kStep + 1

ep.close()
plt.plot([output[0] for output in outputs])
plt.show()