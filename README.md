# phctop

A real-time monitoring tool for PTP Hardware Clocks (PHC) on Linux systems. Similar to `htop` for processes, `phctop` provides a live table view of all PTP hardware clocks and their synchronization status.

## Example output

```
phctop - PTP Hardware Clock Monitor
────────────────────────────────────────────────────────────────────────────────
  DEVICE     INTERFACE    TIME                       RAW                    SYS OFFSET
────────────────────────────────────────────────────────────────────────────────
  system     -            2026-03-26 22:16:07.560    1774559767.560114800   reference
  ptp0       enp4s0       2026-03-26 22:16:07.421    1774559767.421293847   -1140.396 ms
    Master offset: 125.50 µs  Path delay: 45.20 µs
    GM: 00:11:22:ff:fe:33:44:55  Steps: 1  Timescale: TAI (UTC offset: 37s)  Source: GPS
────────────────────────────────────────────────────────────────────────────────
  interval: 1s | Ctrl+C to exit
```

## Features

- Live table view of all PHC devices alongside the system clock
- Interface mapping via `/sys/class/ptp` sysfs
- Raw and human-readable timestamps
- Offset from system clock
- PTP daemon details (port state, master offset, path delay, grandmaster identity) when `ptp4l` is running
- Auto-escalates to sudo if `/dev/ptp*` devices are not readable
- Adapts to terminal width
- Optional view of interfaces without hardware timestamping (`-a`)

## Requirements

- Linux kernel 3.0+ with PTP support
- Python 3.6+
- **linuxptp** package (`phc_ctl` and `pmc`):
  ```bash
  sudo apt-get install linuxptp   # Ubuntu/Debian
  sudo yum install linuxptp       # RHEL/CentOS/Fedora
  sudo pacman -S linuxptp         # Arch Linux
  ```

## Permissions

`phctop` requires read access to `/dev/ptp*`. If not running as root it will auto-escalate via sudo. To avoid needing sudo every time, add your user to the `ptp` group:

```bash
sudo usermod -aG ptp $USER
# log out and back in for the change to take effect
```

## Installation

```bash
# From TestPyPI
pip install --index-url https://test.pypi.org/simple/ phctop

# From source
git clone https://github.com/yourusername/phctop.git
cd phctop
pip install .
```

## Usage

```bash
phctop                # update every second (default)
phctop -i 0.5         # update every 500ms
phctop -a             # include interfaces without HW timestamping
phctop -i 2 -a        # combine options
```

### Options

| Option | Description |
|--------|-------------|
| `-i`, `--interval` | Update interval in seconds (default: 1.0) |
| `-a`, `--all-interfaces` | Show interfaces without hardware timestamping support |
| `--version` | Show version |

## Understanding the output

| Column | Description |
|--------|-------------|
| DEVICE | PHC device name (`ptp0`, `ptp1`, …) |
| INTERFACE | Network interface mapped to this PHC |
| TIME | Human-readable clock time |
| RAW | Raw Unix timestamp (nanosecond precision) |
| SYS OFFSET | Difference between this clock and the system clock |

PTP daemon details (indented below each device) are only shown when `ptp4l` is running:

- **Master offset** — how far this clock is from the master (lower is better)
- **Path delay** — network delay between this clock and the master
- **GM** — grandmaster identity and steps removed
- **Timescale / Source** — TAI/UTC/ARB and time source (GPS, NTP, etc.)

## Troubleshooting

**`phc_ctl` not found** — install the linuxptp package (see Requirements).

**No PHC devices found** — check if your NIC supports hardware timestamping:
```bash
ethtool -T eth0
# look for SOF_TIMESTAMPING_TX_HARDWARE
```

**PTP details show nothing** — `ptp4l` is probably not running on the interface.

## See also

- `ptp4l` — PTP daemon
- `phc2sys` — synchronize system clock to PHC
- `phc_ctl` — PHC control utility
- `pmc` — PTP management client
