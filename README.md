# INF-3200-Ormen-Lange

==================================================
The following command will display the help text for the initialization script that generate host-port pairs and UDP ports, makes the worm script executable, starts the wormgates and finally injects the worm into the network.
```
        python3 init.py -h
```

The following command will display the help text for the test script that randomly crashes segments.
```
        python3 random_kill.py -h
```

The following command will set up a local network of 20 wormgates and inject a worm that will grow to a target size of 15.
.
```
        python3 init.py -e local -w 20 -t 15
```

The following sequence of commands will set up a network of 40 wormgates on the cluster and inject a worm that will grow to a traget size of 20. Then, the kill script will choose 10 wormgates uniformly at random and kill their respective worms. In this case the leader is eligible to be killed as well.
**NOTE:** The worm might behave badly if segments are killed before the worm has grown to its target size.
```
        python3 init.py -e cluster -w 20 -t 15
        python3 random_kill.py -t 10
```
