#!/usr/bin/env python3
"""
phctop - Monitor PTP Hardware Clock times with detailed PTP information
"""

import os
import subprocess
import sys
import time
import re
from datetime import datetime
from pathlib import Path


def get_system_time():
    """Get current system time and raw timestamp"""
    now = datetime.now()
    return now, time.time()


def get_phc_time_raw(phc_device):
    """Get raw time from a specific PHC device using phc_ctl"""
    try:
        result = subprocess.run(
            ['phc_ctl', phc_device, 'get'],
            capture_output=True,
            text=True,
            timeout=2
        )

        if result.returncode == 0:
            output = result.stdout.strip()
            match = re.search(r'clock time is (\d+\.\d+)', output)
            if match:
                return match.group(1)  # Return as string to preserve precision
        elif 'Permission denied' in result.stderr or 'Operation not permitted' in result.stderr:
            return 'EPERM'
        return None
    except (subprocess.TimeoutExpired, subprocess.CalledProcessError, ValueError, FileNotFoundError):
        return None


def get_phc_for_interface(interface):
    """Find which PHC device corresponds to a network interface"""
    try:
        ptp_path = Path(f'/sys/class/net/{interface}/device/ptp')
        if ptp_path.exists():
            entries = [e for e in ptp_path.iterdir() if e.name.startswith('ptp')]
            if entries:
                return f"/dev/{entries[0].name}"
        return None
    except:
        return None


def get_interface_for_phc(phc_num):
    """Find which network interface corresponds to a PHC"""
    try:
        net_path = Path(f'/sys/class/ptp/ptp{phc_num}/device/net')
        if net_path.exists():
            entries = list(net_path.iterdir())
            if entries:
                return entries[0].name
        return None
    except:
        return None


def check_hw_timestamp_support(interface):
    """Check if interface supports hardware timestamping using ethtool"""
    try:
        result = subprocess.run(
            ['ethtool', '-T', interface],
            capture_output=True,
            text=True,
            timeout=2
        )
        
        if result.returncode == 0:
            output = result.stdout
            # Check if hardware timestamping is supported
            if 'SOF_TIMESTAMPING_TX_HARDWARE' in output or 'hardware-transmit' in output.lower():
                return True
        return False
    except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
        return False


def get_all_network_interfaces():
    """Get all network interfaces"""
    interfaces = []
    try:
        net_path = Path('/sys/class/net')
        if not net_path.exists():
            return interfaces
        
        for iface in sorted(net_path.iterdir()):
            if iface.is_dir():
                iface_name = iface.name
                # Skip loopback and virtual interfaces if desired
                if iface_name != 'lo':
                    interfaces.append(iface_name)
        return interfaces
    except:
        return interfaces


def run_pmc_command(command, interface=None):
    """Run a pmc command and return the output"""
    try:
        cmd = ['pmc', '-u', '-b', '0']
        if interface:
            cmd.extend(['-i', interface])
        cmd.append(command)
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=2
        )
        
        if result.returncode == 0:
            return result.stdout
        return None
    except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
        return None


def parse_pmc_output(output, key):
    """Parse PMC output for a specific key"""
    if not output:
        return None
    
    pattern = rf'{key}\s+(.+?)(?:\n|$)'
    match = re.search(pattern, output)
    if match:
        return match.group(1).strip()
    return None


