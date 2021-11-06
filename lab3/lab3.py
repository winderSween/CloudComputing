from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet
from ryu.lib.packet import ether_types
from ryu.lib.packet import arp
from ryu.lib.packet import ipv4
from ryu.lib.packet import tcp
from ryu.lib.packet import icmp
from ryu.lib.packet import udp


class SimpleSwitch13(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(SimpleSwitch13, self).__init__(*args, **kwargs)
        self.mac_to_port = {}
        self.mac_to_port["10.0.0.1"] = "10:00:00:00:00:01"
        self.mac_to_port["10.0.0.2"] = "10:00:00:00:00:02"
        self.mac_to_port["10.0.0.3"] = "10:00:00:00:00:03"
        self.mac_to_port["10.0.0.4"] = "10:00:00:00:00:04"

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        # install table-miss flow entry
        #
        # We specify NO BUFFER to max_len of the output action due to
        # OVS bug. At this moment, if we specify a lesser number, e.g.,
        # 128, OVS will send Packet-In with invalid buffer_id and
        # truncated packet data. In that case, we cannot output packets
        # correctly.  The bug has been fixed in OVS v2.1.0.
        match = parser.OFPMatch()
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER,
                                          ofproto.OFPCML_NO_BUFFER)]
        self.add_flow(datapath, 0, match, actions)

    def add_flow(self, datapath, priority, match, actions, buffer_id=None):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS,
                                             actions)]
        if buffer_id:
            mod = parser.OFPFlowMod(datapath=datapath, buffer_id=buffer_id,
                                    priority=priority, match=match,
                                    instructions=inst)
        else:
            mod = parser.OFPFlowMod(datapath=datapath, priority=priority,
                                    match=match, instructions=inst)
        datapath.send_msg(mod)



    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        # If you hit this you might want to increase
        # the "miss_send_length" of your switch

        if ev.msg.msg_len < ev.msg.total_len:
            self.logger.debug("packet truncated: only %s of %s bytes",
                              ev.msg.msg_len, ev.msg.total_len)
        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        in_port = msg.match['in_port']

        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocols(ethernet.ethernet)[0]

        if eth.ethertype == ether_types.ETH_TYPE_LLDP:
            # ignore lldp packet
            return
        dst = eth.dst
        src = eth.src
        dpid = format(datapath.id, "d").zfill(16)

        self.mac_to_port.setdefault(dpid, {})


        self.logger.info("packet in %s %s %s %s", dpid, src, dst, in_port)


        # ARP
        pk_arp = pkt.get_protocol(arp.arp)
        if pk_arp:

            Arpmac = self.mac_to_port[pk_arp.dst_ip]
            eth_header = ethernet.ethernet(dst=eth.src, src=Arpmac, ethertype=eth.ethertype)
            arp_header = arp.arp(opcode=2, src_mac=Arpmac,
                                 src_ip=pk_arp.dst_ip, dst_mac=eth.src, dst_ip=pk_arp.src_ip)
            reply = packet.Packet()
            reply.add_protocol(eth_header)
            reply.add_protocol(arp_header)

            self._send_packet(datapath, 1, reply)
            print("there is the arp packet::::::::::")

        # IP layer
        pkt_ip = pkt.get_protocol(ipv4.ipv4)
        if pkt_ip:
            src_ip = pkt_ip.src
            dst_ip = pkt_ip.dst
            # tcp packet
            pkt_tcp = pkt.get_protocol(tcp.tcp)
            if pkt_tcp:
                # http packet
                if (datapath.id == 2 or datapath.id == 4) and (pkt_tcp.dst_port == 80) and (in_port == 1):
                    eth_header = ethernet.ethernet(dst=eth.src, src=eth.dst, ethertype=eth.ethertype)
                    ip_header = ipv4.ipv4(src=dst_ip, dst=src_ip, proto=6)
                    tcp_header = tcp.tcp(src_port=pkt_tcp.dst_port, dst_port=pkt_tcp.src_port, ack=pkt_tcp.seq + 1,
                                         bits=0b010100)

                    reply = packet.Packet()
                    reply.add_protocol(eth_header)
                    reply.add_protocol(ip_header)
                    reply.add_protocol(tcp_header)
                    # reply.serialize()
                    print("drop http packet at switch 2 or 4 :::::::")
                    self._send_packet(datapath, in_port, reply)
                # tcp packet
                else:
                    out_port = self._cal_out_port(src, dst, 6, datapath.id)
                    match = parser.OFPMatch(eth_type = 0x0800,ip_proto = 6, ipv4_dst = dst_ip, tcp_dst = pkt_tcp.dst_port)
                    actions = [parser.OFPActionOutput(port = out_port)]
                    self.add_flow(datapath, 500, match, actions)
                    print("send udp packet:::::::::::")
                    self._send_packet(datapath, out_port, pkt)
            # icmp pakcet
            pkt_icmp = pkt.get_protocol(icmp.icmp)
            if pkt_icmp:
                out_port = self._cal_out_port(src, dst, 1, datapath.id)
                match = parser.OFPMatch(eth_type = 0x0800, ip_proto = 1, ipv4_dst = dst_ip)
                actions = [parser.OFPActionOutput(port = out_port)]
                self.add_flow(datapath, 500, match, actions)
                print("send icmp packet::::::::::::")
                self._send_packet(datapath, out_port, pkt)
            # udp packet
            pkt_udp = pkt.get_protocol(udp.udp)
            # udp drop at switch 1 and 4
            if pkt_udp:
                if (datapath.id == 1 or datapath.id == 4) and (in_port == 1):
                    # out_port = self._cal_out_port(src, dst, pkt_ip.proto, datapath.id, in_port)
                    match = parser.OFPMatch(eth_type=0x0800, ip_proto=17, ipv4_dst=dst_ip)
                    actions = []
                    # inst = [parser.OFPInstructionActions(ofproto.OFPIT_CLEAR_ACTIONS, actions)
                    print("drop udp packet at switch 1 or 4::::::::::::::")
                    self.add_flow(datapath,500, match, actions)
                #  udp
                else:
                    out_port = self._cal_out_port(src, dst, 17, datapath.id)
                    match = parser.OFPMatch(eth_type=0x0800, ip_proto=17, ipv4_dst=dst_ip)
                    actions = [parser.OFPActionOutput(port=out_port)]
                    self.add_flow(datapath, 500, match, actions)
                    print("send UDP packet:::::::::::::::")
                    self._send_packet(datapath, out_port, pkt)
    # send packet
    def _send_packet(self, datapath, port, pkt):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        pkt.serialize()
        self.logger.info("packet-out %s" % (pkt,))
        data = pkt.data
        actions = [parser.OFPActionOutput(port=port)]
        out = parser.OFPPacketOut(datapath=datapath, buffer_id=ofproto.OFP_NO_BUFFER, in_port=ofproto.OFPP_CONTROLLER,
                                  actions=actions, data=data)
        datapath.send_msg(out)
    # calculate the outport and the shortest path
    @staticmethod
    def _cal_out_port(src_id,dst_id,protocol,switch_id):
         out_port = 0
         dist = int(dst_id[-1]) - int(src_id[-1])
         if(switch_id != int(dst_id[-1])):
             if (abs(dist) == 2):
                 # icmp and TCP
                 if(protocol == 6 or protocol == 1):
                     out_port = 2
                 # udp
                 elif(protocol == 17):
                     out_port = 3
             # shortest path
             elif (dist == -1 or dist == 3):
                 out_port = 3
             elif (dist == 1 or dist == -3):
                 out_port = 2
         # destination
         else:
             out_port = 1
         return out_port

