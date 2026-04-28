# DoIPConnection

Source: `src/ddt4all/core/doip/doip_connection.py`

DoIP Connection Handler for Ethernet-based diagnostic interfaces

Supports ISO 13400 DoIP protocol for modern automotive diagnostic tools with
Ethernet/WiFi connectivity. Compatible with Bosch MTS, VXDIAG, VAG ODIS, JLR DoIP VCI.

Designed for newer vehicles (2016+) with extended 29-bit CAN identifiers and
modern ECU architectures requiring high-speed Ethernet diagnostics.

## Table Of Contents

- [Method Reference And Flowcharts](#method-reference-and-flowcharts)
- [Initialization Functions](#initialization-functions)
  - [`__init__(self, target_ip='192.168.0.12', target_port=13400)`](#init-self-target-ip-192-168-0-12-target-port-13400)
- [Main Functions](#main-functions)
  - [`vehicle_identification_request(self)`](#vehicle-identification-request-self)
  - [`send_message(self, message_type, payload=b'')`](#send-message-self-message-type-payload-b)
  - [`send_diagnostic_message(self, req_bytes)`](#send-diagnostic-message-self-req-bytes)
  - [`receive_message(self)`](#receive-message-self)
  - [`disconnect(self)`](#disconnect-self)
  - [`diagnostic_session_control(self, session_type)`](#diagnostic-session-control-self-session-type)
  - [`connect(self)`](#connect-self)
- [Auxiliary Functions](#auxiliary-functions)
  - [`alive_check(self)`](#alive-check-self)
- [Flow Summary](#flow-summary)

## Collaborators

- `socket` and `struct`: used for network messages and binary packet layout.
- `DoIPMessageType`: names DoIP payload types.
- `DoIPProtocolError`: reports DoIP protocol failures.

## State

| Attribute | Purpose |
| --- | --- |
| `target_ip` | Target IP address. |
| `target_port` | Target TCP port. |
| `socket` | Network socket. |
| `connection_status` | Whether the connection is active. |
| `source_address` | DoIP source address. |
| `target_address` | DoIP target address. |
| `timeout` | Timeout value. |
| `extended_29bit` | Whether extended 29-bit addressing is enabled. |

## Method Reference And Flowcharts

<a id="initialization-functions"></a>
## Initialization Functions

<a id="init-self-target-ip-192-168-0-12-target-port-13400"></a>
### `__init__(self, target_ip='192.168.0.12', target_port=13400)`

Creates a `DoIPConnection` instance and sets its starting state.

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

<a id="vehicle-identification-request-self"></a>
### `vehicle_identification_request(self)`

Send vehicle identification request according to ISO 13400

```mermaid
flowchart TD
    A([Start]) --> B[Send protocol message]
    B --> C[Receive response]
    C --> D{Response type is expected?}
    D -- Yes --> E[Parse and return result]
    D -- No --> F[Raise or report protocol error]
    E --> G([End])
    F --> G
```

<a id="send-message-self-message-type-payload-b"></a>
### `send_message(self, message_type, payload=b'')`

Send DoIP message

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

<a id="send-diagnostic-message-self-req-bytes"></a>
### `send_diagnostic_message(self, req_bytes)`

Send diagnostic message with addressing according to ISO 13400

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

<a id="receive-message-self"></a>
### `receive_message(self)`

Receive DoIP message

```mermaid
flowchart TD
    A([Start]) --> B{Connection has data?}
    B -- No --> C[Wait, timeout, or return empty data]
    B -- Yes --> D[Read data]
    D --> E[Clean or parse data]
    E --> F[Return data]
    C --> F
```

<a id="disconnect-self"></a>
### `disconnect(self)`

Close DoIP connection

```mermaid
flowchart TD
    A([Start]) --> B{Connection exists?}
    B -- Yes --> C[Close connection]
    B -- No --> D[Skip close]
    C --> E[Clear connection state]
    D --> E
    E --> F([End])
```

<a id="diagnostic-session-control-self-session-type"></a>
### `diagnostic_session_control(self, session_type)`

Control diagnostic session according to ISO 13400

```mermaid
flowchart TD
    A([Start]) --> B[Send protocol message]
    B --> C[Receive response]
    C --> D{Response type is expected?}
    D -- Yes --> E[Parse and return result]
    D -- No --> F[Raise or report protocol error]
    E --> G([End])
    F --> G
```

<a id="connect-self"></a>
### `connect(self)`

Establish DoIP connection

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

<a id="alive-check-self"></a>
### `alive_check(self)`

Perform alive check according to ISO 13400

```mermaid
flowchart TD
    A([Start]) --> B[Send protocol message]
    B --> C[Receive response]
    C --> D{Response type is expected?}
    D -- Yes --> E[Parse and return result]
    D -- No --> F[Raise or report protocol error]
    E --> G([End])
    F --> G
```

## Flow Summary

This summary shows the usual high-level flow through `DoIPConnection`.

```mermaid
flowchart LR
    A[Create object] --> B[Connect or initialize]
    B --> C[Send command or request]
    C --> D[Receive or parse response]
    D --> E[Return result]
    E --> F[Close or disconnect]
```
