# EcuRequest, In Simple English

Source: `src/ddt4all/core/ecu/ecu_request.py`

[EcuRequest](ecu_request_easylang.md) describes one request that can be sent to an ECU. It knows what bytes to send, where user input goes, and how to read values from the ECU answer.

## Table Of Contents

- [Simple Overview](#simple-overview)
- [Other Code Used By This Class](#other-code-used-by-this-class)
- [Stored Values](#stored-values)
- [Important Details For Beginners](#important-details-for-beginners)
- [Method Guide And Flowcharts](#method-guide-and-flowcharts)
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
- [Simple Flow Summary](#simple-flow-summary)

## Simple Overview

This class connects an ECU file definition with a real request.

First it builds the bytes to send. Then it sends them or uses test data. Then it reads named values from the answer.

Input fields and output fields both use [DataItem](data_item_easylang.md) positions and [EcuData](ecu_data_easylang.md) conversion rules.

## Other Code Used By This Class

- [EcuFile](ecu_file_easylang.md): owns this request and provides data definitions.
- [DataItem](data_item_easylang.md): tells where a field is in the bytes.
- [EcuData](ecu_data_easylang.md): converts between bytes and values.
- [options.elm](../options.md#elm): sends the request to hardware in real mode.

## Stored Values

| Attribute | Purpose |
| --- | --- |
| [minbytes](ecu_request_easylang.md#stored-values) | Minimum answer size. |
| [shiftbytescount](ecu_request_easylang.md#stored-values) | Byte shift setting. |
| [replybytes](ecu_request_easylang.md#stored-values) | Default answer bytes. |
| [manualsend](ecu_request_easylang.md#stored-values) | Whether request is manual-send. |
| [sentbytes](ecu_request_easylang.md#stored-values) | Bytes to send before user input is inserted. |
| [dataitems](ecu_request_easylang.md#stored-values) | Fields read from the answer. |
| [sendbyte_dataitems](ecu_request_easylang.md#stored-values) | Fields written into the request. |
| [name](#stored-values) | Request name. |
| [ecu_file](ecu_request_easylang.md#stored-values) | Parent ECU file. |
| [sds](ecu_request_easylang.md#stored-values) | Diagnostic session access flags. |

## Important Details For Beginners

- Input names must exist in both [sendbyte_dataitems](ecu_request_easylang.md#stored-values) and the parent ECU file data map.
- A response starting with [WRONG RESPONSE](diagnostic_responses.md#wrong-response) or [7F](diagnostic_responses.md#negative-response) means failure.
- In simulation mode, explicit `test_data` is used first. If no test data is given, [replybytes](ecu_request_easylang.md#stored-values) is used.
- [sentbytes](ecu_request_easylang.md#stored-values) is split into pairs of hex characters.

## Method Guide And Flowcharts

<a id="initialization-functions"></a>
## Initialization Functions

<a id="init-self-data-ecu-file"></a>
### `__init__(self, data, ecu_file)`

Creates the request from JSON, XML, or a simple name. It also creates the input and output field positions.

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

Builds the request, sends it or simulates it, checks for errors, and returns decoded values.

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

Reads every configured output value from the ECU answer.

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

Starts with the base send bytes and places each user input value into the correct field.

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

Splits the send-byte string into a list like one entry per byte.

```mermaid
flowchart TD
    A([Start]) --> B[Read sentbytes string]
    B --> C[Take two characters at a time]
    C --> D[Return byte list]
```

<a id="get-data-inputs-self"></a>
### `get_data_inputs(self)`

Returns the names of input values this request accepts.

```mermaid
flowchart TD
    A([Start]) --> B[Read sendbyte_dataitems keys]
    B --> C[Return keys]
```

<a id="dump-sentdataitems-self"></a>
### `dump_sentdataitems(self)`

Exports only the fields written into the request.

```mermaid
flowchart TD
    A([Start]) --> B[Create empty dictionary]
    B --> C[Loop over send data items]
    C --> D[Store each DataItem dump]
    D --> E[Return dictionary]
```

<a id="dump-dataitems-self"></a>
### `dump_dataitems(self)`

Exports only the fields read from the answer.

```mermaid
flowchart TD
    A([Start]) --> B[Create empty dictionary]
    B --> C[Loop over receive data items]
    C --> D[Store each DataItem dump]
    D --> E[Return dictionary]
```

<a id="dump-self"></a>
### `dump(self)`

Exports the request as a dictionary for JSON.

```mermaid
flowchart TD
    A([Start]) --> B[Create dictionary]
    B --> C[Add non-default request metadata]
    C --> D[Add name and denied SDS list]
    D --> E[Dump send data items if any]
    E --> F[Dump receive data items if any]
    F --> G[Return dictionary]
```

## Simple Flow Summary

[EcuRequest](ecu_request_easylang.md) builds request bytes, gets an ECU answer, and turns that answer into named values.

```mermaid
flowchart LR
    A[Input values] --> B[build_data_stream]
    B --> C[send_request]
    C --> D[ECU or simulation response]
    D --> E[get_values_from_stream]
    E --> F[Decoded values]
```
