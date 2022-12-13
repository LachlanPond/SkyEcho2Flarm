import uctypes
import math
import network
import socket
import binascii

FLAG_BYTE = 0x7E
CONTROL_ESC_BYTE = 0x7D
KNOTS_MS_CONVERSION_FACTOR = 0.5144444
FT_M_CONVERSION_FACTOR = 0.3048
VERTICAL_VEL_CONVERSTION_FACTOR = 64

TRAFFIC_STRUCT = {
    "start_flag": 0 | uctypes.UINT8,
    "id": 1 | uctypes.UINT8,
    "traffic_alert_status": 2 | uctypes.BFUINT8 | 3 << uctypes.BF_POS | 4 << uctypes.BF_LEN,
    "addr_type": 2 | uctypes.BFUINT8 | 0 << uctypes.BF_POS | 4 << uctypes.BF_LEN,
    "participant_addr": 3 | uctypes.BFUINT32 | 7 << uctypes.BF_POS | 24 << uctypes.BF_LEN,
    "lat": 6 | uctypes.BFUINT32 | 7 << uctypes.BF_POS | 24 << uctypes.BF_LEN,
    "lon": 9 | uctypes.BFUINT32 | 7 << uctypes.BF_POS | 24 << uctypes.BF_LEN,
    "altitude": 12 | uctypes.BFUINT16 | 3 << uctypes.BF_POS | 12 << uctypes.BF_LEN,
    "misc": 13 | uctypes.BFUINT8 | 0 << uctypes.BF_POS | 4 << uctypes.BF_LEN,
    "nav_integrity_category": 14 | uctypes.BFUINT8 | 3 << uctypes.BF_POS | 4 << uctypes.BF_LEN,
    "nav_accuracy_category": 14 | uctypes.BFUINT8 | 0 << uctypes.BF_POS | 4 << uctypes.BF_LEN,
    "horizontal_velocity": 15 | uctypes.BFUINT16 | 3 << uctypes.BF_POS | 12 << uctypes.BF_LEN,
    "vertical_velocity": 16 | uctypes.BFUINT16 | 0 << uctypes.BF_POS | 12 << uctypes.BF_LEN,
    "track": 18 | uctypes.UINT8,
    "emitter_category": 19 | uctypes.UINT8,
    "call_sign": 20 | uctypes.UINT64,
    "emergency_prio_code": 28 | uctypes.BFUINT8 | 3 << uctypes.BF_POS | 4 << uctypes.BF_LEN,
    "spare": 28 | uctypes.BFUINT8 | 0 << uctypes.BF_POS | 4 << uctypes.BF_LEN,
    "crc": 29 | uctypes.UINT16,
    "end_flag": 31 | uctypes.UINT8
}

CRC_STRUCT = {
    "crc": 0 | uctypes.UINT16,
    "crctable": (2 | uctypes.ARRAY, 256 | uctypes.UINT16)
}

def getTwosComplement(number,bits):
    if number >> (bits-1):
        return -((~number + 1) & 2**(bits) - 1)
    else:
        return number

def generateCRCTable(crc_struct):
    for i in range(256):
        crc_struct.crc = (i << 8)
        for y in range(8):
            crc_struct.crc = (crc_struct.crc << 1) ^ (0x1021 if (crc_struct.crc & 0x8000) else 0)
        crc_struct.crctable[i] = crc_struct.crc

def validateCRC(message,crc,crc_struct):
    crc_struct.crc = 0
    for i in range(len(message)):
        crc_struct.crc = crc_struct.crctable[crc_struct.crc >> 8] ^ (crc_struct.crc << 8) ^ message[i]
    return True if crc_struct.crc == crc[1] << 8 | crc[0] else False

def generateNMEACRC(nmea):
    nmea_bytes = bytes(nmea,'utf-8')
    crc = nmea_bytes[0]
    for byte in nmea_bytes[1:-1]:
        crc = crc ^ byte
    return hex(crc >> 3)[-1] + hex(crc & 15)[-1]

