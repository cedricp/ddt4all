# DoIPMessageType

Source: `src/ddt4all/core/doip/doip_message_type.py`

DoIP Message Types according to ISO 13400

## Table Of Contents

- [Method Reference And Flowcharts](#method-reference-and-flowcharts)
- [Initialization Functions](#initialization-functions)
- [Main Functions](#main-functions)
- [Auxiliary Functions](#auxiliary-functions)
- [Flow Summary](#flow-summary)

## Collaborators

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

This summary shows the usual high-level flow through `DoIPMessageType`.

```mermaid
flowchart LR
    A[Protocol name] --> B[Enum value]
    B --> C[DoIP header payload type]
```
