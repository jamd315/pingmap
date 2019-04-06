import json
import urllib.parse

import pandas as pd
import requests

with open("creds.json", "r") as f:
    creds = json.load(f)

gmaps_key = creds["gmaps_key"]
ipdata_co_key = creds["ipdata_co_key"]


def locate_ip(ip_str):
    r = requests.get("https://api.ipdata.co/{}?api-key={}".format(ip_str, ipdata_co_key))
    obj = r.json()
    return obj["latitude"], obj["longitude"]


def locate_street_address(address):
    params = urllib.parse.urlencode({"address": address, "key": gmaps_key})
    r = requests.get("https://maps.googleapis.com/maps/api/geocode/json?{}".format(params))
    json_obj = r.json()
    try:
        lat = json_obj["results"][0]["geometry"]["location"]["lat"]
        lon = json_obj["results"][0]["geometry"]["location"]["lng"]
    except:
        print(json_obj)
        return
    return lat, lon


if __name__ == "__main__":
    df = pd.read_json("client_locations.json")
    df["ip_lat"] = 0
    df["ip_lon"] = 0
    df["lat"] = 0
    df["lon"] = 0
    df[["ip_lat", "ip_lon"]] = list(df["ip"].apply(locate_ip))
    df[["lat", "lon"]] = locate_street_address("1600 Pennsylvania Ave NW")
    print(df.head())