# EcuIdent, In Simple English

Source: `src/ddt4all/core/ecu/ecu_ident.py`

[EcuIdent](ecu_ident_easylang.md) stores the identity of one known ECU. The scanner compares real ECU answers with these stored values to decide which ECU file should be used.

## Table Of Contents

- [Simple Overview](#simple-overview)
- [Other Code Used By This Class](#other-code-used-by-this-class)
- [Stored Values](#stored-values)
- [Important Details For Beginners](#important-details-for-beginners)
- [Method Guide And Flowcharts](#method-guide-and-flowcharts)
  - [Initialization Functions](#initialization-functions)
    - [`__init__(self, diagversion, supplier, soft, version, name, group, href, protocol, projects, address, zipped=False)`](#init-self-diagversion-supplier-soft-version-name-group-href-protocol-projects-address-zipped-false)
  - [Main Functions](#main-functions)
    - [`checkWith(self, diagversion, supplier, soft, version, addr)`](#checkwith-self-diagversion-supplier-soft-version-addr)
    - [`checkApproximate(self, diagversion, supplier, soft, addr)`](#checkapproximate-self-diagversion-supplier-soft-addr)
  - [Auxiliary Functions](#auxiliary-functions)
    - [`dump(self)`](#dump-self)
- [Simple Flow Summary](#simple-flow-summary)

## Simple Overview

[EcuIdent](ecu_ident_easylang.md) does not talk to the car. It only stores known identity data.

When the scanner gets an answer from an ECU, it compares the answer with many [EcuIdent](ecu_ident_easylang.md) objects. If all important fields match, the ECU is identified.

There is also a close-match check. A close match means the supplier and software look right, but the version is not the exact one from the database.

## Other Code Used By This Class

- [EcuDatabase](ecu_database_easylang.md): creates these objects from database files.
- [EcuScanner](ecu_scanner_easylang.md): uses these objects to match ECU answers.
- [EcuFile](ecu_file_easylang.md): can provide identity data that becomes scanner target data.

## Stored Values

| Attribute | Purpose |
| --- | --- |
| [diagversion](ecu_ident_easylang.md#stored-values) | Expected diagnostic version. |
| [supplier](ecu_ident_easylang.md#stored-values) | Expected supplier code. |
| [soft](ecu_ident_easylang.md#stored-values) | Expected software number. |
| [version](ecu_ident_easylang.md#stored-values) | Expected software version for an exact match. |
| [name](#stored-values) | ECU name. |
| [group](ecu_ident_easylang.md#stored-values) | ECU group. |
| [projects](ecu_file_easylang.md#stored-values) | Vehicle projects that use this ECU. |
| [href](ecu_ident_easylang.md#stored-values) | Where the ECU file is stored. |
| [addr](ecu_ident_easylang.md#stored-values) | Diagnostic address. |
| [protocol](ecu_ident_easylang.md#stored-values) | Protocol name like [CAN](protocols.md#can) or [KWP2000](protocols.md#kwp2000). |
| [hash](ecu_ident_easylang.md#stored-values) | Combined identity text. |
| [zipped](ecu_ident_easylang.md#stored-values) | Whether this target came from a zip database. |

## Important Details For Beginners

- The strict match checks diagnostic version, supplier, software, and version.
- Supplier, software, and version are compared as prefixes. This means a shorter database value can still match a longer ECU answer.
- The close match ignores the version field and mainly checks supplier and software.
- When a match works, the object stores the address that was scanned.

## Method Guide And Flowcharts

<a id="initialization-functions"></a>
## Initialization Functions

<a id="init-self-diagversion-supplier-soft-version-name-group-href-protocol-projects-address-zipped-false"></a>
### `__init__(self, diagversion, supplier, soft, version, name, group, href, protocol, projects, address, zipped=False)`

Stores the ECU identity fields and turns the protocol text into one standard value. For example, protocol text that contains [CAN](protocols.md#can) becomes [CAN](protocols.md#can).

```mermaid
flowchart TD
    A([Start]) --> B[Store diagnostic version, supplier, software, version, name, group, href, projects, and address]
    B --> C{Protocol text contains CAN?}
    C -- Yes --> D[Set protocol to CAN]
    C -- No --> E{Protocol text contains KWP?}
    E -- Yes --> F[Set protocol to KWP2000]
    E -- No --> G{Protocol text contains ISO8?}
    G -- Yes --> H[Set protocol to ISO8]
    G -- No --> I{Protocol text contains DOIP?}
    I -- Yes --> J[Set protocol to DOIP]
    I -- No --> K[Set protocol to UNKNOWN]
    D --> L[Build hash from identity fields]
    F --> L
    H --> L
    J --> L
    K --> L
    L --> M[Store zipped flag]
    M --> N([End])
```

<a id="main-functions"></a>
## Main Functions

<a id="checkwith-self-diagversion-supplier-soft-version-addr"></a>
### `checkWith(self, diagversion, supplier, soft, version, addr)`

Checks if an ECU answer is an exact match. If it matches, the method stores the scanned address and returns `True`.

```mermaid
flowchart TD
    A([Start]) --> B{Stored diagnostic version is empty?}
    B -- Yes --> C([Return None])
    B -- No --> D[Compare diagnostic versions as hexadecimal numbers]
    D --> E{Diagnostic versions match?}
    E -- No --> F[Return False]
    E -- Yes --> G[Compare supplier prefix]
    G --> H{Supplier matches?}
    H -- No --> F
    H -- Yes --> I[Compare software prefix]
    I --> J{Software matches?}
    J -- No --> F
    J -- Yes --> K[Compare version prefix]
    K --> L{Version matches?}
    L -- No --> F
    L -- Yes --> M[Store scanned address]
    M --> N[Return True]
```

<a id="checkapproximate-self-diagversion-supplier-soft-addr"></a>
### `checkApproximate(self, diagversion, supplier, soft, addr)`

Checks if an ECU answer is close enough. It ignores the version field, but supplier and software must match exactly after spaces are removed.

```mermaid
flowchart TD
    A([Start]) --> B{Stored diagnostic version is empty?}
    B -- Yes --> C([Return None])
    B -- No --> D[Compare stripped supplier values]
    D --> E{Supplier matches?}
    E -- No --> F[Return False]
    E -- Yes --> G[Compare stripped software values]
    G --> H{Software matches?}
    H -- No --> F
    H -- Yes --> I[Store scanned address]
    I --> J[Return True]
```

<a id="auxiliary-functions"></a>
## Auxiliary Functions

<a id="dump-self"></a>
### `dump(self)`

Returns the identity data as a dictionary that can be written to JSON. It does not include every internal field.

```mermaid
flowchart TD
    A([Start]) --> B[Create dictionary]
    B --> C[Add diagnostic version, supplier, software, and version]
    C --> D[Add group, projects, protocol, and address]
    D --> E[Return dictionary]
    E --> F([End])
```

## Simple Flow Summary

[EcuIdent](ecu_ident_easylang.md) is the known ECU record. The scanner compares a real ECU answer with this record and decides whether it is an exact match, a close match, or not a match.

```mermaid
flowchart LR
    A[Database identity values] --> B[EcuIdent]
    C[Scanned ECU identity values] --> D{Compare}
    B --> D
    D -- Exact --> E[checkWith returns True]
    D -- Close --> F[checkApproximate returns True]
    D -- No --> G[Return False or None]
```
