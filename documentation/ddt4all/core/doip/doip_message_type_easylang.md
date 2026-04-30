# DoIPMessageType, In Simple English

Source: `src/ddt4all/core/doip/doip_message_type.py`

`DoIPMessageType` is one part of the core code. This version uses simple English. It keeps the same meaning as the normal document, but uses shorter sentences.

## Table Of Contents

- [Method Reference And Flowcharts](#method-reference-and-flowcharts)
- [Initialization Functions](#initialization-functions)
- [Main Functions](#main-functions)
- [Auxiliary Functions](#auxiliary-functions)
- [Flow Summary](#flow-summary)

## Other Code Used By This Class

- `socket` and `struct`: used for network messages and binary packet layout.
- `DoIPMessageType`: names DoIP payload types.
- `DoIPProtocolError`: reports DoIP protocol failures.

## Enum Values

| Name | Value |
| --- | --- |
| `VEHICLE_IDENTIFICATION_REQUEST` | `1` |
| `VEHICLE_IDENTIFICATION_RESPONSE` | `2` |
| `VEHICLE_ANNOUNCEMENT` | `3` |
| `DIAGNOSTIC_SESSION_CONTROL` | `16385` |
| `DIAGNOSTIC_MESSAGE` | `16386` |
| `ALIVE_CHECK_REQUEST` | `16387` |
| `ALIVE_CHECK_RESPONSE` | `16388` |
| `ENTITY_STATUS_REQUEST` | `16389` |
| `ENTITY_STATUS_RESPONSE` | `16390` |

## Method Reference And Flowcharts

<a id="initialization-functions"></a>
## Initialization Functions

This class has no methods in this group.

<a id="main-functions"></a>
## Main Functions

This class has no methods in this group.

<a id="auxiliary-functions"></a>
## Auxiliary Functions

This class has no methods in this group.

## Flow Summary

This is the short version of how `DoIPMessageType` is used.

```mermaid
flowchart LR
    A[Protocol name] --> B[Enum value]
    B --> C[DoIP header payload type]
```
