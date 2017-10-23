def strategy1(building_name, time):
	if time <= 7*3600:
		clgstp = 30
		htgstp = 16
		kitclgstp = 30
		kithtgstp = 16
		guestclgstp = 24
		guesthtgstp = 21
		sat = 13
		cwstp = 6.7
	elif time < 17 * 3600 and time > 13 * 3600:
		clgstp = 30
		htgstp = 18
		kitclgstp = 30
		kithtgstp = 18
		guestclgstp = 24
		guesthtgstp = 21
		sat = 13
		cwstp = 8
	else:
		clgstp = 24
		htgstp = 21
		kitclgstp = 26
		kithtgstp = 19
		guestclgstp = 24
		guesthtgstp = 21
		sat = 13
		cwstp = 6.7

	return (clgstp, kitclgstp, guestclgstp, sat, cwstp, htgstp, kithtgstp, guesthtgstp)


def strategy2(time):
	pass

def strategy3(time):
	pass

def baseline(building_name, time):
	if "LargeHotel" in building_name: 
		if time <= 7*3600:
			clgstp = 30
			htgstp = 16
			kitclgstp = 30
			kithtgstp = 16
			guestclgstp = 24
			guesthtgstp = 21
			sat = 13
			cwstp = 6.7
		else:
			clgstp = 24
			htgstp = 21
			kitclgstp = 26
			kithtgstp = 19
			guestclgstp = 24
			guesthtgstp = 21
			sat = 13
			cwstp = 6.7
		#NOTE: Must matching ordering specified in variables.cfg/mapping.json
		return [clgstp, htgstp, kitclgstp, kithtgstp, guestclgstp, guesthtgstp, sat, cwstp]

	if "LargeOffice" in building_name:
		clg = 26.7
		cw = 6.7
		lil = 0.7
		return [clg, cw, lil]


def default(building_name, time):
	return baseline(building_name, time)

