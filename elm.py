'''module contains class for working with ELM327
   version: 160829
   Borrowed from PyRen (modified for this use)
'''

import options

import serial
from serial.tools import list_ports

import sys
import os
import re
import time
import string
from datetime import datetime

snat = {"01": "760", "02": "724", "04": "762", "07": "771", "08": "778", "0D": "775", "0E": "76E", "0F": "770",
        "13": "732", "1B": "7AC", "1C": "76B", "1E": "768", "23": "773", "24": "77D", "26": "765", "27": "76D",
        "29": "764", "2A": "76F", "2C": "772", "2E": "7BC", "32": "776", "3A": "7D2", "40": "727", "4D": "7BD",
        "50": "738", "51": "763", "57": "767", "59": "734", "62": "7DD", "66": "739", "67": "793", "68": "77E",
        "6B": "7B5", "6E": "7E9", "77": "7DA", "79": "7EA", "7A": "7E8", "7C": "77C", "86": "7A2", "87": "7A0",
        "93": "7BB", "95": "7EC", "A5": "725", "A6": "726", "A7": "733", "A8": "7B6", "C0": "7B9", "D1": "7EE",
        "F7": "736", "F8": "737", "FA": "77B", "FD": "76F", "FE": "76C", "FF": "7D0"}
dnat = {"01": "740", "02": "704", "04": "742", "07": "751", "08": "758", "0D": "755", "0E": "74E", "0F": "750",
        "13": "712", "1B": "7A4", "1C": "74B", "1E": "748", "23": "753", "24": "75D", "26": "745", "27": "74D",
        "29": "744", "2A": "74F", "2C": "752", "2E": "79C", "32": "756", "3A": "7D6", "40": "707", "4D": "79D",
        "50": "718", "51": "743", "57": "747", "59": "714", "62": "7DC", "66": "719", "67": "792", "68": "75A",
        "6B": "795", "6E": "7E1", "77": "7CA", "79": "7E2", "7A": "7E0", "7C": "75C", "86": "782", "87": "780",
        "93": "79B", "95": "7E4", "A5": "705", "A6": "706", "A7": "713", "A8": "796", "C0": "799", "D1": "7E6",
        "F7": "716", "F8": "717", "FA": "75B", "FD": "74F", "FE": "74C", "FF": "7D0"}

# Code snippet from https://github.com/rbei-etas/busmaster
negrsp = {"10": "NR: General Reject",
          "11": "NR: Service Not Supported",
          "12": "NR: SubFunction Not Supported",
          "13": "NR: Incorrect Message Length Or Invalid Format",
          "21": "NR: Busy Repeat Request",
          "22": "NR: Conditions Not Correct Or Request Sequence Error",
          "23": "NR: Routine Not Complete",
          "24": "NR: Request Sequence Error",
          "31": "NR: Request Out Of Range",
          "33": "NR: Security Access Denied- Security Access Requested  ",
          "35": "NR: Invalid Key",
          "36": "NR: Exceed Number Of Attempts",
          "37": "NR: Required Time Delay Not Expired",
          "40": "NR: Download not accepted",
          "41": "NR: Improper download type",
          "42": "NR: Can not download to specified address",
          "43": "NR: Can not download number of bytes requested",
          "50": "NR: Upload not accepted",
          "51": "NR: Improper upload type",
          "52": "NR: Can not upload from specified address",
          "53": "NR: Can not upload number of bytes requested",
          "70": "NR: Upload Download NotAccepted",
          "71": "NR: Transfer Data Suspended",
          "72": "NR: General Programming Failure",
          "73": "NR: Wrong Block Sequence Counter",
          "74": "NR: Illegal Address In Block Transfer",
          "75": "NR: Illegal Byte Count In Block Transfer",
          "76": "NR: Illegal Block Transfer Type",
          "77": "NR: Block Transfer Data Checksum Error",
          "78": "NR: Request Correctly Received-Response Pending",
          "79": "NR: Incorrect ByteCount During Block Transfer",
          "7E": "NR: SubFunction Not Supported In Active Session",
          "7F": "NR: Service Not Supported In Active Session",
          "80": "NR: Service Not Supported In Active Diagnostic Mode",
          "81": "NR: Rpm Too High",
          "82": "NR: Rpm Too Low",
          "83": "NR: Engine Is Running",
          "84": "NR: Engine Is Not Running",
          "85": "NR: Engine RunTime TooLow",
          "86": "NR: Temperature Too High",
          "87": "NR: Temperature Too Low",
          "88": "NR: Vehicle Speed Too High",
          "89": "NR: Vehicle Speed Too Low",
          "8A": "NR: Throttle/Pedal Too High",
          "8B": "NR: Throttle/Pedal Too Low",
          "8C": "NR: Transmission Range In Neutral",
          "8D": "NR: Transmission Range In Gear",
          "8F": "NR: Brake Switch(es)NotClosed (brake pedal not pressed or not applied)",
          "90": "NR: Shifter Lever Not In Park ",
          "91": "NR: Torque Converter Clutch Locked",
          "92": "NR: Voltage Too High",
          "93": "NR: Voltage Too Low"}


