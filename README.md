# DDT4all

DDT4all is a DDT2000 clone able to parse DDT2000's database and connect to your vehicle to read/write ECU parameters with an ELM327 cable.

This application is work in progress, so be very carful when using expert mode. If you're brave enough to use it and it's working (or not), please tell me so I can update the tested ECUs database.
Using the application in non expert mode should not be harmful for your vehicle (leave the expert mode button released).

Dependencies:
* Python 2.6 or 2.7
* PyQt 4.6 to 4.8
* An ELM327 (usb preferable WiFi not tested yet)
* The DDT2000 database (you must own it) - Copy the 'ecus' directory from your DDT2000 db (from C:\DDT2000data) to the ddt4all root directory

Copy the  <ecus> directory from your DDT2000 database to the root of the sources tree and launch ddt4all.py

Bugtracking here : https://github.com/cedricp/ddt4all

Happy CAN-Hacking :)

To make this application more reliable, I need to buy hardware, cables and devices, so please consider contributing by making a donation (hardware or money). Of course you can contribute by filling bug reports and sending patches.
[![Donate](https://img.shields.io/badge/Donate-PayPal-green.svg)](https://www.paypal.com/cgi-bin/webscr?cmd=_donations&business=cedricpaille%40gmail%2ecom&lc=CY&item_name=codetronic&currency_code=EUR&bn=PP%2dDonationsBF%3abtn_donateCC_LG%2egif%3aNonHosted)
