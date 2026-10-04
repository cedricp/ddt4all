# Air Quality Management OFF/ON
$addr = 29

can500  # init can macro

10C0
3B0B01	# WithoutSensor
3B1201	# Without Air Quality Management
#3B0B02	# WithLocalSensor
#3B1202	# With Fragrance, Without Ionizer
#1101 	# ECU RESET