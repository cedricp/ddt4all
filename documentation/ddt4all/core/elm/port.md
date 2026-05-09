# Port

Source: `src/ddt4all/core/elm/port.py`

Enhanced serial port and TCP connection handler
Supports USB, Bluetooth, WiFi OBD-II devices with cross-platform compatibility
- Serial ports: USB ELM327, Vlinker FS, ObdLink SX, ELS27
- TCP/WiFi: WiFi ELM327 adapters (192.168.0.10:35000 format)
- Bluetooth: Bluetooth ELM327 adapters

## Table Of Contents

- [Method Reference And Flowcharts](#method-reference-and-flowcharts)
- [Initialization Functions](#initialization-functions)
  - [`init_wifi(self, reinit=False)`](#init-wifi-self-reinit-false)
  - [`init_serial(self, speed)`](#init-serial-self-speed)
  - [`init_doip(self, ip, port)`](#init-doip-self-ip-port)
  - [`init_bluetooth(self)`](#init-bluetooth-self)
  - [`__init__(self, portName, speed, adapter_type)`](#init-self-portname-speed-adapter-type)
- [Main Functions](#main-functions)
  - [`write(self, data)`](#write-self-data)
  - [`read_byte(self)`](#read-byte-self)
  - [`read(self)`](#read-self)
  - [`expect_carriage_return(self, time_out=1)`](#expect-carriage-return-self-time-out-1)
  - [`expect(self, pattern, time_out=1)`](#expect-self-pattern-time-out-1)
  - [`close(self)`](#close-self)
  - [`change_rate(self, rate)`](#change-rate-self-rate)
- [Auxiliary Functions](#auxiliary-functions)
  - [`check_elm(self)`](#check-elm-self)
- [Flow Summary](#flow-summary)

## Collaborators

- `Port`: handles low-level serial, Bluetooth, WiFi, or DoIP transport when used by ELM.
- `options`: provides runtime flags and adapter settings.
- `DeviceManager`: applies adapter-specific settings for supported devices.

## State

| Attribute | Purpose |
| --- | --- |
| `adapter_type` | Adapter type. |
| `_lock` | Internal `_lock` value used by the class. |
| `reconnect_attempts` | Internal `reconnect_attempts` value used by the class. |
| `buff` | Internal `buff` value used by the class. |
| `tcpprt` | Internal `tcpprt` value used by the class. |
| `portType` | Internal `portType` value used by the class. |
| `portName` | Port name. |
| `hdr` | Internal `hdr` value used by the class. |
| `connectionStatus` | Connection status flag. |
| `doip_device` | Internal `doip_device` value used by the class. |
| `tcp_needs_reconnect` | Internal `tcp_needs_reconnect` value used by the class. |
| `settings` | Device-specific settings. |

## Method Reference And Flowcharts

<a id="initialization-functions"></a>
## Initialization Functions

<a id="init-wifi-self-reinit-false"></a>
### `init_wifi(self, reinit=False)`

Enhanced WiFi/TCP connection with better error handling and reconnection

```mermaid
flowchart TD
    A([Start]) --> B[Prepare connection settings]
    B --> C[Open or configure device]
    C --> D{Setup succeeded?}
    D -- Yes --> E[Store connected state and return True]
    D -- No --> F[Store failed state and return False]
    E --> G([End])
    F --> G
```

<a id="init-serial-self-speed"></a>
### `init_serial(self, speed)`

Initialize serial/USB connection with enhanced error handling

```mermaid
flowchart TD
    A([Start]) --> B[Prepare connection settings]
    B --> C[Open or configure device]
    C --> D{Setup succeeded?}
    D -- Yes --> E[Store connected state and return True]
    D -- No --> F[Store failed state and return False]
    E --> G([End])
    F --> G
```

<a id="init-doip-self-ip-port"></a>
### `init_doip(self, ip, port)`

Initialize DoIP connection

```mermaid
flowchart TD
    A([Start]) --> B[Prepare connection settings]
    B --> C[Open or configure device]
    C --> D{Setup succeeded?}
    D -- Yes --> E[Store connected state and return True]
    D -- No --> F[Store failed state and return False]
    E --> G([End])
    F --> G
```

<a id="init-bluetooth-self"></a>
### `init_bluetooth(self)`

Initialize Bluetooth connection

```mermaid
flowchart TD
    A([Start]) --> B[Prepare connection settings]
    B --> C[Open or configure device]
    C --> D{Setup succeeded?}
    D -- Yes --> E[Store connected state and return True]
    D -- No --> F[Store failed state and return False]
    E --> G([End])
    F --> G
```

<a id="init-self-portname-speed-adapter-type"></a>
### `__init__(self, portName, speed, adapter_type)`

Creates a `Port` instance and sets its starting state.

```mermaid
flowchart TD
    A([Start]) --> B[Store constructor arguments]
    B --> C[Set default state fields]
    C --> D{Needs setup work?}
    D -- Yes --> E[Run setup steps]
    D -- No --> F([End])
    E --> F
```

<a id="main-functions"></a>
## Main Functions

<a id="write-self-data"></a>
### `write(self, data)`

Enhanced write method with automatic reconnection and better error handling

```mermaid
flowchart TD
    A([Start]) --> B[Prepare command or bytes]
    B --> C{Connection is ready?}
    C -- No --> D[Return error or raise exception]
    C -- Yes --> E[Send data]
    E --> F[Read or return response]
    F --> G([End])
    D --> G
```

<a id="read-byte-self"></a>
### `read_byte(self)`

Enhanced read_byte with better error handling and reconnection

```mermaid
flowchart TD
    A([Start]) --> B{Connection has data?}
    B -- No --> C[Wait, timeout, or return empty data]
    B -- Yes --> D[Read data]
    D --> E[Clean or parse data]
    E --> F[Return data]
    C --> F
```

<a id="read-self"></a>
### `read(self)`

Enhanced read method with better error handling

```mermaid
flowchart TD
    A([Start]) --> B{Connection has data?}
    B -- No --> C[Wait, timeout, or return empty data]
    B -- Yes --> D[Read data]
    D --> E[Clean or parse data]
    E --> F[Return data]
    C --> F
```

<a id="expect-carriage-return-self-time-out-1"></a>
### `expect_carriage_return(self, time_out=1)`

Runs the `expect_carriage_return` operation for `Port`.

```mermaid
flowchart TD
    A([Start]) --> B[Run method logic]
    B --> C{Operation succeeds?}
    C -- Yes --> D[Return normal result]
    C -- No --> E[Return fallback or raise error]
    D --> F([End])
    E --> F
```

<a id="expect-self-pattern-time-out-1"></a>
### `expect(self, pattern, time_out=1)`

Runs the `expect` operation for `Port`.

```mermaid
flowchart TD
    A([Start]) --> B[Run method logic]
    B --> C{Operation succeeds?}
    C -- Yes --> D[Return normal result]
    C -- No --> E[Return fallback or raise error]
    D --> F([End])
    E --> F
```

<a id="close-self"></a>
### `close(self)`

Enhanced close method with proper cleanup

```mermaid
flowchart TD
    A([Start]) --> B{Connection exists?}
    B -- Yes --> C[Close connection]
    B -- No --> D[Skip close]
    C --> E[Clear connection state]
    D --> E
    E --> F([End])
```

<a id="change-rate-self-rate"></a>
### `change_rate(self, rate)`

Runs the `change_rate` operation for `Port`.

```mermaid
flowchart TD
    A([Start]) --> B[Prepare adapter-specific commands]
    B --> C[Run commands in order]
    C --> D{All commands worked?}
    D -- Yes --> E[Return True]
    D -- No --> F[Print warning and return False]
    E --> G([End])
    F --> G
```

<a id="auxiliary-functions"></a>
## Auxiliary Functions

<a id="check-elm-self"></a>
### `check_elm(self)`

Checks device or protocol state and returns the result.

```mermaid
flowchart TD
    A([Start]) --> B[Read current state]
    B --> C[Evaluate condition]
    C --> D[Return result]
    D --> E([End])
```

## Flow Summary

This summary shows the usual high-level flow through `Port`.

```mermaid
flowchart LR
    A[Create object] --> B[Run method]
    B --> C[Update state or return value]
```
