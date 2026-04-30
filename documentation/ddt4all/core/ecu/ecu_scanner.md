# EcuScanner

Source: `src/ddt4all/core/ecu/ecu_scanner.py`

[EcuScanner](ecu_scanner.md) discovers ECUs that respond on CAN, KWP2000/ISO, or DoIP transports and matches their identification data against the loaded [EcuDatabase](ecu_database.md). It stores exact matches in [ecus](ecu_scanner.md#state), near matches in [approximate_ecus](ecu_scanner.md#state), updates optional UI progress/label widgets, and writes scan findings to the main window log view.

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

## Collaborators

- [EcuDatabase](ecu_database.md): provides known ECU targets, address mappings, available protocol addresses, and vehicle project filters.
- [EcuIdent](ecu_ident.md): represents one known ECU identification target and performs exact or approximate matching.
- [options.elm](../options.md#elm): provides CAN/KWP transport setup, session start, request, and protocol close operations.
- [DoIPDevice](../doip/doip_devices.md): provides DoIP transport setup and request handling.
- [options.main_window.logview](../options.md#main-window-logview): receives HTML-formatted scan result messages.
- [progress](ecu_scanner.md#collaborators), [label](ecu_scanner.md#collaborators), and [qapp](ecu_scanner.md#state): optional UI hooks used during scans.

## State

| Attribute | Purpose |
| --- | --- |
| `totalecu` | Scan counter placeholder reset by [clear](ecu_scanner.md#clear-self); not currently incremented by scanner methods. |
| [ecus](ecu_scanner.md#state) | Exact ECU matches keyed by display name. |
| [approximate_ecus](ecu_scanner.md#state) | Best approximate ECU matches keyed by ECU name. |
| [ecu_database](ecu_scanner.md#state) | Loaded [EcuDatabase](ecu_database.md) instance used for matching and scan address discovery. |
| [num_ecu_found](ecu_scanner.md#state) | Number of exact and approximate matches found during the current scanner lifetime or since [clear](ecu_scanner.md#clear-self). |
| [report_data](ecu_scanner.md#state) | Report data placeholder reset by [clear](ecu_scanner.md#clear-self); not currently populated by scanner methods. |
| [qapp](ecu_scanner.md#state) | Optional Qt application object used to process UI events during progress updates. |
| [current_doip_device](ecu_scanner.md#state) | Created temporarily by [scan_doip](ecu_scanner.md#scan-doip-self-progress-none-label-none-vehiclefilter-none) when DoIP scanning is active. |

## Method Reference And Flowcharts

<a id="initialization-functions"></a>
## Initialization Functions

<a id="init-self"></a>
### `__init__(self)`

Initializes the scanner state and loads a fresh ECU database.

```mermaid
flowchart TD
    A([Start]) --> B[Set totalecu to 0]
    B --> C[Create empty ecus dict]
    C --> D[Create empty approximate_ecus dict]
    D --> E[Instantiate EcuDatabase]
    E --> F[Set num_ecu_found to 0]
    F --> G[Create empty report_data list]
    G --> H[Set qapp to None]
    H --> I([End])
```

<a id="clear-self"></a>
### `clear(self)`

Resets scan result state while keeping the loaded database object.

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

Scans KWP2000/ISO addresses. Simulation mode injects one known ECU result and uses sample responses for selected addresses; hardware mode initializes ISO, starts [10C0](diagnostic_requests.md#10c0), and requests [2180](diagnostic_requests.md#2180).

```mermaid
flowchart TD
    A([Start]) --> B{Simulation mode?}
    B -- Yes --> C[Insert sample KWP ECU into ecus]
    B -- No --> D{options.elm exists?}
    D -- Yes --> E[Initialize ELM through DeviceManager]
    D -- No --> F[Initialize ISO]
    E --> F
    C --> G[Build KWP address list]
    F --> G
    G --> H{vehiclefilter supplied and found?}
    H -- Yes --> I[Collect KWP2000 addresses from vehiclemap]
    H -- No --> J[Use ecu_database.available_addr_kwp]
    I --> K{Any addresses?}
    J --> K
    K -- No --> Z([Return])
    K -- Yes --> L[Initialize progress range]
    L --> M{More KWP addresses?}
    M -- No --> X{Simulation mode?}
    M -- Yes --> N[Increment progress and process UI events]
    N --> O[Print scan address and ECU group]
    O --> P{Simulation mode?}
    P -- No --> Q[Enable slow init option]
    Q --> R{Set ISO address succeeds?}
    R -- No --> M
    R -- Yes --> S[Start ISO session 10C0]
    S --> T[Request 2180]
    P -- Yes --> U{Address has sample response?}
    U -- Yes --> V[Use sample response]
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

Scans DoIP addresses using an independent [DoIPDevice](../doip/doip_devices.md). Hardware mode connects to the configured DoIP endpoint, scans project or database addresses, starts a diagnostic session per address, sends tester-present, reads identification data with [2180](diagnostic_requests.md#2180), and then closes the DoIP connection.

```mermaid
flowchart TD
    A([Start]) --> B{Simulation mode?}
    B -- No --> C[Read target IP, port, and timeout from options]
    C --> D[Create DoIPDevice]
    D --> E[Apply timeout if supported]
    E --> F{Connect succeeds?}
    F -- No --> G[Print connection failure]
    G --> Z([Return])
    F -- Yes --> H[Store current_doip_device]
    B -- Yes --> I[Skip DoIP connection]
    H --> J[Build DoIP address list]
    I --> J
    J --> K{vehiclefilter supplied and found?}
    K -- Yes --> L[Collect DOIP addresses from vehiclemap]
    K -- No --> M{Global doip_addressing available?}
    M -- Yes --> N[Use doip_addressing keys]
    M -- No --> O[Use ecu_database.available_addr_doip]
    L --> P{Any addresses?}
    N --> P
    O --> P
    P -- No --> Q[Print no addresses message]
    Q --> Z
    P -- Yes --> R[Initialize progress range]
    R --> S{More unique DoIP addresses?}
    S -- No --> AC{Simulation mode?}
    S -- Yes --> T[Increment progress and process UI events]
    T --> U{Address mapped?}
    U -- No --> V{Address exists in doip_addressing?}
    V -- Yes --> W[Print DoIP project name]
    V -- No --> X[Print unmapped warning]
    X --> S
    U -- Yes --> Y[Print database ECU group]
    W --> AA{Simulation mode?}
    Y --> AA
    AA -- Yes --> AB[Print simulation-only scan messages]
    AB --> S
    AA -- No --> AD{current_doip_device available?}
    AD -- No --> AE[Print device unavailable]
    AE --> S
    AD -- Yes --> AF[Set target_address from hex address]
    AF --> AG{Start session 10C0 succeeds?}
    AG -- No --> AH[Print communication init failure]
    AH --> S
    AG -- Yes --> AI[Request tester present 3E00]
    AI --> AJ{Positive tester-present response?}
    AJ -- No --> AK[Print negative or failed session message]
    AK --> S
    AJ -- Yes --> AL[Request identification 2180]
    AL --> AM{Identification data length >= 59?}
    AM -- No --> AN[Print no identification data]
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

Scans CAN addresses. It optionally filters addresses by vehicle project, initializes CAN transport when not simulating, and tries the new identification method before falling back to the legacy method.

```mermaid
flowchart TD
    A([Start]) --> B[Set index i to 0]
    B --> C{Simulation mode?}
    C -- No --> D{options.elm exists?}
    D -- Yes --> E[Initialize ELM through DeviceManager]
    D -- No --> F[Initialize CAN]
    E --> F
    C -- Yes --> G[Skip hardware init]
    F --> H[Build CAN address list]
    G --> H
    H --> I{vehiclefilter supplied and found?}
    I -- Yes --> J[Collect CAN addresses from vehiclemap]
    I -- No --> K[Use ecu_database.available_addr_can]
    J --> L{Any addresses?}
    K --> L
    L -- No --> Z([Return])
    L -- Yes --> M[Initialize progress range]
    M --> N{More unique addresses?}
    N -- No --> X{Simulation mode?}
    N -- Yes --> O[Increment progress and process UI events]
    O --> P{Address is 00 or FF?}
    P -- Yes --> N
    P -- No --> Q{Address mapped by elm.addr_exist?}
    Q -- No --> R[Print mapping warning]
    R --> N
    Q -- Yes --> S[Print scan address and ECU group]
    S --> T{Simulation mode?}
    T -- No --> U[Reinitialize CAN and set CAN address]
    T -- Yes --> V[Skip address setup]
    U --> W{identify_new succeeds?}
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

Uses the legacy [2180](diagnostic_requests.md#2180) identification request on CAN, then delegates response parsing and matching to [check_ecu](ecu_scanner.md#check-ecu-self-can-response-label-addr-protocol).

```mermaid
flowchart TD
    A([Start]) --> B{Simulation mode?}
    B -- No --> C[Start CAN session 10C0]
    C --> D{Session started?}
    D -- No --> Z([Return])
    D -- Yes --> E[Request 2180 from ELM]
    B -- Yes --> F{force is False?}
    F -- Yes --> G{Address has built-in sample response?}
    G -- addr 04 --> H[Use sample positive response]
    G -- addr 51 --> I[Use sample positive response]
    G -- addr 7A --> J[Use approximate-match sample response]
    G -- Other --> K[Use 7F 80 negative response]
    F -- No --> E
    H --> L[check_ecu response as CAN]
    I --> L
    J --> L
    K --> L
    E --> L
    L --> M([End])
```

<a id="identify-new-self-addr-label"></a>
### `identify_new(self, addr, label)`

Uses the newer UDS-style identification sequence on CAN: diagnostic version ([22F1A0](diagnostic_requests.md#22f1a0)), supplier ([22F18A](diagnostic_requests.md#22f18a)), software number ([22F194](diagnostic_requests.md#22f194)), and software version ([22F195](diagnostic_requests.md#22f195)). When all required data is available, it delegates matching to [check_ecu2](ecu_scanner.md#check-ecu2-self-diagversion-supplier-soft-version-label-addr-protocol).

```mermaid
flowchart TD
    A([Start]) --> B[Initialize parsed fields]
    B --> C{Simulation mode?}
    C -- No --> D[Start CAN session 1003]
    D --> E{Session started?}
    E -- No --> R[Return False]
    E -- Yes --> F[Request 22F1A0]
    C -- Yes --> G[Use address-specific simulated 22F1A0 response]
    F --> H{Response contains WRONG?}
    H -- Yes --> R
    H -- No --> I[Parse diagversion]
    G --> I
    I --> J{Simulation mode?}
    J -- No --> K[Request 22F18A]
    J -- Yes --> L[Use simulated supplier response]
    K --> M{Response contains WRONG?}
    M -- Yes --> R
    M -- No --> N[Decode supplier]
    L --> N
    N --> O{Simulation mode?}
    O -- No --> P[Request 22F194]
    O -- Yes --> Q[Use simulated software-number response]
    P --> S{Response contains WRONG?}
    S -- Yes --> R
    S -- No --> T[Decode soft]
    Q --> T
    T --> U{Simulation mode?}
    U -- No --> V[Request 22F195]
    U -- Yes --> W[Use simulated software-version response]
    V --> X{Response contains WRONG?}
    X -- Yes --> R
    X -- No --> Y[Decode soft_version]
    W --> Y
    Y --> Z{diagversion empty?}
    Z -- Yes --> R
    Z -- No --> AA[Call check_ecu2 as CAN]
    AA --> AB[Return True]
    R --> AC([End])
    AB --> AC
```

<a id="identify-from-frame-self-addr-can-response"></a>
### `identify_from_frame(self, addr, can_response)`

Matches an already captured CAN response without opening a diagnostic session.

```mermaid
flowchart TD
    A([Start]) --> B[Receive address and CAN response]
    B --> C[Call check_ecu with label None and protocol CAN]
    C --> D([End])
```

<a id="getnumecudb-self"></a>
### `getNumEcuDb(self)`

Returns the number of ECU database entries reported by [EcuDatabase](ecu_database.md).

```mermaid
flowchart TD
    A([Start]) --> B[Read ecu_database.numecu]
    B --> C[Return value]
    C --> D([End])
```

<a id="getnumaddr-self"></a>
### `getNumAddr(self)`

Counts unique diagnostic addresses known by the ELM address maps [elm.dnat](../elm/elm_module.md#address-tables) and [elm.dnat_ext](../elm/elm_module.md#address-tables).

```mermaid
flowchart TD
    A([Start]) --> B[Create empty count list]
    B --> C{More keys in elm.dnat?}
    C -- Yes --> D{Key already counted?}
    D -- No --> E[Append key]
    D -- Yes --> C
    E --> C
    C -- No --> F{More keys in elm.dnat_ext?}
    F -- Yes --> G{Key already counted?}
    G -- No --> H[Append key]
    G -- Yes --> F
    H --> F
    F -- No --> I[Return len(count)]
    I --> J([End])
```

<a id="check-ecu2-self-diagversion-supplier-soft-version-label-addr-protocol"></a>
### `check_ecu2(self, diagversion, supplier, soft, version, label, addr, protocol)`

Matches parsed identification fields against database targets. Exact matches are stored in [ecus](ecu_scanner.md#state); approximate matches are filtered by closest version and stored in [approximate_ecus](ecu_scanner.md#state); unmatched responses are logged.

```mermaid
flowchart TD
    A([Start]) --> B[Initialize approximate list and found flags]
    B --> C{Address in group mapping?}
    C -- Yes --> D[Use mapped ECU type]
    C -- No --> E[Use UNKNOWN ECU type]
    D --> F[Set targetNum to 0]
    E --> F
    F --> G{More database targets?}
    G -- No --> N{No exact match and approximate candidates exist?}
    G -- Yes --> H{Target protocol compatible with requested protocol?}
    H -- No --> I[Increment targetNum]
    I --> G
    H -- Yes --> J{target.checkWith matches?}
    J -- Yes --> K[Store exact target in ecus]
    K --> L[Increment num_ecu_found and update label]
    L --> M[Log green identified ECU line]
    M --> N
    J -- No --> O{target.checkApproximate matches?}
    O -- Yes --> P[Append target to approximate list and mark approximate found]
    O -- No --> I
    P --> I
    N -- Yes --> Q[Find compatible approximate target with smallest version delta]
    Q --> R{Best approximate target found?}
    R -- Yes --> S[Store target in approximate_ecus]
    S --> T[Increment num_ecu_found and update label]
    T --> U[Log blue imperfect match line]
    R -- No --> V([End])
    U --> V
    N -- No --> W{No exact and no approximate found?}
    W -- Yes --> X[Log red no relevant ECU file line]
    W -- No --> V
    X --> V
```

<a id="check-ecu-self-can-response-label-addr-protocol"></a>
### `check_ecu(self, can_response, label, addr, protocol)`

Parses a raw identification response into [diagversion](ecu_ident.md#state), [supplier](ecu_ident.md#state), [soft](ecu_ident.md#state), and [version](ecu_ident.md#state), then delegates matching to [check_ecu2](ecu_scanner.md#check-ecu2-self-diagversion-supplier-soft-version-label-addr-protocol). It supports the legacy long response layout, a DoIP-specific branch, and a shorter CAN/KWP layout.

```mermaid
flowchart TD
    A([Start]) --> B{Response length > 59?}
    B -- Yes --> C[Parse long legacy response fields]
    C --> D[Call check_ecu2]
    D --> Z([End])
    B -- No --> E{Protocol is DOIP?}
    E -- Yes --> F{Response length > 20?}
    F -- No --> G[Print minimal DoIP data message]
    F -- Yes --> H{Response starts with 61 80?}
    H -- Yes --> I[Parse DoIP response fields]
    I --> J[Call check_ecu2]
    H -- No --> K[Print unknown DoIP response format]
    J --> Z
    K --> Z
    G --> Z
    E -- No --> L{Response length > 20?}
    L -- No --> Z
    L -- Yes --> M[Try parsing short CAN/KWP response fields]
    M --> N{Parsing succeeds?}
    N -- Yes --> O[Call check_ecu2]
    N -- No --> P[Return without match]
    O --> Z
    P --> Z
```

<a id="addtarget-self-target"></a>
### `addTarget(self, target)`

Adds an [EcuIdent](ecu_ident.md)-like target directly to the exact-match dictionary using its [name](#state).

```mermaid
flowchart TD
    A([Start]) --> B[Read target.name]
    B --> C[Store target in ecus by name]
    C --> D([End])
```

## Scan Matching Summary

```mermaid
flowchart LR
    A[scan, scan_kwp, scan_doip, identify_from_frame] --> B[Raw ECU identification response]
    B --> C[check_ecu parses fields]
    C --> D[check_ecu2 compares fields with EcuDatabase targets]
    D --> E{Exact match?}
    E -- Yes --> F[Store in ecus and log green result]
    E -- No --> G{Approximate match?}
    G -- Yes --> H[Store closest version in approximate_ecus and log blue result]
    G -- No --> I[Log red no relevant ECU file result]
```