def get_ptp_info(interface):
    """Get detailed PTP information for an interface"""
    info = {
        'protocol': 'N/A',
        'port_state': 'N/A',
        'delay_mechanism': 'N/A',
        'mean_path_delay': 'N/A',
        'offset_from_master': 'N/A',
        'gm_identity': 'N/A',
        'time_source': 'N/A',
        'timescale': 'N/A',
        'steps_removed': 'N/A',
        'utc_offset': None,
    }
    
    if not interface:
        return info
    
    # Get CURRENT_DATA_SET
    current_data = run_pmc_command('GET CURRENT_DATA_SET', interface)
    if current_data:
        offset = parse_pmc_output(current_data, 'offsetFromMaster')
        if offset:
            info['offset_from_master'] = offset
        
        mpd = parse_pmc_output(current_data, 'meanPathDelay')
        if mpd:
            info['mean_path_delay'] = mpd
        
        steps = parse_pmc_output(current_data, 'stepsRemoved')
        if steps:
            info['steps_removed'] = steps
    
    # Get PORT_DATA_SET
    port_data = run_pmc_command('GET PORT_DATA_SET', interface)
    if port_data:
        port_state = parse_pmc_output(port_data, 'portState')
        if port_state:
            info['port_state'] = port_state
        
        delay_mech = parse_pmc_output(port_data, 'delayMechanism')
        if delay_mech:
            # Map delay mechanism codes
            delay_map = {
                '1': 'E2E',
                '2': 'P2P',
                'E2E': 'E2E',
                'P2P': 'P2P',
            }
            info['delay_mechanism'] = delay_map.get(delay_mech, delay_mech)
    
    # Get PARENT_DATA_SET for grandmaster info
    parent_data = run_pmc_command('GET PARENT_DATA_SET', interface)
    if parent_data:
        gm_id = parse_pmc_output(parent_data, 'grandmasterIdentity')
        if gm_id:
            info['gm_identity'] = gm_id
    
    # Get TIME_PROPERTIES_DATA_SET
    time_props = run_pmc_command('GET TIME_PROPERTIES_DATA_SET', interface)
    if time_props:
        time_source = parse_pmc_output(time_props, 'timeSource')
        if time_source:
            # Map time source codes to readable names
            source_map = {
                '0x10': 'ATOMIC_CLOCK',
                '0x20': 'GPS',
                '0x30': 'TERRESTRIAL_RADIO',
                '0x39': 'PTP',
                '0x40': 'NTP',
                '0x50': 'HAND_SET',
                '0x60': 'OTHER',
                '0x90': 'INT_OSC',
                '16': 'ATOMIC_CLOCK',
                '32': 'GPS',
                '48': 'TERRESTRIAL_RADIO',
                '57': 'PTP',
                '64': 'NTP',
                '80': 'HAND_SET',
                '96': 'OTHER',
                '144': 'INT_OSC',
            }
            info['time_source'] = source_map.get(time_source, time_source)
        
        # Check for PTP timescale (0 = ARB, 1 = PTP which follows TAI)
        ptp_timescale = parse_pmc_output(time_props, 'ptpTimescale')
        current_utc_offset = parse_pmc_output(time_props, 'currentUtcOffset')
        
        if current_utc_offset:
            try:
                info['utc_offset'] = int(current_utc_offset)
            except:
                pass
        
        if ptp_timescale == '1':
            info['timescale'] = f'TAI (UTC offset: {current_utc_offset}s)' if current_utc_offset else 'TAI'
        elif ptp_timescale == '0':
            info['timescale'] = 'ARB'
        else:
            info['timescale'] = 'Unknown'
    
    # Determine protocol based on configuration or port state
    # Check if ptp4l is running with gPTP profile
    try:
        result = subprocess.run(
            ['ps', 'aux'],
            capture_output=True,
            text=True,
            timeout=1
        )
        if f'-i {interface}' in result.stdout or interface in result.stdout:
            if '-P' in result.stdout or 'automotive' in result.stdout:
                info['protocol'] = 'gPTP (802.1AS)'
            else:
                info['protocol'] = f'PTPv2 ({info["delay_mechanism"]})'
    except:
        info['protocol'] = f'PTPv2 ({info["delay_mechanism"]})'
    
    return info


def find_all_phcs():
    """Find all available PHC devices"""
    phc_devices = []
    ptp_path = Path('/dev')
    
    for device in sorted(ptp_path.glob('ptp*')):
        phc_devices.append(str(device))
    
    return phc_devices


def format_ns_to_readable(ns_str):
    """Convert nanoseconds string to readable format"""
    try:
        ns = int(ns_str)
        if abs(ns) < 1000:
            return f"{ns} ns"
        elif abs(ns) < 1000000:
            return f"{ns/1000:.2f} µs"
        else:
            return f"{ns/1000000:.3f} ms"
    except:
        return ns_str