cmdb = '''
#v1.0 ;AC P; ATZ                   ; Z                  ; reset all
#v1.0 ;AC P; ATE1                  ; E0, E1             ; Echo off, or on*
#v1.0 ;AC P; ATL0                  ; L0, L1             ; Linefeeds off, or on
#v1.0 ;AC  ; ATI                   ; I                  ; print the version ID
#v1.0 ;AC  ; AT@1                  ; @1                 ; display the device description
#v1.0 ;AC P; ATAL                  ; AL                 ; Allow Long (>7 byte) messages
#v1.0 ;AC  ; ATBD                  ; BD                 ; perform a Buffer Dump
#V1.0 ;ACH ; ATSP4                 ; SP h               ; Set Protocol to h and save it
#v1.0 ;AC  ; ATBI                  ; BI                 ; Bypass the Initialization sequence
#v1.0 ;AC P; ATCAF0                ; CAF0, CAF1         ; Automatic Formatting off, or on*
#v1.0 ;AC  ; ATCFC1                ; CFC0, CFC1         ; Flow Controls off, or on*
#v1.0 ;AC  ; ATCP 01               ; CP hh              ; set CAN Priority to hh (29 bit)
#v1.0 ;AC  ; ATCS                  ; CS                 ; show the CAN Status counts
#v1.0 ;AC  ; ATCV 1250             ; CV dddd            ; Calibrate the Voltage to dd.dd volts
#v1.0 ;AC  ; ATD                   ; D                  ; set all to Defaults
#v1.0 ;AC  ; ATDP                  ; DP                 ; Describe the current Protocol
#v1.0 ;AC  ; ATDPN                 ; DPN                ; Describe the Protocol by Number
#v1.0 ;AC P; ATH0                  ; H0, H1             ; Headers off*, or on
#v1.0 ;AC  ; ATI                   ; I                  ; print the version ID
#v1.0 ;AC P; ATIB 10               ; IB 10              ; set the ISO Baud rate to 10400*
#v1.0 ;AC  ; ATIB 96               ; IB 96              ; set the ISO Baud rate to 9600
#v1.0 ;AC  ; ATL1                  ; L0, L1             ; Linefeeds off, or on
#v1.0 ;AC  ; ATM0                  ; M0, M1             ; Memory off, or on
#v1.0 ; C  ; ATMA                  ; MA                 ; Monitor All
#v1.0 ; C  ; ATMR 01               ; MR hh              ; Monitor for Receiver = hh
#v1.0 ; C  ; ATMT 01               ; MT hh              ; Monitor for Transmitter = hh
#v1.0 ;AC  ; ATNL                  ; NL                 ; Normal Length messages*
#v1.0 ;AC  ; ATPC                  ; PC                 ; Protocol Close
#v1.0 ;AC  ; ATR1                  ; R0, R1             ; Responses off, or on*
#v1.0 ;AC  ; ATRV                  ; RV                 ; Read the input Voltage
#v1.0 ;ACH ; ATSP7                 ; SP h               ; Set Protocol to h and save it
#v1.0 ;ACH ; ATSH 00000000         ; SH wwxxyyzz        ; Set Header to wwxxyyzz
#v1.0 ;AC  ; ATSH 001122           ; SH xxyyzz          ; Set Header to xxyyzz
#v1.0 ;AC P; ATSH 012              ; SH xyz             ; Set Header to xyz
#v1.0 ;AC  ; ATSP A6               ; SP Ah              ; Set Protocol to Auto, h and save it
#v1.0 ;AC  ; ATSP 6                ; SP h               ; Set Protocol to h and save it
#v1.0 ;AC  ; ATCM 123              ; CM hhh             ; set the ID Mask to hhh
#v1.0 ;AC  ; ATCM 12345678         ; CM hhhhhhhh        ; set the ID Mask to hhhhhhhh
#v1.0 ;AC  ; ATCF 123              ; CF hhh             ; set the ID Filter to hhh
#v1.0 ;AC  ; ATCF 12345678         ; CF hhhhhhhh        ; set the ID Filter to hhhhhhhh
#v1.0 ;AC P; ATST FF               ; ST hh              ; Set Timeout to hh x 4 msec
#v1.0 ;AC P; ATSW 96               ; SW 00              ; Stop sending Wakeup messages
#v1.0 ;AC P; ATSW 34               ; SW hh              ; Set Wakeup interval to hh x 20 msec
#v1.0 ;AC  ; ATTP A6               ; TP Ah              ; Try Protocol h with Auto search
#v1.0 ;AC  ; ATTP 6                ; TP h               ; Try Protocol h
#v1.0 ;AC P; ATWM 817AF13E         ; WM [1 - 6 bytes]   ; set the Wakeup Message
#v1.0 ;AC P; ATWS                  ; WS                 ; Warm Start (quick software reset)
#v1.1 ;AC P; ATFC SD 300000        ; FC SD [1 - 5 bytes]; FC, Set Data to [...]
#v1.1 ;AC P; ATFC SH 012           ; FC SH hhh          ; FC, Set the Header to hhh
#v1.1 ;AC P; ATFC SH 00112233      ; FC SH hhhhhhhh     ; Set the Header to hhhhhhhh
#v1.1 ;AC P; ATFC SM 1             ; FC SM h            ; Flow Control, Set the Mode to h
#v1.1 ;AC  ; ATPP FF OFF           ; PP FF OFF          ; all Prog Parameters disabled
#v1.1 ;AC  ; ATPP FF ON            ; PP FF ON           ; all Prog Parameters enabled
#v1.1 ;    ;                       ; PP xx OFF          ; disable Prog Parameter xx
#v1.1 ;    ;                       ; PP xx ON           ; enable Prog Parameter xx
#v1.1 ;    ;                       ; PP xx SV yy        ; for PP xx, Set the Value to yy
#v1.1 ;AC  ; ATPPS                 ; PPS                ; print a PP Summary
#v1.2 ;AC  ; ATAR                  ; AR                 ; Automatically Receive
#v1.2 ;AC 0; ATAT1                 ; AT0, 1, 2          ; Adaptive Timing off, auto1*, auto2
#v1.2 ;    ;                       ; BRD hh             ; try Baud Rate Divisor hh
#v1.2 ;    ;                       ; BRT hh             ; set Baud Rate Timeout
#v1.2 ;ACH ; ATSPA                 ; SP h               ; Set Protocol to h and save it
#v1.2 ; C  ; ATDM1                 ; DM1                ; monitor for DM1 messages
#v1.2 ; C  ; ATIFR H               ; IFR H, S           ; IFR value from Header* or Source
#v1.2 ; C  ; ATIFR0                ; IFR0, 1, 2         ; IFRs off, auto*, or on
#v1.2 ;AC  ; ATIIA 01              ; IIA hh             ; set ISO (slow) Init Address to hh
#v1.2 ;AC  ; ATKW0                 ; KW0, KW1           ; Key Word checking off, or on*
#v1.2 ; C  ; ATMP 0123             ; MP hhhh            ; Monitor for PGN 0hhhh
#v1.2 ; C  ; ATMP 0123 4           ; MP hhhh n          ; and get n messages
#v1.2 ; C  ; ATMP 012345           ; MP hhhhhh          ; Monitor for PGN hhhhhh
#v1.2 ; C  ; ATMP 012345 6         ; MP hhhhhh n        ; and get n messages
#v1.2 ;AC  ; ATSR 01               ; SR hh              ; Set the Receive address to hh
#v1.3 ;    ; AT@2                  ; @2                 ; display the device identifier
#v1.3 ;AC P; ATCRA 012             ; CRA hhh            ; set CAN Receive Address to hhh
#v1.3 ;AC  ; ATCRA 01234567        ; CRA hhhhhhhh       ; set the Rx Address to hhhhhhhh
#v1.3 ;AC  ; ATD0                  ; D0, D1             ; display of the DLC off*, or on
#v1.3 ;AC  ; ATFE                  ; FE                 ; Forget Events
#v1.3 ;AC  ; ATJE                  ; JE                 ; use J1939 Elm data format*
#v1.3 ;AC  ; ATJS                  ; JS                 ; use J1939 SAE data format
#v1.3 ;AC  ; ATKW                  ; KW                 ; display the Key Words
#v1.3 ;AC  ; ATRA 01               ; RA hh              ; set the Receive Address to hh
#v1.3 ;ACH ; ATSP6                 ; SP h               ; Set Protocol to h and save it
#v1.3 ;ACH ; ATRTR                 ; RTR                ; send an RTR message
#v1.3 ;AC  ; ATS1                  ; S0, S1             ; printing of aces off, or on*
#v1.3 ;AC  ; ATSP 00               ; SP 00              ; Erase stored protocol
#v1.3 ;AC  ; ATV0                  ; V0, V1             ; use of Variable DLC off*, or on
#v1.4 ;AC  ; ATCEA                 ; CEA                ; turn off CAN Extended Addressing
#v1.4 ;AC  ; ATCEA 01              ; CEA hh             ; use CAN Extended Address hh
#v1.4 ;AC  ; ATCV 0000             ; CV 0000            ; restore CV value to factory setting
#v1.4 ;AC  ; ATIB 48               ; IB 48              ; set the ISO Baud rate to 4800
#v1.4 ;AC  ; ATIGN                 ; IGN                ; read the IgnMon input level
#v1.4 ;    ;                       ; LP                 ; go to Low Power mode
#v1.4 ;AC  ; ATPB 01 23            ; PB xx yy           ; Protocol B options and baud rate
#v1.4 ;AC  ; ATRD                  ; RD                 ; Read the stored Data
#v1.4 ;AC  ; ATSD 01               ; SD hh              ; Save Data byte hh
#v1.4 ;ACH ; ATSP4                 ; SP h               ; Set Protocol to h and save it
#v1.4 ;AC P; ATSI                  ; SI                 ; perform a Slow (5 baud) Initiation
#v1.4 ;ACH ; ATZ                   ; Z                  ; reset all
#v1.4 ;ACH ; ATSP5                 ; SP h               ; Set Protocol to h and save it
#v1.4 ;AC P; ATFI                  ; FI                 ; perform a Fast Initiation
#v1.4 ;ACH ; ATZ                   ; Z                  ; reset all
#v1.4 ;AC  ; ATSS                  ; SS                 ; use Standard Search order (J1978)
#v1.4 ;AC  ; ATTA 12               ; TA hh              ; set Tester Address to hh
#v1.4 ;ACH ; ATSPA                 ; SP h               ; Set Protocol to h and save it
#v1.4 ;AC  ; ATCSM1                ; CSM0, CSM1         ; Silent Monitoring off, or on*
#v1.4 ;AC  ; ATJHF1                ; JHF0, JHF1         ; Header Formatting off, or on*
#v1.4 ;AC  ; ATJTM1                ; JTM1               ; set Timer Multiplier to 1*
#v1.4 ;AC  ; ATJTM5                ; JTM5               ; set Timer Multiplier to 5
#v1.4b;AC  ; ATCRA                 ; CRA                ; reset the Receive Address filters
#v2.0 ;AC  ; ATAMC                 ; AMC                ; display Activity Monitor Count
#v2.0 ;AC  ; ATAMT 20              ; AMT hh             ; set the Activity Mon Timeout to hh
#v2.1 ;AC  ; ATCTM1                ; CTM1               ; set Timer Multiplier to 1*
#v2.1 ;AC  ; ATCTM5                ; CTM5               ; set Timer Multiplier to 5
#v2.1 ;ACH ; ATZ                   ; Z                  ; reset all
'''


