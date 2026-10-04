
# QR25 Idle speed correction
$addr = 7A

init_can_500 # init can macro

# check ECU

exit_if_not 83 26 8 FF 44
exit_if_not 83 26 17 FF 43

:checkeng
goto_if 1201 5 4 FFFF 0000 runeng

goto engisrun

:runeng

cls
#
#   Run ENGINE
#

if_key q end
wait 1
goto checkeng

:engisrun
cls
var lastResponse = $lastResponse
#
#  Idle Speed
#
value 1201 5 4 FFFF 25 0 2
#
#   ECU is running
#
#  Select correction
#
# Press:
#   0 reset
#   1 +25
#   2 +50
#   3 +75
#   4 +100
#
#  q for Exit
#

if_key 0 key0
if_key 1 key1
if_key 2 key2
if_key 3 key3
if_key 4 key4
if_key q end
wait 1
goto engisrun

:key0
3B0200
goto engisrun

:key1
3B0202
goto engisrun

:key2
3B0204
goto engisrun

:key3
3B0206
goto engisrun

:key4
3B0208
goto engisrun

:end

exit
