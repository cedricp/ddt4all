# DDT4All [![Python App](https://github.com/cedricp/ddt4all/actions/workflows/python-app.yml/badge.svg)](https://github.com/cedricp/ddt4all/actions/workflows/python-app.yml) [![Donate](https://img.shields.io/badge/Donate-PayPal-green.svg)](https://www.paypal.com/cgi-bin/webscr?cmd=_donations&business=cedricpaille%40gmail%2ecom&lc=CY&item_name=codetronic&currency_code=EUR&bn=PP%2dDonationsBF%3abtn_donateCC_LG%2egif%3aNonHosted) [![Discord](https://img.shields.io/discord/1117970325267820675?label=Discord&style=flat-square)](https://discord.gg/cBqDh9bTHP)

DDT4All is a comprehensive tool to create your own ECU parameters screens and connect to a CAN network with various OBD-II interfaces including ELM327, Vlinker FS, VGate, ObdLink SX, and ELS27 adapters.

**Current Version**: v3.0.5 (RC1 - "Okapi-RC1") - Latest stable release with enhanced device support and performance improvements.

## 🚀 **Recent Major Improvements**

### ✅ **Enhanced Device Compatibility & Connection Stability**
- **Multi-Device Support**: Full compatibility with Vlinker FS, VGate, ELM327, ObdLink SX/EX, ELS27 adapters
- **Device-Specific Optimization**: Automatic speed selection and optimal settings for each adapter type
- **Connection Types**: USB, Bluetooth, and WiFi connections with automatic detection
- **Smart Reconnection**: Automatic reconnection with device-specific handling and retry logic
- **Cross-Platform**: Optimized for Windows, Linux, and macOS with platform-specific configurations
- **USB CAN Support**: Added support for specialized USB CAN adapters with fallback handling

### 🌍 **Complete Internationalization (13 Languages)**
- **Fully Translated Interface** in 13 languages with 390+ new translation strings
- **Supported Languages**: English, Français, Deutsch, Español, Italiano, Русский, Polski, Nederlands, Português, Magyar, Română, Српски, Türkçe, Українська
- **Real-time Language Switching** with proper encoding support
- **HTML-Aware Translations** preserving markup while translating content

### ⚡ **Performance & Reliability Improvements**
- **Fast Device Detection**: ~0.014s port scanning with intelligent filtering
- **Thread-Safe Operations**: Proper locking mechanisms for connection stability
- **Enhanced Error Handling**: Comprehensive error recovery and user-friendly messages
- **Memory Optimization**: Improved resource management and cleanup

### 🔧 **New Device & Speed Management**
- **VGate iCar Pro Support**: Full support for enhanced STN-based VGate adapters
- **Intelligent Speed Selection**: Device-specific speed options automatically loaded
- **Optimal Settings Engine**: Automatic timeout and flow control configuration per device
- **Enhanced Vlinker Support**: Improved speed options (No, 57600, 115200) for better performance


