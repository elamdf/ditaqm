import socket
import time
from machine import Pin, I2C
import BME280

HOST = "192.168.3.187"
PORT = 80
#TODO actually make this error-resistent and add support for others
i2c = I2C(scl=Pin(5), sda=Pin(4), freq=100000)

HEADERS = """\
POST /in HTTP/1.1\r
Content-Type: {content_type}\r
Content-Length: {content_length}\r
Host: {host}\r
Connection: close\r
\r\n"""


def dict_to_body(data):
    body = ""
    for key in data:
        body = body + str(key) + "=" + str(data[key]) + "&"
    return body
def get_bme_data(res):
    """get new data from the BME280 sensor"""
    bme = BME280.BME280(i2c=i2c)
    res["temp"] = bme.temperature
    res["humidity"] = bme.humidity
    res["pressure"] = bme.pressure
    res["name"] = "esptest"
    return res

def send():
    body = dict_to_body(get_bme_data({}))
    body_bytes = body.encode('ascii')

    header_bytes = HEADERS.format(
        content_type="application/x-www-form-urlencoded",
        content_length=len(body_bytes),
        host=str(HOST) + ":" + str(PORT)
    ).encode('iso-8859-1')

    payload = header_bytes + body_bytes

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((HOST, PORT))

    s.sendall(payload)

    print(s.recv(1024))
while True:
    send()
    time.sleep(5)