# EcuRequest

Source: `src/ddt4all/core/ecu/ecu_request.py`

[EcuRequest](ecu_request.md) represents one diagnostic request from an ECU file. It knows the bytes to send, which fields can be inserted into those bytes, which values can be decoded from the answer, and which diagnostic session modes are denied.

## Table Of Contents

- [Overview](#overview)
- [Collaborators](#collaborators)
- [State](#state)
- [Implementation Notes](#implementation-notes)
- [Method Reference And Flowcharts](#method-reference-and-flowcharts)
  - [Initialization Functions](#initialization-functions)
    - [`__init__(self, data, ecu_file)`](#init-self-data-ecu-file)
  - [Main Functions](#main-functions)
    - [`send_request(self, inputvalues=None, test_data=None)`](#send-request-self-inputvalues-none-test-data-none)
    - [`get_values_from_stream(self, stream)`](#get-values-from-stream-self-stream)
    - [`build_data_stream(self, data)`](#build-data-stream-self-data)
  - [Auxiliary Functions](#auxiliary-functions)
    - [`get_formatted_sentbytes(self)`](#get-formatted-sentbytes-self)
    - [`get_data_inputs(self)`](#get-data-inputs-self)
    - [`dump_sentdataitems(self)`](#dump-sentdataitems-self)
    - [`dump_dataitems(self)`](#dump-dataitems-self)
    - [`dump(self)`](#dump-self)
- [Flow Summary](#flow-summary)

## Overview

The class is the bridge between static ECU file definitions and live communication. [build_data_stream](ecu_request.md#build-data-stream-self-data) prepares bytes, [send_request](ecu_request.md#send-request-self-inputvalues-none-test-data-none) sends them or uses simulation data, and [get_values_from_stream](ecu_request.md#get-values-from-stream-self-stream) decodes the returned bytes.

Send-side [DataItem](data_item.md) objects define where input values are placed in [sentbytes](ecu_request.md#state). Receive-side [DataItem](data_item.md) objects define where returned values are read from the response stream. Both sides use [EcuData](ecu_data.md) definitions stored on the parent [EcuFile](ecu_file.md).

The [sds](ecu_request.md#state) dictionary records Start Diagnostic Session restrictions. A value of `False` means that access mode is denied for this request.

## Collaborators

- [EcuFile](ecu_file.md): owns the request and provides shared data definitions and endianness.
- [DataItem](data_item.md): stores byte and bit positions for input and output fields.
- [EcuData](ecu_data.md): converts values into request bytes and converts response bytes into display values.
- [options.elm](../options.md#elm): sends the request when the application is not in simulation mode.

## State

| Attribute | Purpose |
| --- | --- |
| [minbytes](ecu_request.md#state) | Minimum expected response size from the ECU definition. |
| [shiftbytescount](ecu_request.md#state) | Configured byte shift for response handling. |
| [replybytes](ecu_request.md#state) | Default or expected response bytes, also used in simulation mode without explicit test data. |
| [manualsend](ecu_request.md#state) | Whether the XML request contains [ManuelSend](xml_ecu_files.md#manuelsend). |
| [sentbytes](ecu_request.md#state) | Base request byte string before input values are inserted. |
| [dataitems](ecu_request.md#state) | Receive-side [DataItem](data_item.md) objects by value name. |
| [sendbyte_dataitems](ecu_request.md#state) | Send-side [DataItem](data_item.md) objects by value name. |
| [name](#state) | Request name. |
| [ecu_file](ecu_request.md#state) | Parent ECU file that supplies data definitions and endianness. |
| [sds](ecu_request.md#state) | Allowed or denied diagnostic session modes. |

## Implementation Notes

- [build_data_stream](ecu_request.md#build-data-stream-self-data) raises `KeyError` when an input name has no send-side [DataItem](data_item.md) or no matching [EcuData](ecu_data.md) definition.
- [send_request](ecu_request.md#send-request-self-inputvalues-none-test-data-none) treats responses starting with [WRONG RESPONSE](diagnostic_responses.md#wrong-response) or [7F](diagnostic_responses.md#negative-response) as failures and returns `None`.
- Simulation mode uses `test_data` when provided; otherwise it returns and decodes [replybytes](ecu_request.md#state).
- [get_formatted_sentbytes](ecu_request.md#get-formatted-sentbytes-self) assumes [sentbytes](ecu_request.md#state) is continuous hexadecimal text without spaces.

## Method Reference And Flowcharts

<a id="initialization-functions"></a>
## Initialization Functions

<a id="init-self-data-ecu-file"></a>
### `__init__(self, data, ecu_file)`

Initializes the request from dictionary data, a blank request name, or an XML node. It sets defaults, stores the parent ECU file, loads denied diagnostic session modes, and creates send-side and receive-side [DataItem](data_item.md) objects.

```mermaid
flowchart TD
    A([Start]) --> B[Set default fields and SDS permissions]
    B --> C[Store parent ECU file]
    C --> D{data is dictionary?}
    D -- Yes --> E[Copy dictionary fields and denied SDS modes]
    E --> F[Create send and receive DataItems]
    D -- No --> G{data is string?}
    G -- Yes --> H[Use string as blank request name]
    G -- No --> I[Read XML request node]
    I --> J[Read access restrictions, manual send, shift, reply, received, and sent data]
    J --> K[Create send and receive DataItems]
    F --> L([End])
    H --> L
    K --> L
```

<a id="main-functions"></a>
## Main Functions

<a id="send-request-self-inputvalues-none-test-data-none"></a>
### `send_request(self, inputvalues=None, test_data=None)`

Builds the outgoing stream, sends it through simulation data or [options.elm](../options.md#elm), handles protocol-level negative responses, decodes returned values, and returns the decoded dictionary.

```mermaid
flowchart TD
    A([Start]) --> B[Use empty input dictionary if inputvalues is None]
    B --> C[Build request byte stream]
    C --> D[Join bytes with spaces]
    D --> E{debug enabled?}
    E -- Yes --> F[Print generated stream]
    E -- No --> G{simulation mode?}
    F --> G
    G -- Yes --> H{test_data provided?}
    H -- Yes --> I[Use test_data as response]
    H -- No --> J[Use replybytes as response]
    G -- No --> K[Send request through options.elm]
    I --> L{Response is WRONG RESPONSE?}
    J --> L
    K --> L
    L -- Yes --> M[Return None]
    L -- No --> N{Response starts with 7F?}
    N -- Yes --> O[Decode ECU error and return None]
    N -- No --> P[Decode values from response stream]
    P --> Q[Return values]
```

<a id="get-values-from-stream-self-stream"></a>
### `get_values_from_stream(self, stream)`

Loops over receive-side data items and decodes each named value from the response stream using the matching [EcuData](ecu_data.md) definition. Missing data definitions raise `KeyError`.

```mermaid
flowchart TD
    A([Start]) --> B[Create empty values dictionary]
    B --> C{More receive data items?}
    C -- No --> D[Return values]
    C -- Yes --> E{Data definition exists in ecu_file.data?}
    E -- No --> F[Raise KeyError]
    E -- Yes --> G[Call EcuData.getDisplayValue]
    G --> H[Store decoded value by name]
    H --> C
```

<a id="build-data-stream-self-data"></a>
### `build_data_stream(self, data)`

Starts with the configured [sentbytes](ecu_request.md#state), then writes each provided input into the correct bit range. Text labels from list mappings are converted back to their numeric raw value before [EcuData.setValue](ecu_data.md#setvalue-self-value-bytes-list-dataitem-ecu-endian-test-mode-false) writes the data.

```mermaid
flowchart TD
    A([Start]) --> B[Split sentbytes into byte list]
    B --> C{More input values?}
    C -- No --> D[Return byte list]
    C -- Yes --> E{Input name exists in sendbyte_dataitems?}
    E -- No --> F[Raise KeyError]
    E -- Yes --> G{Input name exists in ecu_file.data?}
    G -- No --> H[Raise KeyError]
    G -- Yes --> I{Input value is a list label?}
    I -- Yes --> J[Convert label to raw hex value]
    I -- No --> K[Use input value as provided]
    J --> L[Call EcuData.setValue]
    K --> L
    L --> C
```

<a id="auxiliary-functions"></a>
## Auxiliary Functions

<a id="get-formatted-sentbytes-self"></a>
### `get_formatted_sentbytes(self)`

Splits the continuous hexadecimal [sentbytes](ecu_request.md#state) string into a list of two-character byte strings.

```mermaid
flowchart TD
    A([Start]) --> B[Read sentbytes string]
    B --> C[Take two characters at a time]
    C --> D[Return byte list]
```

<a id="get-data-inputs-self"></a>
### `get_data_inputs(self)`

Returns the names of all send-side data items that callers may provide to [build_data_stream](ecu_request.md#build-data-stream-self-data) or [send_request](ecu_request.md#send-request-self-inputvalues-none-test-data-none).

```mermaid
flowchart TD
    A([Start]) --> B[Read sendbyte_dataitems keys]
    B --> C[Return keys]
```

<a id="dump-sentdataitems-self"></a>
### `dump_sentdataitems(self)`

Exports only send-side data item definitions, keyed by input value name.

```mermaid
flowchart TD
    A([Start]) --> B[Create empty dictionary]
    B --> C[Loop over send data items]
    C --> D[Store each DataItem dump]
    D --> E[Return dictionary]
```

<a id="dump-dataitems-self"></a>
### `dump_dataitems(self)`

Exports only receive-side data item definitions, keyed by receive value name.

```mermaid
flowchart TD
    A([Start]) --> B[Create empty dictionary]
    B --> C[Loop over receive data items]
    C --> D[Store each DataItem dump]
    D --> E[Return dictionary]
```

<a id="dump-self"></a>
### `dump(self)`

Exports the request to a compact dictionary. It includes non-default request metadata, the request name, denied SDS modes, and dumped send and receive data items.

```mermaid
flowchart TD
    A([Start]) --> B[Create dictionary]
    B --> C[Add non-default request metadata]
    C --> D[Add name and denied SDS list]
    D --> E[Dump send data items if any]
    E --> F[Dump receive data items if any]
    F --> G[Return dictionary]
```

## Flow Summary

[EcuRequest](ecu_request.md) owns the full request lifecycle: prepare bytes, send or simulate the request, detect ECU errors, and decode named values from the response.

```mermaid
flowchart LR
    A[Input values] --> B[build_data_stream]
    B --> C[send_request]
    C --> D[ECU or simulation response]
    D --> E[get_values_from_stream]
    E --> F[Decoded values]
```
