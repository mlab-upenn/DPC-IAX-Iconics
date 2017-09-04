def map_outputs(output):
	power = output[0]
	time_of_day = output[1]
	day_of_week = output[2]
	bot_temp = output[13]
	mid_temp = output[17]
	top_temp = output[21]


	mapping = {
		'EPSimServer.EnergyPlus.Outputs.WholeBuilding.FacilityTotalElectricDemandPower' : power,
		'EPSimServer.EnergyPlus.Outputs.EMS.DayOfWeek' : day_of_week,
		'EPSimServer.EnergyPlus.Outputs.EMS.TimeOfDay': time_of_day,
		"EPSimServer.EnergyPlus.Outputs.ZoneTemperature.Perimeter_bot_ZN_2" : bot_temp,
		'EPSimServer.EnergyPlus.Outputs.ZoneTemperature.Perimeter_mid_ZN_2' : mid_temp,
		'EPSimServer.EnergyPlus.Outputs.ZoneTemperature.Perimeter_top_ZN_2' : top_temp
	}

	return mapping

def map_inputs():
	input_order = [
	"EPSimServer.EnergyPlus.Inputs.clgsetp",
	"EPSimServer.EnergyPlus.Inputs.cwsetp",
	"EPSimServer.EnergyPlus.Inputs.lilsetp"
	]

	return input_order
