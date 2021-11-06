"""Custom topology example
Two directly connected switches plus a host for each switch:
   host --- switch --- switch --- host
Adding the 'topos' dict with a key/value pair to generate our newly defined
topology enables one to pass in '--topo=mytopo' from the command line.
"""

from mininet.topo import Topo

class MyTopo( Topo ):
    "Simple topology example."

    def build( self ):
        "Create custom topo."

        # Add hosts and switches
        leftHost = self.addHost( 'h1' )
        rightHost = self.addHost( 'h2' )
        ovsa = self.addSwitch( 's1' )
        ovsb = self.addSwitch( 's2' )
        ovsc = self.addSwitch( 's3' )
        ovse = self.addSwitch( 's4' )
        ovsd = self.addSwitch( 's5' )

        # Add links
        self.addLink( leftHost, ovsa, 1, 1 )
        self.addLink( ovsa, ovsb, 2, 1 )
        self.addLink( ovsb, ovsd, 3, 1 )
        self.addLink( ovsa, ovsc, 3, 1)
        self.addLink( ovsc, ovse, 2, 2)
        self.addLink( ovse, ovsd, 3, 2)
        self.addLink( ovsb, ovse, 2, 1)
        self.addLink( ovsd, ovsc, 3, 3)
        self.addLink( ovsd, rightHost, 4, 1 )

topos = { 'mytopo': ( lambda: MyTopo() ) }