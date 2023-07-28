#-*- coding:utf-8 -*-

# Import libraries
import os, sys, threading, time, logging, multiprocessing, sqlite3, struct, subprocess, datetime as dt
import pcapy, dpkt, socket, binascii, traceback, sys, hashlib
from multiprocessing import Process, Queue, Event

# Set constants
PATH_DROPBOX = '/home/pi/Dropbox-Uploader/dropbox_uploader.sh' # Path of Dropbox-Uploader
PATH_DATA = '/home/pi/data' # Path of data storage
PATH_STATS = '/home/pi/stats' # Path of stats storage
DATE_STRING = time.strftime("%y%m%d") + "HMS" + time.strftime("%H%M%S") # Date string

# Set the logging format (subtype for management frame)
SUBTYPES_MANAGEMENT = {
    0: 'association-request',
    1: 'association-response',
    2: 'reassociation-request',
    3: 'reassociation-response',
    4: 'probe-request',
    5: 'probe-response',
    8: 'beacon',
    9: 'announcement-traffic-indication-message',
    10: 'disassociation',
    11: 'authentication',
    12: 'deauthentication',
    13: 'action'
}

# Set the logging format (subtype for control frame)
SUBTYPES_CONTROL = {
    8: 'block-acknowledgement-request',
    9: 'block-acknowledgement',
    10: 'power-save-poll',
    11: 'request-to-send',
    12: 'clear-to-send',
    13: 'acknowledgement',
    14: 'contention-free-end',
    15: 'contention-free-end-plus-acknowledgement'
}

# Set the logging format (subtype for data frame)
SUBTYPES_DATA = {
    0: 'data',
    1: 'data-and-contention-free-acknowledgement',
    2: 'data-and-contention-free-poll',
    3: 'data-and-contention-free-acknowledgement-plus-poll',
    4: 'null',
    5: 'contention-free-acknowledgement',
    6: 'contention-free-poll',
    7: 'contention-free-acknowledgement-plus-poll',
    8: 'qos-data',
    9: 'qos-data-plus-contention-free-acknowledgement',
    10: 'qos-data-plus-contention-free-poll',
    11: 'qos-data-plus-contention-free-acknowledgement-plus-poll',
    12: 'qos-null',
    14: 'qos-contention-free-poll-empty'
}

queue = multiprocessing.Queue()

# Define a function for running a subprocess
def run_subprocess(commands, sleep_time = 1):
    """Run a subprocess and sleep for a moment before moving on."""
    subprocess.Popen(commands)
    time.sleep(sleep_time)

# Define a function for synchronizing the time
def synchronize_time():

    # Print it's time to synchronize the time
    print(f'Synchronize the time')

    time.sleep(5)

    # Set system time using a network time protocol server
    run_subprocess(['sudo', 'ntpdate', '-u', '3.kr.pool.ntp.org'])

    # Set the time zone to Asia/Seoul
    run_subprocess(['sudo', 'timedatectl', 'set-timezone', 'Asia/Seoul'])


# Define a function for uploading files to Dropbox
def upload_file_to_dropbox(file_path, destination):
    try:
        subprocess.run([PATH_DROPBOX, 'upload', file_path, destination], check=True)
    except subprocess.CalledProcessError:
        print(f"Failed to upload {file_path} to Dropbox")
        raise

# Define a function for creating and uploading files to Dropbox
def create_and_upload_file(DATE_STRING, command, filename_prefix):
    file_path = os.path.join(PATH_STATS, f'{filename_prefix}_{DATE_STRING}.txt')
    with open(file_path, 'w') as file:
        subprocess.run(command, stdout=file, check=True)
    upload_file_to_dropbox(file_path, '/')

# Define a function for uploading system information on cloud storage
def upload_cloud(DATE_STRING):
    try:
        print(f'************** Upload system information on cloud storage')

        os.makedirs(PATH_STATS, exist_ok=True)

        create_and_upload_file(DATE_STRING, ['df', '-h'], 'storage')
        create_and_upload_file(DATE_STRING, ['ls', '-alh'], 'list')

        print('Finish upload on cloud')
    except Exception as e:
        print(f'Failed to upload on cloud: {str(e)}')


# Set channels to sensing WiFi
WLAN_CONFIGS = [
    ('wlan1', '1'), # wlan1 by external WiFi dongle for 2.4GHz (channel 1)
    ('wlan2', '6'),  
    ('wlan3', '11'),
]

