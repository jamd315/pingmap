import json

with open("client_locations.json", "r") as f:
    locations = json.load(f)
    

try:
    while True:
        ip = input("IP: ")
        if "stop" in ip:
            break
        addr = input("Address: ")
        locations.append({
            "ip": ip,
            "street_address": addr
        })
except KeyboardInterrupt:
    pass

with open("client_locations.json", "w") as f:
    json.dump(locations, f)