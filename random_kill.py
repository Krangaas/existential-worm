#!/usr/bin/env python3

import os
import argparse
import random
import time

def main(args):
    kills = 0
    host_list = []
    with open("host_list.txt", mode="r") as f:
        for line in f:
            host_list.append(line.splitlines()[0])
    print(host_list)
    random.shuffle(host_list)

    for host in host_list:
        cmd = "curl -X POST 'http://%s/kill_worms'" %(host)
        print(cmd)
        #os.system(cmd)
        kills += 1
        if kills == args.target:
            break
        time.sleep(args.sleep)



def parse_args():
    """ optarg parser """
    p = argparse.ArgumentParser()
    p.add_argument("-t", "--target", required=False, type=int, default=1,
        help ="Default: 1 | Number of segments to kill")
    p.add_argument("-s", "--sleep", required=False, type=int, default=0,
        help ="Default: 10 | Time between each kill")

    args = p.parse_args()
    return args

if __name__ == "__main__":
    args = parse_args()
    main(args)
