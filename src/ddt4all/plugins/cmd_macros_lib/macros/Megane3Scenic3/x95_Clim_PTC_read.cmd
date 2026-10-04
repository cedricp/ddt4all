# Read RTC config
$addr = 29

can500  # init can macro

10C0
2104	# Read PTC config
# HEX 0  DEC  0:Not Configurated
# HEX 1  DEC  1:Without PTC
# HEX 16 DEC 22:PTC 1,6kW
# HEX 10 DEC 16:PTC 1kW
# HEX 18 DEC 24:PTC 1,8kW