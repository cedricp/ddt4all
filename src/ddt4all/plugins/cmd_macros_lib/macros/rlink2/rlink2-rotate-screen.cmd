# Rotate R-Link2 screen
$addr = 13

init_can_500 # init can macro

1003

exit_if_not F18A 6 4 FFFFFF 434150

xor_bits 2130 10 4 10 10

wait 2

# reload rlink2
1101

exit
