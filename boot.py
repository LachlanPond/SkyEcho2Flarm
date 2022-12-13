# boot.py -- run on boot-up
import esp
import gc
import network

esp.osdebug(None)
gc.collect()

# ssid = "SkyFlarm"
# password = ""

# ap = network.WLAN(network.AP_IF)
# ap.active(True)
# ap.config(essid=ssid,password=password)

# while ap.active() == False:
#     pass

# print("Connection successful")
# print(ap.ifconfig())

# def webPage():
#     html = """<html><head><meta name="viewport" content="width=device-width, initial-scale=1"></head>
#     <body><h1>Hello, World!</h1></body></html>"""
#     return html