def timestamp_to_human(timestamp_str):
    """Convert timestamp string to human-readable format"""
    try:
        timestamp = float(timestamp_str)
        dt = datetime.fromtimestamp(timestamp)
        return dt.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
    except:
        return "Invalid"


def calculate_offset_ms(ts1_str, ts2_str):
    """Calculate offset in milliseconds between two timestamps"""
    try:
        ts1 = float(ts1_str)
        ts2 = float(ts2_str)
        return (ts1 - ts2) * 1000
    except:
        return None


def display_times(interval=1, show_all_interfaces=False):
    """Display all PHC times and system time with detailed PTP info"""

    # Check if required tools are available
    try:
        subprocess.run(['phc_ctl'], capture_output=True)
    except FileNotFoundError:
        print("Error: phc_ctl not found. Please install linuxptp package.", file=sys.stderr)
        sys.exit(1)

    try:
        subprocess.run(['pmc'], capture_output=True)
    except FileNotFoundError:
        print("Warning: pmc not found. Detailed PTP info will not be available.", file=sys.stderr)
        time.sleep(2)

    iteration = 0
    first_run = True
    last_line_count = 0

    try:
        while True:
            if not first_run:
                sys.stdout.write('\033[H')
            else:
                sys.stdout.write('\033[2J\033[H')  # clear screen on first run
                first_run = False

            cols = os.get_terminal_size().columns

            output_lines = []
            output_lines.append('phctop - PTP Hardware Clock Monitor')
            output_lines.append('─' * cols)

            # Column widths
            w_dev, w_iface, w_time, w_raw, w_offset = 10, 12, 26, 22, 16

            header = f"  {'DEVICE':<{w_dev}} {'INTERFACE':<{w_iface}} {'TIME':<{w_time}} {'RAW':<{w_raw}} {'SYS OFFSET':<{w_offset}}"
            output_lines.append(header)
            output_lines.append('─' * cols)

            # System time row
            system_dt, system_ts_raw = get_system_time()
            system_ts_str = f"{system_ts_raw:.9f}"
            system_human = system_dt.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
            output_lines.append(f"  {'system':<{w_dev}} {'-':<{w_iface}} {system_human:<{w_time}} {system_ts_str:<{w_raw}} {'reference':<{w_offset}}")

            # Find all PHCs
            phc_devices = find_all_phcs()
            all_interfaces = get_all_network_interfaces()
            shown_interfaces = set()

            if not phc_devices and not show_all_interfaces:
                output_lines.append("\n  No PHC devices found in /dev/ptp*")
            else:
                for phc_device in phc_devices:
                    phc_name = Path(phc_device).name
                    phc_num = phc_name.replace('ptp', '')
                    interface = get_interface_for_phc(phc_num)

                    if interface:
                        shown_interfaces.add(interface)

                    phc_timestamp_str = get_phc_time_raw(phc_device)
                    ptp_info = get_ptp_info(interface) if interface else None

                    if phc_timestamp_str == 'EPERM':
                        time_col, raw_col, offset_col = 'permission denied', '-', '-'
                    elif phc_timestamp_str:
                        time_col = timestamp_to_human(phc_timestamp_str)
                        raw_col = phc_timestamp_str
                        offset_ms = calculate_offset_ms(phc_timestamp_str, system_ts_str)
                        offset_col = f"{offset_ms:+.3f} ms" if offset_ms is not None else '-'
                    else:
                        time_col, raw_col, offset_col = 'unavailable', '-', '-'

                    output_lines.append(f"  {phc_name:<{w_dev}} {(interface or 'N/A'):<{w_iface}} {time_col:<{w_time}} {raw_col:<{w_raw}} {offset_col:<{w_offset}}")

                    # PTP daemon details (only when data is available)
                    if ptp_info:
                        if ptp_info['port_state'] != 'N/A':
                            output_lines.append(f"    Protocol: {ptp_info['protocol']}  Port State: {ptp_info['port_state']}  Delay: {ptp_info['delay_mechanism']}")
                        if ptp_info['offset_from_master'] != 'N/A' or ptp_info['mean_path_delay'] != 'N/A':
                            output_lines.append(f"    Master offset: {format_ns_to_readable(ptp_info['offset_from_master'])}  Path delay: {format_ns_to_readable(ptp_info['mean_path_delay'])}")
                        if ptp_info['gm_identity'] != 'N/A':
                            output_lines.append(f"    GM: {ptp_info['gm_identity']}  Steps: {ptp_info['steps_removed']}  Timescale: {ptp_info['timescale']}  Source: {ptp_info['time_source']}")

                if show_all_interfaces:
                    non_hw = [i for i in all_interfaces if i not in shown_interfaces]
                    if non_hw:
                        output_lines.append('─' * cols)
                        output_lines.append(f"  {'(no PHC)':<{w_dev}} {'INTERFACE':<{w_iface}} software timestamps only")
                        for iface in non_hw:
                            ptp_info = get_ptp_info(iface)
                            state = ptp_info['port_state'] if ptp_info and ptp_info['port_state'] != 'N/A' else '-'
                            output_lines.append(f"  {'-':<{w_dev}} {iface:<{w_iface}} {'-':<{w_time}} port state: {state}")

            output_lines.append('─' * cols)
            output_lines.append(f"  interval: {interval}s | Ctrl+C to exit")

            sys.stdout.write('\033[J')
            for line in output_lines:
                print(line)
            sys.stdout.flush()
            last_line_count = len(output_lines)

            iteration += 1
            time.sleep(interval)

    except KeyboardInterrupt:
        sys.stdout.write(f'\033[{last_line_count + 1};1H\n')
        sys.exit(0)


