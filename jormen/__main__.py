#!/usr/bin/env python3
import os
import sys
import random
import socket
import time

# localhost:8000@9000_localhost:8000@9000_localhost:8000@9000__localhost:8001@9001
ARG_DELIM = "_"
KEYVAL_DELIM = "@"
DICT_DELIM = "*"


class Jorm:
    def __init__(self, leader, mygate, active, bucket, available):
        self.jormpack = os.path.abspath(sys.argv[0])
        self.target = 2
        self.segment_sr = 0        # ratio | send/recv ratio between segment and leader
        self.active = active       # host-port -> wormUDP | wormgates with currently active worms
        self.bucket = bucket       # host-port -> wormUDP | wormgates with currently unresponsive worms
        self.available = available # host-port -> wormUDP | wormgates that are currently unused

        self.mygate = mygate
        self.leader = leader # bool | leader flag
        self.leader_sr_map = {}    # host-port -> ratio | send/recv ratio between leader and segments

        # populate send/recv map with wormgate host-port of active worms

        self.infodump()
        if self.mygate == self.leader:
            for key in self.active:
                if key in self.mygate:
                    pass
                self.leader_sr_map[key] = 0
            self.leader_flood()
        else:
            self.segment_flood()

    def infodump(self):
        print("___________INFO___________")
        print("target:%d (%d)" %(self.target, len(self.active)))
        print("active", self.active)
        print("bucket", self.bucket)
        print("avail", self.available)
        print("leader", self.leader)
        print("self", self.mygate)
        print("leader sr", self.leader_sr_map)
        print("jormpack", self.jormpack)
        print("__________________________")


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
        try:
            name, gate = self.available.popitem()
        except:
            print("go to bucket")
            return
        ret = name + KEYVAL_DELIM + gate
        self.active[name] = gate
        self.leader_sr_map[name] = 0
        return ret, name, gate

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
            if len(self.active) < self.target:
                self.spawn_worm()
            self.infodump()
            self.update_worms()
            time.sleep(2)
            #try:
            #    self.read_msg()
            #except:
            #    print("timed out(leader loop), retrying...")
            #    time.sleep(1)
            #    continue

    def segment_flood(self):
        """ Main loop for segments """
        while True:
            try:
                self.read_msg()
                #self.inform_leader()
            except:
                print("timed out(segment loop), retrying...")
                continue
            time.sleep(2)

    def election(self):
        """ Initiate election """

    def update_worms(self):
        self_name = list(self.leader.keys())[0]
        self_udp = int(self.leader[self_name])
        self_name = self_name.split(":")[0]

        for target_key, target_udp in self.active.items():
            if target_key in self.mygate.keys():
                continue
            target_name = target_key.split(":")[0]
            target_udp = int(target_udp)

            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.bind((self_name, self_udp))
            sock.setblocking(False)
            #sock.settimeout(2)
            msg = b"localhost:8000, hello from Jorm"
            #msg = str.encode(msg)
            sock.sendto(msg, (target_name, target_udp))
            self.leader_sr_map[target_key] += 1
            print("Updated", target_key)
        return


    def read_msg(self):
        self_name = list(self.mygate.keys())[0]
        self_udp = int(self.mygate[self_name])
        self_name = self_name.split(":")[0]

        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(2)
        sock.bind((self_name, self_udp))
        recv_msg = sock.recv(1024)
        key = recv_msg.split(",")
        #if self.leader == self.mygate:
        #    self.leader_sr_map[key] -= 1
        #elif key == list(self.leader.keys())[0]:
        #    self.segment_sr -= 1
        #else:
        #    # send hold on msg
        #    pass
        print("got message:", recv_msg)


    def inform_leader(self):
        self_name = list(self.mygate.keys())[0]
        self_udp = int(self.mygate[self_name])
        self_name = self_name.split(":")[0]

        leader_name = list(self.leader.keys())[0]
        leader_udp = int(self.leader[leader_name])
        leader_name = leader_name.split(":")[0]

        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind((self_name, self_udp))
        sock.setblocking(False)
        sock.settimeout(2)
        msg = b"localhost:8001, hello from segment"
        msg = str.encode(msg)
        sock.sendto(msg, (leader_name, leader_udp))
        self.segment_sr += 1
        print("Informed leader")


def parse_args(str):
    """ Argument parser. Expects a string with arguments delimited by _ """
    args = str.split(ARG_DELIM)
    for i in range(len(args)):
        dict = {}
        if args[i] == "":
            args[i] = dict
        else:
            pairs = args[i].split(DICT_DELIM)
            for p in pairs:
                key, val = p.split(KEYVAL_DELIM)
                dict[key] = val
            args[i] = dict
    return args


def dict_to_string(arg):
    ret = ""
    for key in arg:
        ret = ret + key + KEYVAL_DELIM + arg[key] + DICT_DELIM

    return ret[:-1]


if __name__ == "__main__":
    args = parse_args(sys.argv[1])
    Jorm(args[0], args[1], args[2], args[3], args[4])



    # localhost:8000@9000_localhost:8000@9000_localhost:8000@9000__localhost:8001@9001










#
