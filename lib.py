import uctypes

MESSAGE = {
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
    "horizontal_velocty": 15 | uctypes.BFUINT16 | 3 << uctypes.BF_POS | 12 << uctypes.BF_LEN,
    "vertical_velocty": 16 | uctypes.BFUINT16 | 0 << uctypes.BF_POS | 12 << uctypes.BF_LEN,
    "track": 18 | uctypes.UINT8,
    "emitter_category": 19 | uctypes.UINT8,
    "call_sign": 20 | uctypes.UINT64,
    "emergency_prio_code": 28 | uctypes.UINT8 | 3 << uctypes.BF_POS | 4 << uctypes.BF_LEN,
    "spare": 28 | uctypes.UINT8 | 0 << uctypes.BF_POS | 4 << uctypes.BF_LEN,
    "crc": 29 | uctypes.UINT16,
    "end_flag": 31 | uctypes.UINT8
}

CRC = {
    "crc": 0 | uctypes.UINT16,
    "crctable": (2 | uctypes.ARRAY, 256 | uctypes.UINT16)
}

def generateCRCTable(crc_struct):
    for i in range(256):
        crc_struct.crc = (i << 8)
        for y in range(8):
            crc_struct.crc = (crc_struct.crc << 1) ^ (4129 if (crc_struct.crc & 32768) else 0)
        crc_struct.crctable[i] = crc_struct.crc

def validateCRC(message,crc,crc_struct):
    crc_struct.crc = 0
    for i in range(len(message)):
        crc_struct.crc = crc_struct.crctable[crc_struct.crc >> 8] ^ (crc_struct.crc << 8) ^ message[i]
    return True if crc_struct.crc == crc[1] << 8 | crc[0] else False

def parseMessage(raw_message,crc_struct):
    message = raw_message[1:-3]
    crc = raw_message[-3:-1]
    if validateCRC(message,crc,crc_struct):
        return uctypes.struct(uctypes.addressof(raw_message),MESSAGE,uctypes.BIG_ENDIAN)
    else:
        return False

def parseRawTraffic(raw_data,crc_struct):
    data = bytearray()
    messages = []
    flag_byte = False
    i = 0
    while i < len(raw_data):
        if raw_data[i] == int("7E",16):
            flag_byte = not flag_byte
        if raw_data[i] == int("7D",16):
            i = i + 1
            data.append(raw_data[i] ^ int("20",16))
        else:
            data.append(raw_data[i])
        if not flag_byte:
            if data[1] == int("14",16):
                message = parseMessage(data,crc_struct)
                if message:
                    messages.append(message)
                else:
                    print("CRC Failed")
            data = bytearray()
        i = i + 1
    return messages