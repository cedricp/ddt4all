# switch off and hide error StartStop
$addr = 27

can500  # init can macro

10C0
2E075201 # startstop off
2E076300 # startstop hide
#2E075200 # startstop on
#2E076301 # startstop unhide
