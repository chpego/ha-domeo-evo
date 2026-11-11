# S&P DOMEO EVO for Home Assistant

<img src="https://raw.githubusercontent.com/chpego/ha-domeo-evo/main/custom_components/domeo_evo/brand/icon.png" alt="" width="96" align="right">

Read and control an **S&P DOMEO EVO** heat recovery ventilation unit (225, 315, 450; FL, RD, DHU, Sérénité) from Home Assistant, over its Modbus RTU port.

- **Local.** Through an RS485 to Modbus TCP gateway or a USB RS485 adapter. No cloud, no account.
- **Set up from the UI.** Pick the link, the model and the variant.
- **Safe by design.** It never writes the unit's own address, speed or parity, and it writes nothing until you use a command.

[Version française](README_fr.md)

> [!NOTE]
> This integration is in **beta**. The register map follows the official S&P table, and the first real units are being tested on the [HACF forum](https://forum.hacf.fr/t/vmc-s-p-domeo-evo-225-fl-via-modbus-tcp-rtu/69801). See [Known limitations](#known-limitations).

## Prerequisites

- Home Assistant **2026.10.2** or newer.
- Jumper **JP1** closed on the unit's board. With JP1 open, the unit answers readings but refuses every command. Once JP1 is closed, the unit ignores its own control panel. Cut the power before you open the unit.
- A link to the unit's RS485 terminals (A, B, GND):
  - a **gateway** (Waveshare RS485 TO ETH, Elfin EW11…) in **Modbus TCP to RTU** mode, or
  - a **USB RS485 adapter** on the Home Assistant host.
- Line settings: **19200 baud, 8 data bits, even parity, 1 stop bit**. These are the factory settings. 9600 baud or 2 stop bits, sometimes suggested elsewhere, do not work.

## Installation

[![Open your Home Assistant instance and open this repository in the Marketplace.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=chpego&repository=ha-domeo-evo&category=integration)

Or add it by hand: **Marketplace → ⋮ → Custom repositories**, add `https://github.com/chpego/ha-domeo-evo` with the type **Integration**, then download **S&P DOMEO EVO**. To get the betas, turn on the repository's **Pre-release** switch.

Without the Marketplace, copy `custom_components/domeo_evo` into your `config/custom_components/` folder and restart Home Assistant.

## Setup

[![Open your Home Assistant instance and start setting up S&P DOMEO EVO.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=domeo_evo)

Or go to **Settings → Devices & services → Add integration → S&P DOMEO EVO**, then:

1. Choose **Network** (gateway) or **Serial port** (USB adapter).
2. Enter the gateway address and port (usually 502), or the serial port.
3. Leave the unit ID at **1** unless you changed it.
4. Pick the **model** from the rating plate (225, 315 or 450) and the **variant**. The unit does not report either, and they set the airflow ranges and the humidity settings.

If you also have a YAML `modbus:` configuration for this unit, turn it off, or make sure your gateway accepts several clients (Waveshare: **multi-host**).

## Entities

| Kind | Entities |
| --- | --- |
| Sensors | Airflow, operating mode, the five air temperatures, preheater, control panel, 0-10 V input; integrated humidity (DHU, Sérénité); one sensor per AIRSENS probe (humidity, CO₂ or VOC), found automatically |
| Binary sensors | Filter replacement, defrost, motor faults, temperature probe faults, CLP contact, **Modbus control (JP1)** |
| Switches | Holiday mode, manual bypass, automatic bypass, defrost allowed |
| Buttons | Start boost, stop boost, reset filter alarm |
| Selects | Automatic mode (proportional or agile), CLP contact type |
| Numbers | Low, high and freecooling airflow (limited to the model's range), bypass thresholds, manual bypass duration, filter interval, airflow correction and offset; humidity and air-quality regulation (DHU, Sérénité) |

Some diagnostic and configuration entities are disabled by default. Enable them from the device page.

A button shows **Unknown** until you press it for the first time. That is how Home Assistant shows buttons, not an error.

## What the integration writes

Nothing, until you use a command. It never writes holding registers 40001 to 40003 (the unit's address, speed and parity): a wrong value there cuts the link at the next power cycle. It does not offer the AIRSENS ID reset (coil 9), which forgets the paired probes. It only reads the addresses the S&P table documents.

## Known limitations

Being confirmed on real units:

- **Holiday mode.** The S&P table says coil 4 is *0 = on*, and the integration follows it. A first real unit suggests the opposite. If the switch shows the opposite of what your unit does, please say so in an issue.
- **Stop boost.** The table says writing 0 stops a boost; S&P support told a user it cannot be stopped (it ends on its own). The integration sends the 0 as a multiple-register write (FC16).
- **Filter reset.** The integration writes coil 8, as the table says.

The unit reports no serial number, so Home Assistant cannot recognise it after a change of link settings: use **Reconfigure** on the integration rather than adding it again.

## Troubleshooting

| Symptom | Cause and fix |
| --- | --- |
| A repair says *jumper JP1 is open*, or commands fail with *exception 0x01* | JP1 is open. Cut the power, close JP1, power on. The **Modbus control (JP1)** entity turns on. |
| Setup says *the unit does not answer* | Wrong line settings or wiring. Check 19200 baud, 8E1, A/B not swapped, and the gateway in Modbus TCP to RTU mode. |
| The unit stopped answering after a power cut | Its parity may have been changed by a wrong YAML write to holding register 40003 (address 2). Try odd parity on the gateway, then write `2` back to that register. |
| Humidity stuck at 54 % | No humidity sensor is fitted (FL and RD units). This is what the unit reports. |
| Pre-exchanger temperature unknown | No probe is fitted there; the unit flags it as a fault. |

For a bug report, download the diagnostics (**⋮ → Download diagnostics** on the integration's card) and attach the file to an [issue](https://github.com/chpego/ha-domeo-evo/issues). The gateway address is redacted.

## How it works

The register map lives in [`domeo-evo-modbus`](custom_components/domeo_evo/domeo_evo_modbus/), a library built on [`modbus-connection`](https://home-assistant-libs.github.io/modbus-connection/). It is shipped inside the integration until it is published on PyPI. The integration borrows its link from Home Assistant's `modbus` integration, so it can share a gateway with other Modbus integrations.

## Development

```sh
python3.14 -m venv .venv && . .venv/bin/activate
pip install -r requirements_test.txt
pytest --cov
```

Releases follow [RELEASING.md](RELEASING.md).

## Disclaimer and license

Not affiliated with or endorsed by S&P (Soler & Palau) or Unelvent. Use at your own risk: commands change how your ventilation runs.

[MIT](LICENSE)