def getcandnat(addr):
    a = str(addr)
    if a in dnat:
        return dnat[a]
    return "??"


def getcansnat(addr):
    a = str(addr)
    if a in snat:
        return snat[a]
    return "??"


def get_available_ports():
    ports = []
    #try:
    portlist = list_ports.comports()
    if len(portlist) == 0: return
    iterator = sorted(list(portlist))
    for port, desc, hwid in iterator:
        ports.append((port, desc))
    #except:
    #    print "Problem while scanning ports"

    return ports


class Port:
    '''This is a serial port or a TCP-connection
       if portName looks like a 192.168.0.10:35000
       then it is wifi and we should open tcp connection
       else try to open serial port
    '''

    portType = 0  # 0-serial 1-tcp
    ipaddr = '192.168.0.10'
    tcpprt = 35000
    portName = ""
    portTimeout = 5  # don't change it here. Change in ELM class

    droid = None
    btcid = None

    hdr = None

    def __init__(self, portName, speed, portTimeout):
        options.elm_failed = False
        self.portTimeout = portTimeout

        portName = portName.strip()

        if re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\:\d{1,5}$", portName):
            import socket
            self.ipaddr, self.tcpprt = portName.split(':')
            self.tcpprt = int(self.tcpprt)
            self.portType = 1
            self.hdr = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.hdr.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            try:
                self.hdr.connect((self.ipaddr, self.tcpprt))
                self.hdr.setblocking(True)
            except:
                options.elm_failed = True

        else:
            self.portName = portName
            self.portType = 0
            try:
                self.hdr = serial.Serial(self.portName, baudrate=speed, timeout=portTimeout)
                return
            except Exception as e:
                print "Error: %s" % str(e)
                print "ELM not connected or wrong COM port ", portName
                iterator = sorted(list(list_ports.comports()))
                print ""
                print "Available COM ports:"
                for port, desc, hwid in iterator:
                    print "%-30s \n\tdesc: %s \n\thwid: %s" % (port, desc.decode("windows-1251"), hwid)
                print ""

            options.elm_failed = True
            options.last_error = "Error: %s" % str(e)

    def read(self):
        try:
            byte = ""
            if self.portType == 1:
                try:
                    byte = self.hdr.recv(1)
                except:
                    # print "Unexpected error:", sys.exc_info()
                    pass
            elif self.portType == 2:
                # if self.droid.bluetoothReadReady(self.btcid):
                #  byte = self.droid.bluetoothRead( 1, self.btcid ).result
                if self.droid.bluetoothReadReady():
                    byte = self.droid.bluetoothRead(1).result
            else:
                if self.hdr.inWaiting():
                    byte = self.hdr.read()
        except:
            print '*' * 40
            print '*       Connection to ELM was lost'
            options.simulation_mode = True

        return byte

    def write(self, data):
        try:
            if self.portType == 1:
                return self.hdr.sendall(data)
            elif self.portType == 2:
                # return self.droid.bluetoothWrite(data , self.btcid)
                return self.droid.bluetoothWrite(data)
            else:
                return self.hdr.write(data)
        except:
            print '*' * 40
            print '*       Connection to ELM was lost'
            options.simulation_mode = True

    def expect(self, pattern, time_out=1):
        tb = time.time()  # start time
        self.buff = ""
        try:
            while (True):
                if not options.simulation_mode:
                    byte = self.read()
                else:
                    byte = '>'

                if byte == '\r': byte = '\n'

                self.buff += byte
                tc = time.time()
                if pattern in self.buff:
                    return self.buff
                if (tc - tb) > time_out:
                    return self.buff + "TIMEOUT"
        except:
            pass
        return ''

    # def wait_ok(self):
    #  return self.expect('>')

    def check_elm(self):

        self.hdr.timeout = 2

        for s in [38400, 115200, 230400, 57600, 9600, 500000]:
            print "\r\t\t\t\t\rChecking port speed:", s,
            sys.stdout.flush()

            self.hdr.baudrate = s
            self.hdr.flushInput()
            self.write("\r")

            # search > string
            tb = time.time()  # start time
            self.buff = ""
            while (True):
                if not options.simulation_mode:
                    byte = self.read()
                else:
                    byte = '>'
                self.buff += byte
                tc = time.time()
                if '>' in self.buff:
                    options.port_speed = s
                    print "\nStart COM speed: ", s
                    self.hdr.timeout = self.portTimeout
                    return True
                if (tc - tb) > 1:
                    break
        print "\nELM not responding"
        return False

    def soft_baudrate(self, baudrate):

        if options.simulation_mode:
            return

        if self.portType == 1:  # wifi is not supported
            print "ERROR - wifi do not support changing baud rate"
            return

        print "Changing baud rate to:", baudrate,

        if baudrate == 38400:
            self.write("at brd 68\r")
        elif baudrate == 57600:
            self.write("at brd 45\r")
        elif baudrate == 115200:
            self.write("at brd 23\r")
        elif baudrate == 230400:
            self.write("at brd 11\r")
        elif baudrate == 500000:
            self.write("at brd 8\r")

        # search OK
        tb = time.time()  # start time
        self.buff = ""
        while (True):
            if not options.simulation_mode:
                byte = self.read()
            else:
                byte = 'OK'
            if byte == '\r' or byte == '\n':
                self.buff = ""
                continue
            self.buff += byte
            tc = time.time()
            if 'OK' in self.buff:
                break
            if (tc - tb) > 1:
                print "ERROR - command not supported"
                sys.exit()

        self.hdr.timeout = 1
        if baudrate == 38400:
            self.hdr.baudrate = 38400
        elif baudrate == 57600:
            self.hdr.baudrate = 57600
        elif baudrate == 115200:
            self.hdr.baudrate = 115200
        elif baudrate == 230400:
            self.hdr.baudrate = 230400
        elif baudrate == 500000:
            self.hdr.baudrate = 500000

        # search ELM
        tb = time.time()  # start time
        self.buff = ""
        while True:
            if not options.simulation_mode:
                byte = self.read()
            else:
                byte = 'ELM'
            if byte == '\r' or byte == '\n':
                self.buff = ""
                continue
            self.buff += byte
            tc = time.time()
            if 'ELM' in self.buff:
                break
            if (tc - tb) > 1:
                print "ERROR - rate not supported. Let's go back."
                self.hdr.timeout = self.portTimeout
                self.hdr.baudrate = options.port_speed
                return

        self.write("\r")

        # search >
        tb = time.time()  # start time
        self.buff = ""
        while (True):
            if not options.simulation_mode:
                byte = self.read()
            else:
                byte = '>'
            if byte == '\r' or byte == '\n':
                self.buff = ""
                continue
            self.buff += byte
            tc = time.time()
            if '>' in self.buff:
                break
            if (tc - tb) > 1:
                print "ERROR - something went wrong. Let's get back."
                self.hdr.timeout = self.portTimeout
                self.hdr.baudrate = options.port_speed
                return

        print "OK"
        return


