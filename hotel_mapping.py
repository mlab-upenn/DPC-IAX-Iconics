def map_outputs(output):
	hvac_power = output[7]
	power = output[8]
	time_of_day = output[2]
	day_of_week = output[3]
	current_month = output[0]
	drybulb = output[5]
	humidity = output[6]
	basement = output[9]
	corridor = output[10]
	guest = output[12]
	kitchen = output[11]
	lobby = output[13]



	mapping = {
		"EPSimServer.EnergyPlus.Outputs.WholeBuilding.FacilityTotalElectricDemandPower" : power,
		'EPSimServer.EnergyPlus.Outputs.WholeBuilding.FacilityTotalHVACElectricDemandPower' : hvac_power,
		'EPSimServer.EnergyPlus.Outputs.EMS.DayOfWeek': day_of_week,
		'EPSimServer.EnergyPlus.Outputs.EMS.TimeOfDay': time_of_day,
		"EPSimServer.EnergyPlus.Outputs.EMS.currentMonth" : current_month,
		'EPSimServer.EnergyPlus.Outputs.Environment.Drybulb' : drybulb,
		'EPSimServer.EnergyPlus.Outputs.Environment.Humidity' : humidity,
		'EPSimServer.EnergyPlus.Outputs.ZoneAirTemperature.Basement' : basement,
		'EPSimServer.EnergyPlus.Outputs.ZoneAirTemperature.Corridor' : corridor,
		'EPSimServer.EnergyPlus.Outputs.ZoneAirTemperature.GuestRoom' : guest,
		'EPSimServer.EnergyPlus.Outputs.ZoneAirTemperature.Kitchen' : kitchen,
		'EPSimServer.EnergyPlus.Outputs.ZoneAirTemperature.Lobby' : lobby
	}

	return mapping

def map_inputs():
	input_order = [
	'EPSimServer.EnergyPlus.Inputs.clgsetp',
	'EPSimServer.EnergyPlus.Inputs.htsetp',
	'EPSimServer.EnergyPlus.Inputs.kclgsetp',
	'EPSimServer.EnergyPlus.Inputs.khtsetp',
	'EPSimServer.EnergyPlus.Inputs.gclgsetp',
	'EPSimServer.EnergyPlus.Inputs.ghtsetp',	
	'EPSimServer.EnergyPlus.Inputs.airsetp',
	'EPSimServer.EnergyPlus.Inputs.cwsetp'
	]
	return input_order