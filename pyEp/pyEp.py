import socket
import sys
import time
import subprocess
import os

class ep_process:
	def __init__(self, ip, port, building_path, weather, isWindows=False):
		print("Starting E+")
		FNULL = open('epluslog', 'w')
		global eplus_dir
		for file in os.listdir(building_path):
			if file.endswith('.idf'):
				idf = file
				break

		if isWindows:
			eplus_script = eplus_dir + 'RunEplus'
			idf_path = building_path + '\\' + idf[:-4]
			print(idf_path)
			self.p = subprocess.Popen([eplus_script, idf_path, weather], stdout=FNULL, shell=True, cwd=building_path)		
		else:
			eplus_script = eplus_dir + 'runenergyplus'
			idf_path = building_path + '/' + idf[:-4]
			self.p = subprocess.Popen([eplus_script, idf_path, weather], stdout=FNULL)

		print(eplus_script, building_path, weather)
		
		s = socket.socket()
		s.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1) 
		s.bind((ip, port))
		print("Started Wating for connection on %s %s" 	% (ip, port))
		s.listen(1)
		remote, address = s.accept()
		self.remote = remote
		print("Got connection from " + str(address))

	def close(self):
		print("Closing E+")
		self.remote.send("2 1\n")
		self.remote.close()
		#self.p.terminate()

	def read(self):
		data = ""
		while True:
			packet = self.remote.recv(1024)
			data = data + packet;
			if "\n" in packet: # \n is end flag
				break
		return data

	def write(self, packet):
		self.remote.send(packet)


	#Takes in a packet from ep_process.read() and returns a list of lists corresponding to the real, int, and boolean values
	#Returns an empty list if there are no more outputs, or if an error occured
	def decode_packet(self, packet):
		comp = packet.split(" ")
		comp = comp[:-1]
		comp_values = [float(s) for s in comp]
		output = []
		if comp_values[0] == 2: #Version 2
			if comp_values[1] == 0: # Simulation still running
				num_real = int(comp_values[2])
				num_int = int(comp_values[3])
				num_bool = int(comp_values[4])
				time = comp_values[5]

				reals = comp_values[6:6+num_real]
				ints = [int(comp_values[i]) for i in range(6+num_real, 6+num_real + num_int)]
				bools = [comp_values[i] == 1 for i in range(6+num_real+num_int, 6+num_real+num_int+num_bool)]
				output.append(reals)
				output.append(ints)
				output.append(bools)
			else:
				switch = {
					1 : "Simulation Finished. No output",
					-10 : "Initialization Error",
					-20 : "Time Integration Error",
					-1 : "An Unspecified Error Occured"
				}
				print(switch.get(comp_values[1]))
		else:
			print("Version Error. Use Version 2 of Communication Protocol")
		return output


	#Takes in a list of lists with the real, int, and boolean values to input
	def encode_packet(self, setpoints, time):
		comp = [2, 0, len(setpoints[0]), len(setpoints[1]), len(setpoints[2]), time]		
		for i in range(0,3):
			comp.extend(setpoints[i])
		str_comp = [str(val) for val in comp]
		str_comp.extend("\n")
		output = " ".join(str_comp)
		return output

	#Returns a list of float outputs from E+
	def decode_packet_simple(self, packet):
		comp = packet.split(" ")
		comp = comp[:-1]
		comp_values = [float(s) for s in comp]
		output = []
		if comp_values[0] == 2: #Version 2
			if comp_values[1] == 0: # Simulation still running
				num_real = int(comp_values[2])
				time = comp_values[5]

				reals = comp_values[6:6+num_real]
				output = reals
			else:
				switch = {
					1 : "Simulation Finished. No output",
					-10 : "Initialization Error",
					-20 : "Time Integration Error",
					-1 : "An Unspecified Error Occured"
				}
				print(switch.get(comp_values[1]))
		else:
			print("Version Error. Use Version 2 of Communication Protocol")
		return output

	#Encodes all setpoints as reals to input to energyplus
	def encode_packet_simple(self, setpoints, time):
		comp = [2, 0, len(setpoints), 0, 0, time]	
		comp.extend(setpoints)

		str_comp = [str(val) for val in comp]
		str_comp.extend("\n")
		output = " ".join(str_comp)
		return output

def set_bcvtb_home(path):
	print("Set BCVTB Home")
	os.environ['BCVTB_HOME'] = path # visible in this process + all children

def set_energy_plus_dir(path):
	global eplus_dir
	eplus_dir = path	


def test(ip, port):
	ep = ep_process(ip, port)
	time_step = 0
	logdata = []
	while time_step < 288:
		output = ep.decode_packet_simple(ep.read())
		logdata.append(output)

		setpoints = [26, 7, 0.6]
		ep.write(ep.encode_packet_simple(setpoints, time_step))
		time_step = time_step + 1
	ep.read()
	ep.close()

	print("-------Results-------")
	print([logdata[i][0] for i in x_length])

"""
Energy Plus Protocol Version 1 & 2:
Packet has the form:
      v f dr di db t r1 r2 ... i1 i2 ... b1 b2 ...
where
  v    - version number (1,2)
  f    - flag (0: communicate, 1: finish, -10: initialization error,
               -20: time integration error, -1: unknown error)
  dr   - number of real values
  di   - number of integer values
  db   - number of boolean values
  t    - current simulation time in seconds (format %20.15e)
  r1 r2 ... are real values (format %20.15e)
  i1 i2 ... are integer values (format %d)
  b1 b2 ... are boolean values (format %d)
Note that if f is non-zero, other values after it will not be processed.
"""

if __name__ == "__main__":
	sys.exit(test('localhost', 45095))