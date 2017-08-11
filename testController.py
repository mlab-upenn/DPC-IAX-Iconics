print("HI")
import matlab.engine


eng = matlab.engine.start_matlab(nargout = 0)
# eng.pwd
# eng.startOPC()
# timeSteps = 0
# print("OPC Started Successfully")
# while timeSteps < 288:
# 	outputs = eng.readFromOPC()
# 	print(timeSteps)
# 	print(outputs)
# 	eng.writeToOPC([27, 6.7, 0.7])
# 	timeSteps = timeSteps + 1

# print("Simulation Ended")