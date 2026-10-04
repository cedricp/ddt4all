# Enable AndroidAuto and CarPlay on R-Link2
$addr = 13

init_can_500 # init can macro

1003

# check if it is rlink2
exit_if_not F18A 6 4 FFFFFF 434150

set_bits 2130 10 5 60 60

wait 2

# reload rlink2
1101

exit