### Android porting: 
  - [Wiki Android port](https://github.com/cedricp/ddt4all/wiki/Android-port)
  - [Source Code](https://github.com/cedricp/ecutweaker)
  - [Download](https://github.com/cedricp/ddt4all/releases)

### Notes:
This application is work in progress, so be very careful when using expert mode.
Using the application in non expert mode should not be harmful for your vehicle (leave the expert mode button released).

**Important :**

**Do not use this software if you don't have a strong knowledge of how a CAN network (or ECU) works, you can really do bad things with it, especially if you're working on a vehicle**

**The author declines all responsibility about a bad use of this tool. You are the only responsible**

**This tool is mainly aimed for CAN ISO_TP network study**

## `Cloning Source Code`
### `Dependencies :`
![python_3.13.x](ddt4all_data/icons/Python-3-13-2-new.png)

#### **🔧 Core Requirements (Essential):**
* **Python 3.8.6+ (32-bit/64-bit)** - [Python 3.13](https://www.python.org/downloads/release/python-3132/) recommended
* [PyQt5](https://pypi.org/project/PyQt5/) - GUI framework
* [pyserial](https://pypi.org/project/pyserial/) - Serial communication
* [pyusb](https://pypi.org/project/pyusb/) - USB device support
* [crcmod](https://pypi.org/project/crcmod/) - Checksum functions

#### **🌐 Enhanced Features (Optional but Recommended):**
* [PyQtWebEngine](https://pypi.org/project/PyQtWebEngine/) - Provides `PyQt5.QtWebEngineWidgets` for documentation viewing
* [pywin32](https://pypi.org/project/pywin32/) - Windows serial support (Windows only)

#### **📦 Quick Installation:**
```bash
# Basic installation (minimum requirements)
pip install PyQt5 pyserial pyusb crcmod

# Enhanced installation (recommended)
pip install PyQt5 PyQtWebEngine pyserial pyusb crcmod

# Windows users (additional - recommended)
pip install pywin32

# Complete installation (all features)
pip install -r requirements.txt

# Alternative with specific versions (most stable)
pip install PyQt5==5.15.11 PyQtWebEngine==5.15.7 pyserial==3.5 pyusb==1.2.1 crcmod==1.7
```

#### **⚠️ Important Notes:**
- **PyQt5.QtWebEngineWidgets**: Provided by PyQtWebEngine package, used for enhanced documentation viewing
- **If PyQtWebEngine fails to install**: DDT4All will still work, but documentation viewing will be limited
- **Python Compatibility**: 3.8.6+ supported (32-bit and 64-bit), tested on 3.8.6, 3.10.12, and 3.13+
- **WebEngine Compatibility**: JavaScript disabled to prevent compatibility errors with older WebEngine versions
- **Virtual Environment**: [Recommended setup guide](https://gist.github.com/dreamorosi/e2947827e5de92b69df68c88475eba38)
.
### 🔌 **Supported Diagnostic Adapters**

* **Vlinker FS** - USB/Bluetooth (Recommended for best performance and stability)
* **VGate iCar Pro** - USB/Bluetooth/WiFi (Enhanced STN-based adapter with advanced features)
* **ELM327** - USB/Bluetooth/WiFi (Original with _PIC18F25K80_, some Chinese clones supported)
* **ObdLink SX** - USB (High-speed professional adapter with RTS/CTS flow control)
* **ObdLink EX** - USB (Professional adapter, tested and confirmed working)
* **ELS27** - USB (Alternative ELM327-compatible adapter)
* **ELS27 V5** - USB (Enhanced ELS27 with CAN on pins 12-13, improved compatibility)
* **USB CAN Adapters** - USB (Specialized CAN adapters with automatic fallback handling)

#### **Connection Methods:**
- **USB Serial**: Serial-over-USB connection with automatic driver detection (most adapters)
- **USB Direct**: Native USB communication for specialized CAN adapters
- **Bluetooth**: Wireless connection with pairing support
- **WiFi**: TCP/IP connection (format: `192.168.0.10:35000`)

#### **Latest Improvements:**
- **Enhanced USB Support**: Added dedicated handling for USB ELM327 adapters (`STD_USB`)
- **USB CAN Adapters**: New support for specialized USB CAN interfaces with intelligent fallback
- **Device Normalization**: Improved adapter type mapping for better device recognition
- **Connection Reliability**: Enhanced error handling and timeout management per device type

> **Note**: Most adapters (ELM327, Vlinker, VGate, ObdLink, ELS27) use serial-over-USB communication through standard COM ports. USB CAN adapters now have dedicated support with automatic fallback to ensure compatibility.

#### **📋 Supported Device Configuration:**

| Device | Speed Options | Default | Timeout | Flow Control | Best For | Notes |
|--------|---------------|---------|---------|--------------|----------|-------|
| **Vlinker FS** | No, 57600, 115200 | 38400 | 3s | None | **Enhanced** | Most stable, best compatibility |
| **VGate iCar Pro** | No, 115200, 230400, 500000, 1000000 | 115200 | 2s | None | **Enhanced** | STN-based, very high speeds |
| **ELM327 Original** | Standard speeds | 38400 | 5s | None | **General use** | Verify PIC18F25K80 chip |
| **ELM327 Clone** | Standard speeds | 9600-38400 | 5s | None | **Budget option** | Test different baud rates |
| **ELM327 USB** | Standard speeds | 38400 | 5s | None | **USB Direct** | Dedicated USB ELM327 support |
| **ObdLink SX** | No, 500000, 1000000, 2000000 | 115200 | 2s | RTS/CTS | **Professional** | Highest speeds, premium adapter |
| **ObdLink EX** | No, 500000, 1000000, 2000000 | 115200 | 2s | RTS/CTS | **Professional** | Confirmed working, professional grade |
| **ELS27** | Standard speeds | 38400 | 4s | None | **Alternative** | Good ELM327 alternative |
| **ELS27 V5** | Standard speeds | 38400 | 4s | None | **Enhanced** | CAN pins 12-13, PyRen/Renolink compatible |
| **USB CAN** | Varies | 38400 | 5s | None | **Specialized** | Intelligent fallback, auto-detection |

#### **⚙️ Connection Optimization Tips:**
- **USB**: Most stable, recommended for diagnostic work
- **Bluetooth**: Good for mobile use, may have occasional dropouts
- **WiFi**: Convenient but requires stable network (format: `192.168.0.10:35000`)
- **Speed Selection**: Each adapter now has device-specific speed options for optimal performance
- **Troubleshooting**: Use built-in connection test for automatic optimization

#### **🚀 New Speed Selection Feature:**
DDT4All now automatically provides optimal speed options based on your selected adapter:
- **Automatic Detection**: Device-specific speed ranges are automatically loaded
- **Performance Optimization**: Each adapter gets speeds suited to its capabilities
- **Easy Selection**: Simply choose your adapter type and select from available speeds

#### **⚡ Technical Speed Implementation:**
**VGate iCar Pro** (STN-based, high-speed capable):
- Available: No, 115200, 230400, 500000, 1000000 bps
- Default: 115200 bps (speedcombo index 2)

**Vlinker FS** (Moderate speeds, stable):
- Available: No, 57600, 115200 bps  
- Default: 38400 bps

**ObdLink SX/EX** (Professional, highest speeds):
- Available: No, 500000, 1000000, 2000000 bps
- Default: 115200 bps with RTS/CTS flow control

**ELM327 variants** (Standard compatibility):
- Speed fallback: 38400, 115200, 230400, 57600, 9600, 500000, 1000000, 2000000 bps
- Default: 38400 bps

#### **🔍 Device Identification Guide:**
- **Vlinker FS**: Usually labeled "Vlinker FS" or "OBDII WiFi"
- **VGate iCar Pro**: Labeled "VGate" or "iCar Pro", often with WiFi/Bluetooth indicators
- **ELM327 Original**: Look for "PIC18F25K80" chip marking
- **ELM327 Clone**: Various markings, test with 9600-38400 baud
- **ELM327 USB**: Dedicated USB connector, may show as "STD_USB" in interface
- **ObdLink SX**: Professional blue/black housing, "OBDLink SX" branding
- **ObdLink EX**: Professional housing, "OBDLink EX" branding, similar to SX
- **ELS27**: Similar to ELM327 but with "ELS27" marking
- **ELS27 V5**: Enhanced ELS27 with "V5" marking, CAN pins 12-13, better driver compatibility
- **USB CAN**: Specialized CAN adapters, various manufacturers, auto-detected as "USBCAN"

#### **⚡ Quick Setup Guide:**
1. **Connect Device**: USB/Bluetooth/WiFi as appropriate
2. **Launch DDT4All**: Application will auto-detect most devices
3. **Test Connection**: Use built-in connection test feature
4. **Optimize Settings**: Adjust baud rate if needed based on device type

#### **✅ User-Tested Devices:**
- **ObdLink EX**: Confirmed working by community user with excellent results
- **Vlinker FS**: Extensively tested, recommended for best compatibility
- **VGate iCar Pro**: Enhanced adapter with excellent speed capabilities
- **ELM327 Original**: Well-tested with PIC18F25K80 chip
- **ELS27 V5**: Enhanced compatibility, works with PyRen and Renolink drivers

> **Note**: If you have successfully tested other devices with DDT4All, please let us know so we can update this list!

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

## 🚀 **Key Features**

### **🔧 Diagnostic Functions**
- **Read/Clear DTC**: Comprehensive diagnostic trouble code management
- **Manual ECU Requests**: Direct communication with vehicle control units
- **AutoScan ECUs**: Automatic detection and file selection
- **Live Data Monitoring**: Real-time parameter viewing and logging

### **📊 Advanced Capabilities**
- **Log Recorder**: Comprehensive data logging with export functionality
- **Screen Recorder**: Automated capture via autorefresh with CSV export
- **CAN Bus Sniffing**: Read/decode non-ISOTP frames for advanced diagnostics
- **Plugin System**: Extensible Python-based plugin architecture for automated functions
- **Real-time Monitoring**: Live data visualization and parameter monitoring
- **Custom Scripts**: Support for vehicle-specific automation scripts

### **🔌 Plugin System**
DDT4All includes a comprehensive plugin system located in `ddtplugins/` with ready-to-use modules:

- **`ab90_reset.py`** - AB90 module reset functionality
- **`card_programming.py`** - ECU card programming utilities
- **`clio3_eps_reset.py`** - Clio 3 EPS (Electric Power Steering) reset
- **`clio4_eps_reset.py`** - Clio 4 EPS reset procedures
- **`laguna2_uch_reset.py`** - Laguna 2 UCH (Under Hood Control) reset
- **`laguna3_uch_reset.py`** - Laguna 3 UCH reset procedures
- **`megane2_uch_reset.py`** - Megane 2 UCH reset
- **`megane3_ab_reset.py`** - Megane 3 AB (AirBag) reset
- **`megane3_eps_reset.py`** - Megane 3 EPS reset
- **`megane3_uch_reset.py`** - Megane 3 UCH reset
- **`rsat4_reset.py`** - RSAT4 system reset
- **`vin_crc.py`** - VIN checksum calculation utilities
- **`zoe_waterpump_counter_reset.py`** - Zoe water pump counter reset

The plugin architecture allows developers to create custom automation scripts for specific vehicle procedures and ECU operations.

### **⚡ Performance & Compatibility**
- **Protocol Support**: CAN / KWP2000 bus protocols
- **High-Speed Parsing**: Internal JSON format for optimal performance
- **Database Compression**: ZIP compression for efficient storage
- **Cross-Platform**: Windows, Linux, macOS support

---

## 📦 **Installation Guide**

### **🪟 Windows Installation**
```bash
# Navigate to project directory
cd ddt4all

# Create virtual environment
python -m venv ./venv

# Activate virtual environment
.\venv\Scripts\activate.bat

# Install dependencies
.\venv\Scripts\pip install -r requirements.txt

# Launch application
.\venv\Scripts\python .\main.py
```

### **🐧 Linux/macOS Installation**
```bash
# Navigate to project directory
cd ddt4all

# Create virtual environment
python3 -m venv ./venv

# Set permissions (if needed)
chmod +x ./venv/bin/activate

# Activate virtual environment
source ./venv/bin/activate

# Install dependencies
pip install -r ./requirements.txt

# Launch application
python ./main.py
```

### **🔧 Linux Ubuntu Fix**
If you encounter Qt platform plugin "xcb" errors:
```bash
sudo apt-get install --reinstall libxcb-xinerama0
```

---

## 🚀 **Quick Launch**

### **🪟 Windows**
```bash
cd ddt4all
.\venv\Scripts\activate.bat
.\venv\Scripts\python .\main.py
```

### **🐧 Linux/macOS**
```bash
cd ddt4all
source ./venv/bin/activate
python ./main.py
```

### **💡 Pro Tip**
Create desktop shortcuts or shell aliases for faster access:
```bash
# Linux/macOS alias example
alias ddt4all='cd /path/to/ddt4all && source ./venv/bin/activate && python ./main.py'
```

## Platforms

* Gnu/Linux (**Ubuntu approved**)
* Windows (**For winXP, 2000, vista, try the [winXP](https://github.com/cedricp/ddt4all/tree/winXP) branch** (_Not updated version_))
* MacOS

## Videos

* [Changing roof minimum speed operation on Megane II Cabriolet](https://www.youtube.com/watch?v=6oiXV1Srg7E)
* [Checking AirBag firing lines](https://www.youtube.com/watch?v=zTiqUaWeuT0)
* [Clearing Airbag DTC](https://www.youtube.com/watch?v=oQ3WcKlsvrw)
* [Can bus sniffing (Russian)](https://www.youtube.com/watch?v=SjDC7fUMWmg)
* [ECU Parameters changes](https://www.youtube.com/watch?v=i9VkErEpoDE)

## 🔧 **Troubleshooting**

### **Connection Issues**

#### **No Serial Connection**
* **Linux**: Check user rights to access serial port [Ubuntu Guide](https://askubuntu.com/questions/58119/changing-permissions-on-serial-port)
  ```bash
  sudo usermod -a -G dialout $USER
  # Logout and login again
  ```
* **Windows**: 
  * Check serial drivers installation
  * Try to disable antivirus software
  * Run as administrator if needed

#### **Device Not Detected**
1. **Check Physical Connection**: Ensure device is properly connected and powered
2. **Try Different Baud Rates**: Use the connection test feature to try different speeds
3. **Driver Installation**: Ensure device drivers are properly installed
4. **Port Permissions**: Check port access permissions (Linux/macOS)

#### **ELS27 V5 Specific Issues**
If your ELS27 V5 is not detected:
1. **Verify Driver Installation**: Ensure PyRen/Renolink drivers are properly installed
2. **Check Device Manager**: Device should appear as COM port or USB Serial device
3. **Try Different USB Ports**: Some ELS27 V5 units are sensitive to USB port selection
4. **Manual Port Selection**: ELS27 V5 may appear as "FTDI", "CH340", or "CP210x" device
5. **Test All Available Ports**: Use connection test on each COM port to find your device
6. **CAN Pin Configuration**: ELS27 V5 uses CAN on pins 12-13 (configured automatically)
7. **Baud Rate Testing**: Try 38400, 9600, and 115200 baud rates if auto-detection fails

#### **WiFi Connection Issues**
* **Format**: Use `IP:PORT` format (e.g., `192.168.0.10:35000`)
* **Network**: Ensure device and computer are on the same network
* **Firewall**: Check firewall settings for port blocking

#### **Connection Test Feature**
DDT4All now includes a built-in connection test that provides:
- **Automatic device detection** and identification
- **Connection validation** with detailed error messages
- **Troubleshooting suggestions** for common issues
- **Performance metrics** and connection quality assessment

### **Installation Issues**

#### **PyQtWebEngine / QtWebEngineWidgets Problems**
If you encounter issues with PyQtWebEngine installation:

```bash
# Try installing specific version
pip install PyQtWebEngine==5.15.7

# If that fails, try without version constraint
pip install PyQtWebEngine

# Alternative: Install without WebEngine (basic functionality)
pip install PyQt5 pyserial pyusb crcmod
```

**Note**: DDT4All gracefully handles missing PyQtWebEngine:
- ✅ **Core functionality**: Works perfectly without WebEngine
- ⚠️ **Documentation viewing**: Limited to basic text display
- 🔧 **Error handling**: Shows warning but continues normally

#### **Windows-Specific Issues**
```bash
# Install Windows-specific dependencies
pip install pywin32

# If serial port access fails
# Run Command Prompt as Administrator and install:
pip install pywin32
python -m pywin32_postinstall -install
```

#### **Python 3.8.6 (32-bit) Specific Notes**
✅ **Fully Supported**: DDT4All works perfectly with Python 3.8.6 32-bit

**Installation for Python 3.8.6 (32-bit):**
```bash
# Core requirements (always work)
pip install PyQt5 pyserial pyusb crcmod

# Windows support (recommended)
pip install pywin32

# WebEngine (may not be available for 32-bit)
pip install PyQtWebEngine  # If this fails, DDT4All still works fine
```

**32-bit Considerations:**
- ✅ **Core functionality**: 100% compatible
- ⚠️ **PyQtWebEngine**: May not be available for Python 3.8 32-bit
- ✅ **Graceful fallback**: Uses basic text widget if WebEngine unavailable
- ✅ **All OBD devices**: Full compatibility with all supported adapters

### **Performance Optimization**
- **Device Selection**: Vlinker FS recommended for best performance
- **Connection Type**: USB generally more stable than Bluetooth/WiFi
- **System Resources**: Close unnecessary applications for better performance

## 🌍 **Language Support**

DDT4All supports **13 languages** with ongoing translation improvements:

| Language | Code | Status | Recent Updates | Contributors |
|----------|------|--------|----------------|--------------|
| English | en_US | ✅ Complete | Native | Core Team |
| Français | fr | 📝 Complete | Core Team | Core Team |
| Português | pt | 📝 Complete | Core Team | Core Team |
| Deutsch | de | 🔄 Enhanced | +30 new strings | Community |
| Español | es | 🔄 Enhanced | +30 new strings | Community |
| Italiano | it | 🔄 Enhanced | +30 new strings | Community |
| Русский | ru | 🔄 Enhanced | +30 new strings | Community |
| Polski | pl | 🔄 Enhanced | +30 new strings | Community |
| Nederlands | nl | 🔄 Enhanced | +30 new strings | Community |
| Magyar | hu | 🔄 Enhanced | +30 new strings | Community |
| Română | ro | 🔄 Enhanced | +30 new strings | Community |
| Српски | sr | 🔄 Enhanced | +30 new strings | Community |
| Türkçe | tr | 🔄 Enhanced | +30 new strings | Community |
| Українська | uk_UA | 🔄 Enhanced | +30 new strings | Community |

### **Recent Translation Improvements:**
- **390+ New Translation Strings** added across all languages
- **Connection & Error Messages** now fully localized
- **Device-Specific Messages** translated for better troubleshooting
- **HTML-Aware Translation** preserving formatting while translating content
- **Compiled .mo Files** ready for immediate use

### **Translation Status:**
- ✅ **Core Interface**: Fully translated in all languages
- 🔄 **Enhanced Features**: Recently improved with new connection messages
- 📝 **Ongoing**: Community contributions welcome for refinements

### **Contributing Translations:**
We welcome contributions to improve existing translations or add new languages. Translation files are located in `ddt4all_data/locale/`. Recent focus areas include device connection messages and error handling.

### **🛠️ Development Tools:**
- **Translation Tools**: Located in `ddt4all_data/tools/` for managing .po/.mo files
- **Automated Testing**: GitHub Actions workflow ensures code quality
- **Cross-Platform Building**: Support for Linux, Windows, and macOS builds
- **Build Scripts**: Automated installer generation for Windows (InnoSetup)

### **📁 Project Structure:**
```
ddt4all/
├── main.py                 # Main application entry point
├── elm.py                  # ELM327 and OBD-II adapter communication
├── ecu.py                  # ECU communication and protocols
├── options.py              # Configuration and settings management
├── parameters.py           # Parameter definitions and handling
├── dataeditor.py          # Data editing and validation
├── displaymod.py          # Display modules and widgets
├── sniffer.py             # CAN bus sniffing functionality
├── uiutils.py             # UI utilities and helpers
├── version.py             # Version information
├── requirements.txt       # Python dependencies
├── ecu.zip               # ECU DATABASE (download separately)
├── ddtplugins/           # Plugin system directory
│   ├── README.md         # Plugin documentation
│   └── *.py              # Individual plugin modules
└── ddt4all_data/         # Application data and resources
    ├── config.json       # User configuration
    ├── locale/           # Translation files (13 languages)
    ├── icons/            # Application icons
    ├── tools/            # Development and build tools
    ├── inno-win-setup/   # Windows installer configuration
    └── mac-os/           # macOS build configuration
```

## 📋 **Important Information**

### **📦 Database Requirements**
**⚠️ Critical**: The ECU database is **NOT included** in this repository due to size constraints.

**You must install the database separately:**
1. **ecu.zip method**: Download and place `ecu.zip` in the root directory
2. **Full mode**: Clone the complete repository with database files
3. **Database location**: Place database files in the same directory as `main.py`

**Without the database, DDT4All will not function properly.**

### **🐛 Report Bugs**
Report bugs you found in [issues](https://github.com/cedricp/ddt4all/issues).
To help us fix the problem quickly, please:
- **Take a screenshot** of the error you encounter
- **Attach your log file** (located in the `Logs/` folder)
- **Add [Bug]** to the title for quick identification
- **Include system information** (OS, Python version, adapter type)

### **💡 Suggestions/Ideas**
Tell us what you think we can do better in [discussions](https://github.com/cedricp/ddt4all/discussions).
Give detailed description to help us understand what you are looking for. Add [Suggestion] to the title to help us quickly identify the category of the issue. Your suggestion might not be accepted, but we value all community input! :)

### **⚖️ Legal Disclaimer**
This Website and Project is in no way affiliated with, authorized, maintained, sponsored or endorsed by ANYONE. This is an independent and unofficial project for educational use ONLY. Do not use for any other purpose than education, testing and research.

---

## **🎯 Final Notes**

**Happy CAN-Hacking!** 🚗💻

### **🤝 Support the Project**
To make this application more reliable and add support for new devices, hardware donations are needed. Please consider contributing:
- **💰 Financial donations** via [PayPal](https://www.paypal.com/cgi-bin/webscr?cmd=_donations&business=cedricpaille%40gmail%2ecom&lc=CY&item_name=codetronic&currency_code=EUR&bn=PP%2dDonationsBF%3abtn_donateCC_LG%2egif%3aNonHosted)
- **🔧 Hardware donations** (OBD-II adapters, cables, ECU devices)
- **🐛 Bug reports** and patches
- **📖 Documentation** improvements
- **🌍 Translation** contributions

### **📞 Community & Support**
- **Discord**: [Join our community](https://discord.gg/cBqDh9bTHP) for real-time support
- **GitHub Issues**: Technical problems and bug reports
- **GitHub Discussions**: Feature requests and general discussions
