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
    os.system("shuf -i 49152-65535 -n 3 | sed 's/^/localhost:/' > host_list.txt")
    hosts = []
    with open("host_list.txt", mode="r") as f:
        for line in f:
            hosts.append(line.splitlines()[0])
    entry_gate = hosts[0]
    for i in range(len(hosts)):
        udp = random.randint(49152, 65535)
        hosts[i] = hosts[i]+ "@%d" %(udp)

    # localhost:8000@9000_localhost:8000@9000_localhost:8000@9000__localhost:8001@9001
    arg = hosts[0] + ARG_DELIM + hosts[0] + ARG_DELIM + hosts[0] + ARG_DELIM + ARG_DELIM
    for host in hosts:
        if host == hosts[0]:
            continue
        else:
            arg = arg + host + "*"
    arg = arg[:-1]
    print(arg)
    os.system("./make_python_zip_executable.sh jormen")
    subprocess.Popen("cat host_list.txt | ./wormgates_start.sh", shell=True)
    cmd = "curl -X POST 'http://%s/worm_entrance?args='%s'' --data-binary @jormen.bin" %(entry_gate, arg)
    print(cmd)
    time.sleep(2)
    os.system(cmd)





































def parse_args():
    """ optarg parser """
    p = argparse.ArgumentParser()
    p.add_argument("-e", "--env", required=False, type=str, default="cluster",
        help ="Default: cluster | Specify environment. Valid inputs are: (cluster | local)")

    p.add_argument("-w", "--wormgates", required=False, type=int, default=8,
        help ="Default: 8 | Number of wormgates to use")

    p.add_argument("-D", "--debug", required=False, type=int, default=0,
        help ="Default: 0 | if 1, print resultant terminal commands and exit")

    args = p.parse_args()
    return args

if __name__ == "__main__":
    args = parse_args()
    main(args)
