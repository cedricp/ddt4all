# EcuData, In Simple English

Source: `src/ddt4all/core/ecu/ecu_data.py`

[EcuData](ecu_data_easylang.md) explains how one ECU value is stored in bytes. It can turn raw bytes into a value for the user, and it can put a user value back into request bytes.

## Table Of Contents

- [Simple Overview](#simple-overview)
- [Other Code Used By This Class](#other-code-used-by-this-class)
- [Stored Values](#stored-values)
- [Important Details For Beginners](#important-details-for-beginners)
- [Method Guide And Flowcharts](#method-guide-and-flowcharts)
  - [Initialization Functions](#initialization-functions)
    - [`__init__(self, data, name='')`](#init-self-data-name)
    - [`init(self, data)`](#init-self-data)
  - [Main Functions](#main-functions)
    - [`setValue(self, value, bytes_list, dataitem, ecu_endian, test_mode=False)`](#setvalue-self-value-bytes-list-dataitem-ecu-endian-test-mode-false)
    - [`getIntValue(self, resp, dataitem, ecu_endian)`](#getintvalue-self-resp-dataitem-ecu-endian)
    - [`getHexValue(self, resp, dataitem, ecu_endian)`](#gethexvalue-self-resp-dataitem-ecu-endian)
    - [`getDisplayValue(self, elm_data, dataitem, ecu_endian)`](#getdisplayvalue-self-elm-data-dataitem-ecu-endian)
  - [Auxiliary Functions](#auxiliary-functions)
    - [`dump(self)`](#dump-self)
- [Simple Flow Summary](#simple-flow-summary)

## Simple Overview

[EcuData](ecu_data_easylang.md) says how to understand bytes. [DataItem](data_item_easylang.md) says where the bytes are. Both are needed.

To read a value, the code first cuts the right bits out of the ECU answer, then converts them into something readable.

To write a value, the code converts user input into raw bits and places those bits into the request bytes.

## Other Code Used By This Class

- [DataItem](data_item_easylang.md): tells where the value is inside the bytes.
- [EcuRequest](ecu_request_easylang.md): uses this class to build requests and read answers.
- [utils.hex8_tosigned](utils.md#hex8-tosigned) and [utils.hex16_tosigned](utils.md#hex16-tosigned): help with signed numbers.
- [utils.cleanhtml](utils.md#cleanhtml): cleans comments before export.

## Stored Values

| Attribute | Purpose |
| --- | --- |
| [bitscount](ecu_data_easylang.md#stored-values) | Number of bits in the value. |
| [scaled](ecu_data_easylang.md#stored-values) | Whether the value uses a formula. |
| [signed](ecu_data_easylang.md#stored-values) | Whether the number can be negative. |
| [byte](ecu_data_easylang.md#stored-values) | Whether it is byte-based. |
| [binary](ecu_data_easylang.md#stored-values) | Whether it is marked as binary. |
| [bytescount](ecu_data_easylang.md#stored-values) | Number of bytes in the value. |
| [bytesascii](ecu_data_easylang.md#stored-values) | Whether bytes are text. |
| [step](ecu_data_easylang.md#stored-values) | Formula multiplier. |
| [offset](ecu_data_easylang.md#stored-values) | Formula offset. |
| [divideby](ecu_data_easylang.md#stored-values) | Formula divisor. |
| [format](ecu_data_easylang.md#stored-values) | Optional number format. |
| [lists](ecu_data_easylang.md#stored-values) | Map from number to text label. |
| [items](ecu_data_easylang.md#stored-values) | Map from text label to number. |
| [description](ecu_data_easylang.md#stored-values) | Description text. |
| [unit](ecu_data_easylang.md#stored-values) | Unit text. |
| [comment](ecu_data_easylang.md#stored-values) | Comment text. |
| [name](#stored-values) | Value name. |

## Important Details For Beginners

- Display scaling uses this formula: `(raw * step + offset) / divideby`.
- When writing ASCII text, text is made exactly as long as [bytescount](ecu_data_easylang.md#stored-values).
- Signed conversion is safest for one-byte and two-byte values.
- Little-endian handling is custom and more complex than just reversing bytes.

## Method Guide And Flowcharts

<a id="initialization-functions"></a>
## Initialization Functions

<a id="init-self-data-name"></a>
### `__init__(self, data, name='')`

Creates a value definition with simple default settings. If data is given, it calls [init](ecu_data_easylang.md#init-self-data) to load the real settings.

```mermaid
flowchart TD
    A([Start]) --> B[Set default size, scaling, signedness, byte, binary, and ASCII settings]
    B --> C[Set default formula, format, lists, text fields, and name]
    C --> D{data is provided?}
    D -- Yes --> E[Call init with data]
    D -- No --> F([End])
    E --> F
```

<a id="init-self-data"></a>
### `init(self, data)`

Loads the real settings from a dictionary or XML. These settings tell the code how many bits to read and how to convert the raw value.

```mermaid
flowchart TD
    A([Start]) --> B{data is a dictionary?}
    B -- Yes --> C[Copy known dictionary fields]
    C --> D{lists exist?}
    D -- Yes --> E[Build lists and reverse items maps]
    D -- No --> F([End])
    E --> F
    B -- No --> G[Store XML node and read Name]
    G --> H[Read Description, Comment, and List items]
    H --> I{Bytes element exists?}
    I -- Yes --> J[Set byte mode, byte count, bit count, and ASCII flag]
    I -- No --> K[Keep byte defaults]
    J --> L{Bits element exists?}
    K --> L
    L -- Yes --> M[Set bit count, byte count, signed flag, binary flag, and scaled settings]
    L -- No --> F
    M --> F
```

<a id="main-functions"></a>
## Main Functions

<a id="setvalue-self-value-bytes-list-dataitem-ecu-endian-test-mode-false"></a>
### `setValue(self, value, bytes_list, dataitem, ecu_endian, test_mode=False)`

Writes a user value into request bytes. It first converts the value into raw bits, then puts those bits into the correct byte and bit position.

```mermaid
flowchart TD
    A([Start]) --> B[Calculate zero-based start byte and start bit]
    B --> C[Resolve endian from ECU setting and DataItem override]
    C --> D{Value is ASCII bytes?}
    D -- Yes --> E[Pad or truncate text and convert characters to hex]
    D -- No --> F[Keep numeric or hex input]
    E --> G{Value is scaled?}
    F --> G
    G -- Yes --> H{test_mode?}
    H -- No --> I[Convert decimal input with reverse scaling formula]
    H -- Yes --> J[Read value as hexadecimal test data]
    G -- No --> K[Validate list or string hex input unless test_mode]
    I --> L[Convert raw integer to padded binary]
    J --> L
    K --> L
    L --> M[Extract affected request bytes as binary]
    M --> N{Little endian?}
    N -- Yes --> O[Insert bits using three-step little-endian logic]
    N -- No --> P[Insert bits in normal order from start bit]
    O --> Q[Convert modified binary back to hex bytes]
    P --> Q
    Q --> R[Write modified bytes back into bytes_list]
    R --> S[Return bytes_list]
```

<a id="getintvalue-self-resp-dataitem-ecu-endian"></a>
### `getIntValue(self, resp, dataitem, ecu_endian)`

Gets the raw hex value with [getHexValue](ecu_data_easylang.md#gethexvalue-self-resp-dataitem-ecu-endian) and converts it into an integer.

```mermaid
flowchart TD
    A([Start]) --> B[Call getHexValue]
    B --> C{Hex value is None?}
    C -- Yes --> D[Return None]
    C -- No --> E[Convert hexadecimal text to integer]
    E --> F[Return integer]
```

<a id="gethexvalue-self-resp-dataitem-ecu-endian"></a>
### `getHexValue(self, resp, dataitem, ecu_endian)`

Cuts the correct bits out of a raw ECU answer and returns them as hex text. If the answer is too short, it returns `None`.

```mermaid
flowchart TD
    A([Start]) --> B[Resolve endian from ECU setting and DataItem override]
    B --> C[Remove spaces from response]
    C --> D{All characters are hexadecimal?}
    D -- No --> E[Use empty response]
    D -- Yes --> F[Split response into byte strings]
    E --> F
    F --> G[Calculate start byte, start bit, bit count, and required byte count]
    G --> H{Response contains enough bytes?}
    H -- No --> I[Return None]
    H -- Yes --> J[Build binary string from required bytes]
    J --> K{Little endian?}
    K -- Yes --> L[Extract bits using little-endian rules]
    K -- No --> M[Extract normal bit range]
    L --> N[Convert bits to padded hex text]
    M --> N
    N --> O[Return hex value]
```

<a id="getdisplayvalue-self-elm-data-dataitem-ecu-endian"></a>
### `getDisplayValue(self, elm_data, dataitem, ecu_endian)`

Reads a value from an ECU answer and turns it into text for the user. It can decode ASCII, show a list label, handle signed numbers, or apply a formula.

```mermaid
flowchart TD
    A([Start]) --> B[Call getHexValue]
    B --> C{Hex value is None?}
    C -- Yes --> D[Return None]
    C -- No --> E{ASCII mode?}
    E -- Yes --> F[Decode UTF-8 text and return it]
    E -- No --> G{Scaled mode?}
    G -- No --> H[Convert raw hex to integer]
    H --> I[Apply signed conversion if configured]
    I --> J{Integer has a list label?}
    J -- Yes --> K[Return mapped label]
    J -- No --> L[Return original hex value]
    G -- Yes --> M[Convert raw hex to integer and apply signed conversion if needed]
    M --> N{divideby is zero?}
    N -- Yes --> O[Print warning and return None]
    N -- No --> P[Apply display scaling formula]
    P --> Q[Apply configured decimal format if present]
    Q --> R[Return display string]
```

<a id="auxiliary-functions"></a>
## Auxiliary Functions

<a id="dump-self"></a>
### `dump(self)`

Exports the data definition as a name and a dictionary. Default values are mostly left out to keep JSON smaller.

```mermaid
flowchart TD
    A([Start]) --> B[Create empty dictionary]
    B --> C[Add size, type, and conversion fields when not default]
    C --> D[Add list mappings if present]
    D --> E[Add unit and cleaned comment if present]
    E --> F[Return name and dictionary]
```

## Simple Flow Summary

[EcuData](ecu_data_easylang.md) turns ECU bytes into readable values and turns user values back into request bytes.

```mermaid
flowchart LR
    A[ECU response bytes] --> B[getHexValue]
    B --> C[getDisplayValue]
    C --> D[User-readable value]
    E[User input] --> F[setValue]
    F --> G[Request bytes sent to ECU]
```
