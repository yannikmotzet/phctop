# phctop

A real-time monitoring tool for PTP Hardware Clocks (PHC) on Linux systems. Similar to `htop` for processes or `iotop` for disk I/O, `phctop` provides a live view of all PTP hardware clocks and their synchronization status.

## Features

- **Real-time monitoring** of all PTP Hardware Clock (PHC) devices
- **System clock comparison** to show offset between PHCs and system time
- **Detailed PTP information** including:
  - Protocol type (PTPv2 E2E/P2P or gPTP/802.1AS)
  - Port state (MASTER, SLAVE, LISTENING, etc.)
  - Delay mechanism (End-to-End or Peer-to-Peer)
  - Offset from master clock
  - Mean path delay
  - Timescale (TAI/UTC/ARB) with UTC offset
  - Time source (GPS, ATOMIC_CLOCK, NTP, etc.)
  - Grandmaster identity
  - Steps removed from grandmaster
- **Interface mapping** showing which network interface belongs to each PHC
- **Configurable update interval** for monitoring
- **Optional display** of interfaces without hardware timestamping support

## Requirements

### System Requirements
- Linux with kernel support for PTP (kernel 3.0+)
- Network interface card with hardware timestamping support
- Python 3.6 or higher

### Dependencies
- **linuxptp** package (provides `phc_ctl` and `pmc` commands)
  ```bash
  # Ubuntu/Debian
  sudo apt-get install linuxptp
  
  # RHEL/CentOS/Fedora
  sudo yum install linuxptp
  
  # Arch Linux
  sudo pacman -S linuxptp
  ```

- **ethtool** (usually pre-installed on most Linux distributions)

## Installation

### Install from TestPyPI (Current)

The package is currently available on TestPyPI for testing:

```bash
pip install --index-url https://test.pypi.org/simple/ phctop
```

After installation, you can run it directly:
```bash
phctop --version
phctop
```

### Install from PyPI (Coming Soon)

Once published to the main PyPI repository:

```bash
pip install phctop
```

### Install from Source

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/phctop.git
   cd phctop
   ```

2. Install using pip:
   ```bash
   pip install .
   
   # For development installation (editable mode)
   pip install -e .
   
   # With development dependencies
   pip install -e ".[dev]"
   ```

### Manual Installation (Without pip)

If you prefer to install the script directly:

1. Download `phctop.py` from the repository
2. Make it executable:
   ```bash
   chmod +x phctop.py
   ```
3. Move to system PATH (optional):
   ```bash
   sudo cp phctop.py /usr/local/bin/phctop
   ```

## Usage

### Basic Usage

```bash
# Monitor with default 1-second update interval
phctop

# Monitor with custom update interval (0.5 seconds)
phctop -i 0.5

# Show all network interfaces (including those without HW timestamping)
phctop -a

# Combine options
phctop -i 2 -a
```

### Command Line Options

```
phctop [-h] [-i INTERVAL] [-a] [--version]

Options:
  -h, --help            Show help message and exit
  -i, --interval INTERVAL
                        Update interval in seconds (default: 1.0)
  -a, --all-interfaces  Show all network interfaces, including those
                        without hardware timestamping support
  --version             Show program's version number and exit
```

### Examples

**Monitor with fast updates (500ms):**
```bash
phctop -i 0.5
```

**Monitor with slower updates (5 seconds):**
```bash
phctop -i 5
```

**Show all interfaces including software-only timestamp interfaces:**
```bash
phctop -a
```

## Output Explained

### Display Sections

1. **System Clock**
   - Shows current system time (UTC/Linux timescale)
   - Used as reference point for all PHC offsets

2. **PHC Devices**
   - Each PHC device shows:
     - Device name (PTP0, PTP1, etc.)
     - Associated network interface
     - Current time (human-readable and raw timestamp)
     - Offset from system clock in milliseconds
     - PTP protocol and configuration details
     - Synchronization status and statistics

3. **Interfaces Without Hardware Timestamping** (with `-a` flag)
   - Lists network interfaces that don't support hardware timestamps
   - Shows if PTP is running in software mode

### Example Output

```
============================================================================
phctop - PTP Hardware Clock Monitor - 2025-02-07 14:23:45
============================================================================

SYSTEM CLOCK
  Time: 2025-02-07 14:23:45.123 | Raw: 1707318225.123456789
  Timescale: UTC/Linux | Offset: 0.000 ms (reference)

────────────────────────────────────────────────────────────────────────────
PTP0                 Interface: eth0           Device: /dev/ptp0
  Time: 2025-02-07 14:23:45.125 | Raw: 1707318225.125789012
  Offset from system clock: +2.332 ms
  Protocol: PTPv2 (E2E)          Port State: SLAVE           Delay Mech: E2E
  Timescale: TAI (UTC offset: 37s) Time Source: GPS
  Offset from Master: 125.50 µs         Mean Path Delay: 45.20 µs
  Steps Removed: 1                GM Identity: 00:11:22:33:44:55:66:77
```

### Understanding the Metrics

- **Offset from system clock**: How much the PHC differs from system time
- **Port State**: 
  - `MASTER`: This clock is the time source for others
  - `SLAVE`: Synchronized to a master clock
  - `LISTENING`: Not synchronized, listening for master
  - `PASSIVE`: Backup mode
- **Offset from Master**: How far this clock is from the master (lower is better)
- **Mean Path Delay**: Network delay between this clock and master
- **Steps Removed**: How many hops away from the grandmaster clock
- **Timescale**:
  - `TAI`: International Atomic Time (no leap seconds)
  - `UTC`: Coordinated Universal Time (with leap seconds)
  - `ARB`: Arbitrary timescale

## Troubleshooting

### "phc_ctl not found"
Install the linuxptp package:
```bash
sudo apt-get install linuxptp
```

### "No PHC devices found"
- Check if your network card supports hardware timestamping:
  ```bash
  ethtool -T eth0
  ```
- Look for `SOF_TIMESTAMPING_TX_HARDWARE` and `SOF_TIMESTAMPING_RX_HARDWARE`

### Permission denied errors
Some operations may require root privileges:
```bash
sudo phctop
```

### PTP information shows "N/A"
- Make sure `ptp4l` is running on the interface
- Check if you have permission to query PTP management messages

## Use Cases

- **Time-sensitive networking**: Monitor IEEE 802.1AS (gPTP) synchronization in automotive or industrial networks
- **Financial trading systems**: Verify sub-microsecond time accuracy
- **Telecommunications**: Monitor PTP synchronization in 5G networks
- **Test labs**: Debug PTP synchronization issues
- **Data centers**: Monitor time synchronization across distributed systems

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Author

Created for monitoring PTP Hardware Clocks in precision timing applications.

**Note:** This tool was developed with assistance from Claude (Anthropic), an AI assistant. The core logic, Python implementation, and documentation were generated through collaborative AI-assisted development.

## See Also

- `ptp4l` - PTP daemon (part of linuxptp)
- `phc2sys` - Synchronize system clock to PHC
- `phc_ctl` - PHC control utility
- `pmc` - PTP management client
- `htop` - Interactive process viewer (inspiration for this tool)

## Version History

- **1.0.0** - Initial release
  - Real-time PHC monitoring
  - PTP status information
  - Interface mapping
  - Configurable update intervals