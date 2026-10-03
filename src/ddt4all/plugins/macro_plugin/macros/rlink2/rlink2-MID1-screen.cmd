# Repair script for rlink2 black screen
$addr = 13

init_can_500 # init can macro

1003

# check if it is rlink2
exit_if_not F18A 6 4 FFFFFF 434150

# MID 1  480x800
2E230301F404080801E03C0000039D000A0005006E03200AD7022C006967

wait 2
# reload rlink2
1101

exit
