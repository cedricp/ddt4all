# DoIPProtocolError, In Simple English

Source: `src/ddt4all/core/doip/doip_protocol_error.py`

`DoIPProtocolError` is one part of the core code. This version uses simple English. It keeps the same meaning as the normal document, but uses shorter sentences.

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

This is the short version of how `DoIPProtocolError` is used.

```mermaid
flowchart LR
    A[Protocol problem] --> B[Raise DoIPProtocolError]
    B --> C[Caller handles failure]
```
