# OBDDevice

Source: `src/ddt4all/core/usbdevice/obd_device.py`

`OBDDevice` is part of the ddt4all core layer.

## Table Of Contents

- [Method Reference And Flowcharts](#method-reference-and-flowcharts)
- [Initialization Functions](#initialization-functions)
  - [`init_can(self)`](#init-can-self)
  - [`__init__(self)`](#init-self)
- [Main Functions](#main-functions)
  - [`start_session_can(self, start_session)`](#start-session-can-self-start-session)
  - [`set_can_addr(self, addr, ecu, canline=0)`](#set-can-addr-self-addr-ecu-canline-0)
  - [`request(self, req, positive='', cache=True, serviceDelay='0')`](#request-self-req-positive-cache-true-servicedelay-0)
  - [`close_protocol(self)`](#close-protocol-self)
  - [`clear_cache(self)`](#clear-cache-self)
- [Auxiliary Functions](#auxiliary-functions)
- [Flow Summary](#flow-summary)

## Collaborators

- `usb.core`, `usb.util`, and `usb.legacy`: access USB devices.
- `options`: provides translated messages and device settings.
- `elm` address helpers: convert ECU addresses for CAN setup.

## State

| Attribute | Purpose |
| --- | --- |
| `device` | Underlying device handle. |
| `connectionStatus` | Connection status flag. |
| `currentaddress` | Current diagnostic address. |
| `startSession` | Last started diagnostic session. |
| `rsp_cache` | Response cache. |
| `device_type` | Detected or configured device type. |
| `settings` | Device-specific settings. |

## Method Reference And Flowcharts

<a id="initialization-functions"></a>
## Initialization Functions

<a id="init-can-self"></a>
### `init_can(self)`

Runs the `init_can` operation for `OBDDevice`.

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

<a id="init-self"></a>
### `__init__(self)`

Creates a `OBDDevice` instance and sets its starting state.

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

<a id="start-session-can-self-start-session"></a>
### `start_session_can(self, start_session)`

Runs the `start_session_can` operation for `OBDDevice`.

```mermaid
flowchart TD
    A([Start]) --> B[Run method logic]
    B --> C{Operation succeeds?}
    C -- Yes --> D[Return normal result]
    C -- No --> E[Return fallback or raise error]
    D --> F([End])
    E --> F
```

<a id="set-can-addr-self-addr-ecu-canline-0"></a>
### `set_can_addr(self, addr, ecu, canline=0)`

Sets set can addr data on the object or connected device.

```mermaid
flowchart TD
    A([Start]) --> B[Prepare value or address]
    B --> C[Send or store setting]
    C --> D[Return result if any]
    D --> E([End])
```

<a id="request-self-req-positive-cache-true-servicedelay-0"></a>
### `request(self, req, positive='', cache=True, serviceDelay='0')`

Sends a request and returns the response.

```mermaid
flowchart TD
    A([Start]) --> B[Prepare request bytes]
    B --> C{Connection is ready?}
    C -- No --> D[Return error or raise exception]
    C -- Yes --> E[Send request]
    E --> F[Receive response]
    F --> G[Return response]
    D --> H([End])
    G --> H
```

<a id="close-protocol-self"></a>
### `close_protocol(self)`

Closes the active connection or protocol.

```mermaid
flowchart TD
    A([Start]) --> B{Connection exists?}
    B -- Yes --> C[Close connection]
    B -- No --> D[Skip close]
    C --> E[Clear connection state]
    D --> E
    E --> F([End])
```

<a id="clear-cache-self"></a>
### `clear_cache(self)`

Clear L2 cache before screen update

```mermaid
flowchart TD
    A([Start]) --> B[Run method logic]
    B --> C{Operation succeeds?}
    C -- Yes --> D[Return normal result]
    C -- No --> E[Return fallback or raise error]
    D --> F([End])
    E --> F
```

<a id="auxiliary-functions"></a>
## Auxiliary Functions

This class has no methods in this group.

## Flow Summary

This summary shows the usual high-level flow through `OBDDevice`.

```mermaid
flowchart LR
    A[Create object] --> B[Run method]
    B --> C[Update state or return value]
```
