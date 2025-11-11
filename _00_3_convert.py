import os
import csv
import re
import configparser
from collections import defaultdict
from datetime import datetime, timedelta

def load_config():
    """Загрузка конфигурации из config.ini"""
    config = configparser.ConfigParser()
    config_file = 'config.ini'
    
    if not os.path.exists(config_file):
        print("ERROR: config.ini not found! Please run run.py first to create configuration.")
        exit(1)
    
    config.read(config_file)
    
    # Получаем пути из config.ini
    raw_path = config.get('PATHS', 'raw_data')
    convert_path = config.get('PATHS', 'convert_data')
    
    return raw_path, convert_path

def get_raw_dir():
    """Получить путь к RAW данным (загружается каждый раз)"""
    raw_path, _ = load_config()
    return raw_path

def get_out_dir():
    """Получить путь к обработанным данным (загружается каждый раз)"""
    _, convert_path = load_config()
    return convert_path

def get_gap_second():
    """Получить значение gap_time из config.ini (используется как gap_second)"""
    config = configparser.ConfigParser()
    config_file = 'config.ini'
    
    if not os.path.exists(config_file):
        print("ERROR: config.ini not found! Please run run.py first to create configuration.")
        exit(1)
    
    config.read(config_file)
    gap_time = config.get('SETTINGS', 'gap_time', fallback='0')
    return int(gap_time)

# Directory paths now loaded from config.ini dynamically

def extract_frequency_from_filename(filename):
    """
    Extracts frequency from filename and formats it with dashes.
    
    Args:
        filename: String containing the filename with frequency information
        
    Returns:
        Formatted frequency string (e.g., "433-450-000") or None if not found
    """
    # Search for frequency pattern in filename (digits followed by _Hz)
    match = re.search(r'(\d+)_Hz', filename)
    if match:
        freq_str = match.group(1)
        # Format 9-digit frequency as XXX-XXX-XXX
        if len(freq_str) == 9:
            formatted = f"{freq_str[:3]}-{freq_str[3:6]}-{freq_str[6:]}"
            return formatted
        # Format 6-digit frequency as XXX-XXX
        elif len(freq_str) == 6:
            formatted = f"{freq_str[:3]}-{freq_str[3:]}"
            return formatted
        # Format other lengths by splitting into groups of 3
        else:
            formatted = '-'.join([freq_str[i:i+3] for i in range(0, len(freq_str), 3)])
            return formatted
    return None

def find_matching_decoded_file(call_events_filename, all_files):
    """
    Finds the corresponding decoded_messages.log file for a given call_events.log file.
    Matches based on date, frequency, and time (within 2 seconds tolerance).
    
    Args:
        call_events_filename: Name of the call_events.log file
        all_files: List of all files in the directory
        
    Returns:
        Name of matching decoded_messages.log file or None if not found
    """
    # Extract date, time, and frequency from call_events filename
    match = re.match(r'(\d{8})_(\d{6})\.(\d+)_(\d+)_Hz_.*_call_events\.log', call_events_filename)
    if not match:
        return None
    
    date_str = match.group(1)
    time_str = match.group(2)
    freq_str = match.group(4)
    
    # Convert time to datetime object for comparison
    base_datetime = datetime.strptime(f"{date_str}_{time_str}", "%Y%m%d_%H%M%S")
    
    # Search for decoded_messages file with similar parameters
    for filename in all_files:
        # Skip non-decoded_messages files
        if not filename.endswith('_decoded_messages.log'):
            continue
            
        # Check if frequency matches
        if f"{freq_str}_Hz" not in filename:
            continue
            
        # Extract date and time from decoded_messages filename
        decoded_match = re.match(r'(\d{8})_(\d{6})\.(\d+)_(\d+)_Hz_.*_decoded_messages\.log', filename)
        if not decoded_match:
            continue
            
        decoded_date = decoded_match.group(1)
        decoded_time = decoded_match.group(2)
        
        # Check if date matches
        if decoded_date != date_str:
            continue
            
        # Check if time difference is within 2 seconds tolerance
        decoded_datetime = datetime.strptime(f"{decoded_date}_{decoded_time}", "%Y%m%d_%H%M%S")
        time_diff = abs((decoded_datetime - base_datetime).total_seconds())
        
        if time_diff <= 2:
            return filename
    
    return None

