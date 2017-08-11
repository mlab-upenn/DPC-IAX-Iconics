import OpenOPC


opc = OpenOPC.open_client()
opc.connect('ICONICS.Simulator')
print("Connected to ICONICS.Simulator")

print("Start Control Loop")
opc.write(('EnergyPlus.Control.Start', 1))
time = 0
while time = opc.read('EnergyPlus.Control.Time') < 288:
