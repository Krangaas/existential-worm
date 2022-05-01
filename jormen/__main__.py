#!/usr/bin/env python3
from hashlib import new
import os
from platform import node
import sys
import random
import socket
import time
import json
import ast

# localhost:8000@9000_localhost:8000@9000_localhost:8000@9000__localhost:8001@9001
ARG_DELIM = "_"
KEYVAL_DELIM = "@"
DICT_DELIM = "*"

class NewLeader(Exception): pass

class Jorm:
    def __init__(self, leader, mygate, active, bucket, available, target):
        self.jormpack = os.path.abspath(sys.argv[0])
        self.target = int(target)
        self.segment_sr = 0        # ratio | send/recv ratio between segment and leader
        self.active = active       # host-port -> wormUDP | wormgates with currently active worms
        self.bucket = bucket       # host-port -> wormUDP | wormgates with currently unresponsive worms
        self.available = available # host-port -> wormUDP | wormgates that are currently unused

        self.mygate = mygate
        self.leader = leader # bool | leader flag
        self.leader_sr_map = {}    # host-port -> ratio | send/recv ratio between leader and segments

        # populate send/recv map with wormgate host-port of active worms

        self.infodump()
        self.core()


    def infodump(self, all=False):
        print("___________INFO___________")
        if all:
            print("target:%d (%d)" %(self.target, len(self.active)))
            print("active", self.active)
            print("bucket", self.bucket)
            print("avail", self.available)
            print("leader", self.leader)
            print("self", self.mygate)
            print("jormpack", self.jormpack)
        if self.leader == self.mygate:
            print("leader sr", self.leader_sr_map)
        else:
            print("segment sr", self.segment_sr)
        print("__________________________")


    def spawn_worm(self):
        yourgate, target_wormgate, target_wormUDP = self.pick_available_gate()
        leader = dict_to_string(self.leader)
        active = dict_to_string(self.active)
        bucket = dict_to_string(self.bucket)
        available = dict_to_string(self.available)
        args = leader + ARG_DELIM + yourgate + ARG_DELIM + active + ARG_DELIM + bucket + ARG_DELIM + available + ARG_DELIM + str(self.target)
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
        try:
            while True:
                if self.leader == self.mygate:
                    for key in self.active:
                        if key in self.mygate:
                            pass
                        self.leader_sr_map[key] = 0
                    self.leader_flood()
                else:
                    self.segment_flood()
        except NewLeader:
            time.sleep(1)
            self.core()

            #self.election()


    def leader_flood(self):
        """ Main loop for the leader """
        while True:
            self.infodump(all=True)
            while len(self.active) < self.target:
                self.spawn_worm()
            self.update_worms()
            #time.sleep(2)
            try:
                self.read_msg()
            except socket.timeout:
                print("timed out(leader loop), retrying...")
                time.sleep(1)
                #continue


    def segment_flood(self):
        """ Main loop for segments """
        while True:
            try:
                self.segment_read_msg()
            except socket.timeout:
                print("No response from leader, timeout. Selecting new leader...")
                self.election()
            time.sleep(2)
            self.update_available()
            self.inform_leader()
            self.infodump(all=True)



    def election(self):
        """ Initiate election """

        del self.active[list(self.leader.keys())[0]]
        pop_segment = list(next(iter(self.active.items())))
        format_segment = "{" + "'" + pop_segment[0] + "'" + ":" + "'" + pop_segment[1] + "'" + "}"
        new_leader = ast.literal_eval(format_segment)
        self.leader = new_leader
        time.sleep(1)
        raise NewLeader


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
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
            sock.bind((self_name, self_udp))
            sock.setblocking(False)
            #sock.settimeout(2)
            msg = "update#%s" %(self.active)
            msg = str.encode(msg)
            sock.sendto(msg, (target_name, target_udp))
            self.leader_sr_map[target_key] += 1
        return


    def segment_read_msg(self):
        self_name = list(self.mygate.keys())[0]
        self_udp = int(self.mygate[self_name])
        self_name = self_name.split(":")[0]

        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        sock.settimeout(10)
        sock.bind((self_name, self_udp))
        recv_msg = sock.recv(1024)
        sock.close()
        key = recv_msg.decode().split("#")[0]

        if key == 'update':
            update_str = recv_msg.decode().split("#")[1]
            update_dict = ast.literal_eval(update_str)
            if self.active != update_dict:
                self.active = update_dict
            self.segment_sr = 0
        else:
            if self.leader == self.mygate:
                self.leader_sr_map[key] = 0
            elif key == list(self.leader.keys())[0]:
                self.segment_sr = 0
            else:
                # send hold on msg
                pass

    def update_available(self):
        delete_list = []
        for key in self.active:
            if key in self.available:
                delete_list.append(key)

        for seg in delete_list:
            del self.available[seg]



    def read_msg(self):
        self_name = list(self.mygate.keys())[0]
        self_udp = int(self.mygate[self_name])
        self_name = self_name.split(":")[0]

        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        sock.settimeout(2)
        sock.bind((self_name, self_udp))
        recv_msg = sock.recv(1024)
        sock.close()
        key = recv_msg.decode().split(",")[0]
        if self.leader == self.mygate:
            self.leader_sr_map[key] = 0
        elif key == list(self.leader.keys())[0]:
            self.segment_sr = 0
        else:
            # send hold on msg
            pass


    def inform_leader(self):
        self_name = list(self.mygate.keys())[0]
        self_udp = int(self.mygate[self_name])
        self_name = self_name.split(":")[0]

        leader_name = list(self.leader.keys())[0]
        leader_udp = int(self.leader[leader_name])
        leader_name = leader_name.split(":")[0]

        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        sock.bind((self_name, self_udp))
        sock.setblocking(False)
        sock.settimeout(2)
        msg = "%s, hello from segment" %(list(self.mygate.keys())[0])
        msg = str.encode(msg)
        sock.sendto(msg, (leader_name, leader_udp))
        self.segment_sr += 1


def parse_args(str):
    """ Argument parser. Expects a string with arguments delimited by _ """
    args = str.split(ARG_DELIM)
    target = args.pop()
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
    args.append(target)
    return args


def dict_to_string(arg):
    ret = ""
    for key in arg:
        ret = ret + key + KEYVAL_DELIM + arg[key] + DICT_DELIM

    return ret[:-1]


if __name__ == "__main__":
    args = parse_args(sys.argv[1])
    Jorm(args[0], args[1], args[2], args[3], args[4], args[5])



    # localhost:8000@9000_localhost:8000@9000_localhost:8000@9000__localhost:8001@9001










#
