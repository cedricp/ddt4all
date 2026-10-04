# Repair script for rlink2 black screen
$addr = 13

init_can_500 # init can macro

1003

# check if it is rlink2
exit_if_not F18A 6 4 FFFFFF 434150

# HIGH 2 768x1024
2E2303032802131303003C000004500014001E001E040014E8002C006967

wait 2
# reload rlink2
1101

exit
