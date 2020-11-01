# NEW : Android port
[Wiki](https://github.com/cedricp/ddt4all/wiki/Android-port)

# DDT4All

DDT4All is tool to create your own ECU parameters screens and connect to a CAN network with a cheap ELM327 interface.

This application is work in progress, so be very careful when using expert mode.
Using the application in non expert mode should not be harmful for your vehicle (leave the expert mode button released).

**Important :**

**Do not use this software if you don't have a strong knowledge of how a CAN network (or ECU) works, you can really do bad things with it, especially if you're working on a vehicle**

**The author declines all responsibility about a bad use of this tool. You are the only responsible**

**This tool is mainly aimed for CAN ISO_TP network study**

## Dependencies :
* Python 3.8
* PyQt 5
* An ELM327, ELS327 or OBDLink SX 

## Windows installer

Get the fully packaged installer here : [Release area](https://github.com/cedricp/ddt4all/releases)

## Supported diagnostic adapters (so far)

* **ELM327** USB/BlueTooth/WiFi (Original one with _PIC18F25K80_, Chinese clone not working)
* **ObdLink** SX
* **ELS27**

## Features :

* Read/Clear DTC
* Manual ECU request
* Log recorder
* Plugins system for automated functions
* CAN / KWP2000 supported bus protocols
* AutoScan ECUs and select the related files
* Internal JSON file format for high speed parsing
* Database zip compression of converted JSON files
* Can bus sniffing (Read/Decode non-ISOTP frames)
* Screen recorder (via autorefresh button) and export to CSV format

## How to launch the application ?

* Windows : double click DDT4ALL.BAT file
* Linux : from a terminal, type `python ddt4all.py`


## Platforms

* Gnu/Linux (**Ubuntu approved**)
* Windows (**For winXP, 2000, vista, try the 'winXP' branch**)
* MacOS

## Videos

* [Changing roof minimum speed operation on Megane II Cabriolet](https://www.youtube.com/watch?v=6oiXV1Srg7E)
* [Checking AirBag firing lines](https://www.youtube.com/watch?v=zTiqUaWeuT0)
* [Clearing Airbag DTC](https://www.youtube.com/watch?v=oQ3WcKlsvrw)
* [Can bus sniffing (Russian)](https://www.youtube.com/watch?v=SjDC7fUMWmg)
* [ECU Parameters changes](https://www.youtube.com/watch?v=i9VkErEpoDE)

## Troubleshootings

### No serial connection

* Linux : Check user rights to access serial port [Ubuntu](https://askubuntu.com/questions/58119/changing-permissions-on-serial-port)
* Windows :
  * Check serial drivers installation
  * Try to disable antivirus software

## Informations

[Windows archive with embedded Python/PyQt here](https://github.com/cedricp/ddt4all/releases)

Bugtracking here : https://github.com/cedricp/ddt4all

Happy CAN-Hacking :)

To make this application more reliable, I need to buy hardware, cables and devices, so please consider contributing by making a donation (hardware or money). Of course you can contribute by filling bug reports and sending patches.
[![Donate](https://img.shields.io/badge/Donate-PayPal-green.svg)](https://www.paypal.com/cgi-bin/webscr?cmd=_donations&business=cedricpaille%40gmail%2ecom&lc=CY&item_name=codetronic&currency_code=EUR&bn=PP%2dDonationsBF%3abtn_donateCC_LG%2egif%3aNonHosted)
