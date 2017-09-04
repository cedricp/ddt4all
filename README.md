# DDT4all

DDT4all is a DDT2000 clone able to parse DDT2000's database, create/modifiy your own ECU parameters screens and connect to your vehicle with an ELM327 cable.

This application is work in progress, so be very carful when using expert mode. If you're brave enough to use it and it's working (or not), please tell me so I can update the tested ECUs database.
Using the application in non expert mode should not be harmful for your vehicle (leave the expert mode button released).

## Dependencies :
* Python 2.7
* PyQt 4.8
* An ELM327 or OBDLink SX (usb preferable WiFi not tested yet)
* The DDT2000 database (you must own it) - Copy the 'ecus' directory from your DDT2000 db (from C:\DDT2000data) to the ddt4all root directory

### Install dependencies on Ubuntu :

* `sudo apt-get install python-qt4`

## Windows installer

Get the fully packaged installer here : [Release area](https://github.com/cedricp/ddt4all/releases)

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

## How to install database ?

Copy the 'ecus' directory from your DDT2000 database to the root of the sources tree and launch ddt4all.py, you are now ready to use it

## How to launch the application ?

* Windows : double click DDT4ALL.BAT file
* Linux : from a terminal, type `python ddt4all.py`

## How to compress XML files ?

### From a terminal :

* `python parameters.py --zipconvert`
* remove/move 'ecus' directory

### From the application :

* Go to menu 'File' > 'Zip database'
* remove 'ecus' directory

## Notes

* You can edit an original DDT2000 XML file after having saved it in JSON format.
* You can create your own ECU screens.

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

[Windows archive with embedded Python/PyQt here](https://drive.google.com/open?id=0B2LgdbfJUsUZWGVJWFJlTVdHVHc)

Bugtracking here : https://github.com/cedricp/ddt4all

Happy CAN-Hacking :)

To make this application more reliable, I need to buy hardware, cables and devices, so please consider contributing by making a donation (hardware or money). Of course you can contribute by filling bug reports and sending patches.
[![Donate](https://img.shields.io/badge/Donate-PayPal-green.svg)](https://www.paypal.com/cgi-bin/webscr?cmd=_donations&business=cedricpaille%40gmail%2ecom&lc=CY&item_name=codetronic&currency_code=EUR&bn=PP%2dDonationsBF%3abtn_donateCC_LG%2egif%3aNonHosted)
