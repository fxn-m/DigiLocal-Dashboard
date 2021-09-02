from math import radians, cos, sin, asin, sqrt

def haversine(lon1, lat1, lon2, lat2):
    # convert decimal degrees to radians 
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    # haversine formula 
    dlon = lon2 - lon1 
    dlat = lat2 - lat1 
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a)) 
    # Radius of earth in kilometers is 6371
    m = 6371* c *1000
    return m

def setcolour(x):
    if (x < 4) or (x == 8):
        return "#90EE90" #LightGreen
    elif x == 5 or x == 6 or x == 9:
        return "#FFA07A" #LightSalmon
    elif x == 4 or x == 7 or x == 10:
        return "#F08080" #LightCoral