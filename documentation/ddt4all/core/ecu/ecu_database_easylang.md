# EcuDatabase, In Simple English

Source: `src/ddt4all/core/ecu/ecu_database.py`

[EcuDatabase](ecu_database_easylang.md) loads the list of known ECUs. The scanner uses it to know which addresses to scan and which ECU identity values count as a match.

## Table Of Contents

- [Simple Overview](#simple-overview)
- [Other Code Used By This Class](#other-code-used-by-this-class)
- [Stored Values](#stored-values)
- [Important Details For Beginners](#important-details-for-beginners)
- [Method Guide And Flowcharts](#method-guide-and-flowcharts)
  - [Initialization Functions](#initialization-functions)
    - [`__init__(self, forceXML=False)`](#init-self-forcexml-false)
  - [Main Functions](#main-functions)
    - [`getTargetsByHref(self, href)`](#gettargetsbyhref-self-href)
    - [`getTargets(self, name)`](#gettargets-self-name)
    - [`getTarget(self, name)`](#gettarget-self-name)
  - [Auxiliary Functions](#auxiliary-functions)
    - [`dump(self)`](#dump-self)
- [Simple Flow Summary](#simple-flow-summary)

## Simple Overview

The class reads target data from JSON, zip, and XML sources.

Each target becomes an [EcuIdent](ecu_ident_easylang.md) object.

The scanner uses the target list for matching and the address lists for scanning.

## Other Code Used By This Class

- [EcuIdent](ecu_ident_easylang.md): stores one known ECU identity.
- [EcuScanner](ecu_scanner_easylang.md): uses this database during scans.
- [options.ecus_dir](../options.md#ecus-dir): tells where the XML ECU list can be found.
- [addressing](ecu_database_module.md#addressing) and [doip_addressing](ecu_database_module.md#doip-addressing): provide known address names.

## Stored Values

| Attribute | Purpose |
| --- | --- |
| [targets](ecu_database_easylang.md#stored-values) | All known ECU identity targets. |
| [vehiclemap](ecu_database_easylang.md#stored-values) | Vehicle project to addresses. |
| [numecu](ecu_database_easylang.md#stored-values) | Number of loaded ECU entries. |
| [available_addr_kwp](ecu_database_easylang.md#stored-values) | Known KWP addresses. |
| [available_addr_can](ecu_database_easylang.md#stored-values) | Known CAN addresses. |
| [available_addr_doip](ecu_database_easylang.md#stored-values) | Known DoIP addresses. |
| [addr_group_mapping_long](ecu_database_easylang.md#stored-values) | Address to long ECU group name. |
| [addr_group_mapping](ecu_database_easylang.md#stored-values) | Address to ECU group name. |

## Important Details For Beginners

- The JSON loader supports a misspelled key for compatibility with older data.
- Targets without auto-ident values can still be added.
- Zip loading may add some targets twice because of the current code structure.
- `dump` does not include DoIP targets.

## Method Guide And Flowcharts

<a id="initialization-functions"></a>
## Initialization Functions

<a id="init-self-forcexml-false"></a>
### `__init__(self, forceXML=False)`

Creates the database lists, reads JSON, zip, and XML data, and builds target and address lookup tables.

```mermaid
flowchart TD
    A([Start]) --> B[Create empty targets, vehicle map, counters, address lists, and group maps]
    B --> C[Seed maps from doip_addressing and addressing]
    C --> D[Read ./json/*.json.targets files]
    D --> E[Create EcuIdent targets and update vehicle and address maps]
    E --> F{ecu.zip exists and forceXML is False?}
    F -- Yes --> G[Read db.json from zip]
    G --> H[Create zipped EcuIdent targets and update maps]
    F -- No --> I[Skip zip database]
    H --> J{eculist.xml exists?}
    I --> J
    J -- Yes --> K[Parse XML functions and targets]
    K --> L[Create XML EcuIdent targets and update maps]
    J -- No --> M([End])
    L --> M
```

<a id="main-functions"></a>
## Main Functions

<a id="gettargetsbyhref-self-href"></a>
### `getTargetsByHref(self, href)`

Returns all targets that point to the same ECU file path.

```mermaid
flowchart TD
    A([Start]) --> B[Create empty result list]
    B --> C[Loop over targets]
    C --> D{href matches?}
    D -- Yes --> E[Append target]
    D -- No --> C
    E --> C
    C --> F[Return result list]
```

<a id="gettargets-self-name"></a>
### `getTargets(self, name)`

Returns all targets with this name.

```mermaid
flowchart TD
    A([Start]) --> B[Create empty result list]
    B --> C[Loop over targets]
    C --> D{Name matches?}
    D -- Yes --> E[Append target]
    D -- No --> C
    E --> C
    C --> F[Return result list]
```

<a id="gettarget-self-name"></a>
### `getTarget(self, name)`

Returns the first target with this name, or `None`.

```mermaid
flowchart TD
    A([Start]) --> B[Loop over targets]
    B --> C{Name matches?}
    C -- Yes --> D[Return target]
    C -- No --> B
    B --> E[Return None]
```

<a id="auxiliary-functions"></a>
## Auxiliary Functions

<a id="dump-self"></a>
### `dump(self)`

Exports supported scanner targets to JSON text. DoIP targets are not included by this method.

```mermaid
flowchart TD
    A([Start]) --> B[Create empty list]
    B --> C[Loop over targets]
    C --> D{Protocol is CAN, KWP2000, or ISO8?}
    D -- Yes --> E[Append target dump]
    D -- No --> C
    E --> C
    C --> F[Return formatted JSON text]
```

## Simple Flow Summary

[EcuDatabase](ecu_database_easylang.md) loads known ECU data and gives the scanner targets and addresses.

```mermaid
flowchart LR
    A[JSON target files] --> D[EcuDatabase]
    B[ecu.zip] --> D
    C[eculist.xml] --> D
    D --> E[EcuIdent targets]
    D --> F[Vehicle project map]
    D --> G[Protocol address lists]
```
