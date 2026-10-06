# DDT4All Source Code

This directory contains the main source code for the DDT4All application.

## Directory Structure

```
src/
├── ddt4all/           # Main application package
│   ├── __init__.py
│   ├── __main__.py    # Entry point for python -m ddt4all
│   ├── main.py        # Main application entry point
│   ├── file_manager.py # File and directory management utilities
│   ├── options.py     # Configuration and settings management
│   ├── version.py     # Application version and contributor information
│   │
│   ├── cli/           # Command-line interface
│   │   ├── cli_args_parser.py
│   │   ├── cmd_handlers/
│   │   └── helpers.py
│   │
│   ├── core/          # Core functionality modules
│   │   ├── elm/       # ELM327/adapter communication
│   │   │   ├── elm.py
│   │   │   ├── device_manager.py
│   │   │   ├── port.py
│   │   │   └── constants.py
│   │   │
│   │   ├── ecu/       # ECU database and protocols
│   │   │   ├── ecu_database.py
│   │   │   ├── ecu_scanner.py
│   │   │   ├── ecu_device.py
│   │   │   ├── ecu_file.py
│   │   │   ├── ecu_request.py
│   │   │   ├── ecu_ident.py
│   │   │   ├── data_item.py
│   │   │   └── utils.py
│   │   │
│   │   ├── doip/      # DoIP protocol support
│   │   │   ├── doip_connection.py
│   │   │   ├── doip_devices.py
│   │   │   ├── doip_message_type.py
│   │   │   └── doip_protocol_error.py
│   │   │
│   │   ├── parameters/ # Parameter handling
│   │   │   └── helpers.py
│   │   │
│   │   └── usbdevice/ # USB device support
│   │       ├── obd_device.py
│   │       ├── usb_can.py
│   │       └── constants.py
│   │
│   ├── plugins/       # Plugin system (vehicle-specific modules)
│   │   ├── ab90_reset.py
│   │   ├── card_programming.py
│   │   ├── clio3_eps_reset.py
│   │   ├── clio4_eps_reset.py
│   │   ├── cmd_macros.py
│   │   ├── cmd_macros_lib/ # DDT2000 macros engine + bundled macros
│   │   ├── laguna2_uch_reset.py
│   │   ├── laguna3_uch_reset.py
│   │   ├── megane2_uch_reset.py
│   │   ├── megane3_ab_reset.py
│   │   ├── megane3_eps_reset.py
│   │   ├── megane3_uch_reset.py
│   │   ├── rsat4_reset.py
│   │   ├── vin_crc.py
│   │   └── zoe_waterpump_counter_reset.py
│   │
│   ├── ui/            # User interface components
│   │   ├── main_window/
│   │   ├── widgets/
│   │   └── dialogs/
│   │
│   ├── generated/     # Auto-generated resources
│   │   └── resources_rc.py
│   │
│   └── resources/     # Application resources
│       ├── icons/
│       └── projects.json
```

## Key Modules

- **main.py** - Main application entry point with GUI setup and connection management
- **elm.py** - ELM327/adapter communication protocol with device-specific implementations
- **ecu.py** - ECU database management and vehicle communication
- **options.py** - Configuration management and device settings persistence
- **version.py** - Application version and contributor information

## Installation

See the main [README.md](../README.md) at the project root for installation instructions.

## Development

```bash
# Install in development mode
pip install -e .

# Run the application
python -m ddt4all