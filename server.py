# !/usr/bin/env python
# -*- coding: utf-8 -*-

import socket
import threading
import requests
import json
import csv
import time
import datetime
from opencage.geocoder import OpenCageGeocode as geocoder
from apiCommunication.bahn.BahnApi import BahnApi
from apiCommunication.doorbell import Doorbell


class Server(object):
    def __init__(self, host='', port=9999):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind((host, port))
        self.socket.listen(10)
        self.clients = []
        self.clientanzahl = 0
        self.real = False

    def starts(self):
        print("Server laeuft! Mit Strg+C Server stoppen!")
        while True:
            clientsocket, (host, port) = self.socket.accept()
            self._handle_connection(clientsocket, host, port)

    def _handle_connection(self, clientsocket, host, port):
        thread = threading.Thread(target=self._connection_handler,
                                  args=(clientsocket,))
        thread.daemon = True
        thread.start()
        self.clients.append(clientsocket)
        # self.clientanzahl = self.clientanzahl + 1
        self.process_new_connection(clientsocket)

    def startDoorBell(self, clientsocket):
        thread = threading.Thread(target=self.doorBellConnection(clientsocket))
        thread.start()

    def doorBellConnection(self, clientsocket):
        if Doorbell.DoorBell().run():
            print("INFO - Sending Command someone is at The Door")

            self.send_data(clientsocket, "door")

        self.doorBellConnection(clientsocket)

    def _connection_handler(self, clientsocket):
        data_buffer = ""
        keep_socket_alive = True
        while keep_socket_alive:
            data = clientsocket.recv(1024).decode('utf-8')
            if not data:
                break
            data_buffer += data
            while '\n' in data_buffer:
                data, data_buffer = data_buffer.split('\n', 1)
                data = data.strip()
                keep_socket_alive = self.process_message(clientsocket, data)
        self._disconnect_client(clientsocket)

    def _disconnect_client(self, clientsocket):
        self.process_close_connection(clientsocket)
        self.clients.remove(clientsocket)
        clientsocket.close()

    def send_data(self, clientsocket, data):
        try:
            clientsocket.sendall('{}\n'.format(data).encode('utf-8'))
        except socket.error as error:
            print("Fehler beim Versenden: {}".format(error))

    def send_to_all(self, data):
        for clientsocket in self.clients:
            self.send_data(clientsocket, data)

    def process_new_connection(self, clientsocket):
        """in abgeleiteter Klasse ggf. überschreiben"""
        if self.clientanzahl < 1:
            self.send_data(clientsocket, 'Start')
            self.connection_stimmt(clientsocket)
            self.clientanzahl += 1
        else:
            self._disconnect_client(clientsocket)

    def process_close_connection(self, clientsocket):
        """in abgeleiteter Klasse ggf. überschreiben"""
        self.clientanzahl -= 1

    def process_message(self, clientsocket, data):
        command, _, data = data.partition('_')
        time_now = datetime.datetime.now().strftime('%D:%H:%M:%S')
        print(time_now + ": Command-" + command + " Data-" + data)
        if self.real == False:
            self.connection_stimmt(clientsocket)
        if self.real == True:
            if command == "Bahn":
                ret = 'Bahn_' + BahnApi().retAnMain(data)
                self.send_data(clientsocket, ret)
            if command == "weather":
                city, country = data.split("-")
                ret = "Wetter_" + Weather().retAnMain(city, country)
                self.send_data(clientsocket, ret)
        self.send_data(clientsocket, "Next")
        return True

    def connection_stimmt(self, clientsocket):
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        time_now = datetime.datetime.now().strftime('%D:%H:%M:%S')
        print(local_ip)
        if (local_ip == "192.168.178.127" or local_ip == '127.0.1.1'):
            self.real = True
            print("Verbindungsaufbau mit " + local_ip + ", um: " + time_now)


class Weather():
    def init(self, lat, lon):
        key = "4cf6fec3a220ac5699c371800f684535"
        url = "https://api.openweathermap.org/data/2.5/forecast"
        unit = "metric"
        req = "{url}?lat={lat}&lon={lon}&appid={key}&units={unit}".format(url=url, lat=lat, lon=lon, key=key, unit=unit)
        return req

    def retAnMain(self, city, country):
        cords = self.geoFinder(city, country)
        req = self.init(cords[0], cords[1])
        response = requests.get(req).text
        weatherInfo = json.loads(response)
        temp = []
        ret = ""
        if weatherInfo['cod'] != "404":
            main = weatherInfo['list']

            for temp in main:
                currentTimeDate = datetime.datetime.now() + datetime.timedelta(days=1)
                now = currentTimeDate.strftime('%Y-%m-%dT%H:%M:%S')
                if (temp['dt_txt'] <= now):
                    temp1 = temp['weather']
                    ret += "weather: " + str(temp1[0]['description']) + "-"
                    temp2 = temp['main']
                    ret += "Temperature: " + str(temp2['temp']) + "-"
                    ret += "Feel: " + str(temp2['temp_max']) + "-"
                    ret += "Time: " + str(temp['dt_txt']) + "-"
                    ret += "|"
        return ret

    def geoFinder(self, city, country):
        key = "12777322a4074455aa52e944ee0eaff1"
        query = '{city}, {country}'.format(city=city, country=country)
        results = geocoder(key).geocode(query)
        ret = []
        for potcity in results:
            if (potcity['confidence'] >= 9):
                retval = potcity['geometry']
                ret.append(retval['lat'])
                ret.append(retval['lng'])
                return ret


if __name__ == '__main__':
    server = Server()
    server.starts()
