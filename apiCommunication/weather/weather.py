import requests
import json
import datetime
from opencage.geocoder import OpenCageGeocode as geocoder

class Weather():
    def init(self, lat, lon):
        key = ""
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