# Set commands for configuring wlan mode
def configure_wlan_mode(device_name, channel):
    interface = device_name + 'mon'
    command_monitor_enable = f"ifconfig {device_name} down; iw dev {device_name} interface add {interface} type monitor; ifconfig {interface} down; iw dev {interface} set type monitor; ifconfig {interface} up"
    command_monitor_channel = f"iw dev {interface} set channel {channel}"
    command_monitor_disable = f"iw dev {interface} del; ifconfig {device_name} up"
    return (interface, command_monitor_enable, command_monitor_channel, command_monitor_disable)

# Define a function for checking whether the MAC address is randomized or not
def is_random_mac(address):    
    return 1 if address[0] & 0b10 else 0

# Define a function for hashing the MAC address
def hash_mac_address(address):
    # Convert the MAC address to a string
    mac_address = ':'.join('%02x' % b for b in address)

    # If the MAC address is broadcast, return the MAC address as it is
    if mac_address == "ff:ff:ff:ff:ff:ff" or mac_address is None:
        return mac_address

    # Hash the MAC address
    hashed_mac_address = hashlib.sha256(mac_address.encode()).hexdigest()
    return hashed_mac_address

# Define a function for writing the data
def writer(DATE_STRING):

    # Create a storage for the data
    if not os.path.exists(PATH_DATA):
        os.makedirs(PATH_DATA)

    db = sqlite3.connect(PATH_DATA + '/' + 'raw_wifi_' + DATE_STRING + '.sqlite3') # Define a storage
    db.text_factory = str

    def write(stop):
        while not stop.is_set():
            try:
                logging.info('Writing...')
                cursor = db.cursor()
                for _ in range(0, queue.qsize()):
                    item = queue.get_nowait()
                    insert = (
                        "insert into packets values"
                        "("
                        ":timestamp,"
                        ":type,"
                        ":subtype,"
                        ":strength,"
                        ":source_address,"
                        ":source_address_randomized,"
                        ":destination_address,"
                        ":destination_address_randomized,"
                        ":access_point_name,"
                        ":access_point_address,"
                        ":access_point_address_randomized,"
                        ":sequence_number,"
                        ":channel,"
                        ":info"
                        ")"
                    )
                    cursor.execute(insert, item)
                db.commit()
                cursor.close()
                time.sleep(1)  # seconds
            except Queue.Empty:
                pass
            except KeyboardInterrupt:
                pass


    cursor = db.cursor()
    create = (
        "create table if not exists packets"
        "("
        "timestamp,"
        "type,"
        "subtype,"
        "strength,"
        "source_address,"
        "source_address_randomized,"
        "destination_address,"
        "destination_address_randomized,"
        "access_point_name,"
        "access_point_address,"
        "access_point_address_randomized,"
        "sequence_number,"
        "channel,"
        "info"
        ")"
    )
    cursor.execute(create)
    db.commit()
    cursor.close()
    stop = multiprocessing.Event()
    multiprocessing.Process(target=write, args=[stop]).start()
    return stop

