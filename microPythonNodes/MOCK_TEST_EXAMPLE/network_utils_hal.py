'''
Menymp mar 2026

this hardware abstraction layer is intended to decouple common abstraction layer classes for python versions

for use in windows

these utilities are 

'''
import socket
from uuid import getnode as get_mac_addr

class network_utils_hal():
    def get_ip(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        print(ip)
        s.close()
        return ip

    def get_mac(self):
        mac = get_mac_addr()
        mac_formatted = ':'.join(("%012X" % mac)[i:i+2] for i in range(0, 12, 2))
        print(mac_formatted)
        return mac_formatted