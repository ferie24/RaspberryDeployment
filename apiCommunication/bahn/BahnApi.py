
import csv
import datetime
import requests
import json


class BahnApi:
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
        evaNR = self.stationConfig(ray, time_now_output)
        ray = station.split('_')
        if evaNR == 'error':
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
            if temp4[0] > time_now and ray[2] == temp1['name']:
                print(time_now_output, temp1['name'], "-", temp2['time'])
                return temp1['name'] + " " + temp2['time']