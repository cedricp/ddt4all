# light and rain sensor off or on
$addr = 26

can500  # init can macro

10C0
#3BA017FF # light sensor on
3BA01700 # light sensor off
#3BA012FF # rain sensor on
3BA01200 # rain sensor off

exit