class ELM:
    '''ELM327 class'''

    port = 0
    lf = 0
    vf = 0

    keepAlive = 4  # send startSession to CAN after silence if startSession defined
    busLoad = 0  # I am sure than it should be zero
    srvsDelay = 0  # the delay next command requested by service
    lastCMDtime = 0  # time when last command was sent to bus
    portTimeout = 5  # timeout of port (com or tcp)
    elmTimeout = 0  # timeout set by ATST

    # error counters
    error_frame = 0
    error_bufferfull = 0
    error_question = 0
    error_nodata = 0
    error_timeout = 0
    error_rx = 0
    error_can = 0

    response_time = 0

    buff = ""
    currentprotocol = ""
    currentsubprotocol = ""
    currentaddress = ""
    startSession = ""
    lastinitrsp = ""

    rsp_cache = {}
    l1_cache = {}

    ATR1 = True
    ATCFC0 = False

    portName = ""

    lastMessage = ""

    def __init__(self, portName, speed, startSession='10C0'):
        for s in [int(speed), 38400, 115200, 230400, 57600, 9600, 500000]:
            print "Tryi opening port %s at %i" % (portName, s)
            self.sim_mode = options.simulation_mode
            self.portName = portName

            if not options.simulation_mode:
                self.port = Port(portName, s, self.portTimeout)

            if not os.path.exists("./logs"):
                os.mkdir("./logs")

            if len(options.log) > 0:
                self.lf = open("./logs/elm_" + options.log, "at")
                self.vf = open("./logs/ecu_" + options.log, "at")

            self.lastCMDtime = 0
            self.ATCFC0 = options.opt_cfc0

            res = self.send_raw("atz")
            if not 'ELM' in res:
                options.elm_failed = True
                options.last_error = "No ELM interface on port %s" % portName
            else:
                options.last_error = ""
                options.elm_failed = False
                break

    def __del__(self):
        try:
            if not self.sim_mode:
                self.port.write("atz\r")
        except:
            pass

    def clear_cache(self):
        ''' Clear L2 cache before screen update
        '''
        self.rsp_cache = {}


    def request(self, req, positive='', cache=True, serviceDelay="0"):
        ''' Check if request is saved in L2 cache.
            If not then
              - make real request
              - convert responce to one line
              - save in L2 cache
            returns response without consistency check
        '''
        if cache and req in self.rsp_cache.keys():
            return self.rsp_cache[req]

        # send cmd
        rsp = self.cmd(req, serviceDelay)

        # parse response
        res = ""
        for s in rsp.split('\n'):
            if ':' in s:
                res += s[2:].strip() + ' '
            else:  # response consists only of one frame
                if s.replace(' ', '').startswith(positive.replace(' ', '')):
                    res += s.strip() + ' '

        rsp = res

        # populate L2 cache
        self.rsp_cache[req] = rsp

        # save log
        if self.vf != 0:
            tmstr = datetime.now().strftime("%H:%M:%S.%f")[:-3]
            self.vf.write(tmstr + ";" + dnat[self.currentaddress] + ";" + req + ";" + rsp + "\n")
            self.vf.flush()

        return rsp

    def errorval(self, val):
        if val in negrsp.keys():
            return negrsp[val]

    def cmd(self, command, serviceDelay="0"):

        tb = time.time()  # start time

        # Ensure time gap between commands
        dl = self.busLoad + self.srvsDelay - tb + self.lastCMDtime
        if ((tb - self.lastCMDtime) < (self.busLoad + self.srvsDelay)) and "AT" not in command.upper():
            time.sleep(self.busLoad + self.srvsDelay - tb + self.lastCMDtime)

        tb = time.time()  # renew start time

        # If we are on CAN and there was more than keepAlive seconds of silence and
        # start_session_can was executed then send startSession command again
        # if ((tb-self.lastCMDtime)>self.keepAlive and self.currentprotocol=="can"
        if ((tb - self.lastCMDtime) > self.keepAlive
            and len(self.startSession) > 0):

            # log KeepAlive event
            if self.lf != 0:
                tmstr = datetime.now().strftime("%H:%M:%S.%f")[:-3]
                self.lf.write("#[" + tmstr + "]" + "KeepAlive\n")
                self.lf.flush()

                # send keepalive
            self.send_cmd(self.startSession)
            self.lastCMDtime = time.time()  # for not to get into infinite loop

        # send command
        cmdrsp = self.send_cmd(command)
        self.lastCMDtime = tc = time.time()

        # check for shifted responce
        # if ('AT' in command.upper()) and (command.upper() not in cmdrsp.upper()) and not options.simulation_mode:
        #  #try to wait a bit moere
        #  delayedrsp = self.port.expect('>')
        #  if command.upper() in delayedrsp.upper():
        #    cmdrsp = delayedrsp

        # add srvsDelay to time gap before send next command
        self.srvsDelay = float(serviceDelay) / 1000.

        # check for negative response
        for l in cmdrsp.split('\n'):
            l = l.strip().upper()
            if l.startswith("7F") and len(l) == 8 and l[6:8] in negrsp.keys():
                print l, negrsp[l[6:8]]
                if self.lf != 0:
                    self.lf.write("#[" + str(tc - tb) + "] rsp:" + l + ":" + negrsp[l[6:8]] + "\n")
                    self.lf.flush()
        return cmdrsp

    def send_cmd(self, command):
        if "AT" in command.upper() or self.currentprotocol != "can":
            return self.send_raw(command)
        if self.ATCFC0:
            return self.send_can_cfc0(command)
        else:
            return self.send_can(command)

    def send_can(self, command):
        command = command.strip().replace(' ', '')

        if len(command) % 2 != 0 or len(command) == 0: return "ODD ERROR"
        if not all(c in string.hexdigits for c in command): return "HEX ERROR"

        # do framing
        raw_command = []
        cmd_len = len(command) / 2
        if cmd_len < 8:  # single frame
            # check L1 cache here
            if command in self.l1_cache.keys():
                raw_command.append(("%0.2X" % cmd_len) + command + self.l1_cache[command])
            else:
                raw_command.append(("%0.2X" % cmd_len) + command)
        else:
            # first frame
            raw_command.append("1" + ("%0.3X" % cmd_len)[-3:] + command[:12])
            command = command[12:]
            # consecutive frames
            frame_number = 1
            while (len(command)):
                raw_command.append("2" + ("%X" % frame_number)[-1:] + command[:14])
                frame_number = frame_number + 1
                command = command[14:]

        responses = []

        # send farmes
        for f in raw_command:
            # send next frame
            frsp = self.send_raw(f)
            # analyse response (1 phase)
            for s in frsp.split('\n'):
                if s.strip() == f:  # echo cancelation
                    continue
                s = s.strip().replace(' ', '')
                if len(s) == 0:  # empty string
                    continue
                if all(c in string.hexdigits for c in s):  # some data
                    if s[:1] == '3':  # flow control, just ignore it in this version
                        continue
                    responses.append(s)

        # analyse response (2 phases)
        result = ""
        noerrors = True
        cfarame = 0  # frame counter
        nbytes = 0  # number bytes in response
        nfarmes = 0  # numer frames in response

        if len(responses) == 0:  # no data in response
            return ""

        if len(responses) == 1:  # single frame response
            if responses[0][:1] == '0':
                nbytes = int(responses[0][1:2], 16)
                nframes = 1
                result = responses[0][2:2 + nbytes * 2]
            else:  # wrong response (not all frames received)
                self.error_frame += 1
                noerrors = False
        else:  # multi frame response
            if responses[0][:1] == '1':  # first frame
                nbytes = int(responses[0][1:4], 16)
                nframes = nbytes / 7 + 1
                cframe = 1
                result = responses[0][4:16]
            else:  # wrong response (first frame omitted)
                self.error_frame += 1
                noerrors = False

            for fr in responses[1:]:
                if fr[:1] == '2':  # consecutive frames
                    tmp_fn = int(fr[1:2], 16)
                    if tmp_fn != (cframe % 16):  # wrong response (frame lost)
                        self.error_frame += 1
                        noerrors = False
                        continue
                    cframe += 1
                    result += fr[2:16]
                else:  # wrong response
                    self.error_frame += 1
                    noerrors = False

        # Check for negative
        if result[:2] == '7F':
            noerrors = False

        # check for negative response (repeat the same as in cmd())
        if result[:2] == '7F' and result[6:8] in negrsp.keys():
            if self.vf != 0:
                tmstr = datetime.now().strftime("%H:%M:%S.%f")[:-3]
                self.vf.write(
                    tmstr + ";" + dnat[self.currentaddress] + ";" + command + ";" + result + ";" + negrsp[result[6:8]] + "\n")
                self.vf.flush()

        # populate L1 cache
        if noerrors and nframes < 16 and command[:1] == '2' and not options.opt_n1c:
            self.l1_cache[command] = str(nframes)

        if len(result) / 2 >= nbytes and noerrors:
            # split by bytes and return
            result = ' '.join(a + b for a, b in zip(result[::2], result[1::2]))
            return result
        else:
            return "WRONG RESPONSE" 

    def send_can_cfc0(self, command):

        command = command.strip().replace(' ', '')

        if len(command) % 2 != 0 or len(command) == 0: return "ODD ERROR"
        if not all(c in string.hexdigits for c in command): return "HEX ERROR"

        # do framing
        raw_command = []
        cmd_len = len(command) / 2
        if cmd_len < 8:  # single frame
            raw_command.append(("%0.2X" % cmd_len) + command)
        else:
            # first frame
            raw_command.append("1" + ("%0.3X" % cmd_len)[-3:] + command[:12])
            command = command[12:]
            # consecutive frames
            frame_number = 1
            while (len(command)):
                raw_command.append("2" + ("%X" % frame_number)[-1:] + command[:14])
                frame_number = frame_number + 1
                command = command[14:]

        responses = []

        # send frames
        BS = 1  # Burst Size
        ST = 0  # Frame Interval
        Fc = 0  # Current frame
        Fn = len(raw_command)  # Number of frames

        while Fc < Fn:

            # enable responses
            if not self.ATR1:
                frsp = self.send_raw('at r1')
                self.ATR1 = True

            tb = time.time()  # time of sending (ff)

            if len(raw_command[Fc]) == 16:
                frsp = self.send_raw(raw_command[Fc])  # we'll get only 1 frame: fc, ff or sf
            else:
                frsp = self.send_raw(raw_command[Fc] + '1')  # we'll get only 1 frame: fc, ff or sf
            Fc = Fc + 1

            # analyse response
            for s in frsp.split('\n'):

                if s.strip()[:len(raw_command[Fc - 1])] == raw_command[Fc - 1]:  # echo cancelation
                    continue

                s = s.strip().replace(' ', '')
                if len(s) == 0:  # empty string
                    continue

                if all(c in string.hexdigits for c in s):  # some data
                    if s[:1] == '3':  # FlowControl

                        # extract Burst Size
                        BS = s[2:4]
                        BS = int(BS, 16)

                        # extract Frame Interval
                        ST = s[4:6]
                        if ST[:1].upper() == 'F':
                            ST = int(ST[1:2], 16) * 100
                        else:
                            ST = int(ST, 16)
                        print 'BS:', BS, 'ST:', ST
                        break  # go to sending consequent frames
                    else:
                        responses.append(s)
                        continue

            # sending consequent farmes according to FlowControl

            cf = min(BS - 1, (Fn - Fc) - 1)  # number of frames to send without responce

            # disable responses
            if cf > 0:
                if self.ATR1:
                    frsp = self.send_raw('at r0')
                    self.ATR1 = False

            while cf > 0:
                cf = cf - 1

                # Ensure time gap between frames according to FlowControl
                tc = time.time()  # current time
                if (tc - tb) * 1000. < ST:
                    time.sleep(ST / 1000. - (tc - tb))
                tb = tc

                frsp = self.send_raw(raw_command[Fc])
                Fc += 1

        # now we are going to receive data. st or ff should be in responses[0]
        if len(responses) != 1:
            # print "Something went wrong. len responces != 1"
            return "WRONG RESPONSE"

        result = ""
        noerrors = True
        cfarame = 0  # frame counter
        nbytes = 0  # number bytes in response
        nfarmes = 0  # numer frames in response

        if responses[0][:1] == '0':  # single frame (sf)
            nbytes = int(responses[0][1:2], 16)
            nframes = 1
            result = responses[0][2:2 + nbytes * 2]

        elif responses[0][:1] == '1':  # first frame (ff)
            nbytes = int(responses[0][1:4], 16)
            nframes = nbytes / 7 + 1
            cframe = 1
            result = responses[0][4:16]

            # receiving consecutive frames
            while len(responses) < nframes:
                # now we should send ff
                sBS = hex(min(nframes - len(responses), 0xf))[2:]
                frsp = self.send_raw('300' + sBS + '00' + sBS)

                # analyse response
                for s in frsp.split('\n'):

                    if s.strip()[:len(raw_command[Fc - 1])] == raw_command[Fc - 1]:  # echo cancelation
                        continue

                    s = s.strip().replace(' ', '')
                    if len(s) == 0:  # empty string
                        continue

                    if all(c in string.hexdigits for c in s):  # some data
                        responses.append(s)
                        if s[:1] == '2':  # consecutive frames (cf)
                            tmp_fn = int(s[1:2], 16)
                            if tmp_fn != (cframe % 16):  # wrong response (frame lost)
                                self.error_frame += 1
                                noerrors = False
                                continue
                            cframe += 1
                            result += s[2:16]
                        continue

        else:  # wrong response (first frame omitted)
            self.error_frame += 1
            noerrors = False

        if len(result) / 2 >= nbytes and noerrors:
            # split by bytes and return
            result = ' '.join(a + b for a, b in zip(result[::2], result[1::2]))
            return result
        else:
            return "WRONG RESPONSE"

    def send_raw(self, command):

        tb = time.time()  # start time

        # save command to log
        if self.lf != 0:
            # tm = str(time.time())
            tmstr = datetime.now().strftime("%H:%M:%S.%f")[:-3]
            self.lf.write(">[" + tmstr + "]" + command + "\n")
            self.lf.flush()

        # send command
        if not options.simulation_mode:
            self.port.write(str(command + "\r").encode("utf-8"))  # send command

        # receive and parse responce
        while (True):
            tc = time.time()
            if options.simulation_mode:
                break
            self.buff = self.port.expect('>', self.portTimeout)
            tc = time.time()
            if (tc - tb) > self.portTimeout and "TIMEOUT" not in self.buff:
                self.buff += "TIMEOUT"
            if "TIMEOUT" in self.buff:
                self.error_timeout += 1
                break
            if command in self.buff:
                break
            elif self.lf != 0:
                tmstr = datetime.now().strftime("%H:%M:%S.%f")[:-3]
                self.lf.write("<[" + tmstr + "]" + self.buff + "<shifted>" + command + "\n")
                self.lf.flush()

        # count errors
        if "?" in self.buff:
            self.error_question += 1
        if "BUFFER FULL" in self.buff:
            self.error_bufferfull += 1
        if "NO DATA" in self.buff:
            self.error_nodata += 1
        if "RX ERROR" in self.buff:
            self.error_rx += 1
        if "CAN ERROR" in self.buff:
            self.error_can += 1

        self.response_time = ((self.response_time * 9) + (tc - tb)) / 10

        # save responce to log
        if self.lf != 0:
            # tm = str(time.time())
            self.lf.write("<[" + str(round(tc - tb, 3)) + "]" + self.buff + "\n")
            self.lf.flush()

        return self.buff

    def close_protocol(self):
        self.cmd("atpc")

    def start_session_can(self, start_session):
        self.startSession = start_session
        self.cmd(self.startSession)

    def init_can(self):

        self.currentprotocol = "can"
        self.currentaddress = "7e0"
        self.startSession = ""
        self.lastCMDtime = 0
        self.l1_cache = {}

        if self.lf != 0:
            tmstr = datetime.now().strftime("%x %H:%M:%S.%f")[:-3]
            self.lf.write('#' * 60 + "\n#[" + tmstr + "] Init CAN\n" + '#' * 60 + "\n")
            self.lf.flush()
        self.cmd("at ws")
        self.cmd("at e1")
        self.cmd("at s0")
        self.cmd("at h0")
        self.cmd("at l0")
        self.cmd("at al")
        self.cmd("at caf0")
        if self.ATCFC0:
            self.cmd("at cfc0")

        self.lastCMDtime = 0

    def get_can_addr(self, txa):
        for d in dnat.keys():
            if dnat[d] == txa:
                return d
        return None

    def set_can_addr_inv(self, addr, ecu):

        if self.currentprotocol == "can" and self.currentaddress == addr:
            return

        if self.lf != 0:
            self.lf.write('#' * 60 + "\n#connect to: " + ecu['ecuname'] + " Addr:" + addr + "\n" + '#' * 60 + "\n")
            self.lf.flush()

        self.currentprotocol = "can"
        self.currentaddress = addr
        self.startSession = ""
        self.lastCMDtime = 0
        self.l1_cache = {}

        RXa = dnat[addr]
        TXa = snat[addr]

        self.cmd("at sh " + TXa)
        self.cmd("at cra " + RXa)
        self.cmd("at fc sh " + TXa)
        self.cmd("at fc sd 30 00 00")  # status BS STmin
        self.cmd("at fc sm 1")
        if 'brp' in ecu.keys() and ecu['brp'] == "1":  # I suppose that brp=1 means 250kBps CAN
            self.cmd("at sp 8")
        else:
            self.cmd("at sp 6")
        # self.cmd("at al")
        return (TXa, RXa)

    def set_can_addr(self, addr, ecu):

        if self.currentprotocol == "can" and self.currentaddress == addr:
            return

        if self.lf != 0:
            self.lf.write('#' * 60 + "\n#connect to: " + ecu['ecuname'] + " Addr:" + addr + "\n" + '#' * 60 + "\n")
            self.lf.flush()

        self.currentprotocol = "can"
        self.currentaddress = addr
        self.startSession = ""
        self.lastCMDtime = 0
        self.l1_cache = {}

        TXa = dnat[addr]
        RXa = snat[addr]

        self.cmd("at sh " + TXa)
        self.cmd("at cra " + RXa)
        self.cmd("at fc sh " + TXa)
        self.cmd("at fc sd 30 00 00")  # status BS STmin
        self.cmd("at fc sm 1")
        if 'brp' in ecu.keys() and ecu['brp'] == "1":  # I suppose that brp=1 means 250kBps CAN
            self.cmd("at sp 8")
        else:
            self.cmd("at sp 6")
        # self.cmd("at al")
        return (TXa, RXa)

    def start_session_iso(self, start_session):
        self.startSession = start_session

        if len(self.startSession) > 0:
            self.lastinitrsp = self.cmd(self.startSession)

    def init_iso(self):
        self.currentprotocol = "iso"
        self.currentsubprotocol = ""
        self.currentaddress = ""
        self.startSession = ""
        self.lastCMDtime = 0
        self.lastinitrsp = ""

        if self.lf != 0:
            tmstr = datetime.now().strftime("%x %H:%M:%S.%f")[:-3]
            self.lf.write('#' * 60 + "\n#[" + tmstr + "] Init ISO\n" + '#' * 60 + "\n")
            self.lf.flush()
        self.cmd("at ws")
        self.cmd("at e1")
        self.cmd("at l1")
        self.cmd("at d1")

    def set_iso_addr(self, addr, ecu):

        if self.currentprotocol == "iso" and self.currentaddress == addr and self.currentsubprotocol == ecu['protocol']:
            return

        if self.lf != 0:
            self.lf.write('#' * 60 + "\n#connect to: " + ecu['ecuname'] + " Addr:" + addr + " Protocol:" + ecu[
                'protocol'] + "\n" + '#' * 60 + "\n")
            self.lf.flush()

        self.currentprotocol = "iso"
        self.currentsubprotocol = ecu['protocol']
        self.currentaddress = addr
        self.startSession = ""
        self.lastCMDtime = 0
        self.lastinitrsp = ""

        self.cmd("at sh 81 " + addr + " f1")     # set address
        self.cmd("at sw 96")                     # wakeup message period 3 seconds
        self.cmd("at wm 81 " + addr + " f1 3E")  # set wakeup message
        self.cmd("at ib10")                      # baud rate 10400
        self.cmd("at st ff")                     # set timeout to 1 second
        self.cmd("at at 0")                      # disable adaptive timing

        if 'PRNA2000' in ecu['protocol'].upper() or options.opt_si:
            self.cmd("at sp 4")  # slow init mode 4
            if len(ecu['slowInit']) > 0:
                self.cmd("at iia " + ecu['slowInit'])  # address for slow init
            rsp = self.lastinitrsp = self.cmd("at si")  # for slow init mode 4
            if 'ERROR' in rsp and len(ecu['fastInit']) > 0:
                ecu['protocol'] = ''
                if self.lf != 0:
                    self.lf.write('### Try fast init\n')
                    self.lf.flush()

                    # if 'PRNA2000' not in ecu['protocol'].upper() :
        if 'OK' not in self.lastinitrsp:
            self.cmd("at sp 5")  # fast init mode 5
            self.lastinitrsp = self.cmd("at fi")  # perform fast init mode 5
            # self.lastinitrsp = self.cmd("81")         #init bus

        self.cmd("at at 1")  # enable adaptive timing