def parseMessage(raw_message,crc_struct):
    message = raw_message[1:-3]
    crc = raw_message[-3:-1]
    if validateCRC(message,crc,crc_struct):
        return uctypes.struct(uctypes.addressof(raw_message),TRAFFIC_STRUCT,uctypes.BIG_ENDIAN)
    else:
        return False

def parseRawGDL90(raw_data,crc_struct):
    data = bytearray()
    messages = []
    flag_byte = False
    i = 0
    while i < len(raw_data):
        if raw_data[i] == FLAG_BYTE:
            flag_byte = not flag_byte
        if raw_data[i] == CONTROL_ESC_BYTE:
            i = i + 1
            data.append(raw_data[i] ^ 0x20)
        else:
            data.append(raw_data[i])
        if not flag_byte:
            message = parseMessage(data,crc_struct)
            if message:
                messages.append(message)
            else:
                print("CRC Failed")
            data = bytearray()
        i += 1
    return messages

def getRelNorth(lat_traffic_raw,lat_own_raw):
    # Convert from 24-bit signed int to degrees
    lat_traffic = getTwosComplement(lat_traffic_raw,24) * (180/2**24)
    lat_own = getTwosComplement(lat_own_raw,24) * (180/2**24)

    # Convert to radians for Haversine formula
    lat_traffic = math.radians(lat_traffic)
    lat_own = math.radians(lat_own)
    lat_delta = lat_own - lat_traffic
    EARTH_RADIUS = 6371e3

    # Haversine formula
    a = math.sin(lat_delta/2) * math.sin(lat_delta/2)
    c = 2 * math.atan2(math.sqrt(a),math.sqrt(1-a))
    d = EARTH_RADIUS * c

    if lat_traffic > lat_own:
        return d
    else:
        return -d

def getRelEast(lat_traffic_raw,lon_traffic_raw,lat_own_raw,lon_own_raw):
    # Convert from 24-bit signed int to degrees
    lat_traffic = getTwosComplement(lat_traffic_raw,24) * (180/2**24)
    lon_traffic = getTwosComplement(lon_traffic_raw,24) * (180/2**24)
    lat_own = getTwosComplement(lat_own_raw,24) * (180/2**24)
    lon_own = getTwosComplement(lon_own_raw,24) * (180/2**24)

    # Convert to radians for Haversine formula
    lat_traffic = math.radians(lat_traffic)
    lon_traffic = math.radians(lon_traffic)
    lat_own = math.radians(lat_own)
    lon_own = math.radians(lon_own)
    lon_delta = lon_own - lon_traffic
    EARTH_RADIUS = 6371e3

    # Haversine formula
    a = math.cos(lat_own) * math.cos(lat_traffic) * math.sin(lon_delta/2) * math.sin(lon_delta/2)
    print(a)
    c = 2 * math.atan2(math.sqrt(a),math.sqrt(1-a))
    d = EARTH_RADIUS * c

    if lon_traffic > lon_own:
        return d
    else:
        return -d

def getRelVert(traffic_alt_raw, own_alt_raw):
    traffic_alt = traffic_alt_raw * 25 - 1000
    print("Traffic Alt: " + str(traffic_alt))
    own_alt = own_alt_raw * 25 - 1000
    rel_alt = (traffic_alt - own_alt)
    rel_alt = min(rel_alt,32767)
    rel_alt = max(rel_alt,-32768)
    return rel_alt

def getIDType(address_type):
    # 0 = ADS-B with ICAO address
    # 2 = TIS-B with ICAO address
    if address_type in [0,2]:
        return 1
    else:
        return 0

def getTrack(track):
    return round(track * (360/256))

def getGroundSpeed(horizontal_velocity):
    print(horizontal_velocity/2)
    print(round((horizontal_velocity * KNOTS_MS_CONVERSION_FACTOR)/2))
    return round((horizontal_velocity * KNOTS_MS_CONVERSION_FACTOR)/2)

