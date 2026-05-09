# EcuScanner, In Simple English

Source: `src/ddt4all/core/ecu/ecu_scanner.py`

[EcuScanner](ecu_scanner_easylang.md) searches for ECUs. An ECU is a small computer in a car.

The scanner can talk to ECUs with CAN, KWP2000 / ISO, or DoIP. When an ECU answers, the scanner reads identity data from the answer. Then it compares this data with the loaded [EcuDatabase](ecu_database_easylang.md).

If the answer matches exactly, the scanner stores the ECU in [ecus](ecu_scanner_easylang.md#stored-values).

If the answer is close, but not perfect, the scanner stores the ECU in [approximate_ecus](ecu_scanner_easylang.md#stored-values).

The scanner can also update progress widgets in the user interface and write messages to the main log window.

## Table Of Contents

- [Method Reference And Flowcharts](#method-reference-and-flowcharts)
- [Initialization Functions](#initialization-functions)
  - [`__init__(self)`](#init-self)
  - [`clear(self)`](#clear-self)
- [Main Functions](#main-functions)
  - [`scan_kwp(self, progress=None, label=None, vehiclefilter=None)`](#scan-kwp-self-progress-none-label-none-vehiclefilter-none)
  - [`scan_doip(self, progress=None, label=None, vehiclefilter=None)`](#scan-doip-self-progress-none-label-none-vehiclefilter-none)
  - [`scan(self, progress=None, label=None, vehiclefilter=None, canline=0)`](#scan-self-progress-none-label-none-vehiclefilter-none-canline-0)
- [Auxiliary Functions](#auxiliary-functions)
  - [`identify_old(self, addr, label, force=False)`](#identify-old-self-addr-label-force-false)
  - [`identify_new(self, addr, label)`](#identify-new-self-addr-label)
  - [`identify_from_frame(self, addr, can_response)`](#identify-from-frame-self-addr-can-response)
  - [`getNumEcuDb(self)`](#getnumecudb-self)
  - [`getNumAddr(self)`](#getnumaddr-self)
  - [`check_ecu2(self, diagversion, supplier, soft, version, label, addr, protocol)`](#check-ecu2-self-diagversion-supplier-soft-version-label-addr-protocol)
  - [`check_ecu(self, can_response, label, addr, protocol)`](#check-ecu-self-can-response-label-addr-protocol)
  - [`addTarget(self, target)`](#addtarget-self-target)
- [Scan Matching Summary](#scan-matching-summary)

## Other Code Used By This Class

- [EcuDatabase](ecu_database_easylang.md): gives the scanner the known ECU list, address names, scan addresses, and vehicle project filters.
- [EcuIdent](ecu_ident_easylang.md): represents one known ECU from the database. It can check if an ECU answer matches it.
- [options.elm](../options.md#elm): talks to the adapter for CAN and KWP scans.
- [DoIPDevice](../doip/doip_devices_easylang.md): talks to ECUs over DoIP.
- [options.main_window.logview](../options.md#main-window-logview): shows scan messages in the main window.
- [progress](ecu_scanner_easylang.md#other-code-used-by-this-class), [label](ecu_scanner_easylang.md#other-code-used-by-this-class), and [qapp](ecu_scanner_easylang.md#stored-values): optional user interface objects used while scanning.

## Stored Values

| Attribute | Simple meaning |
| --- | --- |
| `totalecu` | A counter-like value. It is reset by [clear](ecu_scanner_easylang.md#clear-self), but this class does not currently increase it. |
| [ecus](ecu_scanner_easylang.md#stored-values) | Exact ECU matches, stored by display name. |
| [approximate_ecus](ecu_scanner_easylang.md#stored-values) | Best close ECU matches, stored by ECU name. |
| [ecu_database](ecu_scanner_easylang.md#stored-values) | The loaded [EcuDatabase](ecu_database_easylang.md) object used for scans and matching. |
| [num_ecu_found](ecu_scanner_easylang.md#stored-values) | Number of exact and close matches found since the scanner was created or cleared. |
| [report_data](ecu_scanner_easylang.md#stored-values) | Report data list. It is reset by [clear](ecu_scanner_easylang.md#clear-self), but this class does not currently fill it. |
| [qapp](ecu_scanner_easylang.md#stored-values) | Optional Qt application object. It lets the UI update during long scans. |
| [current_doip_device](ecu_scanner_easylang.md#stored-values) | Temporary DoIP device used during a DoIP scan. |

## Method Reference And Flowcharts

<a id="initialization-functions"></a>
## Initialization Functions

<a id="init-self"></a>
### `__init__(self)`

Creates a new scanner object. It sets empty result containers and loads a fresh ECU database.

```mermaid
flowchart TD
    A([Start]) --> B[Set totalecu to 0]
    B --> C[Create empty ecus dictionary]
    C --> D[Create empty approximate_ecus dictionary]
    D --> E[Create EcuDatabase]
    E --> F[Set num_ecu_found to 0]
    F --> G[Create empty report_data list]
    G --> H[Set qapp to None]
    H --> I([End])
```

<a id="clear-self"></a>
### `clear(self)`

Clears scan results and counters. It keeps the already loaded database.

```mermaid
flowchart TD
    A([Start]) --> B[Set totalecu to 0]
    B --> C[Clear ecus]
    C --> D[Clear approximate_ecus]
    D --> E[Set num_ecu_found to 0]
    E --> F[Clear report_data]
    F --> G([End])
```

<a id="main-functions"></a>
## Main Functions

<a id="scan-kwp-self-progress-none-label-none-vehiclefilter-none"></a>
### `scan_kwp(self, progress=None, label=None, vehiclefilter=None)`

Scans KWP2000 / ISO addresses.

In simulation mode, it first adds one example KWP ECU to [ecus](ecu_scanner_easylang.md#stored-values).

In real mode, it initializes the ELM device and ISO communication.

Then it builds the address list:

- if `vehiclefilter` is set, it uses KWP2000 addresses for that vehicle project
- otherwise, it uses all known KWP addresses from the database

For each address, real mode sets the ISO address, starts session [10C0](diagnostic_requests.md#10c0), and sends request [2180](diagnostic_requests.md#2180).

Simulation mode uses example answers for selected addresses.

Each answer is passed to [check_ecu](ecu_scanner_easylang.md#check-ecu-self-can-response-label-addr-protocol) with protocol `KWP`.

At the end, it closes the protocol in real mode.

```mermaid
flowchart TD
    A([Start]) --> B{Simulation mode?}
    B -- Yes --> C[Add example KWP ECU to ecus]
    B -- No --> D{ELM object exists?}
    D -- Yes --> E[Initialize ELM with DeviceManager]
    D -- No --> F[Initialize ISO]
    E --> F
    C --> G[Build KWP address list]
    F --> G
    G --> H{vehiclefilter is set and known?}
    H -- Yes --> I[Collect KWP2000 addresses from vehiclemap]
    H -- No --> J[Use all available KWP addresses]
    I --> K{Any addresses?}
    J --> K
    K -- No --> Z([Return])
    K -- Yes --> L[Set progress range]
    L --> M{More KWP addresses?}
    M -- No --> X{Simulation mode?}
    M -- Yes --> N[Update progress and process UI events]
    N --> O[Print scanned address and ECU group]
    O --> P{Simulation mode?}
    P -- No --> Q[Enable slow init option]
    Q --> R{Set ISO address worked?}
    R -- No --> M
    R -- Yes --> S[Start ISO session 10C0]
    S --> T[Request 2180]
    P -- Yes --> U{Address has example answer?}
    U -- Yes --> V[Use example answer]
    U -- No --> M
    T --> W[Call check_ecu as KWP]
    V --> W
    W --> M
    X -- No --> Y[Close ELM protocol]
    X -- Yes --> AA([End])
    Y --> AA
```

<a id="scan-doip-self-progress-none-label-none-vehiclefilter-none"></a>
### `scan_doip(self, progress=None, label=None, vehiclefilter=None)`

Scans DoIP addresses.

DoIP means diagnostics over IP. It uses a network connection instead of the normal ELM CAN / KWP adapter.

In real mode, the method reads the DoIP target IP, port, and timeout from `options`. Then it creates a [DoIPDevice](../doip/doip_devices_easylang.md) and connects to it.

Then it builds the address list:

- if `vehiclefilter` is set, it uses DoIP addresses for that vehicle project
- otherwise, it uses addresses from [doip_addressing](ecu_database_module.md#doip-addressing) when available
- if [doip_addressing](ecu_database_module.md#doip-addressing) is not available, it uses DoIP addresses from the database

For each address, it prints the ECU group or a warning. In real mode, it sets the DoIP target address, starts session [10C0](diagnostic_requests.md#10c0), sends tester-present request [3E00](diagnostic_requests.md#3e00), and then requests identity data with [2180](diagnostic_requests.md#2180).

If enough identity data is returned, the bytes are converted to a hex string and passed to [check_ecu](ecu_scanner_easylang.md#check-ecu-self-can-response-label-addr-protocol) with protocol [DoIP](protocols.md#doip).

In simulation mode, it only prints what would be scanned.

At the end, real mode closes the DoIP connection.

```mermaid
flowchart TD
    A([Start]) --> B{Simulation mode?}
    B -- No --> C[Read DoIP IP, port, and timeout from options]
    C --> D[Create DoIPDevice]
    D --> E[Set timeout if supported]
    E --> F{Connection worked?}
    F -- No --> G[Print connection failure]
    G --> Z([Return])
    F -- Yes --> H[Store current_doip_device]
    B -- Yes --> I[Skip DoIP connection]
    H --> J[Build DoIP address list]
    I --> J
    J --> K{vehiclefilter is set and known?}
    K -- Yes --> L[Collect DOIP addresses from vehiclemap]
    K -- No --> M{doip_addressing is available?}
    M -- Yes --> N[Use doip_addressing keys]
    M -- No --> O[Use database DoIP addresses]
    L --> P{Any addresses?}
    N --> P
    O --> P
    P -- No --> Q[Print no addresses message]
    Q --> Z
    P -- Yes --> R[Set progress range]
    R --> S{More unique DoIP addresses?}
    S -- No --> AC{Simulation mode?}
    S -- Yes --> T[Update progress and process UI events]
    T --> U{Address is mapped?}
    U -- No --> V{Address exists in doip_addressing?}
    V -- Yes --> W[Print DoIP project name]
    V -- No --> X[Print unmapped address warning]
    X --> S
    U -- Yes --> Y[Print database ECU group]
    W --> AA{Simulation mode?}
    Y --> AA
    AA -- Yes --> AB[Print simulation-only messages]
    AB --> S
    AA -- No --> AD{current_doip_device exists?}
    AD -- No --> AE[Print device unavailable]
    AE --> S
    AD -- Yes --> AF[Set target address from hex address]
    AF --> AG{Start session 10C0 worked?}
    AG -- No --> AH[Print communication start failure]
    AH --> S
    AG -- Yes --> AI[Send tester-present request 3E00]
    AI --> AJ{Positive tester-present answer?}
    AJ -- No --> AK[Print negative or failed session message]
    AK --> S
    AJ -- Yes --> AL[Request identity data with 2180]
    AL --> AM{Identity data length is at least 59?}
    AM -- No --> AN[Print no identification data message]
    AM -- Yes --> AO[Format bytes as hex response]
    AO --> AP[Call check_ecu as DoIP]
    AN --> S
    AP --> S
    AC -- No --> AQ{current_doip_device exists?}
    AQ -- Yes --> AR[Disconnect if supported]
    AR --> AS[Set current_doip_device to None]
    AQ -- No --> AT([End])
    AS --> AT
    AC -- Yes --> AT
```

<a id="scan-self-progress-none-label-none-vehiclefilter-none-canline-0"></a>
### `scan(self, progress=None, label=None, vehiclefilter=None, canline=0)`

Scans CAN addresses.

In real mode, it initializes the ELM device and CAN communication.

Then it builds the address list:

- if `vehiclefilter` is set, it uses CAN addresses for that vehicle project
- otherwise, it uses all known CAN addresses from the database

It skips invalid addresses `00` and `FF`. It also skips addresses that are not mapped by the ELM code.

For each valid address, it sets the CAN address. Then it tries [identify_new](ecu_scanner_easylang.md#identify-new-self-addr-label). If that fails, it tries [identify_old](ecu_scanner_easylang.md#identify-old-self-addr-label-force-false).

At the end, it closes the protocol in real mode.

```mermaid
flowchart TD
    A([Start]) --> B[Set counter i to 0]
    B --> C{Simulation mode?}
    C -- No --> D{ELM object exists?}
    D -- Yes --> E[Initialize ELM with DeviceManager]
    D -- No --> F[Initialize CAN]
    E --> F
    C -- Yes --> G[Skip hardware initialization]
    F --> H[Build CAN address list]
    G --> H
    H --> I{vehiclefilter is set and known?}
    I -- Yes --> J[Collect CAN addresses from vehiclemap]
    I -- No --> K[Use all available CAN addresses]
    J --> L{Any addresses?}
    K --> L
    L -- No --> Z([Return])
    L -- Yes --> M[Set progress range]
    M --> N{More unique addresses?}
    N -- No --> X{Simulation mode?}
    N -- Yes --> O[Update progress and process UI events]
    O --> P{Address is 00 or FF?}
    P -- Yes --> N
    P -- No --> Q{ELM knows this address?}
    Q -- No --> R[Print address mapping warning]
    R --> N
    Q -- Yes --> S[Print scanned address and ECU group]
    S --> T{Simulation mode?}
    T -- No --> U[Initialize CAN and set CAN address]
    T -- Yes --> V[Skip address setup]
    U --> W{identify_new works?}
    V --> W
    W -- Yes --> N
    W -- No --> Y[Run identify_old]
    Y --> N
    X -- No --> AA[Close ELM protocol]
    X -- Yes --> AB([End])
    AA --> AB
```

<a id="auxiliary-functions"></a>
## Auxiliary Functions

<a id="identify-old-self-addr-label-force-false"></a>
### `identify_old(self, addr, label, force=False)`

Uses the older CAN identity request.

In real mode, it starts CAN session [10C0](diagnostic_requests.md#10c0). If the session fails, it stops. If the session works, it sends request [2180](diagnostic_requests.md#2180).

In simulation mode, it uses built-in example answers for some addresses.

After it has an answer, it calls [check_ecu](ecu_scanner_easylang.md#check-ecu-self-can-response-label-addr-protocol).

```mermaid
flowchart TD
    A([Start]) --> B{Simulation mode?}
    B -- No --> C[Start CAN session 10C0]
    C --> D{Session started?}
    D -- No --> Z([Return])
    D -- Yes --> E[Send request 2180 with ELM]
    B -- Yes --> F{force is False?}
    F -- Yes --> G{Address has example answer?}
    G -- addr 04 --> H[Use example positive answer]
    G -- addr 51 --> I[Use example positive answer]
    G -- addr 7A --> J[Use example close-match answer]
    G -- Other --> K[Use 7F 80 negative answer]
    F -- No --> E
    H --> L[Check answer as CAN]
    I --> L
    J --> L
    K --> L
    E --> L
    L --> M([End])
```

<a id="identify-new-self-addr-label"></a>
### `identify_new(self, addr, label)`

Uses the newer CAN identity method.

In real mode, it starts CAN session [1003](diagnostic_requests.md#1003). If that fails, the method returns `False`.

Then it asks the ECU for four values:

| Request | Meaning |
| --- | --- |
| [22F1A0](diagnostic_requests.md#22f1a0) | Diagnostic version |
| [22F18A](diagnostic_requests.md#22f18a) | Supplier |
| [22F194](diagnostic_requests.md#22f194) | Software number |
| [22F195](diagnostic_requests.md#22f195) | Software version |

If any request returns `WRONG`, the method returns `False`.

If all data is valid, it calls [check_ecu2](ecu_scanner_easylang.md#check-ecu2-self-diagversion-supplier-soft-version-label-addr-protocol) and returns `True`.

In simulation mode, it uses built-in example answers.

```mermaid
flowchart TD
    A([Start]) --> B[Create empty identity fields]
    B --> C{Simulation mode?}
    C -- No --> D[Start CAN session 1003]
    D --> E{Session started?}
    E -- No --> R[Return False]
    E -- Yes --> F[Request 22F1A0]
    C -- Yes --> G[Use simulated 22F1A0 answer for address]
    F --> H{Answer contains WRONG?}
    H -- Yes --> R
    H -- No --> I[Read diagnostic version]
    G --> I
    I --> J{Simulation mode?}
    J -- No --> K[Request 22F18A]
    J -- Yes --> L[Use simulated supplier answer]
    K --> M{Answer contains WRONG?}
    M -- Yes --> R
    M -- No --> N[Decode supplier text]
    L --> N
    N --> O{Simulation mode?}
    O -- No --> P[Request 22F194]
    O -- Yes --> Q[Use simulated software-number answer]
    P --> S{Answer contains WRONG?}
    S -- Yes --> R
    S -- No --> T[Decode software number]
    Q --> T
    T --> U{Simulation mode?}
    U -- No --> V[Request 22F195]
    U -- Yes --> W[Use simulated software-version answer]
    V --> X{Answer contains WRONG?}
    X -- Yes --> R
    X -- No --> Y[Decode software version]
    W --> Y
    Y --> Z{Diagnostic version is empty?}
    Z -- Yes --> R
    Z -- No --> AA[Call check_ecu2 as CAN]
    AA --> AB[Return True]
    R --> AC([End])
    AB --> AC
```

<a id="identify-from-frame-self-addr-can-response"></a>
### `identify_from_frame(self, addr, can_response)`

Checks an already captured CAN answer.

It does not open a diagnostic session. It just passes the answer to [check_ecu](ecu_scanner_easylang.md#check-ecu-self-can-response-label-addr-protocol).

```mermaid
flowchart TD
    A([Start]) --> B[Receive address and CAN answer]
    B --> C[Call check_ecu with no label and protocol CAN]
    C --> D([End])
```

<a id="getnumecudb-self"></a>
### `getNumEcuDb(self)`

Returns the number of ECU entries in the database.

```mermaid
flowchart TD
    A([Start]) --> B[Read ecu_database.numecu]
    B --> C[Return that number]
    C --> D([End])
```

<a id="getnumaddr-self"></a>
### `getNumAddr(self)`

Counts unique diagnostic addresses from [elm.dnat](../elm/elm_module.md#address-tables) and [elm.dnat_ext](../elm/elm_module.md#address-tables).

It does not count the same address twice.

```mermaid
flowchart TD
    A([Start]) --> B[Create empty count list]
    B --> C{More keys in elm.dnat?}
    C -- Yes --> D{Already counted?}
    D -- No --> E[Add key to count list]
    D -- Yes --> C
    E --> C
    C -- No --> F{More keys in elm.dnat_ext?}
    F -- Yes --> G{Already counted?}
    G -- No --> H[Add key to count list]
    G -- Yes --> F
    H --> F
    F -- No --> I[Return number of counted keys]
    I --> J([End])
```

<a id="check-ecu2-self-diagversion-supplier-soft-version-label-addr-protocol"></a>
### `check_ecu2(self, diagversion, supplier, soft, version, label, addr, protocol)`

Compares parsed ECU identity values with all known targets in the database.

The parsed values are:

- diagnostic version
- supplier
- software number
- software version
- address
- protocol

The method first checks if the protocol fits. Then it tries to find an exact match.

If there is no exact match, it remembers close matches. A close match has the same diagnostic version, supplier, and software number, but not necessarily the same version.

If there are several close matches, it keeps the one with the closest version number.

It writes different log messages:

- green for exact matches
- blue for close matches
- red when no useful ECU file was found

```mermaid
flowchart TD
    A([Start]) --> B[Create empty close-match list and flags]
    B --> C{Address has ECU group name?}
    C -- Yes --> D[Use mapped ECU type]
    C -- No --> E[Use UNKNOWN ECU type]
    D --> F[Set targetNum to 0]
    E --> F
    F --> G{More database targets?}
    G -- No --> N{No exact match and close matches exist?}
    G -- Yes --> H{Target protocol fits scan protocol?}
    H -- No --> I[Increase targetNum]
    I --> G
    H -- Yes --> J{Exact match?}
    J -- Yes --> K[Store target in ecus]
    K --> L[Increase found counter and update label]
    L --> M[Write green identified ECU log message]
    M --> N
    J -- No --> O{Close match?}
    O -- Yes --> P[Add target to close-match list]
    O -- No --> I
    P --> I
    N -- Yes --> Q[Find close match with smallest version difference]
    Q --> R{Best close match found?}
    R -- Yes --> S[Store target in approximate_ecus]
    S --> T[Increase found counter and update label]
    T --> U[Write blue not-perfect-match log message]
    R -- No --> V([End])
    U --> V
    N -- No --> W{No exact and no close match?}
    W -- Yes --> X[Write red no relevant ECU file log message]
    W -- No --> V
    X --> V
```

<a id="check-ecu-self-can-response-label-addr-protocol"></a>
### `check_ecu(self, can_response, label, addr, protocol)`

Reads identity values from a raw ECU answer.

The raw answer is a string of hexadecimal bytes.

The method supports three formats:

- a long legacy format
- a DoIP format
- a shorter CAN / KWP format

After it reads the values, it calls [check_ecu2](ecu_scanner_easylang.md#check-ecu2-self-diagversion-supplier-soft-version-label-addr-protocol).

If parsing fails, it stops without adding a match.

```mermaid
flowchart TD
    A([Start]) --> B{Answer length is greater than 59?}
    B -- Yes --> C[Read long legacy identity fields]
    C --> D[Call check_ecu2]
    D --> Z([End])
    B -- No --> E{Protocol is DOIP?}
    E -- Yes --> F{Answer length is greater than 20?}
    F -- No --> G[Print minimal DoIP data message]
    F -- Yes --> H{Answer starts with 61 80?}
    H -- Yes --> I[Read DoIP identity fields]
    I --> J[Call check_ecu2]
    H -- No --> K[Print unknown DoIP format message]
    J --> Z
    K --> Z
    G --> Z
    E -- No --> L{Answer length is greater than 20?}
    L -- No --> Z
    L -- Yes --> M[Try to read short CAN or KWP fields]
    M --> N{Parsing worked?}
    N -- Yes --> O[Call check_ecu2]
    N -- No --> P[Return without match]
    O --> Z
    P --> Z
```

<a id="addtarget-self-target"></a>
### `addTarget(self, target)`

Adds one target directly to the exact ECU match dictionary.

The key is `target.name`.

```mermaid
flowchart TD
    A([Start]) --> B[Read target.name]
    B --> C[Store target in ecus]
    C --> D([End])
```

## Scan Matching Summary

This is the short version of the whole scan process.

```mermaid
flowchart LR
    A[scan, scan_kwp, scan_doip, or identify_from_frame] --> B[Raw ECU identity answer]
    B --> C[check_ecu reads fields from the answer]
    C --> D[check_ecu2 compares fields with database targets]
    D --> E{Exact match?}
    E -- Yes --> F[Store in ecus and write green log message]
    E -- No --> G{Close match?}
    G -- Yes --> H[Store closest version in approximate_ecus and write blue log message]
    G -- No --> I[Write red no relevant ECU file log message]
```
