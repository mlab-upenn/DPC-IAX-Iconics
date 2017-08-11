import socket
import xml.etree.ElementTree as ET
import os

class socket_builder:

	#Path to the main folder with all the subfolders with each buildings

	def __init__(self, path):
		self.path = path

	def build(self):
		with cd(self.path):
			buildings = next(os.walk('.'))[1]
			configs = []
			for building in buildings:
				with cd(self.path + "/" + building):
					idf = None
					for file in os.listdir('.'):
						if file.endswith('.idf'):
							idf = file
							break

					if idf is None:
						break

					port = self.get_free_port()
					configs.append((port, building, idf))
					print(port)
					xml = self.build_XML(port)
					#xml.write('socket.cfg', encoding='ISO-8859-1')
		return configs

	def get_free_port(self):
		s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		s.bind(("",0))
		s.listen(1)
		port = s.getsockname()[1]
		s.close()
		return port

	def build_XML(self, port):
		tree = ET.ElementTree()
		bcvtb_client = ET.Element('BCVTB-client')
		ipc = ET.SubElement(bcvtb_client, 'ipc')
		socket_ele = ET.SubElement(ipc, 'socket')
		socket_ele.set('port', str(port))
		socket_ele.set('hostname', 'localhost')
		tree._setroot(bcvtb_client)
		tree.write('socket.cfg', encoding='ISO-8859-1')


class cd:
	"""Context manager for changing the current working directory"""
	def __init__(self, newPath):
		self.newPath = os.path.expanduser(newPath)

	def __enter__(self):
		self.savedPath = os.getcwd()
		os.chdir(self.newPath)

	def __exit__(self, etype, value, traceback):
		os.chdir(self.savedPath)