def getClimbRate(vertical_velocity_raw):
    vertical_velocity = getTwosComplement(vertical_velocity_raw,12) * VERTICAL_VEL_CONVERSTION_FACTOR
    # Convert ft/min to m/min
    climb_rate = vertical_velocity * FT_M_CONVERSION_FACTOR
    # Convert m/min to m/s
    climb_rate = climb_rate / 60
    return round(climb_rate,1)

def getAircraftType(emitter_cat):
    # Gliders
    if emitter_cat == 9:
        return "1"
    # Aircraft with reciprocating engine(s)
    elif emitter_cat in [1,2,6]:
        return "8"
    # Rotorcraft
    elif emitter_cat == 7:
        return "3"
    # Aircraft with jet/turboprop engine(s)
    elif emitter_cat in [3,4,5]:
        return "9"
    # Skydiver
    elif emitter_cat == 11:
        return "4"
    # Hang glider / paraglider
    elif emitter_cat == 12:
        return "6"
    # Light than air
    elif emitter_cat == 10:
        return "B"
    # UAV
    elif emitter_cat == 14:
        return "D"
    # Static obstacle
    elif emitter_cat in [19,20,21]:
        return "F"
    # Unknown
    else:
        return "A"

def genNMEATrafficMessage(traffic_data,ownship_data):
    # $PFLAA,<AlarmLevel>,<RelativeNorth>,<RelativeEast>,<RelativeVertical>,<IDType>,
    # <ID>,<Track>,<TurnRate>,<GroundSpeed>,<ClimbRate>,<AcftType>,<NoTrack>
    nmea = "PFLAA,"
    nmea += str(traffic_data.traffic_alert_status) + ","
    nmea += str(getRelNorth(traffic_data.lat,ownship_data.lat)) + ","
    nmea += str(getRelEast(traffic_data.lat,traffic_data.lon,ownship_data.lat,ownship_data.lon)) + ","
    nmea += str(getRelVert(traffic_data.altitude,ownship_data.altitude)) + ","
    nmea += str(getIDType(traffic_data.addr_type)) + ","
    nmea += ","
    nmea += str(getTrack(traffic_data.track)) + ","
    nmea += ","
    nmea += str(getGroundSpeed(traffic_data.horizontal_velocity)) + ","
    nmea += str(getClimbRate(traffic_data.vertical_velocity)) + ","
    nmea += getAircraftType(traffic_data.emitter_category) + ","
    nmea += "0,"
    nmea += "1,"
    nmea += ","

    crc = generateNMEACRC(nmea)

    nmea = "$" + nmea + "*" + crc

    return nmea

def connectSkyEcho(ssid,pwd):
    sta_if = network.WLAN(network.STA_IF)
    if not sta_if.isconnected():
        print('connecting to SkyEcho2...')
        sta_if.active(True)
        sta_if.connect(ssid, pwd)
        while not sta_if.isconnected():
            pass
    print('network config:', sta_if.ifconfig())

    addr_info = socket.getaddrinfo(sta_if.ifconfig()[0], 4000)
    addr = addr_info[0][-1]

    s = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    s.bind(addr)
    return s

def printTrafficData(traffic,ownship):
    callsign = ""
    i = 7
    while i > 0:
        callsign = callsign + chr((traffic.call_sign >> i*8) & 0xFF)
        i -= 1
    print("Call Sign:" + callsign)
    print("Rel North: " + str(getRelNorth(traffic.lat,ownship.lat)))
    print("Rel East: " + str(getRelEast(traffic.lat,traffic.lon,ownship.lat,ownship.lon)))
    print("Rel Vert: " + str(getRelVert(traffic.altitude,ownship.altitude)))
    print("My Alt " + str((ownship.altitude * 25) - 1000))
    print("Track: " + str(getTrack(traffic.track)))
    print("Ground Speed: " + str(getGroundSpeed(traffic.horizontal_velocity)))
    print("Climb Rate: " + str(getClimbRate(traffic.vertical_velocity)))
    print("Type: " + str(getAircraftType(traffic.emitter_category)))