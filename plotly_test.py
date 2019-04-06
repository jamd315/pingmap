import os
import subprocess
import socket
import json
import struct
import threading

import requests
import plotly
import plotly.plotly as py
import plotly.graph_objs as go
import pandas as pd

from network_tools import ping, resolve_to_ip


# Load credentials from creds.json
with open("creds.json", "r") as f:
    creds = json.load(f)

ipdata_co_key = creds["ipdata_co_key"]
gmaps_key = creds["gmaps_key"]
mapbox_token = creds["mapbox_token"]

    

def locate_ip(ip_str):
    """Use ipdata.co api to get lat and lon of a given ip"""
    r = requests.get("https://api.ipdata.co/{}?api-key={}".format(ip_str, ipdata_co_key))
    obj = r.json()
    return obj["latitude"], obj["longitude"]


def threaded_ping(df):
    """Accepts a pandas DataFrame with an ip column and adds a connection column with ping time in ms"""
    results = []
    def _ping_wrap(ip):
        results.append((ip, ping(ip)))
    threads = []
    for ip in df["ip"]:
        t = threading.Thread(target=_ping_wrap, args=(ip,))
        t.start()
        threads.append(t)
    for t in threads:
        t.join()
    results = pd.DataFrame(results, columns=["ip", "connection"])
    return df.merge(results, on="ip")


if __name__ == "__main__":
    df = pd.read_json("endpoints.json")
    print("Endpoints loaded from file...")
    df["ip"] = df["endpoint"].apply(resolve_to_ip)
    print("IP Addresses resolved...")
    df = threaded_ping(df)
    print("Pings finished...")
    df["lat"] = 0
    df["lon"] = 0
    df[["lat", "lon"]] = list(df["ip"].apply(locate_ip))
    print("IP Addresses located...")
    df["text"] = df["endpoint"] + "<br>" + df["connection"].astype(str).apply(lambda x: "{:.5}".format(x)) + "ms"

    scl = [[0,"rgb(0, 0, 255)"], [0.001, "rgb(0, 255, 0)"], [1,"rgb(255, 0, 0)"]]
    
    data = [
        go.Scattermapbox(
            lon = df["lon"],
            lat = df["lat"],
            text = df["text"],
            mode = "markers",
            marker = dict(
                color = df["connection"],
                size = 16,
                opacity = 0.8,
                colorscale = scl,
                cmin = -1,
                cmax = df["connection"].max()
            )
        )
    ]

    layout = dict(
            title = "AWS Connectivity", 
            mapbox = go.layout.Mapbox(
                accesstoken = mapbox_token,
                bearing = 0,
                center = go.layout.mapbox.Center(
                    lat = 39.5,
                    lon = -119.8
                ),
                pitch = 0,
                zoom = 10
            )
        )

    fig = go.Figure(data=data, layout=layout)
    plotly.offline.plot(fig, filename="connectionmap.html" )
    print("Showing map")