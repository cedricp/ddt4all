# DataItem

Source: `src/ddt4all/core/ecu/data_item.py`

[DataItem](data_item.md) describes where one named value is located inside a request or response byte stream. It does not know how to convert the value itself; it only stores the byte position, bit offset, optional endian override, and reference flag that other classes need when reading or writing data.

## Table Of Contents

- [Overview](#overview)
- [Collaborators](#collaborators)
- [State](#state)
- [Implementation Notes](#implementation-notes)
- [Method Reference And Flowcharts](#method-reference-and-flowcharts)
  - [Initialization Functions](#initialization-functions)
    - [`__init__(self, item, req_endian, name='')`](#init-self-item-req-endian-name)
  - [Main Functions](#main-functions)
  - [Auxiliary Functions](#auxiliary-functions)
    - [`dump(self)`](#dump-self)
- [Flow Summary](#flow-summary)

## Overview

[DataItem](data_item.md) is the positional half of ECU data handling. [EcuData](ecu_data.md) knows how many bits a value uses and how the raw bytes should be converted, while [DataItem](data_item.md) tells [EcuData](ecu_data.md) where those bits start in a concrete request or response.

The class supports two input formats. Dictionary input is used when loading JSON-style ECU data. XML node input is used when loading legacy XML ECU files. Both branches fill the same attributes, so the rest of the code can treat the result the same way.

Byte positions are stored as one-based values. [EcuData](ecu_data.md) converts [firstbyte](data_item.md#state) to a zero-based index when slicing Python lists or strings.

## Collaborators

- [EcuRequest](ecu_request.md): creates [DataItem](data_item.md) objects for send-byte input fields and receive-byte output fields.
- [EcuData](ecu_data.md): uses [firstbyte](data_item.md#state), [bitoffset](data_item.md#state), and [endian](data_item.md#state) when extracting values from ECU responses or inserting values into request bytes.
- XML ECU files: provide [Name](xml_ecu_files.md#name), [FirstByte](xml_ecu_files.md#firstbyte), [BitOffset](xml_ecu_files.md#bitoffset), [Endian](xml_ecu_files.md#endian), and [Ref](xml_ecu_files.md#ref) attributes.
- JSON ECU files: provide lowercase dictionary keys such as [firstbyte](data_item.md#state), [bitoffset](data_item.md#state), [ref](data_item.md#state), and [endian](data_item.md#state).

## State

| Attribute | Purpose |
| --- | --- |
| [firstbyte](data_item.md#state) | One-based byte position where the value starts. A value of `0` means no explicit start byte was stored. |
| [bitoffset](data_item.md#state) | Bit offset inside the first byte. A value of `0` means the value starts at the first bit used by the encoding logic. |
| [ref](data_item.md#state) | Whether the XML data item was marked as a reference with [Ref="1"](xml_ecu_files.md#ref). |
| [endian](data_item.md#state) | Optional endian override for this data item. [EcuData](ecu_data.md) lets this override the ECU/request endian setting. |
| [req_endian](data_item.md#state) | Endianness inherited from the request or ECU file. The current [DataItem](data_item.md) methods store it but do not use it directly. |
| [name](#state) | Data item name. For dictionary input, the name is passed separately; for XML input, it comes from the [Name](xml_ecu_files.md#name) attribute. |

## Implementation Notes

- Dictionary input and XML input use different field names: JSON uses lowercase keys, while XML uses capitalized attributes.
- [firstbyte](data_item.md#state) from XML is converted to `int`; dictionary input is copied as provided.
- [bitoffset](data_item.md#state) from XML is converted to `int`; dictionary input is copied as provided.
- [ref](data_item.md#state) defaults to `False`. XML sets it to `True` only when [Ref](xml_ecu_files.md#ref) exists and equals `1`.
- `dump` intentionally omits default values for [firstbyte](data_item.md#state), [bitoffset](data_item.md#state), and [endian](data_item.md#state), but it writes [ref](data_item.md#state) when [ref](data_item.md#state) is `False`. This mirrors the current code exactly, even though it may look surprising at first glance.
- [req_endian](data_item.md#state) is not included in `dump`, because it belongs to the surrounding request or ECU file context rather than to the serialized data item itself.

## Method Reference And Flowcharts

<a id="initialization-functions"></a>
## Initialization Functions

<a id="init-self-item-req-endian-name"></a>
### `__init__(self, item, req_endian, name='')`

Initializes a positional data item from either a dictionary or an XML node. It first sets defaults, stores the inherited request endianness, and then fills position and metadata fields from the selected input format. Dictionary input uses the separately supplied [name](#state); XML input reads the name from the node.

```mermaid
flowchart TD
    A([Start]) --> B[Set default firstbyte, bitoffset, ref, and endian values]
    B --> C[Store req_endian]
    C --> D{item is a dictionary?}
    D -- Yes --> E[Set name from constructor argument]
    E --> F{Dictionary has firstbyte?}
    F -- Yes --> G[Copy firstbyte]
    F -- No --> H[Keep default firstbyte]
    G --> I{Dictionary has bitoffset?}
    H --> I
    I -- Yes --> J[Copy bitoffset]
    I -- No --> K[Keep default bitoffset]
    J --> L{Dictionary has ref?}
    K --> L
    L -- Yes --> M[Copy ref]
    L -- No --> N[Keep default ref]
    M --> O{Dictionary has endian?}
    N --> O
    O -- Yes --> P[Copy endian]
    O -- No --> Q[Keep default endian]
    P --> Z([End])
    Q --> Z
    D -- No --> R[Read Name attribute from XML]
    R --> S{FirstByte attribute exists?}
    S -- Yes --> T[Convert FirstByte to int]
    S -- No --> U[Keep default firstbyte]
    T --> V{BitOffset attribute exists?}
    U --> V
    V -- Yes --> W[Convert BitOffset to int]
    V -- No --> X[Keep default bitoffset]
    W --> Y[Read optional Endian and Ref attributes]
    X --> Y
    Y --> Z
```

<a id="main-functions"></a>
## Main Functions

This class has no methods in this group.

<a id="auxiliary-functions"></a>
## Auxiliary Functions

<a id="dump-self"></a>
### `dump(self)`

Serializes the stored data item position to a compact dictionary. The method writes only non-default position and endian fields, except for [ref](data_item.md#state), which is written when it is `False` according to the current implementation. The inherited [req_endian](data_item.md#state) and the data item [name](#state) are not included in the output.

```mermaid
flowchart TD
    A([Start]) --> B[Create empty dictionary]
    B --> C{firstbyte is not 0?}
    C -- Yes --> D[Add firstbyte]
    C -- No --> E[Skip firstbyte]
    D --> F{bitoffset is not 0?}
    E --> F
    F -- Yes --> G[Add bitoffset]
    F -- No --> H[Skip bitoffset]
    G --> I{ref is False?}
    H --> I
    I -- Yes --> J[Add ref]
    I -- No --> K[Skip ref]
    J --> L{endian is set?}
    K --> L
    L -- Yes --> M[Add endian]
    L -- No --> N[Skip endian]
    M --> O[Return dictionary]
    N --> O
    O --> P([End])
```

## Flow Summary

[DataItem](data_item.md) turns a JSON or XML field-position definition into the small set of coordinates that [EcuData](ecu_data.md) needs for byte and bit operations.

```mermaid
flowchart LR
    A[JSON dictionary or XML DataItem node] --> B[DataItem]
    B --> C[firstbyte and bitoffset]
    B --> D[optional endian override]
    C --> E[EcuData extracts or inserts bits]
    D --> E
```
