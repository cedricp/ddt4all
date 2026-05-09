# DoIPProtocolError

Source: `src/ddt4all/core/doip/doip_protocol_error.py`

DoIP Protocol specific errors

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

This summary shows the usual high-level flow through `DoIPProtocolError`.

```mermaid
flowchart LR
    A[Protocol problem] --> B[Raise DoIPProtocolError]
    B --> C[Caller handles failure]
```
