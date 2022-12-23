# main.py -- put your code here!
import network
import socket
import json
import io

config = json.load(io.open("config.json"))

print(config)

html = """<!DOCTYPE html>
<html>
    <head> <title>ESP8266 Pins</title> </head>
    <body> <h1>ESP8266 Pins</h1>
        <table border="1"> <tr><th>Pin</th><th>Value</th></tr> %s </table>
    </body>
    <form action="/">
        <input type="hidden" name="isButtonPressed" value="true">
        <input type="submit">
    </form>
</html>
"""

ap = network.WLAN(network.AP_IF)
ap.active(True)
ap.config(essid='SkyEcho2Flarm', password="password123")

addr = socket.getaddrinfo('0.0.0.0',80)[0][-1]

s = socket.socket()
s.bind(addr)
s.listen(1)

print('listening on',addr)

while True:
    cl,addr = s.accept()
    print('client connected from',addr)
    cl_file = cl.makefile('rwb',0)
    while True:
        line = cl_file.readline()
        if not line or line == b'\r\n':
            break
    response = html
    cl.send('HTTP/1.0 200 OK\r\nContent-type: text/html\r\n\r\n')
    cl.send(response)
    while True:
        data = s.recv(100)
        if data:
            print(str(data,'utf8'), end='')
        else:
            break
    cl.close()