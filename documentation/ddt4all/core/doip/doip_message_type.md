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

- `enum`: provides the `Enum` base class used by `DoIPMessageType`.

## Enum Values

| Name | Value |
| --- | --- |
| `VEHICLE_IDENTIFICATION_REQUEST` | `0x0001` |
| `VEHICLE_IDENTIFICATION_RESPONSE` | `0x0002` |
| `VEHICLE_ANNOUNCEMENT` | `0x0003` |
| `DIAGNOSTIC_SESSION_CONTROL` | `0x4001` |
| `DIAGNOSTIC_MESSAGE` | `0x4002` |
| `ALIVE_CHECK_REQUEST` | `0x4003` |
| `ALIVE_CHECK_RESPONSE` | `0x4004` |
| `ENTITY_STATUS_REQUEST` | `0x4005` |
| `ENTITY_STATUS_RESPONSE` | `0x4006` |

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
