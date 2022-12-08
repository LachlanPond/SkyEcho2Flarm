# main.py -- put your code here!
import network
import uctypes
import socket
import binascii
from lib import *

ssid = "SkyEcho_8189"
pwd = ""

sta_if = network.WLAN(network.STA_IF)
if not sta_if.isconnected():
    print('connecting to network...')
    sta_if.active(True)
    sta_if.connect(ssid, pwd)
    while not sta_if.isconnected():
        pass
print('network config:', sta_if.ifconfig())

addr_info = socket.getaddrinfo(sta_if.ifconfig()[0], 4000)
addr = addr_info[0][-1]

s = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
s.bind(addr)

# Define CRC struct
crc_data = bytes(uctypes.sizeof(CRC,uctypes.LITTLE_ENDIAN))
crc_data = uctypes.struct(uctypes.addressof(crc_data),CRC,uctypes.LITTLE_ENDIAN)
generateCRCTable(crc_data)

while True:
    raw_data = s.recv(2048)
    messages = parseRaw(raw_data,crc_data)
    for message in messages:
        print(message.track)