# DeviceManager, In Simple English

Source: `src/ddt4all/core/elm/device_manager.py`

`DeviceManager` is one part of the core code. This version uses simple English. It keeps the same meaning as the normal document, but uses shorter sentences.

## Table Of Contents

- [Method Reference And Flowcharts](#method-reference-and-flowcharts)
- [Initialization Functions](#initialization-functions)
  - [`initialize_device(elm_instance, device_type=None)`](#initialize-device-elm-instance-device-type-none)
- [Main Functions](#main-functions)
  - [`normalize_adapter_type(adapter_type)`](#normalize-adapter-type-adapter-type)
  - [`enable_enhanced_features(elm_instance, device_type)`](#enable-enhanced-features-elm-instance-device-type)
  - [`detect_device_type(elm_instance)`](#detect-device-type-elm-instance)
- [Auxiliary Functions](#auxiliary-functions)
  - [`get_optimal_settings(device_type)`](#get-optimal-settings-device-type)
  - [`_swap_vgate_pins(elm_instance)`](#swap-vgate-pins-elm-instance)
  - [`_swap_usbcan_pins(elm_instance)`](#swap-usbcan-pins-elm-instance)
  - [`_swap_obdlink_pins(elm_instance)`](#swap-obdlink-pins-elm-instance)
  - [`_swap_els27_pins(elm_instance)`](#swap-els27-pins-elm-instance)
  - [`_swap_derlek_diag3_pins(elm_instance)`](#swap-derlek-diag3-pins-elm-instance)
  - [`_swap_derlek_diag2_pins(elm_instance)`](#swap-derlek-diag2-pins-elm-instance)
  - [`_enable_stpx_mode(elm_instance)`](#enable-stpx-mode-elm-instance)
  - [`_auto_swap_pins(elm_instance, device_type)`](#auto-swap-pins-elm-instance-device-type)
- [Flow Summary](#flow-summary)

## Other Code Used By This Class

- `Port`: handles low-level serial, Bluetooth, WiFi, or DoIP transport when used by ELM.
- `options`: provides runtime flags and adapter settings.
- `DeviceManager`: applies adapter-specific settings for supported devices.

## Method Reference And Flowcharts

<a id="initialization-functions"></a>
## Initialization Functions

<a id="initialize-device-elm-instance-device-type-none"></a>
### `initialize_device(elm_instance, device_type=None)`

Complete device initialization with enhanced features

```mermaid
flowchart TD
    A([Start]) --> B[Prepare connection settings]
    B --> C[Open or configure device]
    C --> D{Setup succeeded?}
    D -- Yes --> E[Store connected state and return True]
    D -- No --> F[Store failed state and return False]
    E --> G([End])
    F --> G
```

<a id="main-functions"></a>
## Main Functions

<a id="normalize-adapter-type-adapter-type"></a>
### `normalize_adapter_type(adapter_type)`

Normalize UI adapter types to internal device types

```mermaid
flowchart TD
    A([Start]) --> B[Run method logic]
    B --> C{Operation succeeds?}
    C -- Yes --> D[Return normal result]
    C -- No --> E[Return fallback or raise error]
    D --> F([End])
    E --> F
```

<a id="enable-enhanced-features-elm-instance-device-type"></a>
### `enable_enhanced_features(elm_instance, device_type)`

Enable enhanced features based on device type

```mermaid
flowchart TD
    A([Start]) --> B[Prepare adapter-specific commands]
    B --> C[Run commands in order]
    C --> D{All commands worked?}
    D -- Yes --> E[Return True]
    D -- No --> F[Print warning and return False]
    E --> G([End])
    F --> G
```

<a id="detect-device-type-elm-instance"></a>
### `detect_device_type(elm_instance)`

Auto-detect device type from ELM responses

```mermaid
flowchart TD
    A([Start]) --> B[Run method logic]
    B --> C{Operation succeeds?}
    C -- Yes --> D[Return normal result]
    C -- No --> E[Return fallback or raise error]
    D --> F([End])
    E --> F
```

<a id="auxiliary-functions"></a>
## Auxiliary Functions

<a id="get-optimal-settings-device-type"></a>
### `get_optimal_settings(device_type)`

Get optimal connection settings for specific device types

```mermaid
flowchart TD
    A([Start]) --> B[Read requested value or device data]
    B --> C{Read succeeds?}
    C -- Yes --> D[Return value]
    C -- No --> E[Return fallback or empty value]
    D --> F([End])
    E --> F
```

<a id="swap-vgate-pins-elm-instance"></a>
### `_swap_vgate_pins(elm_instance)`

Swap pins for VGate adapters using STN protocol

```mermaid
flowchart TD
    A([Start]) --> B[Prepare adapter-specific commands]
    B --> C[Run commands in order]
    C --> D{All commands worked?}
    D -- Yes --> E[Return True]
    D -- No --> F[Print warning and return False]
    E --> G([End])
    F --> G
```

<a id="swap-usbcan-pins-elm-instance"></a>
### `_swap_usbcan_pins(elm_instance)`

Swap pins for USB CAN adapters

```mermaid
flowchart TD
    A([Start]) --> B[Prepare adapter-specific commands]
    B --> C[Run commands in order]
    C --> D{All commands worked?}
    D -- Yes --> E[Return True]
    D -- No --> F[Print warning and return False]
    E --> G([End])
    F --> G
```

<a id="swap-obdlink-pins-elm-instance"></a>
### `_swap_obdlink_pins(elm_instance)`

Swap pins for OBDLink adapters

```mermaid
flowchart TD
    A([Start]) --> B[Prepare adapter-specific commands]
    B --> C[Run commands in order]
    C --> D{All commands worked?}
    D -- Yes --> E[Return True]
    D -- No --> F[Print warning and return False]
    E --> G([End])
    F --> G
```

<a id="swap-els27-pins-elm-instance"></a>
### `_swap_els27_pins(elm_instance)`

Swap pins for ELS27 adapters

```mermaid
flowchart TD
    A([Start]) --> B[Prepare adapter-specific commands]
    B --> C[Run commands in order]
    C --> D{All commands worked?}
    D -- Yes --> E[Return True]
    D -- No --> F[Print warning and return False]
    E --> G([End])
    F --> G
```

<a id="swap-derlek-diag3-pins-elm-instance"></a>
### `_swap_derlek_diag3_pins(elm_instance)`

Swap pins for DerleK USB-DIAG3 adapters

```mermaid
flowchart TD
    A([Start]) --> B[Prepare adapter-specific commands]
    B --> C[Run commands in order]
    C --> D{All commands worked?}
    D -- Yes --> E[Return True]
    D -- No --> F[Print warning and return False]
    E --> G([End])
    F --> G
```

<a id="swap-derlek-diag2-pins-elm-instance"></a>
### `_swap_derlek_diag2_pins(elm_instance)`

Swap pins for DerleK USB-DIAG2 adapters

```mermaid
flowchart TD
    A([Start]) --> B[Prepare adapter-specific commands]
    B --> C[Run commands in order]
    C --> D{All commands worked?}
    D -- Yes --> E[Return True]
    D -- No --> F[Print warning and return False]
    E --> G([End])
    F --> G
```

<a id="enable-stpx-mode-elm-instance"></a>
### `_enable_stpx_mode(elm_instance)`

Enable STPX mode for enhanced long command support

```mermaid
flowchart TD
    A([Start]) --> B[Prepare adapter-specific commands]
    B --> C[Run commands in order]
    C --> D{All commands worked?}
    D -- Yes --> E[Return True]
    D -- No --> F[Print warning and return False]
    E --> G([End])
    F --> G
```

<a id="auto-swap-pins-elm-instance-device-type"></a>
### `_auto_swap_pins(elm_instance, device_type)`

Auto-swap pins based on device type

```mermaid
flowchart TD
    A([Start]) --> B[Run method logic]
    B --> C{Operation succeeds?}
    C -- Yes --> D[Return normal result]
    C -- No --> E[Return fallback or raise error]
    D --> F([End])
    E --> F
```

## Flow Summary

This is the short version of how `DeviceManager` is used.

```mermaid
flowchart LR
    A[Create object] --> B[Run method]
    B --> C[Update state or return value]
```
