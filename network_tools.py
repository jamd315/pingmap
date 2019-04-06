"""
http://courses.cs.vt.edu/cs4254/fall04/slides/raw_6.pdf
https://osqa-ask.wireshark.org/questions/11061/icmp-checksum
https://people.eecs.berkeley.edu/~istoica/tmp/i3-stable/i3_client/ping.h
"""
import os
import socket
import json
import struct
import time
import statistics


def int_to_ip(i):
    return socket.inet_ntoa(struct.pack("!L", i))


class ICMP_header:
    def __init__(self, type_=None, code=None, checksum=None, ID=None, seq=None):
        self.type = type_
        self.code = code
        self.checksum = checksum
        self.ID = ID
        self.seq = seq

    def calc_checksum(self):
        # Sum the WORDs and get the complement
        self.checksum = 0
        words_sum = 0
        words_sum += self.type << 8
        words_sum += self.checksum
        words_sum += self.ID
        words_sum += self.seq
        words_sum &= 0xFFFF
        self.checksum = ~words_sum
        self.checksum &= 0xFFFF  # Clamp to u_short

    def get_payload(self):
        return struct.pack("!BBHHH", self.type, self.code, self.checksum, self.ID, self.seq)

    @staticmethod
    def from_bytes(data):
        return ICMP_header(*struct.unpack("!BBHHH", data))

    def __str__(self):
        return str(self.__dict__)

    def __repr__(self):
        return self.__str__()


class IP_header:
    def __init__(self, version, header_len, service_type, total_length, ID, flags, TTL, protocol, checksum, iaSrc, iaDst):
        self.version = version
        self.header_len = int(header_len * 32 / 8)  # Number of WORDs (32 bit number) stored as bytes
        self.service_type = service_type  # DCSP
        self.total_length = total_length
        self.ID = ID
        flag_dict = {
            0b0000: "Default",
            0b0001: "Don't Fragment",
            0b0010: "More Fragments"
        }
        self.flags = flag_dict[flags]
        self.TTL = TTL
        self.protocol = "ICMP" if protocol == 1 else "Not ICMP"
        self.checksum = checksum
        self.iaSrc = int_to_ip(iaSrc)
        self.iaDst = int_to_ip(iaDst)
    
    @staticmethod
    def from_bytes(data):
        VIHL, service_type, total_length, ID, flags, TTL, protocol, checksum, iaSrc, iaDst = struct.unpack("!BBhhhBBHII", data)
        ver = VIHL & 0b111100000 >> 4
        hdr_len = VIHL & 0b00001111
        return IP_header(
            version=ver,
            header_len=hdr_len,
            service_type=service_type,
            total_length=total_length,
            ID=ID,
            flags=flags,
            TTL=TTL,
            protocol=protocol,
            checksum=checksum,
            iaSrc=iaSrc,
            iaDst=iaDst
        )
    
    def __str__(self):
        return self.__repr__()
    
    def __repr__(self):
        return str(self.__dict__)


def resolve_to_ip(ip_or_addr):
    try:
        return socket.gethostbyname(ip_or_addr)
    except socket.gaierror:
        print("Failed to resolve {}".format(ip_or_addr))
        return False


def ping(ip_str, seq=1):
    """Pings an ip and returns the time in ms, or -1 if it fails"""
    ip_str = resolve_to_ip(ip_str)
    if not ip_str:
        return -1
    ICMP_request = ICMP_header(8, 0, 0, os.getpid(), seq)
    ICMP_request.calc_checksum()
    with socket.socket(socket.AF_INET, socket.SOCK_RAW, 1) as sock:
        sock.settimeout(1)
        sock.connect((ip_str, 1))
        t1 = time.time()
        sock.send(ICMP_request.get_payload())
        try:
            resp = sock.recv(1024)
            t2 = time.time()
        except socket.timeout:
            return -1  # Failed to connect
    IP_response = IP_header.from_bytes(resp[:20])
    ICMP_response = ICMP_header.from_bytes(resp[20:])
    if ICMP_response.type == 0 and ICMP_response.code == 0 and ICMP_response.seq == ICMP_request.seq:
        #time.sleep(1)
        return (t2 - t1) * 1000
    return -1


if __name__ == "__main__":
    print("Pinging 8.8.8.8 100 times...")
    times = [ping("8.8.8.8", i) for i in range(100)]
    print("Mean:  ", statistics.mean(times))
    print("Stdev: ", statistics.stdev(times))
