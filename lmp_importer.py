import csv, datetime, hh_import

lmp = []
with open('chicago12-13lmp.csv') as f:
	reader = csv.reader(f, delimiter=',')
	for row in reader:
		lmp = [float(price) for price in row]

start_date = datetime.datetime(2016, 1, 1, 0, 0, 0)
time_range = [start_date + datetime.timedelta(minutes = 60*i) for i in range(0, len(lmp))]

name = "LMP"
path = 'C:\Users\Expresso Logic\Documents\GitHub\DPC-IAX-Iconics\HHImport\Source\\'
tag_name = 	"ua:HyperHistorian\\\\Configuration/EnergyPlus/LMP"
importer = hh_import.hh_import(name, path, tag_name)
importer.export(time_range, lmp)
