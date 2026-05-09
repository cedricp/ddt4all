# DoIPDevice, In Simple English

Source: `src/ddt4all/core/doip/doip_devices.py`

`DoIPDevice` is one part of the core code. This version uses simple English. It keeps the same meaning as the normal document, but uses shorter sentences.

## Table Of Contents

- [Method Reference And Flowcharts](#method-reference-and-flowcharts)
- [Initialization Functions](#initialization-functions)
  - [`init_can(self)`](#init-can-self)
  - [`__init__(self, target_ip='192.168.0.12')`](#init-self-target-ip-192-168-0-12)
- [Main Functions](#main-functions)
  - [`start_session_can(self, start_session)`](#start-session-can-self-start-session)
  - [`set_can_addr(self, addr, ecu, canline=0)`](#set-can-addr-self-addr-ecu-canline-0)
  - [`request(self, req, positive='', cache=True, serviceDelay='0')`](#request-self-req-positive-cache-true-servicedelay-0)
  - [`disconnect(self)`](#disconnect-self)
  - [`connect(self)`](#connect-self)
- [Auxiliary Functions](#auxiliary-functions)
- [Flow Summary](#flow-summary)

## Other Code Used By This Class

- `socket` and `struct`: used for network messages and binary packet layout.
- `DoIPMessageType`: names DoIP payload types.
- `DoIPProtocolError`: reports DoIP protocol failures.

## Stored Values

| Attribute | Purpose |
| --- | --- |
| `doip` | Internal `doip` value used by the class. |
| `connectionStatus` | Connection status flag. |
| `currentaddress` | Current diagnostic address. |
| `startSession` | Last started diagnostic session. |
| `rsp_cache` | Response cache. |
| `device_type` | Detected or configured device type. |
| `settings` | Device-specific settings. |
| `timeout` | Timeout value. |
| `target_address` | DoIP target address. |

## Method Reference And Flowcharts

<a id="initialization-functions"></a>
## Initialization Functions

<a id="init-can-self"></a>
### `init_can(self)`

Initialize CAN communication over DoIP

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

<a id="init-self-target-ip-192-168-0-12"></a>
### `__init__(self, target_ip='192.168.0.12')`

Creates a `DoIPDevice` object and sets its starting state.

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

Start diagnostic session over DoIP using ISO 13400

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

Set CAN addressing for DoIP communication with Electric ECU support Special support for Electric ECUs and EVC (Electric Vehicle Controller) in newer vehicles.

```mermaid
flowchart TD
    A([Start]) --> B[Prepare value or address]
    B --> C[Send or store setting]
    C --> D[Return result if any]
    D --> E([End])
```

<a id="request-self-req-positive-cache-true-servicedelay-0"></a>
### `request(self, req, positive='', cache=True, serviceDelay='0')`

Send diagnostic request over DoIP with proper error handling

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

<a id="disconnect-self"></a>
### `disconnect(self)`

Close DoIP connection gracefully

```mermaid
flowchart TD
    A([Start]) --> B{Connection exists?}
    B -- Yes --> C[Close connection]
    B -- No --> D[Skip close]
    C --> E[Clear connection state]
    D --> E
    E --> F([End])
```

<a id="connect-self"></a>
### `connect(self)`

Open DoIP connection with vehicle identification

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

<a id="auxiliary-functions"></a>
## Auxiliary Functions

This class has no methods in this group.

## Flow Summary

This is the short version of how `DoIPDevice` is used.

```mermaid
flowchart LR
    A[Create object] --> B[Connect or initialize]
    B --> C[Send command or request]
    C --> D[Receive or parse response]
    D --> E[Return result]
    E --> F[Close or disconnect]
```
