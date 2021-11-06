#!/usr/bin/python

"""
This setup the topology in lab3-part1
"""

from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import Controller, RemoteController
from mininet.cli import CLI
from mininet.log import setLogLevel, info
from mininet.util import dumpNodeConnections
from mininet.link import Link, Intf, TCLink
import os 
from time import sleep
import sys

N=input("port number: ")
host = [0 for _ in range(N*N//2)]
core = [0 for _ in range(N//2)]
switch = [0 for _ in range(N)]
class Topology(Topo):
    
    
    def __init__(self):
        "Create Topology."
        
        # Initialize topology
        Topo.__init__(self)
        #
        #
        # #### There is a rule of naming the hosts and switch, so please follow the rules like "h1", "h2" or "s1", "s2" for hosts and switches!!!!
        #
        # # Add hosts
        # host1 = self.addHost('h1', ip='10.0.0.1/24')
        #
        #
        # # Add switches
        # swA = self.addSwitch('s1')
        # swB = self.addSwitch('s2')
        #
        #
        # self.addLink(host1, swA)
        # self.addLink(swA, swB, 2, 2)    # Connect port 1 of switch A with port 2 of switch B

        # Add hosts
        for i in range(N * N // 2):
            hostname='host%s'%(i+1)
            host[i]=self.addHost(hostname)

        # Add switches
        for i in range(N):
            switchname='switch%s'%(i+1)
            switch[i]=self.addSwitch(switchname)
        #Add core
        for j in range(N//2):
            corename='core%s'%(j+1)
            core[j]=self.addSwitch(corename)

        # Link between host and L1 switch
        for i in range(N):
            for j in range(N*N//2):
                self.addLink(host[j],switch[i])

        #Link between switch to core
        for i in range(N//2):
            for j in range(N):
                self.addLink(core[i],switch[j])



# This is for "mn --custom"
topos = { 'mytopo': ( lambda: Topology() ) }




# This is for "python *.py"
if __name__ == '__main__':
    setLogLevel( 'info' )
            
    topo = Topology()
    net = Mininet(topo=topo, link=TCLink)       # The TCLink is a special setting for setting the bandwidth in the future.
    
    # 1. Start mininet
    net.start()
    
    
    # Wait for links setup (sometimes, it takes some time to setup, so wait for a while before mininet starts)
    print "\nWaiting for links to setup . . . .",
    sys.stdout.flush()
    for time_idx in range(3):
        print ".",
        sys.stdout.flush()
        sleep(1)
    
        
    # 2. Start the CLI commands
    info( '\n*** Running CLI\n' )
    CLI( net )
    
    
    # 3. Stop mininet properly
    net.stop()


    ### If you did not close the mininet, please run "mn -c" to clean up and re-run the mininet 