#!/usr/bin/env python3

import os
import subprocess
import argparse
import random
import time

ARG_DELIM = "_"
KEYVAL_DELIM = "@"
DICT_DELIM = "*"

def main(args):
    """  """
    # generate host port pairs
    if args.env == "local":
        gen_cmd = "shuf -i 49152-65535 -n %d | sed 's/^/localhost:/' > host_list.txt" %(args.wormgates)
        os.system(gen_cmd)
    elif args.env == "cluster":
        gen_cmd = "./generate_hosts.sh %d" %(args.wormgates)
        os.system(gen_cmd)
        host_list = []
        with open('host_list.txt', mode='r') as f:
            for line in f:
                port = random.randint(49152, 65535)
                host = line.splitlines()[0]
                # add port number to addresses
                host_list.append(host + ":" + str(port)+ "\n")
        with open('host_list.txt', mode="w") as f:
            f.writelines(host_list)

    hosts = []
    host_udp = []

    # append host port pairs to list
    with open("host_list.txt", mode="r") as f:
        for line in f:
            hosts.append(line.splitlines()[0])

    # generate udp port in ephemeral port range and append to host-port-udp list
    for i in range(len(hosts)):
        udp = random.randint(49152, 65535)
        host_udp.append(hosts[i] + KEYVAL_DELIM + str(udp))

    # This file is strictly used for demo purposes
    with open("host_udp.txt", mode="w") as f:
        for entry in host_udp:
            f.write(entry + "\n")

    # generate wormgate input argument in this format:
    # localhost:8000@9000_localhost:8000@9000_localhost:8000@9000__localhost:8001@9001
    arg = host_udp[0] + ARG_DELIM + host_udp[0] + ARG_DELIM + host_udp[0] + ARG_DELIM + ARG_DELIM
    for host in host_udp:
        if host == host_udp[0]:
            continue
        else:
            arg = arg + host + DICT_DELIM
    arg = arg[:-1] + ARG_DELIM + str(args.target)
    print(arg)
    # make worm code executable
    os.system("./make_python_zip_executable.sh jormen")

    # start wormgates in new terminals
    if args.env == "local":
        for host in hosts:
            p = host.split(":")[1]
            cmd = "gnome-terminal -e 'bash -c \"python3 wormgate.py -p %s\"'" %(p)
            os.system(cmd)
    elif args.env == "cluster":
        cmd = "cat host_list.txt | ./wormgates_start.sh"
        os.system(cmd)

    time.sleep(2)

    # inject worm package
    cmd = "curl -X POST 'http://%s/worm_entrance?args='%s'' --data-binary @jormen.bin" %(hosts[0], arg)
    os.system(cmd)




def parse_args():
    """ optarg parser """
    p = argparse.ArgumentParser()
    p.add_argument("-e", "--env", required=False, type=str, default="cluster",
        help ="Default: cluster | Specify environment. Valid inputs are: (cluster | local)")

    p.add_argument("-w", "--wormgates", required=False, type=int, default=8,
        help ="Default: 3 | Number of wormgates to use")

    p.add_argument("-t", "--target", required=False, type=int, default=3,
        help ="Default: 3 | Target worm  segment length")

    args = p.parse_args()
    return args

if __name__ == "__main__":
    args = parse_args()
    main(args)
