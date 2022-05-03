#!/usr/bin/env python3
from hashlib import new
import os
from platform import node
import sys
import random
import socket
import threading
import time
import json
import ast

# localhost:8000@9000_localhost:8000@9000_localhost:8000@9000__localhost:8001@9001
ARG_DELIM = "_"
KEYVAL_DELIM = "@"
DICT_DELIM = "*"
LOWER_SR_TRESHOLD = 50
UPPER_SR_TRESHOLD = 100
TIMEOUT = 10

class NewLeader(Exception): pass


# ToDo:
# Election                                                      # DONE
# spawn new segment if we don't receive a reply                 # DONE
# bruke bucket?                                                 # påbynt
# thread curl (SPEEDUP)                                         # tricky
# retry bucket                                                  # ez
# update segments with bucket and targets                       # ez
# generate host.sh


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
        self.time = True

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
        if len(self.available) != 0:
            yourgate, target_wormgate, target_wormUDP = self.pick_available_gate()
        else:
            if len(self.bucket) == 0:
                diff = self.target - len(self.active)
                self.target = self.target - diff
                return
            else:
                # BUCKET LOGIC
                pass

        leader = dict_to_string(self.leader)
        active = dict_to_string(self.active)
        bucket = dict_to_string(self.bucket)
        available = dict_to_string(self.available)
        args = leader + ARG_DELIM + yourgate + ARG_DELIM + active + ARG_DELIM + bucket + ARG_DELIM + available + ARG_DELIM + str(self.target)
        #THREAD THIS SHIT
        cmd = "curl -X POST 'http://%s/worm_entrance?args='%s'' --data-binary @%s" %(target_wormgate, args, self.jormpack)
        print(cmd)
        os.system(cmd)


    def pick_available_gate(self):
        try:
            name, gate = self.available.popitem()
        except:
            print("go to bucket")
            return -1
        ret = name + KEYVAL_DELIM + gate
        self.active[name] = gate
        self.leader_sr_map[name] = 0
        return ret, name, gate


    def core(self):
        """ Core loop """
        while True:
            try:
                if self.leader == self.mygate:
                    for key in self.active:
                        if key in self.mygate:
                            pass
                        self.leader_sr_map[key] = 0
                    self.leader_flood()
                else:
                    self.segment_flood()
            except NewLeader:
                pass


    def leader_flood(self):
        """ Main loop for the leader """
        if self.time == True:
            t1 = time.time()
        while True:
            self.infodump()
            if len(self.active) < self.target:
                self.spawn_worm()
                time.sleep(0.1)
            if self.time == True:
                if len(self.active) == self.target:
                    t2 = time.time()
                    t_tot = t2 - t1
                    print("____________TIME____________")
                    print("time taken to grow from 1 to ", self.target, " time: ", t_tot)
                    print("____________________________")
                    self.time = False

            self.update_worms()
            try:
                self.read_msg()
            except socket.timeout:
                self.unresponsive_segment()
            else:
                self.unresponsive_segment()


    def segment_flood(self):
        """ Main loop for segments """
        while True:
            try:
                self.segment_read_msg()
            except socket.timeout:
                print("No response from leader, timeout. Selecting new leader...")
                self.election()
            time.sleep(random.random())
            self.inform_leader()
            self.infodump(all=True)


    def unresponsive_segment(self):
        # assumes that the highest value in the leader_sr_map points to the unresponsive segment.
        segment = max(self.leader_sr_map, key=self.leader_sr_map.get)
        SR_value = self.leader_sr_map[segment]
        threshold = LOWER_SR_TRESHOLD
        if self.target > 10:
            threshold = UPPER_SR_TRESHOLD
        # conclude that a segment is unresponsive if we haven't received a reply within T sends.
        if SR_value > threshold:
            #move to bucket
            seg_udp = self.active[segment]
            #self.bucket[segment] = seg_udp
            del self.active[segment]        # delete unresponsive segment from self.active
            # although, we might not need to delete or even use a bucket. Since we dont care if a msg is received,
            # we can keep sending and listening to this segment in case it becomes responsive again.
            del self.leader_sr_map[segment]


    def election(self):
        """ Initiate election """

        del self.active[list(self.leader.keys())[0]]    # current leader not responsive, delete from self.active
        del self.leader[list(self.leader.keys())[0]]    # delete current leader from self.leader

        segment = list(self.active.keys())[0]   # pick first active segment
        seg_udp = self.active[segment]          # first active segment udp
        formatted_seg = "{" + "'" + segment + "'" + ":" + "'" + seg_udp + "'" + "}" # str formatting
        new_leader = ast.literal_eval(formatted_seg)                                # convert to dict
        self.leader = new_leader
        #self.recent_election = True

        raise NewLeader


    def new_leader_elected(self):
        # not in use
        self_name = list(self.leader.keys())[0]
        self_udp = int(self.leader[self_name])
        self_name = self_name.split(":")[0]

        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        sock.setblocking(False)
        sock.bind((self_name, self_udp))

        for target_key, target_udp in self.active.items():
            if target_key in self.mygate.keys():
                continue
            target_name = target_key.split(":")[0]
            target_udp = int(target_udp)
            msg = "election#%s#%s#%s" % (self.active, self.leader, self.available)
            msg = str.encode(msg)
            sock.sendto(msg, (target_name, target_udp))
        sock.close()


    def update_worms(self):
        """ UDP update; Inform segments about other segments that are active. """
        self_name = list(self.leader.keys())[0]
        self_udp = int(self.leader[self_name])
        self_name = self_name.split(":")[0]

        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        sock.setblocking(False)
        sock.bind((self_name, self_udp))

        # Send update to all segments in self.active
        for target_key, target_udp in self.active.items():
            if target_key in self.mygate.keys():
                continue
            target_name = target_key.split(":")[0]
            target_udp = int(target_udp)


            msg = "update#%s#%s" %(self.active, self.available)
            msg = str.encode(msg)
            sock.sendto(msg, (target_name, target_udp))
            self.leader_sr_map[target_key] += 1
        sock.close()


    def segment_read_msg(self):
        self_name = list(self.mygate.keys())[0]
        self_udp = int(self.mygate[self_name])
        self_name = self_name.split(":")[0]

        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        sock.settimeout(TIMEOUT)
        sock.bind((self_name, self_udp))
        recv_msg = sock.recv(1024)
        sock.close()
        key = recv_msg.decode().split("#")[0]

        if key == 'update':
            # update self.active and self.available
            active_dict = ast.literal_eval(recv_msg.decode().split("#")[1])
            avail = ast.literal_eval(recv_msg.decode().split("#")[2])
            if self.active != active_dict:
                self.active = active_dict
            if self.available != avail:
                self.available = avail
            self.segment_sr = 0
        else:
            if self.leader == self.mygate:
                self.leader_sr_map[key] = 0
            elif key == list(self.leader.keys())[0]:
                self.segment_sr = 0
            else:
                # send hold on msg
                pass


    def read_msg(self):
        self_name = list(self.mygate.keys())[0]
        self_udp = int(self.mygate[self_name])
        self_name = self_name.split(":")[0]

        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        sock.settimeout(TIMEOUT)
        sock.bind((self_name, self_udp))
        recv_msg = sock.recv(1024)

        sock.close()
        key = recv_msg.decode().split(",")[0]
        if self.leader == self.mygate:
            self.leader_sr_map[key] = 0


    def inform_leader(self):
        """ Ping leader, informing that segment is active. """
        self_name = list(self.mygate.keys())[0]
        self_udp = int(self.mygate[self_name])
        self_name = self_name.split(":")[0]

        leader_name = list(self.leader.keys())[0]
        leader_udp = int(self.leader[leader_name])
        leader_name = leader_name.split(":")[0]

        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        sock.setblocking(False)
        sock.bind((self_name, self_udp))

        msg = "%s, hello from segment" %(list(self.mygate.keys())[0])
        msg = str.encode(msg)
        sock.sendto(msg, (leader_name, leader_udp))
        sock.close()
        self.segment_sr += 1


    def update_available(self):
        delete_list = []
        for key in self.active:
            if key in self.available:
                delete_list.append(key)

        for seg in delete_list:
            del self.available[seg]


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