def parse_decoded_messages(decoded_file_path):
    """
    Parses decoded_messages.log file and returns multiple indexes for better matching.
    Now includes time-range matching for entries within 5 seconds.
    Optimized with sorted time index for faster lookups.
    
    Args:
        decoded_file_path: Path to the decoded_messages.log file
        
    Returns:
        Tuple of four dictionaries for different lookup strategies
    """
    decoded_data = defaultdict(list)
    timestamp_data = defaultdict(list)
    cc_by_timestamp = defaultdict(str)
    # Store all entries with parsed datetime for time-range matching
    time_indexed_data = []
    
    try:
        with open(decoded_file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                # Skip empty lines and header lines
                if not line or line.startswith('DECODED Message Logger'):
                    continue
                
                # Pattern: 20250511 134604,PASSED,CC:1 ... FM:128128 TO:601 ...
                parts = line.split(',', 2)
                if len(parts) >= get_gap_second():
                    timestamp_str = parts[0]  # 20250511 134604
                    message = parts[2]
                    
                    # Extract Color Code (CC), From ID (FM), and To ID (TO)
                    cc_match = re.search(r'CC:(\d+)', message)
                    fm_match = re.search(r'FM:(\d+)', message)
                    to_match = re.search(r'TO:(\d+)', message)
                    
                    # If we found a CC value, store it for this timestamp
                    if cc_match:
                        cc_value = cc_match.group(1)
                        cc_by_timestamp[timestamp_str] = cc_value
                    
                    data_entry = {
                        'cc': cc_match.group(1) if cc_match else '',
                        'from': fm_match.group(1) if fm_match else '',
                        'to': to_match.group(1) if to_match else '',
                        'timestamp': timestamp_str
                    }
                    
                    # Parse timestamp for time-range matching
                    try:
                        dt = datetime.strptime(timestamp_str, "%Y%m%d %H%M%S")
                        data_entry['datetime'] = dt
                        time_indexed_data.append(data_entry)
                    except:
                        pass
                    
                    # Store in timestamp-only index
                    timestamp_data[timestamp_str].append(data_entry)
                    
                    # Store in timestamp_from index if FROM exists
                    if fm_match:
                        from_id = fm_match.group(1)
                        key = f"{timestamp_str}_{from_id}"
                        decoded_data[key].append(data_entry)
        
        # Sort time_indexed_data by datetime for potential binary search optimization
        # This makes time-range searches faster
        time_indexed_data.sort(key=lambda x: x.get('datetime', datetime.min))
                        
    except Exception as e:
        print(f"Error reading decoded_messages file: {e}")
    
    return decoded_data, timestamp_data, cc_by_timestamp, time_indexed_data

def convert_timestamp_to_decoded_format(timestamp):
    """
    Converts timestamp from call_events format to decoded_messages format.
    
    Args:
        timestamp: Timestamp string in format "2025:05:11:13:46:04"
        
    Returns:
        Formatted timestamp string "20250511 134604" or None if conversion fails
    """
    try:
        parts = timestamp.strip('"').split(':')
        if len(parts) == 6:
            date_str = f"{parts[0]}{parts[1]:0>2}{parts[2]:0>2}"
            time_str = f"{parts[3]}{parts[4]}{parts[5]}"
            return f"{date_str} {time_str}"
    except:
        pass
    return None

def find_color_code_with_time_range(decoded_data, timestamp_data, cc_by_timestamp, time_indexed_data, decoded_timestamp, from_field):
    """
    Tries multiple strategies to find the color code and TO field for a given timestamp.
    Includes time-range matching for entries within 5 seconds.
    
    Args:
        decoded_data: Dictionary with timestamp_from as keys
        timestamp_data: Dictionary with timestamp only as keys
        cc_by_timestamp: Dictionary with CC values by timestamp
        time_indexed_data: List of entries with datetime objects for time-range matching
        decoded_timestamp: Converted timestamp string
        from_field: FROM field value
        
    Returns:
        Tuple of (color_code, to_field) or ('', '')
    """
    if not decoded_timestamp:
        return '', ''
    
    color_code = ''
    to_field = ''
    
    # Strategy 1: Direct CC lookup by timestamp
    if decoded_timestamp in cc_by_timestamp:
        color_code = cc_by_timestamp[decoded_timestamp]
    
    # Strategy 2: Try exact match with timestamp and FROM
    if from_field:
        search_key = f"{decoded_timestamp}_{from_field}"
        if search_key in decoded_data and decoded_data[search_key]:
            match = decoded_data[search_key][0]
            if match.get('cc'):
                color_code = match['cc']
            if match.get('to'):
                to_field = match['to']
    
    # Strategy 3: Look in all entries at this timestamp
    if decoded_timestamp in timestamp_data:
        for entry in timestamp_data[decoded_timestamp]:
            # Update color_code if found and not already set
            if entry.get('cc') and not color_code:
                color_code = entry['cc']
            # Try to match FROM field
            if str(entry.get('from', '')) == str(from_field):
                if entry.get('cc'):
                    color_code = entry['cc']
                if entry.get('to'):
                    to_field = entry['to']
                break  # Found exact match, stop looking
    
    # Strategy 4: Time-range matching (within 5 seconds)
    # If we still don't have TO or CC, search within time range
    if (not to_field or not color_code) and time_indexed_data:
        try:
            # Parse the decoded timestamp to datetime
            search_dt = datetime.strptime(decoded_timestamp, "%Y%m%d %H%M%S")
            
            # Search within 5 seconds before and after
            for entry in time_indexed_data:
                if 'datetime' in entry:
                    time_diff = abs((entry['datetime'] - search_dt).total_seconds())
                    if time_diff <= 5:  # Within 5 seconds
                        # Check if FROM matches
                        if str(entry.get('from', '')) == str(from_field):
                            if entry.get('cc') and not color_code:
                                color_code = entry['cc']
                            if entry.get('to') and not to_field:
                                to_field = entry['to']
                            # Found a good match, can stop if we have both values
                            if color_code and to_field:
                                break
        except:
            pass
    
    return color_code, to_field

def process_multiple_files(files_data, decoded_files_data, output_file):
    """
    Processes multiple call_events files and combines them into a single output file.
    Enriches data with information from decoded_messages files when available.
    
    Args:
        files_data: Dictionary of call_events filenames and their paths
        decoded_files_data: Dictionary of decoded_messages filenames and their paths
        output_file: Path to the output file
        
    Returns:
        True if successful, False otherwise
    """
    
    # Create output directory if it doesn't exist
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    try:
        with open(output_file, 'w', encoding='utf-8', newline='') as outfile:
            writer = csv.writer(outfile, quoting=csv.QUOTE_ALL)
            
            # Write header row with all column names
            new_header = ['TIMESTAMP', 'DURATION_MS', 'PROTOCOL', 'EVENT', 'FROM', 'TO', 'TIMESLOT', 'COLOR_CODE', 'ALGORITHM', 'KEY', 'DETAILS']
            writer.writerow(new_header)
            
            # Process each call_events file
            for filename, input_file in files_data.items():
                if not os.path.exists(input_file):
                    print(f"  ERROR: File not found: {input_file}")
                    continue
                
                # Check file size
                file_size = os.path.getsize(input_file)
                print(f"  Processing {filename} ({file_size} bytes)")
                
                if file_size == 0:
                    print(f"    WARNING: File is empty!")
                    continue
                
                # Load data from decoded_messages if available
                decoded_data = {}
                timestamp_data = {}
                cc_by_timestamp = {}
                time_indexed_data = []
                
                if filename in decoded_files_data:
                    decoded_file = decoded_files_data[filename]
                    print(f"    Using decoded_messages: {os.path.basename(decoded_file)}")
                    decoded_data, timestamp_data, cc_by_timestamp, time_indexed_data = parse_decoded_messages(decoded_file)
                
                # Write source file comment
                outfile.write(f"# Source file: {filename}\n")
                
                with open(input_file, 'r', encoding='utf-8') as infile:
                    reader = csv.reader(infile)
                    
                    # Check if file has content
                    first_line = next(reader, None)
                    if first_line is None:
                        print(f"    WARNING: File {filename} is empty!")
                        continue
                    
                    # Check if it's a header line
                    if first_line and len(first_line) > 0 and first_line[0] == "TIMESTAMP":
                        print(f"    Found header, skipping...")
                        # Header was skipped, continue with normal processing
                    else:
                        # If not header, process it as data
                        if first_line and len(first_line) >= 10:
                            print(f"    No header found, processing first line as data")
                            row = first_line
                            # Process this row (code continues below)
                            # [Processing code for first row would go here - same as in loop below]
                    
                    row_count = 0
                    for row in reader:
                        row_count += 1
                        
                        if len(row) >= 10:
                            # Extract basic fields from call_events
                            timestamp = row[0]
                            duration_ms = row[1]
                            protocol = row[2]
                            event = row[3]
                            from_field = row[4]
                            to_field = row[5]
                            timeslot = row[8]
                            color_code = ""
                            algorithm = ""
                            key = ""
                            details = row[9]
                            
                            # Always try to enrich from decoded_messages if available
                            if decoded_data or timestamp_data or cc_by_timestamp or time_indexed_data:
                                # Convert timestamp to decoded_messages format
                                decoded_timestamp = convert_timestamp_to_decoded_format(timestamp)
                                
                                if decoded_timestamp:
                                    # Find color code and TO field using multiple strategies including time-range
                                    found_cc, found_to = find_color_code_with_time_range(
                                        decoded_data, timestamp_data, cc_by_timestamp, time_indexed_data,
                                        decoded_timestamp, from_field
                                    )
                                    
                                    if found_cc:
                                        color_code = found_cc
                                    if found_to and not to_field:
                                        to_field = found_to
                            
                            # Process DETAILS field
                            if details:
                                # Extract CC, FM, TO from DETAILS if present
                                if "CC:" in details or "FM:" in details or "TO:" in details:
                                    # Extract CC, FM, TO from any part of the string
                                    cc_match = re.search(r'CC:(\d+)', details)
                                    fm_match = re.search(r'FM:(\d+)', details)
                                    to_match = re.search(r'TO:(\d+)\s+(?!UDP)', details)
                                    
                                    # Update fields if found and not already set
                                    if cc_match and not color_code:
                                        color_code = cc_match.group(1)
                                    
                                    if fm_match and not from_field:
                                        from_field = fm_match.group(1)
                                    
                                    if to_match and not to_field:
                                        to_field = to_match.group(1)
                                    
                                    # Remove CC, FM, TO from details string
                                    details = re.sub(r'CC:\d+\s*', '', details)
                                    details = re.sub(r'FM:\d+\s*', '', details)
                                    # Remove only the first TO (not the one in IP TO:)
                                    if "IP" in details:
                                        details = re.sub(r'TO:(\d+)\s+(?=IP)', '', details)
                                    else:
                                        details = re.sub(r'TO:\d+\s*', '', details)
                                    
                                    # Process strings with IP addresses
                                    if "IP FROM:" in details or "IP TO:" in details:
                                        details = re.sub(r'IP FROM:', 'IP:', details)
                                        details = re.sub(r'UNKNOWN PACKET:[A-Fa-f0-9]+', 'UNKNOWN PACKET:', details)
                                        details = re.sub(r'INVALID HEADER\s+null', 'INVALID HEADER', details)
                                    
                                    details = details.strip()
                                
                                # Process ENCRYPTION information
                                if "ENCRYPTION ALGORITHM:" in details or "ALGORITHM:" in details or "HYTERA ENCRYPTED ALGORITHM:" in details:
                                    # Standard encryption pattern
                                    enc_match = re.search(r'ENCRYPTION ALGORITHM:(\w+)\s+(\w+)\s+KEY:(\d+)', details)
                                    if enc_match:
                                        algorithm = enc_match.group(2)
                                        key = enc_match.group(3)
                                        details = re.sub(r'ENCRYPTION ALGORITHM:\w+\s+\w+\s+KEY:\d+\s*', '', details)
                                        if not details.strip():
                                            details = "ENCRYPTED"
                                    
                                    # RC4/EP encryption pattern
                                    enc_rc4_match = re.search(r'ENCRYPTION ALGORITHM:(\w+)\s+(RC4/EP)\s+KEY:(\d+)', details)
                                    if enc_rc4_match:
                                        algorithm = enc_rc4_match.group(2)
                                        key = enc_rc4_match.group(3)
                                        
                                        # Preserve IV if present
                                        if "IV:" in details:
                                            iv_match = re.search(r'(IV:.*)$', details)
                                            if iv_match:
                                                details = "ENCRYPTED " + iv_match.group(1).strip()
                                            else:
                                                details = "ENCRYPTED"
                                        else:
                                            details = "ENCRYPTED"
                                    
                                    # Process HYTERA BP encryption
                                    hytera_bp_match = re.search(r'HYTERA ENCRYPTED ALGORITHM:(HYTERA\s+BP)\s+KEY:(\d+)', details)
                                    if hytera_bp_match:
                                        algorithm = hytera_bp_match.group(1)
                                        key = hytera_bp_match.group(2)
                                        
                                        # Preserve IV if present
                                        if "IV:" in details:
                                            iv_match = re.search(r'IV:([A-Fa-f0-9]+)', details)
                                            if iv_match:
                                                details = f"ENCRYPTED IV:{iv_match.group(1)}"
                                            else:
                                                details = "ENCRYPTED"
                                        else:
                                            details = "ENCRYPTED"
                                    
                                    # Alternative ALGORITHM pattern
                                    alg_rc4_match = re.search(r'ALGORITHM:(\w+)\s+(RC4/EP)\s+KEY:(\d+)', details)
                                    if alg_rc4_match:
                                        algorithm = alg_rc4_match.group(2)
                                        key = alg_rc4_match.group(3)
                                        details = re.sub(r'ALGORITHM:\w+\s+RC4/EP\s+KEY:\d+\s*', '', details)
                                        if not details.strip():
                                            details = "ENCRYPTED"
                                    
                                    # SERVICE OPTIONS [ENCRYPTED] pattern
                                    elif "SERVICE OPTIONS [ENCRYPTED]" in details:
                                        service_match = re.search(r'SERVICE OPTIONS \[ENCRYPTED\] ENCRYPTION ALGORITHM:(\w+)\s+(\w+)\s+KEY:(\d+)', details)
                                        if service_match:
                                            algorithm = service_match.group(2)
                                            key = service_match.group(3)
                                            details = "ENCRYPTED"
                                    
                                    details = details.strip()
                                
                                # Handle SERVICE OPTIONS [ENCRYPTED] without algorithm info
                                if "SERVICE OPTIONS [ENCRYPTED]" in details and "ENCRYPTION ALGORITHM:" not in details:
                                    details = re.sub(r'SERVICE OPTIONS \[ENCRYPTED\]', 'ENCRYPTED', details)
                                    details = details.strip()
                                
                                # Ensure ENCRYPTED label for encrypted messages
                                if algorithm in ["AES256", "RC4/EP", "HYTERA BP"] and (not details or details.strip() == ""):
                                    details = "ENCRYPTED"
                                
                                # Clean various packet types (only if no IP addresses present)
                                if "IP:" not in details:
                                    details = re.sub(r'((?:ENCRYPTED\s+)?UNKNOWN PACKET:)[A-Fa-f0-9]+', r'\1', details)
                                    details = re.sub(r'(DEFINED SHORT DATA PACKET:)[A-Fa-f0-9]+', r'\1', details)
                                    details = re.sub(r'(HDR:)[A-Fa-f0-9]+', r'\1', details)
                                    details = re.sub(r'(PACKET:)[A-Fa-f0-9]+', r'\1', details)
                                    details = re.sub(r'(SHORT DATA:)[A-Fa-f0-9]+', r'\1', details)
                                
                                # Clean MESSAGE content
                                if 'MESSAGE:' in details and 'Error:' in details:
                                    details = re.sub(r'(MESSAGE:\s*Error:).*', r'\1', details, flags=re.DOTALL)
                                elif 'MESSAGE:' in details and 'Error:' not in details:
                                    details = re.sub(r'(MESSAGE:).*', r'\1', details, flags=re.DOTALL)
                                
                                details = details.strip()
                            
                            # Write processed row to output file
                            new_row = [timestamp, duration_ms, protocol, event, from_field, to_field, timeslot, color_code, algorithm, key, details]
                            writer.writerow(new_row)
                    
                    print(f"    Total rows processed: {row_count}")
                    if row_count == 0:
                        print(f"    WARNING: No data rows found in {filename}")
                
                # Add separator comment between files
                outfile.write("#\n")
        
        print(f"Combined file successfully created: {output_file}")
        return True
        
    except Exception as e:
        print(f"Error creating combined file: {e}")
        return False

def main():
    """
    Main function that orchestrates the processing of DMR log files.
    Finds all call_events.log files, matches them with decoded_messages.log files,
    groups them by frequency, and processes each group into combined output files.
    """
    
    print("Starting DMR Log Processing...")
    print(f"Raw data directory: {get_raw_dir()}")
    print(f"Output directory: {get_out_dir()}")
    
    # Check if directories exist
    if not os.path.exists(get_raw_dir()):
        print(f"ERROR: Raw data directory does not exist: {get_raw_dir()}")
        return
    
    # Get list of all files in the raw data directory
    all_files = os.listdir(get_raw_dir())
    
    # Find all call_events.log files
    call_events_files = [f for f in all_files if f.endswith('_call_events.log')]
    
    if not call_events_files:
        print("No call_events.log files found in directory")
        print(f"Files in directory: {len(all_files)}")
        if all_files:
            print("Sample files:")
            for f in all_files[:5]:
                print(f"  - {f}")
        return
    
    print(f"Found {len(call_events_files)} call_events.log files")
    
    # Group files by frequency
    frequency_groups = defaultdict(dict)
    decoded_files_map = defaultdict(dict)
    
    for filename in call_events_files:
        # Extract and format frequency from filename
        formatted_freq = extract_frequency_from_filename(filename)
        if formatted_freq:
            input_file = os.path.join(get_raw_dir(), filename)
            frequency_groups[formatted_freq][filename] = input_file
            
            # Find corresponding decoded_messages file
            decoded_filename = find_matching_decoded_file(filename, all_files)
            if decoded_filename:
                decoded_file_path = os.path.join(get_raw_dir(), decoded_filename)
                decoded_files_map[formatted_freq][filename] = decoded_file_path
                print(f"Found match:\n  {filename}\n  -> {decoded_filename}")
        else:
            print(f"Could not extract frequency from filename: {filename}")
    
    # Process each frequency group
    for frequency, files_data in frequency_groups.items():
        print(f"\nProcessing frequency {frequency}:")
        for filename in files_data.keys():
            print(f"  - {filename}")
            if frequency in decoded_files_map and filename in decoded_files_map[frequency]:
                print(f"    (with decoded_messages)")
        
        # Create output filename based on frequency
        output_filename = f"{frequency}.txt"
        output_file = os.path.join(get_out_dir(), output_filename)
        
        # Get decoded files for this frequency
        decoded_files = decoded_files_map.get(frequency, {})
        
        # Process all files for this frequency
        success = process_multiple_files(files_data, decoded_files, output_file)
        
        if success:
            print(f"✓ Files for frequency {frequency} successfully combined -> {output_filename}")
        else:
            print(f"✗ Error processing files for frequency {frequency}")
    
    print("\nProcessing complete!")

if __name__ == "__main__":
    main()