#http traffic with port 80 H1->H2 
sudo ovs-ofctl add-flow s1 in_port=1,priority=100,dl_type=0x0800,nw_proto=6,tcp_dst=80,action=output:2
sudo ovs-ofctl add-flow s2 in_port=1,priority=100,dl_type=0x0800,nw_proto=6,tcp_dst=80,action=output:3
sudo ovs-ofctl add-flow s5 in_port=1,priority=100,dl_type=0x0800,nw_proto=6,tcp_dst=80,action=output:4

#other traffic H1->H2 
sudo ovs-ofctl add-flow s1 in_port=1,priority=0,actions=output:3
sudo ovs-ofctl add-flow s3 in_port=1,priority=0,actions=output:2
sudo ovs-ofctl add-flow s4 in_port=2,priority=0,actions=output:3
sudo ovs-ofctl add-flow s5 in_port=2,priority=0,actions=output:4

#http traffic with port 80 H2->H1 
sudo ovs-ofctl add-flow s5 in_port=4,priority=100,dl_type=0x0800,nw_proto=6,tcp_src=80,action=output:3
sudo ovs-ofctl add-flow s3 in_port=3,priority=100,dl_type=0x0800,nw_proto=6,tcp_src=80,action=output:1
sudo ovs-ofctl add-flow s1 in_port=3,priority=100,dl_type=0x0800,nw_proto=6,tcp_src=80,action=output:1

#other traffic H2->H1 
sudo ovs-ofctl add-flow s5 in_port=4,priority=0,actions=output:1
sudo ovs-ofctl add-flow s2 in_port=3,priority=0,actions=output:2
sudo ovs-ofctl add-flow s4 in_port=1,priority=0,actions=output:2
sudo ovs-ofctl add-flow s3 in_port=2,priority=0,actions=output:1
sudo ovs-ofctl add-flow s1 in_port=3,priority=0,actions=output:1