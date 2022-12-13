# main.py -- put your code here!
import network
import uctypes
import socket
import binascii
import micropython
import sys
from lib import *

OWNSHIP_ID = 0xA
TRAFFIC_ID = 0x14

OWNSHIP_POPULATED_FLAG = False

skyecho_ssid = "SkyEcho_8189"
skyecho_pwd = ""

# Define CRC struct
crc_data = bytes(uctypes.sizeof(CRC_STRUCT,uctypes.LITTLE_ENDIAN))
crc_data = uctypes.struct(uctypes.addressof(crc_data),CRC_STRUCT,uctypes.LITTLE_ENDIAN)
generateCRCTable(crc_data)

# Define CRC struct
ownship_data = bytes(uctypes.sizeof(TRAFFIC_STRUCT,uctypes.LITTLE_ENDIAN))

s = connectSkyEcho(skyecho_ssid,skyecho_pwd)

while True:
    raw_data = s.recv(2048)
    messages = parseRawGDL90(raw_data,crc_data)
    for message in messages:
        if message.id == OWNSHIP_ID:
            ownship_data = message
            OWNSHIP_POPULATED_FLAG = True
        elif message.id == TRAFFIC_ID and OWNSHIP_POPULATED_FLAG:
            print(genNMEATrafficMessage(message,ownship_data))
            printTrafficData(message,ownship_data)