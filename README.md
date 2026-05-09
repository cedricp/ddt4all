# DDT4All 
[![DDT4ALL APP](https://github.com/cedricp/ddt4all/actions/workflows/python-app.yml/badge.svg)](https://github.com/cedricp/ddt4all/actions/workflows/python-app.yml)
[![Donate](https://img.shields.io/badge/Donate-PayPal-green.svg)](https://www.paypal.com/cgi-bin/webscr?cmd=_donations&business=cedricpaille%40gmail%2ecom&lc=CY&item_name=codetronic&currency_code=EUR&bn=PP%2dDonationsBF%3abtn_donateCC_LG%2egif%3aNonHosted) 
[![Discord](https://img.shields.io/discord/1117970325267820675?label=Discord&style=flat-square)](https://discord.gg/cBqDh9bTHP)
[![Python Package](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-GPL%203.0-green.svg)](https://opensource.org/licenses/GPL-3.0)

DDT4All is a comprehensive tool to create your own ECU parameters screens and connect to a CAN network with various OBD-II interfaces including ELM327, Vlinker FS, VGate, ObdLink SX, and ELS27 adapters.

**Current Version**: v3.0.8 (Tuatara) - Production-ready with enhanced device support, STN/STPX protocols, and comprehensive translation system.

## 🚀 **Recent Major Improvements**

### ✅ **Enhanced Device Compatibility & Connection Stability**
- **Multi-Device Support**: Full compatibility with Vlinker FS, VGate, ELM327, ObdLink SX/EX, ELS27 adapters
- **Device-Specific Optimization**: Automatic speed selection and optimal settings for each adapter type
- **Connection Types**: USB, Bluetooth, and WiFi connections with automatic detection
- **Smart Reconnection**: Automatic reconnection with device-specific handling and retry logic
- **Cross-Platform**: Optimized for Windows, Linux, and macOS with platform-specific configurations
- **USB CAN Support**: Added support for specialized USB CAN adapters with fallback handling

### 🌟 **Enhanced Device Manager with STN/STPX Support (v3.0.8)**
- **Intelligent Device Detection**: Automatic adapter identification via `ATI` command
- **Enhanced DeviceManager**: Centralized configuration with STN/STPX support
- **VGate STN Protocol**: Full STN implementation with automatic pin swapping
- **STPX Mode**: Enhanced long command support with comprehensive error handling
- **OBDLink Enhanced Features**: CAN Address Filtering (CAF) and STN optimizations
- **DerleK USB 3 Support**: Complete pin swapping and configuration management
- **ELS27 Integration**: Specific CAN pin configuration (12-13) support
- **Auto-Configuration**: Device-specific settings automatically applied
- **Fallback Support**: Graceful degradation for unsupported devices
- **Performance Optimization**: Enhanced communication speeds up to 1,000,000 bps
- **Fully Translated Interface** in 13 languages with comprehensive translation coverage
- **Supported Languages**: English, Français (fr), Czech(cs_CZ), Deutsch (de), Español (es), Italiano (it), Русский (ru), Polski (pl), Nederlands (nl), Português (pt), Magyar (hu), Română (ro), Српски (sr), Türkçe (tr), Українська (uk_UA)
- **Real-time Language Switching** with proper encoding support
- **HTML-Aware Translations** preserving markup while translating content

### ⚡ **Performance & Reliability Improvements**
- **Enhanced Device Detection**: Optimized port scanning with intelligent device identification
- **Thread-Safe Operations**: QThread-based operations with proper synchronization for connection stability
- **Enhanced Error Handling**: Comprehensive error recovery and user-friendly messages
- **Memory Optimization**: Improved resource management and cleanup

### 🔧 **New Device & Speed Management**
- **VGate iCar Pro Support**: Full support for VGate adapters with high-speed communication
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

![python_3.13.x](setup_tools/Python-3-13-2-new.png)

#### **Modern Python Packaging (Recommended)**
DDT4All now uses modern Python packaging with `pyproject.toml` for streamlined installation:

```bash
# Clone the repository
git clone https://github.com/cedricp/ddt4all.git
cd ddt4all

# Install in development mode (recommended for developers)
pip install -e .

# Install with optional dependencies
pip install -e ".[dev]"          # Development tools
pip install -e ".[can]"          # CAN bus support
pip install -e ".[network]"      # Network protocols
pip install -e ".[bluetooth]"   # Bluetooth support (Linux/Windows)

# Install all optional dependencies
pip install -e ".[dev,can,network,bluetooth]"
```

#### **Core Requirements (Essential):**
* **Python 3.8+** - [Python 3.10+](https://www.python.org/downloads/) recommended
* [PyQt5](https://pypi.org/project/PyQt5/) - GUI framework (>=5.15.0,<5.16.0)
* [pyserial](https://pypi.org/project/pyserial/) - Serial communication (==3.5)
* [pyusb](https://pypi.org/project/pyusb/) - USB device support (==1.2.1)
* [crcmod](https://pypi.org/project/crcmod/) - Checksum functions (==1.7)

#### **Enhanced Features (Optional but Recommended):**
* [PyQtWebEngine](https://pypi.org/project/PyQtWebEngine/) - Enhanced documentation viewing
* [pywin32](https://pypi.org/project/pywin32/) - Windows serial support (Windows only, >=227)
* [python-can](https://pypi.org/project/python-can/) - Advanced CAN bus support (>=4.0.0)
* [obd](https://pypi.org/project/obd/) - OBD-II protocol support (>=0.7.1)

#### **Development Tools:**
* [PyQt5-stubs](https://pypi.org/project/PyQt5-stubs/) - Type hints for PyQt5
* [pytest](https://pypi.org/project/pytest/) - Testing framework
* [pytest-cov](https://pypi.org/project/pytest-cov/) - Coverage reporting
* [pytest-qt](https://pypi.org/project/pytest-qt/) - PyQt testing utilities

#### **Legacy Installation (Alternative):**
```bash
# Manual dependency installation
pip install "PyQt5>=5.15.0,<5.16.0" "PyQtWebEngine>=5.15.0,<5.16.0" pyserial==3.5 pyusb==1.2.1 crcmod==1.7

# Windows-specific dependencies
pip install pywin32>=227
```

#### **Important Notes:**
- **Modern Packaging**: Uses `pyproject.toml` for dependency management and build configuration
- **Python Compatibility**: 3.8+ supported (32-bit and 64-bit), tested on 3.8.6, 3.10.12, 3.13.x
- **WebEngine Compatibility**: Optional PyQtWebEngine support with graceful fallback
- **Virtual Environment**: [Recommended setup guide](https://gist.github.com/dreamorosi/e2947827e5de92b69df68c88475eba38)
- **Development Mode**: Use `pip install -e .` for development to enable editable installs
### 🔌 **Supported Diagnostic Adapters**

* **Vlinker FS** - USB/Bluetooth (Recommended for best performance and stability)
* **VGate iCar Pro** - USB/Bluetooth/WiFi (High-speed adapter with communication up to 1,000,000 bps)
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
| **VGate iCar Pro** | No, 115200, 230400, 500000, 1000000 | 115200 | 2s | None | **Enhanced** | High-speed adapter, very high speeds |
| **ELM327 Original** | Standard speeds | 38400 | 5s | None | **General use** | Verify PIC18F25K80 chip |
| **ELM327 Clone** | Standard speeds | 9600-38400 | 5s | None | **Budget option** | Test different baud rates |
| **ELM327 USB** | Standard speeds | 38400 | 5s | None | **USB Direct** | Dedicated USB ELM327 support |
| **ObdLink SX** | No, 500000, 1000000, 2000000 | 115200 | 2s | RTS/CTS | **Professional** | Highest speeds, premium adapter |
| **ObdLink EX** | No, 500000, 1000000, 2000000 | 115200 | 2s | RTS/CTS | **Professional** | Confirmed working, professional grade |
| **ELS27** | Standard speeds | 38400 | 4s | None | **Alternative** | Good ELM327 alternative |
| **ELS27 V5** | Standard speeds | 38400 | 4s | None | **Enhanced** | CAN pins 12-13, PyRen/Renolink compatible |
| **DERLEK USB-DIAG2** | Standard speeds | 38400 | 4s | None | **Professional** | Auto pin swapping, STN/STPX support |
| **DERLEK USB-DIAG3** | Standard speeds | 38400 | 4s | None | **Professional** | Auto pin swapping, STN/STPX support |
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

Next, you need to get the source code.

```sh
git clone https://github.com/cedricp/ddt4all.git
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
- **Database Format**: Supports both XML and compressed ZIP formats for optimal storage
- **Database Compression**: ZIP compression with automatic ecu.zip handling for efficient storage
- **Cross-Platform**: Windows, Linux, macOS support with platform-specific optimizations

---

## 🏗️ **Application Architecture**

### **Core Modules**
- **`main.py`** - Main application entry point with GUI setup and connection management
- **`elm.py`** - ELM327/adapter communication protocol with device-specific implementations
- **`ecu.py`** - ECU database management and vehicle communication
- **`parameters.py`** - Parameter parsing, JSON/XML conversion, and ZIP database handling
- **`options.py`** - Configuration management and device settings persistence
- **`sniffer.py`** - CAN bus monitoring with QThread-based real-time data capture
- **`usbdevice.py`** - USB device handling and specialized CAN adapter support
- **`dataeditor.py`** - ECU data editing and modification interface
- **`displaymod.py`** - GUI display modules and graphical elements
- **`uiutils.py`** - UI utilities and helper functions
- **`version.py`** - Application version and contributor information

### **Threading Implementation**
- **QThread-based Architecture**: Uses Qt's threading system for non-blocking operations  
- **snifferThread**: Real-time CAN bus monitoring without UI freezing (`sniffer.py`)
- **Connection Management**: Thread-safe serial communication with `threading.Lock()` in ELM class
- **Device Detection**: Enhanced port scanning with intelligent device identification
- **Timer-based Operations**: QTimer for periodic updates and connection monitoring

### **Database Format Support**
- **XML Format**: Original ECU database format for development and compatibility
- **ZIP Compression**: Automatic `ecu.zip` detection and extraction for distribution
- **JSON Conversion**: Internal conversion between XML and JSON for performance
- **Graphics Support**: ZIP-embedded graphics extraction for ECU interface elements

## 📦 **Installation Guide**

### **Modern Installation (Recommended)**
```bash
# Clone the repository
git clone https://github.com/cedricp/ddt4all.git
cd ddt4all

# Create virtual environment
python -m venv ./venv

# Activate virtual environment
# Windows:
.\venv\Scripts\activate.bat
# Linux/macOS:
source ./venv/bin/activate

# Install DDT4All with dependencies
pip install -e .

# Launch application
ddt4all
```

### **Development Installation**
```bash
# Install with development tools (testing, linting, etc.)
pip install -e ".[dev]"

# Linux: Fix Qt platform plugin issues (if needed)
sudo apt-get install --reinstall libxcb-xinerama0

# Launch application in development mode
python -m ddt4all
```

---

## 🚀 **Quick Launch**

### **🪟 Windows**
```bash
# After installation with pip install -e .
ddt4all
```

### **🐧 Linux/macOS**
```bash
# After installation with pip install -e .
ddt4all
```

### **💡 Pro Tip**
Create desktop shortcuts or shell aliases for faster access:

#### **Shell Aliases**
```bash
# Linux/macOS - Modern installation
alias ddt4all='ddt4all'

# Linux/macOS - Development mode
alias ddt4all-dev='cd /path/to/ddt4all && source ./venv/bin/activate && python -m ddt4all'

# Windows (PowerShell)
Set-Alias -Name ddt4all -Value "ddt4all"
```

#### **Desktop Shortcuts**
- **Windows**: Right-click desktop > New > Shortcut > Target: `ddt4all`
- **Linux**: Create `.desktop` file in `~/.local/share/applications/`
- **macOS**: Drag application from Applications folder to Dock

#### **Batch Scripts**
```bash
# Windows batch file (ddt4all.bat)
@echo off
cd /d "C:\path\to\ddt4all"
call .\venv\Scripts\activate.bat
ddt4all

# Linux/macOS shell script (ddt4all.sh)
#!/bin/bash
cd /path/to/ddt4all
source ./venv/bin/activate
ddt4all
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
| Français | fr | ✅ Complete | Core Team | Core Team |
| Português | pt | ✅ Complete | Core Team | Core Team |
| Czech | cs_CZ | 🔄 Enhanced | +30 new strings | Community |
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
We welcome contributions to improve existing translations or add new languages. Translation files are located in `locales/`. Recent focus areas include device connection messages and error handling.

### **🛠️ Development Tools:**
- **Automated Testing**: GitHub Actions workflow ensures code quality
- **Cross-Platform Building**: Support for Linux, Windows, and macOS builds
- **Build Scripts**: Automated installer generation for Windows (InnoSetup)

### **📁 Modern Project Structure:**
```python
ddt4all/
|--------------------------------------------------------------------------
| pyproject.toml         # Modern Python packaging configuration
| README.md              # Project documentation
| license.txt            # GPL-3.0 license
| src/                   # Source code directory
|   |-- ddt4all/         # Main package
|       |-- main.py      # Main application entry point
|       |-- version.py   # Version and contributor information
|       |-- options.py   # Configuration and settings management
|       |-- file_manager.py # File and directory management utilities
|       |-- cli/         # Command-line interface
|       |   |-- cli_args_parser.py
|       |   |-- cmd_handlers/
|       |   |-- helpers.py
|       |-- core/        # Core functionality modules
|       |   |-- elm/     # ELM327/adapter communication
|       |   |   |-- elm.py
|       |   |   |-- device_manager.py
|       |   |   |-- port.py
|       |   |   |-- constants.py
|       |   |-- ecu/     # ECU database and protocols
|       |   |   |-- ecu_database.py
|       |   |   |-- ecu_scanner.py
|       |   |   |-- ecu_device.py
|       |   |   |-- ecu_file.py
|       |   |   |-- ecu_request.py
|       |   |   |-- ecu_ident.py
|       |   |   |-- data_item.py
|       |   |   |-- utils.py
|       |   |-- doip/    # DoIP protocol support
|       |   |   |-- doip_connection.py
|       |   |   |-- doip_devices.py
|       |   |   |-- doip_message_type.py
|       |   |   |-- doip_protocol_error.py
|       |   |-- parameters/ # Parameter handling
|       |   |   |-- helpers.py
|       |   |-- usbdevice/ # USB device support
|       |       |-- obd_device.py
|       |       |-- usb_can.py
|       |       |-- constants.py
|       |-- plugins/     # Plugin system (13 vehicle-specific modules)
|       |   |-- ab90_reset.py
|       |   |-- card_programming.py
|       |   |-- clio3_eps_reset.py
|       |   |-- clio4_eps_reset.py
|       |   |-- laguna2_uch_reset.py
|       |   |-- laguna3_uch_reset.py
|       |   |-- megane2_uch_reset.py
|       |   |-- megane3_ab_reset.py
|       |   |-- megane3_eps_reset.py
|       |   |-- megane3_uch_reset.py
|       |   |-- rsat4_reset.py
|       |   |-- vin_crc.py
|       |   |-- zoe_waterpump_counter_reset.py
|       |-- ui/          # User interface components
|       |   |-- main_window/
|       |   |-- widgets/
|       |   |-- dialogs/
|       |-- generated/   # Auto-generated resources
|       |   |-- resources_rc.py
|       |-- resources/  # Application resources
|       |   |-- icons/
|       |   |-- projects.json
| tests/                 # Test suite
|   |-- unit/           # Unit tests
|   |-- integration/    # Integration tests
|   |-- smoke/          # Smoke tests
|   |-- resources/      # Test resources
| setup_tools/          # Build and packaging tools
|   |-- inno-win-setup/ # Windows installer (InnoSetup)
|   |   |-- wininstaller.iss
|   |   |-- version.h
|   |   |-- win32_deps/
|   |-- mac-os/         # macOS build scripts
|   |   |-- builddmg.sh
|   |   |-- main.spec
|   |   |-- entitlements.plist
|   |-- README.md       # Build tools documentation
| locales/              # Translation files (15 languages)
| resources.qrc         # Qt resource configuration
| config.json           # Default configuration
| logs/                 # Application logs directory
| vehicles/             # Vehicle-specific data
| json/                 # JSON database directory
```

## 📋 **Important Information**

<!-- ### **📦 Database Requirements**
**⚠️ Critical**: The ECU database is **NOT included** in this repository due to size constraints.

**You must install the database separately:**
1. **ecu.zip method**: Download and place `ecu.zip` in the root directory
2. **Full mode**: Clone the complete repository with database files
3. **Database location**: Place database files in the same directory as `main.py`

**Without the database, DDT4All will not function properly.** -->

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

## 🔧 **Technical Implementation**

### **Enhanced DeviceManager Architecture**
The DDT4All Enhanced DeviceManager provides intelligent adapter management with automatic feature detection:

```python
# Automatic device initialization
from elm import DeviceManager
DeviceManager.initialize_device(elm_instance)
```

#### **Device Detection Process**
1. **ATI Command Analysis**: Extracts device identification from ELM responses
2. **Adapter Type Normalization**: Maps UI types to internal device types
3. **Capability Assessment**: Determines STN/STPX and pin swapping support
4. **Automatic Configuration**: Applies optimal settings without user intervention

#### **Supported Device Classes**
- **STN-based Adapters**: VGate, OBDLink (enhanced protocol support)
- **Standard ELM327**: Basic functionality with fallback support
- **Specialized Adapters**: ELS27, DerleK USB 3 (custom configurations)
- **Unknown Devices**: Graceful degradation with standard settings

#### **STN/STPX Implementation**
- **Protocol Detection**: Automatic STN capability identification
- **Enhanced Commands**: Large message mode, flow control, extended addressing
- **Error Handling**: Comprehensive verification with fallback mechanisms
- **Performance Optimization**: High-speed communication up to 2,000,000 bps

#### **Pin Swapping Logic**
- **Device-Specific Commands**: Tailored pin swapping for each adapter type
- **Verification Testing**: Automatic validation of pin swap success
- **Fallback Handling**: Graceful degradation if pin swapping fails

### **Integration Points**
- **Ecu_scanner**: Uses DeviceManager for CAN and KWP scanning
- **Connection Management**: Automatic device initialization during connection
- **Error Recovery**: Robust handling of device-specific issues

This enhanced architecture ensures optimal performance across all supported adapters while maintaining backward compatibility and providing a seamless user experience.
