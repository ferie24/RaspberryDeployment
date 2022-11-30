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


class Server(object):
    def __init__(self, host='', port=9999):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind((host, port))
        self.socket.listen(10)
        self.clients = []
        self.clientanzahl = 0
        self.real = False

    def start(self):
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
                ret = 'Bahn_' + Bahn_Api().retAnMain(data)
                self.send_data(clientsocket, ret)
            if command == "weather":
                city, country = data.split("-")
                ret = "Wetter_" + Weather().retanMain(city, country)
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


class Bahn_Api:
    def __init__(self):
        self.time_test = None
        self.evaNR = None
        self.time_now = None

    def stationConfig(self, ray, time_now_output):
        print(time_now_output, ray[0], ray[1], ray[2])  # 0 ist die Stadt und 1 ist die Station und 2 ist der Zug
        with open('../../../../Desktop/asdf/D_Bahnhof_2020_alle.csv') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                temp1 = row['EVA_NR;DS100;IFOPT;NAME;Verkehr;Laenge;Breite;Betreiber_Name;Betreiber_Nr;Status;']
                temp2 = temp1.split(';')
                try:
                    temp3 = temp2[3].split("-")
                    if (temp3[0] == ray[0] and temp3[1] == ray[1]):
                        return temp2[0]
                except:
                    pass

    def retAnMain(self, station):
        time_test = datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S') + ".00Z"
        time_now_output = datetime.datetime.now().strftime('%D:%H:%M:%S:')
        time_now = datetime.datetime.now().strftime('%H:%M:%S')
        ray = station.split('_')
        evaNR = Bahn_Api().stationConfig(ray, time_now_output)
        ray = station.split('_')
        if (evaNR == 'error'):
            return 'error'
        params = {
            'station': evaNR,
            'date': time_test,
            'profile': 'dbregio'
        }
        marudor = requests.get('https://marudor.de/api/hafas/v2/arrivalStationBoard', params=params).text
        marudorInfo = json.loads(marudor)
        for marudorTemp in marudorInfo:
            temp1 = marudorTemp['train']
            temp2 = marudorTemp['arrival']
            temp3 = temp2['time'].split('T')
            temp4 = temp3[1].split('.')
            if (temp4[0] > time_now and ray[2] == temp1['name']):
                print(time_now_output, temp1['name'], "-", temp2['time'])
                return (temp1['name'] + " " + temp2['time'])


class Weather():
    def init(self, lat, lon):
        key = "4cf6fec3a220ac5699c371800f684535"
        url = "https://api.openweathermap.org/data/2.5/forecast"
        unit = "metric"
        req = "{url}?lat={lat}&lon={lon}&appid={key}&units={unit}".format(url=url, lat=lat, lon=lon, key=key, unit=unit)
        return req

    def retanMain(self, city, country):
        cords = self.geofinder(city, country)
        req = self.init(cords[0], cords[1])
        response = requests.get(req).text
        weatherInfo = json.loads(response)
        temp = []
        if weatherInfo['cod'] != "404":
            main = weatherInfo['list']
            ret = ""
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

    def geofinder(self, city, country):
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
    server.start()
