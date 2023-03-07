# -*- coding: utf-8 -*-
import datetime
import geopy
import json
import requests
from collections import OrderedDict
from naomi import plugin
from naomi import profile


WEEKDAY_NAMES = {
    0: 'Monday',
    1: 'Tuesday',
    2: 'Wednesday',
    3: 'Thursday',
    4: 'Friday',
    5: 'Saturday',
    6: 'Sunday'
}


class NWSWeatherPlugin(plugin.SpeechHandlerPlugin):
    def __init__(self, *args, **kwargs):
        super(NWSWeatherPlugin, self).__init__(*args, **kwargs)
        self.user_agent = 'Naomi 1.0'

    def intents(self):
        return {
            'NWSWeatherIntent': {
                'locale': {
                    'en-US': {
                        'keywords': {
                            'ForecastKeyword': [
                                'WEATHER',
                                'FORECAST',
                                'WEATHER REPORT',
                                'WEATHER FORECAST'
                            ],
                            'WeatherTypePresentKeyword': [
                                'SNOWING',
                                'RAINING',
                                'WINDY',
                                'SLEETING',
                                'SUNNY'
                            ],
                            'WeatherTypeFutureKeyword': [
                                'SNOW',
                                'RAIN',
                                'BE WINDY',
                                'SLEET',
                                'BE SUNNY'
                            ],
                            'LocationKeyword': [
                                'SEATTLE',
                                'SAN FRANCISCO',
                                'TOKYO'
                            ],
                            'TimeKeyword': [
                                "MORNING",
                                "AFTERNOON",
                                "EVENING",
                                "NIGHT"
                            ],
                            'DayKeyword': [
                                "TODAY",
                                "TOMORROW",
                                "SUNDAY",
                                "MONDAY",
                                "TUESDAY",
                                "WEDNESDAY",
                                "THURSDAY",
                                "FRIDAY",
                                "SATURDAY"
                            ]
                        },
                        'templates': [
                            "WHAT IS THE {ForecastKeyword} IN {LocationKeyword}",
                            "WHAT IS THE {ForecastKeyword} FOR {DayKeyword}",
                            "WHAT IS THE {ForecastKeyword} FOR {LocationKeyword}",
                            "WHAT IS THE {ForecastKeyword} FOR {LocationKeyword} ON {DayKeyword}",
                            "WHAT IS THE {ForecastKeyword} FOR {LocationKeyword} ON {DayKeyword} {TimeKeyword}",
                            "IS IT {WeatherTypePresentKeyword} IN {LocationKeyword}",
                            "WILL IT {WeatherTypeFutureKeyword} THIS {TimeKeyword}",
                            "WILL IT {WeatherTypeFutureKeyword} {DayKeyword}",
                            "WILL IT {WeatherTypeFutureKeyword} {DayKeyword} {TimeKeyword}",
                            "WHEN WILL IT {WeatherTypeFutureKeyword}",
                            "WHEN WILL IT {WeatherTypeFutureKeyword} IN {LocationKeyword}"
                        ]
                    },
                    'fr-FR': {
                        'keywords': {
                            'WeatherTypePresentKeyword': [
                                'IL NEIGE',
                                'IL PLUIE',
                                'IL VENT'
                            ],
                            'WeatherTypeTodayFutureKeyword': [
                                'SERA-T-IL NEIGE',
                                'PLEUVRA-T-IL',
                                'DU VENT',
                                'SERA-CE VENTEUX',
                                'SERA-T-IL DU VENT',
                                'SERA-T-IL ENSOLEILLÉ'
                            ],
                            'WeatherTypeTomorrowFutureKeyword': [
                            ],
                            'LocationKeyword': [
                                'SEATTLE',
                                'SAN FRANCISCO',
                                'TOKYO'
                            ],
                            'TimeKeyword': [
                                "MATIN",
                                "MIDI",
                                "SOIR"
                            ],
                            'DayKeyword': [
                                "AUJOURD'HUI",
                                "DEMAIN",
                                "DIMANCHE",
                                "LUNDI",
                                "MARDI",
                                "MERCREDI",
                                "JEUDI",
                                "VENDREDI",
                                "SAMEDI"
                            ]
                        },
                        'templates': [
                            "QUELLE EST LA MÉTÉO À {LocationKeyword}",
                            "QUELLES SONT LES PRÉVISIONS POUR {DayKeyword}",
                            "QUELLES SONT LES PRÉVISIONS POUR {LocationKeyword}",
                            "QUELLES SONT LES PRÉVISIONS POUR {LocationKeyword} {DayKeyword}",
                            "QUELLES SONT LES PRÉVISIONS POUR {LocationKeyword} LE {DayKeyword} {TimeKeyword}",
                            "{WeatherTypePresentKeyword} À {LocationKeyword}",
                            "{WeatherTypeFutureKeyword} CET {TodayTimeKeyword}",
                            "{WeatherTypeFutureKeyword} {DayKeyword}",
                            "{WeatherTypeFutureKeyword} {DayKeyword} {TimeKeyword}",
                            "{WeatherTypeFutureKeyword}",
                            "{WeatherTypeFutureKeyword} À {LocationKeyword}"
                        ]
                    }
                },
                'action': self.handle
            }
        }

    def settings(self):
        _ = self.gettext
        return OrderedDict(
            [
                (
                    ('nws_weather', 'address'), {
                        'title': _('Please enter your city and state'),
                        'description': _('Please enter your city and state, which will be used to provide weather information')
                    }
                )
            ]
        )

    def handle(self, intent, mic):
        # Ideally, we could use our list of countries to check if any country
        # appears in the input, then check for regions in the current country,
        # and finally cities in the selected region, so I should be able to
        # ask for the weather in Paris, France and have it tell me even if my
        # base location is Hoboken, New Jersey.
        # For now we just check to see if "Today" or "Tomorrow" appear
        # in the text, and return the requested day's weather.
        # First, establish the cityId
        _ = self.gettext
        text = intent['input']
        # Generate the forecast url for the default address
        address = profile.get_profile_var(["nws_weather", "address"])
        # I was trying to pull the address from the template match strings
        # unfortunately, this matches so loosely that it usually just returns
        # a random garbage string.
        # for instance:
        #   input: KID MAGIC VOICE WHAT IS TODAY'S WEATHER FORECAST
        #   Matches:
        #       'ForecastKeyword': ['WEATHER', 'FORECAST']
        #       'LocationKeyword': ["TODAY'S FORECAST {ForecastKeyword}"]
        # if('LocationKeyword' in intent['matches']):
        #    for address in intent['matches']['LocationKeyword']:
        #        if address in 
        #    address = intent['matches']['LocationKeyword']
        if not (profile.get_profile_var(["nws_weather", address, 'gridId'])):
            geolocator = geopy.geocoders.Nominatim(user_agent=self.user_agent)
            location = geolocator.geocode(address)
            locationresponse = requests.get(
                f"https://api.weather.gov/points/{location.latitude},{location.longitude}",
                headers={'User-Agent': self.user_agent},
                timeout=2
            )
            jsondoc = str(locationresponse.content, 'utf-8')
            locationdata = json.loads(jsondoc)
            profile.set_profile_var(["nws_weather", address, "gridId"], locationdata['properties']['gridId'])
            profile.set_profile_var(["nws_weather", address, "gridX"], locationdata['properties']['gridX'])
            profile.set_profile_var(["nws_weather", address, "gridY"], locationdata['properties']['gridY'])
            profile.save_profile()
        gridId = profile.get_profile_var(["nws_weather", address, "gridId"])
        gridX = profile.get_profile_var(["nws_weather", address, "gridX"])
        gridY = profile.get_profile_var(["nws_weather", address, "gridY"])
        forecasturl = f"https://api.weather.gov/gridpoints/{gridId}/{gridX},{gridY}/forecast"
        snark = True
        if(forecasturl):
            forecastresponse = requests.get(
                forecasturl,
                headers={'User-Agent': self.user_agent},
                timeout=2
            )
            if(forecastresponse.status_code == 200):
                jsondoc = str(forecastresponse.content, 'utf-8')
                weatherdata = json.loads(jsondoc)
                forecast = {}
                for period in weatherdata['properties']['periods']:
                    forecastdate = period['startTime'][:10]
                    if not forecastdate in forecast:
                        forecast[forecastdate] = {}
                        forecast[forecastdate]['weather'] = []
                    forecast[forecastdate]["weather"].append(
                        _(
                            "{} the forecast is calling for {}"
                        ).format(
                            period['name'],
                            period["detailedForecast"]
                        )
                    )
                if(not forecast):
                    mic.say(
                        _("Sorry, forecast information is not currently available")
                    )
                today = datetime.date.today()
                todaydate = "{:4d}-{:02d}-{:02d}".format(
                    today.year,
                    today.month,
                    today.day
                )
                tomorrow = today + datetime.timedelta(days=1)
                tomorrowdate = "{:4d}-{:02d}-{:02d}".format(
                    tomorrow.year,
                    tomorrow.month,
                    tomorrow.day
                )
                if(_("today") in text.lower()):
                    if(todaydate in forecast.keys()):
                        for weatherforecast in forecast[todaydate]["weather"]:
                            mic.say(
                                weatherforecast
                            )
                        snark = False
                elif(_("tomorrow") in text.lower()):
                    if(tomorrowdate in forecast.keys()):
                        for weatherforecast in forecast[tomorrowdate]["weather"]:
                            mic.say(
                                weatherforecast
                            )                    
                        snark = False
                else:
                    for day in sorted(forecast.keys()):
                        for weatherforecast in forecast[day]["weather"]:
                            mic.say(
                                weatherforecast
                            )                    
                        snark = False
            else:
                raise Exception(forecastresponse.reason)
        else:
            mic.say("I have no location on record. Please run Naomi --repopulate and select a city.")
            snark = False
        if snark:
            mic.say(_("I don't know. Why don't you look out the window?"))
