# DDT4ALL（简体中文说明）

[![Build](https://github.com/cedricp/ddt4all/actions/workflows/python-app.yml/badge.svg)](https://github.com/cedricp/ddt4all/actions/workflows/python-app.yml)
[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-GPL%203.0-green.svg)](https://opensource.org/licenses/GPL-3.0)

DDT4ALL 是一款用于 CAN 总线车辆网络的跨平台诊断软件。它支持创建自定义 ECU 参数界面，并可通过 ELM327、Vlinker FS、VGate iCar Pro、OBDLink SX/EX、ELS27 等 OBD-II 适配器与 ECU 通信。

- **当前版本：** `v3.1.3`（Celestial Nemean）
- **许可证：** [GPL-3.0-or-later](https://opensource.org/licenses/GPL-3.0)
- 英文原文：[README.md](README.md)

---

## 警告

- 本软件仍在持续开发中。只有完全了解相关操作时才应使用**专家模式**。
- 在非专家模式下，本工具设计为不会对车辆造成影响；请保持专家模式按钮处于未启用状态。
- **如果不了解 CAN 网络或 ECU 的工作原理，请勿使用本软件。** 对实车操作可能造成严重损坏。
- 本软件仅用于维护、测试和研究。作者不对任何使用后果负责；**风险由您自行承担。**

---

## 功能

- **诊断：** 读取/清除 DTC、手动发送 ECU 请求、自动扫描 ECU、实时监测参数。
- **界面：** 自定义 ECU 参数界面设计器、屏幕录制器和数据编辑器。
- **网络：** 支持 CAN 总线嗅探（实时非阻塞采集）、DoIP 和 KWP2000。
- **数据库：** XML + ZIP（自动处理 `ecu.zip`）、内部 JSON 转换和图形资源提取。
- **自动化：** 车辆专用流程插件，以及可扩展的 Python 命令行界面。
- **国际化：** 15 种语言的 gettext/polib 目录，支持实时切换和 HTML 字符串。

---

## 支持的设备

| 设备 | 可用速率 | 默认波特率 | 超时 | 流控 | 类别 | 说明 |
|------|----------|-----------:|------|------|------|------|
| VLinker FS | 57600、115200 | 38400 | 3 秒 | 无 | 增强型 | 稳定性和兼容性最佳 |
| VGate iCar Pro | 115200、230400、500000、1000000 | 115200 | 2 秒 | 无 | 增强型 | 高速（最高 1,000,000 bps） |
| ELM327（原厂） | 标准 | 38400 | 5 秒 | 无 | 通用 | 通常标注为 `PIC18F25K80` |
| ELM327（克隆） | 标准 | 9600–38400 | 5 秒 | 无 | 经济型 | 可尝试不同波特率 |
| ELM327 USB | 标准 | 38400 | 5 秒 | 无 | USB | 专用 ELM327 USB（`STD_USB`） |
| OBDLink SX | 500k / 1M / 2M | 115200 | 2 秒 | RTS/CTS | 专业型 | 最高速度适配器 |
| OBDLink EX | 500k / 1M / 2M | 115200 | 2 秒 | RTS/CTS | 专业型 | 已测试确认 |
| ELS27 | 标准 | 38400 | 4 秒 | 无 | 替代型 | ELM327 的良好替代品 |
| ELS27 V5 | 标准 | 38400 | 4 秒 | 无 | 增强型 | CAN 使用 12、13 脚；兼容 PyRen / Renolink |
| DERLEK USB-DIAG2/3 | 标准 | 38400 | 4 秒 | 无 | 专业型 | 自动交换引脚，支持 STN/STPX* |
| USB CAN | 不定 | 38400 | 5 秒 | 无 | 专用 | 自动检测/回退 |

> \* DERLEK USB-DIAG2/3 尚未在真实硬件上完成验证。

### 连接方式

- **USB：** 推荐用于诊断；通过 COM/LPT 串口连接。
- **蓝牙：** 使用方便，但偶尔可能断连。
- **WiFi：** 使用 TCP/IP，格式为 `IP:PORT`，例如 `192.168.0.10:35000`。

多数适配器会作为标准串口出现。专用 USB-CAN / USB-ELM327 设备由软件原生处理，并具备自动回退机制。

---

## 语言支持

gettext 翻译目录保存在 `locales/`，并编译到 `src/ddt4all/generated/locales/`。英语为源语言（即 `msgid`）。已包含法语、葡萄牙语、德语、西班牙语、意大利语、俄语、波兰语、荷兰语、匈牙利语、罗马尼亚语、塞尔维亚语、土耳其语、捷克语、乌克兰语和简体中文。

所有翻译目录均应完整填写 `msgstr`、不含 `#, fuzzy` 标记，并保留原有 `%s` 和命名占位符。

`.mo` 为编译产物，故意不提交到 Git 仓库。缺少 `.mo` 时，应用会自动加载源 `.po` 翻译目录；仅在生成可发布安装包时需要执行：

```bash
python scripts/i18n.py po-to-mo
```

---

## 系统要求

- **Python** `>=3.8`（建议 3.10 或更新版本）
- **PyQt5** `>=5.15, <5.16`：图形界面
- **PyQtWebEngine** `>=5.15, <5.16`：可选，用于完整 HTML 文档视图
- **pyserial** `==3.5`：串口通信
- **pyusb** `==1.2.1`：USB 通信
- **crcmod** `==1.7`、**polib**、**platformdirs**
- **pywin32** `>=227`：仅 Windows 串口支持

## 安装

### 现代安装方式（推荐）

```bash
git clone https://github.com/cedricp/ddt4all.git
cd ddt4all
python -m venv ./venv

# 激活虚拟环境
# Windows：
.\venv\Scripts\activate.bat
# Linux / macOS：
source ./venv/bin/activate

# 安装包（开发时使用可编辑模式）
pip install -e .

# 启动应用
ddt4all
# 或者
python -m ddt4all
```

### 安装可选功能

```bash
pip install -e ".[dev]"                    # pytest、代码检查
pip install -e ".[can]"                    # python-can、obd
pip install -e ".[network]"                # requests、websockets
pip install -e ".[bluetooth]"              # pybluez / bleak
# 全部安装：
pip install -e ".[dev,can,network,bluetooth]"
```

### 旧式安装方式（手动安装依赖）

```bash
pip install "PyQt5>=5.15,<5.16" "PyQtWebEngine>=5.15,<5.16" pyserial==3.5 pyusb==1.2.1 crcmod==1.7 polib platformdirs
```

---

## 平台说明

- **Linux：** 将当前用户加入 `dialout` 组以访问串口：
  ```bash
  sudo usermod -a -G dialout $USER
  # 注销并重新登录
  ```
- **Windows：** 请确认已安装串口/USB 驱动且适配器已分配 COM 端口。端口访问失败时，请使用管理员权限运行。
- **macOS：** 若 `pip install -e .` 报可编辑安装错误，请先更新打包工具：
  ```bash
  python3 -m pip install --upgrade pip setuptools wheel
  python3 -m pip install -e .
  ```
  若运行时缺少包数据（`resources/projects.json not found`），请在仓库根目录重新安装：
  ```bash
  python3 -m pip install --force-reinstall -e .
  ```

## 快速开始

```bash
# 安装成功后
ddt4all
# 或在开发模式下从源码启动：
python -m ddt4all
```

使用内置**连接测试**功能，让 DDT4ALL 自动检测适配器和正确的波特率。检测完成后会自动应用最佳设备配置。

### 快捷命令/别名（可选）

```bash
# Linux / macOS
alias ddt4all-dev='cd /path/to/ddt4all && source ./venv/bin/activate && python -m ddt4all'
# Windows（PowerShell）
Set-Alias -Name ddt4all -Value "ddt4all"
```

## 插件系统

车辆专用流程以 Python 模块形式存放于 `src/ddt4all/plugins/`：

- `ab90_reset.py`：AB90 安全气囊复位
- `card_programming.py`：ECU 卡片编程
- `clio3_eps_reset.py`、`clio4_eps_reset.py`：Clio 3/4 EPS 复位
- `laguna2_uch_reset.py`、`laguna3_uch_reset.py`：Laguna 2/3 UCH 工具
- `megane2_uch_reset.py`、`megane3_uch_reset.py`：Megane 2/3 UCH 工具
- `megane3_ab_reset.py`：Megane 3 安全气囊复位
- `megane3_eps_reset.py`：Megane 3 EPS 工具
- `rsat4_reset.py`：RSAT4 系统复位
- `vin_crc.py`：VIN CRC 计算
- `zoe_waterpump_counter_reset.py`：ZOE 水泵计数复位

该插件架构允许为其他 ECU 与品牌扩展自定义流程。

---

## 架构

### 核心模块

- `src/ddt4all/main.py`：入口（PyQt 图形界面与连接处理）
- `src/ddt4all/version.py`：版本、代号与贡献者
- `src/ddt4all/options.py`：配置与设备设置持久化
- `src/ddt4all/file_manager.py`：文件和目录工具
- `src/ddt4all/cli/`：命令行处理程序（DoIP、参数、USB 设备）

### 通信

- `core/elm/`：ELM327/适配器通信
- `core/ecu/`：ECU 数据库、文件和扫描
- `core/doip/`：DoIP（基于 IP 的诊断）协议支持
- `core/parameters/helpers.py`：参数解析和辅助工具
- `core/usbdevice/`：USB CAN 设备

### 现代界面、数据与线程

- `ui/`：主窗口、小部件和对话框；`ui/sniffer/` 提供基于 QThread 的 CAN 嗅探。
- `generated/`：编译资源和翻译目录；`resources.qrc`：Qt 资源描述文件。
- `vehicles/`：车型专用文件；`json/`：JSON 数据库；`logs/`：运行日志。
- 网络嗅探采用 QThread，ELM 层使用 `threading.Lock()` 保护串口操作，`QTimer` 用于定时刷新和连接监测。

---

## 测试

```bash
pip install -e ".[dev]"
pytest
```

测试位于 `tests/`（`unit`、`integration`、`smoke`）。GitHub Actions 工作流 `python-app.yml` 会在多个操作系统上运行测试。

## 发布/构建

- **Windows：** InnoSetup 安装器位于 `setup_tools/inno-win-setup/`。
- **macOS：** 使用 `setup_tools/mac-os/builddmg.sh` 构建 DMG。
- **Linux：** AppImage 构建脚本/工作流位于 `setup_tools/`。

发布前请运行 `python scripts/i18n.py po-to-mo` 生成翻译二进制文件。预构建安装包发布在 [Releases 页面](https://github.com/cedricp/ddt4all/releases)。

---

## 故障排除

### 连接

- **未显示串口：** 检查驱动。Linux 请确认用户属于 `dialout` 组；Windows 可尝试以管理员身份运行。
- **未检测到适配器：** 使用连接测试逐一测试 COM/USB 端口；尝试 38400、9600、115200 等波特率。
- **ELS27 V5：** 检查驱动（PyRen / Renolink），然后手动选择正确串口；设备可能显示为 `FTDI`、`CH340` 或 `CP210x`。
- **WiFi：** 使用 `IP:PORT` 格式，确保处于同一局域网且防火墙开放。

### 安装

- **缺少 PyQtWebEngine：** DDT4All 仍可运行，只是完整的网页文档视图受限。
- **Windows 串口失败：** 重新安装 `pywin32`，然后以管理员权限执行 `python -m pywin32_postinstall -install`。

## 文档、社区与贡献

- **文档和视频：** 参阅项目 [Wiki](https://github.com/cedricp/ddt4all/wiki) 与 YouTube 频道。
- **Discord：** [加入社区](https://discord.gg/cBqDh9bTHP)
- **问题反馈：** [GitHub Issues](https://github.com/cedricp/ddt4all/issues)
- **讨论：** [GitHub Discussions](https://github.com/cedricp/ddt4all/discussions)
- **报告缺陷：** 请附截图、`Logs/` 文件、标题中的 `[Bug]`、操作系统、Python 和适配器信息。
- **建议：** 请新建标题包含 `[Suggestion]` 的讨论。
- **翻译：** 在 `locales/` 下改进或添加语言目录。
- **捐赠：** 欢迎 PayPal/GitHub Sponsors 资金捐赠或 OBD-II、ECU 等硬件捐赠。

## 许可证与免责声明

本项目是 GPL-3.0-or-later 许可证下的**自由软件**。DDT4ALL 是独立、非官方的教育工具，与任何车辆或软件品牌均无关联。它仅供学习、测试和研究使用，不能替代原厂或台架诊断工具。在实车上使用的风险由您自行承担；请阅读本文开头的警告。

**祝您 CAN 总线学习愉快！** 🚗🔧
