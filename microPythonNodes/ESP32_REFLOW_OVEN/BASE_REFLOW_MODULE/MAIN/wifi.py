import network

max_wait = 10

def wlanConnect(ssid, password):
    global max_wait
    wlan = network.WLAN(network.STA_IF)
    if not wlan.isconnected():
        wlan.active(True)
        wlan.connect(ssid, password)
        print('Connecting to: %s' % ssid)
        timeout = time.ticks_ms()
        while not wlan.isconnected():
            time.sleep(0.15)
            if (time.ticks_diff (time.ticks_ms(), timeout) > 15000):
                break
        if wlan.isconnected():
            print('Successful connection to: %s' % ssid)
            print('IP: %s\nSUBNET: %s\nGATEWAY: %s\nDNS: %s' % wlan.ifconfig()[0:4])
        else:
            wlan.active(False)
            print('Failed to connect to: %s' % ssid)
    else:
        print('Connected\nIP: %s\nSUBNET: %s\nGATEWAY: %s\nDNS: %s' % wlan.ifconfig()[0:4])
    return wlan