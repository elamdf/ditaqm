"""
HTTP-based setup over WLAN, configures sensor name, host, user login
"""
# TODO check unique first and then register sens
from machine import Pin, I2C
import time
import re
import json
import socket
import machine
from webtool import WebTool
import pages
import urequests as requests


# ************************
# Configure the ESP32 wifi
# as Access Point mode.
import network



# ************************
# Configure the socket connection
# over TCP/IP
import socket

# AF_INET - use Internet Protocol v4 addresses
# SOCK_STREAM means that it is a TCP socket.
# SOCK_DGRAM means that it is a UDP socket.

# ************************
# Function for creating the
# web page to be displayed
POST_HEADERS = {'content-type': 'application/json'}

class SensorConfig(WebTool):
    """Basic sensor configuration- host to push to, sensor name, and optional user login"""
    def __init__(self, sock, config_file="config.json"):
        super().__init__(sock, config_file=config_file)
        self.host = 0
        self.username = 0
        self.password = 0
        self.sensorname = 0
        print('setup init done')
    def update_from_config(self):
        """Update progress (host, sensor name, login entered) from config file"""
        with open(self.config_file, "r") as config_file:
            config_data = json.load(config_file)
            if "host" in config_data:
                self.host = config_data["host"]
            if "username" in config_data:
                self.username = config_data["username"]
            if "sensorname" in config_data:
                self.sensorname = config_data["sensor"]
    def update_config(self):
        """Update config file from instance variables"""
        super().say("Updating config...")
        with open(self.config_file, "r+") as config_file:
            config_data = json.load(config_file)
            if self.host:
                config_data["host"] = self.host
            if self.username:
                config_data["username"] = self.username
                config_data["password"] = self.password
            if self.sensorname:
                config_data["sensorname"] = self.sensorname
            config_file.seek(0) # maybe unnecessary
            json.dump(config_data, config_file)
        super().say("config updated!")


    @staticmethod
    def check_host_up(host):
        """Use the '/test' endpoint to check if the give host is up, returns the HTTP response"""
        try:
            resp = requests.get(str(host + "/test")).text
            if resp == "OK":
                return "OK"
            return str(resp)
        except Exception as e: # TODO make more specific
            return e
    def name_sensor(self, desired_sensor_name):
        """
        Attempts to register a sensor with the given name at the host
        returns http code or error if it occurs
        """
        uname = json.dumps({"sensorname":desired_sensor_name})
        try:
            resp = requests.post(str(self.host + "/api/regSens"), headers = POST_HEADERS, data=uname).json()
            return resp.code
        except Exception as e:
            return e

    def route_request(self, wanted_dir, params):
        """Takes the desired directory and returns the appropriate HTML page as a string"""
        page_to_return = pages.setup_home_page()
        if wanted_dir == "host":
            if 'host' in params:
                if self.check_host_up(params['host']) == "OK":
                    self.host = params['host']
                    page_to_return = pages.setup_home_page()
                else:
                    page_to_return = pages.host_page(retry=True)
            else:
                page_to_return = pages.host_page()
        elif wanted_dir == "login":
            if self.host:
                page_to_return = pages.login_page()
        elif wanted_dir == "namesens":
            if self.host:
                if "sensname" in params:
                    if self.name_sensor(params["sensname"]) == 200: # TODO maybe add the error message to the page / print to oled
                        page_to_return = pages.setup_home_page()
                        self.sensorname = params["sensname"]
                    else:
                        page_to_return = pages.name_sensor(retry=True)
                else:
                    page_to_return = pages.name_sensor()
        self.update_config()
        return page_to_return
    def run(self):
        """Handler user configuration through HTML pages"""
        print('starting main loop')
        super().say("http://" + str(self.sta.ifconfig()[0]))
        print(self.sta.ifconfig())
        while True:
            self.update_from_config()
            print('waiting for a request')
            conn, wanted_dir, params = super().recieve_request()
            print('request recieved and parsed!')
            print("wanted dir is " +  str(wanted_dir))
            super().send_page(conn, self.route_request(wanted_dir, params))