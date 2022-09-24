# DDT4All [![Python App](https://github.com/Furtif/ddt4all/actions/workflows/python-app.yml/badge.svg?branch=update)](https://github.com/Furtif/ddt4all/actions/workflows/python-app.yml) [![Donate](https://img.shields.io/badge/Donate-PayPal-green.svg)](https://www.paypal.com/cgi-bin/webscr?cmd=_donations&business=cedricpaille%40gmail%2ecom&lc=CY&item_name=codetronic&currency_code=EUR&bn=PP%2dDonationsBF%3abtn_donateCC_LG%2egif%3aNonHosted)
DDT4All is tool to create your own ECU parameters screens and connect to a CAN network with a cheap ELM327 interface.

### NEW: [Wiki Android port](https://github.com/cedricp/ddt4all/wiki/Android-port)

### Notes:
This application is work in progress, so be very careful when using expert mode.
Using the application in non expert mode should not be harmful for your vehicle (leave the expert mode button released).

**Important :**

**Do not use this software if you don't have a strong knowledge of how a CAN network (or ECU) works, you can really do bad things with it, especially if you're working on a vehicle**

**The author declines all responsibility about a bad use of this tool. You are the only responsible**

**This tool is mainly aimed for CAN ISO_TP network study**

## `Cloning Source Code`
### `Dependencies :`
<img src="https://user-images.githubusercontent.com/11718525/135937807-fd3e0fd2-a31a-47a4-90c6-b0bb1d0704d4.png"></img>
* [Python 3.10](https://www.python.org/downloads/release/python-3105/) 
* [PySide2](https://pypi.org/project/PySide2/)
* [pyusb](https://pypi.org/project/pyusb/)
* [pyserial](https://pypi.org/project/pyserial/)
* [crcmod](https://pypi.org/project/crcmod/)
* [Python virtual environment](https://gist.github.com/dreamorosi/e2947827e5de92b69df68c88475eba38)

### Supported diagnostic adapters (so far)

* **ELM327** USB/BlueTooth/WiFi (Original one with _PIC18F25K80_, Chinese clone not working)
* **ObdLink** SX
* **ELS27**

Next, you need to get the source code.  This source code repository uses git submodules. So when you clone the source code, you will need to clone recursively:

```
git clone --recursive https://github.com/cedricp/ddt4all.git
```

Or if you already cloned without the recursive option, you can update the submodules by running:

```
git clone --recursive https://github.com/cedricp/ddt4all.git
cd ddt4all
git submodule update --init --recursive
```

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
* Screen recorder (via autorefresh button) and export to CSV format

## How to launch the application ?
* A terminal, type `python main.py`


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

Bugtracking here : https://github.com/cedricp/ddt4all

Happy CAN-Hacking :)

To make this application more reliable, I need to buy hardware, cables and devices, so please consider contributing by making a donation (hardware or money). Of course you can contribute by filling bug reports and sending patches.
