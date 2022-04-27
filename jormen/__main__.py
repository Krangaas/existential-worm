#!/usr/bin/env python3
import os
import sys
import random
import socket

# localhost:8000@9000_localhost:8000@9000___localhost:8001@9001
ARG_DELIM = "_"
KEYVAL_DELIM = "@"
DICT_DELIM = "*"


class Jorm:
    def __init__(self, leader, mygate, active, bucket, available):
        self.jormpack = os.path.abspath(sys.argv[0])
        self.segment_sr = 0        # ratio | send/recv ratio between segment and leader
        self.active = active       # host-port -> wormUDP | wormgates with currently active worms
        self.bucket = bucket       # host-port -> wormUDP | wormgates with currently unresponsive worms
        self.available = available # host-port -> wormUDP | wormgates that are currently unused

        self.mygate = mygate
        self.leader = leader # bool | leader flag
        self.leader_sr_map = {}    # host-port -> ratio | send/recv ratio between leader and segments

        # populate send/recv map with wormgate host-port of active worms
        for key in self.active:
            self.leader_sr_map[key] = 0
        self.infodump()
        if self.mygate == self.leader:
            self.spawn_worm()

    def infodump(self):
        print("active", self.active)
        print("bucket", self.bucket)
        print("avail", self.available)
        print("leader", self.leader)
        print("self", self.mygate)
        print("leader sr", self.leader_sr_map)
        print("jormpack", self.jormpack)


    def spawn_worm(self):
        yourgate, target_wormgate, target_wormUDP = self.pick_available_gate()
        leader = dict_to_string(self.leader)
        active = dict_to_string(self.active)
        bucket = dict_to_string(self.bucket)
        available = dict_to_string(self.available)
        args = leader + ARG_DELIM + yourgate + ARG_DELIM + active + ARG_DELIM + bucket + ARG_DELIM + available
        cmd = "curl -X POST 'http://%s/worm_entrance?args='%s'' --data-binary @%s" %(target_wormgate, args, self.jormpack)
        print(cmd)
        os.system(cmd)

    def pick_available_gate(self):
        key, val = self.available.popitem()
        ret = key + KEYVAL_DELIM + val
        self.active[key] = val
        return ret, key, val

    def core(self):
        """ Core loop """
        while True:
            if self.leader == self.mygate:
                self.leader_flood()
            else:
                self.segment_flood()

            self.election()

    def leader_flood(self):
        """ Main loop for the leader """
        while True:
            pass

    def segment_flood(self):
        """ Main loop for segments """
        while True:
            pass

    def election(self):
        """ Initiate election """

    def update_worm(self, host, port, args):
        host_name = host.split(":")[0]
        print("hostname:",host_name)
        print("port:",port)

        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        udp_host = socket.gethostname()
        print("udp_host:", udp_host)
        upd_port = port
        print("mygate: ", self.mygate)

        sock.bind((udp_host,upd_port))
        msg = b"hello from Jorm"

        while True:
            print ("waiting...")
            data,addr = sock.recvfrom(1024)
            print("Recieved:", data, "from", addr)
            sock.sendto(msg, (host_name, 45000))


def parse_args(str):
    """ Argument parser. Expects a string with arguments delimited by _ """
    print(str)
    args = str.split(ARG_DELIM)
    print(args)
    print("arg0")
    args[0] = string_to_dict(args[0])
    print("arg1")
    args[1] = string_to_dict(args[1])
    print("arg2")
    args[2] = string_to_dict(args[2])
    print("arg3")
    args[3] = string_to_dict(args[3])
    print("arg4")
    args[4] = string_to_dict(args[4])
    return args

def string_to_dict(arg):
    dict = {}
    if arg == "":
        return dict
    pairs = arg.split('*')
    for i in pairs:
        print(i.split('@'))
        key, val = i.split('@')
        dict[key] = val
    return dict

def dict_to_string(arg):
    ret = ""
    for key in arg:
        ret = ret + key + KEYVAL_DELIM + arg[key] + DICT_DELIM

    return ret[:-1]

if __name__ == "__main__":
    print(sys.argv)
    print(os.path.abspath(sys.argv[0]))
    args = parse_args(sys.argv[1])
    Jorm(args[0], args[1], args[2], args[3], args[4])


    # localhost:8000@9000_localhost:8000@9000___localhost:8001@9001