def collect_wifi(interface, channel):
    max_packet_size = -1  # bytes
    promiscuous = 1  # boolean masquerading as an int
    timeout = 1  # milliseconds
    packets = None
    
    try:
        packets = pcapy.open_live(interface, max_packet_size, promiscuous, timeout)
    except Exception as e:
        print(f"An error occurred when trying to open the interface {interface}: {str(e)}")
        return

    packets.setfilter('')  # bpf syntax (empty string = everything)

    def loops(header, data):
        try:
            timestamp = dt.datetime.now().isoformat()
            try:
                packet = dpkt.radiotap.Radiotap(data)
            except dpkt.dpkt.UnpackError as e:
                print(f"Failed to unpack packet: {binascii.hexlify(data)}")
                raise e

            packet_signal = packet.ant_sig.db  # dBm            
            frame = packet.data
            packet_len = socket.ntohs(packet.length)
            index = packet_len + 22
            info = binascii.hexlify(data).decode()

            # Get sqeuence number and fragment number
            try:
                seq = struct.unpack('<H', data[index:index+2])[0]
                frag = struct.unpack('<H', data[index+2:index+4])[0]

            # If the packet is not data frame, set sequence number and fragment number to NULL       
            except struct.error:
                seq = 'NULL'
                frag = 'NULL'

            if frame.type == dpkt.ieee80211.MGMT_TYPE and SUBTYPES_MANAGEMENT[frame.subtype] != 'beacon':
                record = {
                    'timestamp': timestamp,
                    'type': 'management',
                    'subtype': SUBTYPES_MANAGEMENT[frame.subtype],
                    'strength': packet_signal,
                    'source_address': hash_mac_address(frame.mgmt.src),
                    'source_address_randomized': is_random_mac(frame.mgmt.src),
                    'destination_address': hash_mac_address(frame.mgmt.dst),
                    'destination_address_randomized': is_random_mac(frame.mgmt.dst),
                    'access_point_name': frame.ssid.data if hasattr(frame, 'ssid') else '(n/a)',
                    'access_point_address': hash_mac_address(frame.mgmt.bssid),
                    'access_point_address_randomized': is_random_mac(frame.mgmt.bssid),
                    'sequence_number': seq,
                    'channel': channel,
                    'info': info
                }

                queue.put(record)

            elif frame.type == dpkt.ieee80211.DATA_TYPE:
                record = {
                    'timestamp': timestamp,
                    'type': 'data',
                    'subtype': SUBTYPES_DATA[frame.subtype],
                    'strength': packet_signal,
                    'source_address': hash_mac_address(frame.data_frame.src),
                    'source_address_randomized': is_random_mac(frame.data_frame.src),
                    'destination_address': hash_mac_address(frame.data_frame.dst),
                    'destination_address_randomized': is_random_mac(frame.data_frame.dst),
                    'access_point_name': '(n/a)',  # not available in data packets
                    'access_point_address': hash_mac_address(frame.data_frame.bssid) if hasattr(frame.data_frame, 'bssid') else '(n/a)',
                    'access_point_address_randomized': is_random_mac(frame.data_frame.bssid) if hasattr(frame.data_frame, 'bssid') else '(n/a)',                    
                    'sequence_number': seq,
                    'channel': channel,
                    'info': info
                }
                queue.put(record)


        except Exception as e:
            logging.error(traceback.format_exc())

    packets.loop(-1, loops)

# Define a function for collecting bluetooth
def collect_bluetooth(DATE_STRING):
    
    if not os.path.exists(PATH_DATA):
        os.makedirs(PATH_DATA)

    PATH_DATA + '/' + 'raw_wifi_' + DATE_STRING + '.sqlite3'

    # Bluetooth Collection
    print(f'********** Start collecting bluetooth')
    os.system(f"Bluelog/bluelog -n -t -f -a 5 -d -o {PATH_DATA}/raw_bluelog_{DATE_STRING}.txt")
    time.sleep(1)

# Define a function for optimizing power usage
def optimize_power_usage():
    print(f'****** Optimize power usage (disable HDMI and internal wifi) after 60 seconds')
    
    # Disable HDMI completely
    os.system('sudo /opt/vc/bin/tvservice -p && sudo /opt/vc/bin/tvservice -o')

    # Internal wifi
    os.system('sudo ifconfig wlan0 down')    

def start():

    # Print start code
    print(f'************* Start *************')
    
    # Synchronize the time
    synchronize_time()

    # Print current time cynchonized
    print(f'Current time: {dt.datetime.now().isoformat()}')    
    
    # Wait for 25 seconds for the system to be ready
    print(f'Wait for 25 seconds for the system to be ready')
    time.sleep(25)
        
    # Upload system information on cloud storage    
    upload_cloud(DATE_STRING)

    # Optimize power usage (disable HDMI and internal wifi) after 60 seconds    
    threading.Timer(60, optimize_power_usage)

    # Start collecting bluetooth    
    collect_bluetooth(DATE_STRING)

    # Configure wlan mode
    print(f'******** Configure wlan mode')
    wlan_configs = [configure_wlan_mode(*cfg) for cfg in WLAN_CONFIGS]

    # Enable monitor mode    
    print(f'********* Enable monitor mode')
    for wlan in wlan_configs:
        subprocess.run(wlan[1], shell=True)  # Enable monitor
        subprocess.run(wlan[2], shell=True)  # Set channel
    time.sleep(5)

    # Start collecting wifi
    print(f'******** Start collecting wifi')
    stop_writing = writer(DATE_STRING)
    try:
        processes = []
        for i, wlan in enumerate(wlan_configs):            
            print(f'start wlan{i+1}')
            process = Process(target = collect_wifi, args=(wlan[0], wlan[2].split()[-1]))
            processes.append(process)
            process.start()

        for process in processes:
            process.join()

    except KeyboardInterrupt:
        print(f"'******** Interrupted by user (Ctrl+C)")

    finally:
        # Stop writing
        stop_writing.set()
        # Disable monitor mode
        for wlan in wlan_configs:
            subprocess.run(wlan[3].split())

start()