def elm_checker(port, speed, logview, app):
    good = 0
    total = 0
    pycom = 0
    vers = ''

    elm = ELM(port, speed)
    if options.elm_failed:
        return False
    elm.portTimeout = 5

    for st in cmdb.split('#'):
        cm = st.split(';')

        if len(cm) > 1:
            if 'C' not in cm[1].upper():
                continue

            if len(cm[2].strip()):

                res = elm.send_raw(cm[2])

                if 'H' in cm[1].upper():
                    continue
                total += 1
                print cm[2] + " " + res.strip()
                if '?' in res:
                    chre = '<font color=red>[FAIL]</font>'
                    if 'P' in cm[1].upper():
                        pycom += 1
                # Timeout is not an error
                elif 'TIMEOUT' in res:
                    chre = '<font color=green>[OK/TIMEOUT]</font>'
                    good += 1
                    vers = cm[0]
                else:
                    chre = '<font color=green>[OK]</font>'
                    good += 1
                    vers = cm[0]

                logview.append("%5s %10s %s" % (cm[0], cm[2], chre))
                app.processEvents()

    if pycom > 0:
        logview.append('<font color=red>Incompatible adapter on ARM core</font> \n')
    logview.append('Result: ' + str(good) + ' succeeded from ' + str(total) + '\nELM Max version:' + vers + '\n')
    return True