#!/usr/bin/env python3
import os
import argparse
import socket


def main(args):

    target_size = args.target_size
    leader_name, leader_udp = args.target.split(":")

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
    sock.setblocking(False)
    #sock.bind((self_name, self_udp))
    msg = "target,%s" %(target_size)
    msg = str.encode(msg)
    sock.sendto(msg, (leader_name, int(leader_udp)))
    sock.close()

def parse_args():
    """ optarg parser """
    p = argparse.ArgumentParser()
    p.add_argument("-s", "--target_size", required=False, type=int, default=1,
        help ="Default: 1 | grow to size")
    p.add_argument("-t", "--target", required=True, type=str,
        help = "host:udp pair of leader")

    args = p.parse_args()
    return args

if __name__ == "__main__":
    args = parse_args()
    print(args)
    main(args)