def check_phc_permissions():
    """Return True if we can read PHC devices, False if permission denied"""
    devices = sorted(Path('/dev').glob('ptp*'))
    if not devices:
        return True  # No devices — not a permissions issue
    return os.access(str(devices[0]), os.R_OK | os.W_OK)


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description='phctop - Monitor PTP Hardware Clocks in real-time',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s              Update display every second (default)
  %(prog)s -i 0.5       Update every 500ms
  %(prog)s -i 2         Update every 2 seconds
  %(prog)s -a           Show all interfaces including those without HW timestamping

Displays:
  - PHC device name and path (/dev/ptpX)
  - Network interface mapping
  - Human-readable time and raw timestamp
  - Offset from system clock
  - PTP protocol (PTPv2 E2E/P2P or gPTP)
  - Port state (MASTER, SLAVE, LISTENING, etc.)
  - Delay mechanism (E2E or P2P)
  - Offset from master and mean path delay
  - Timescale (TAI/UTC/ARB) with UTC offset
  - Time source (GPS, ATOMIC_CLOCK, NTP, etc.)
  - Grandmaster identity
  - Steps removed from grandmaster
  - Interfaces without hardware timestamping support (with -a flag)

Requirements:
  - linuxptp package (for phc_ctl and pmc commands)
  - Root/sudo privileges may be required for some operations
        """
    )
    
    parser.add_argument(
        '-i', '--interval',
        type=float,
        default=1.0,
        help='Update interval in seconds (default: 1.0)'
    )
    
    parser.add_argument(
        '-a', '--all-interfaces',
        action='store_true',
        help='Show all network interfaces, including those without hardware timestamping support'
    )
    
    parser.add_argument(
        '--version',
        action='version',
        version='phctop 1.0.0'
    )
    
    args = parser.parse_args()

    if args.interval <= 0:
        print("Error: Interval must be greater than 0", file=sys.stderr)
        sys.exit(1)

    # Re-exec with sudo if PHC devices exist but aren't readable
    if os.geteuid() != 0 and not check_phc_permissions():
        print("Insufficient permissions to read PHC devices. Re-running with sudo...")
        script = os.path.abspath(sys.argv[0])
        os.execvp('sudo', ['sudo', sys.executable, script] + sys.argv[1:])

    display_times(interval=args.interval, show_all_interfaces=args.all_interfaces)


if __name__ == '__main__':
    main()