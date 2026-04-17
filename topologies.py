#!/usr/bin/env python3
"""
Bandwidth Measurement Topologies - Mininet Script
==================================================
Project: Orange Level - SDN Mininet Simulation
Course: Computer Networks - UE24CS252B
PES University

Description:
    Implements THREE network topologies for bandwidth comparison:

    Topology 1 – Linear (Single Path)
        h1 ─── s1 ─── s2 ─── h2
        Demonstrates: baseline point-to-point bandwidth

    Topology 2 – Star (Hub-and-Spoke)
             h1
              │
        h3 ─ s1 ─ h2
              │
             h4
        Demonstrates: shared switch bandwidth, multi-client performance

    Topology 3 – Tree (Hierarchical, 2-level)
                  s1
               /      \
             s2          s3
           / \          / \
          h1  h2       h3  h4
        Demonstrates: inter-switch bandwidth vs intra-switch bandwidth

Usage:
    # Run with Ryu controller (start controller first):
    #   ryu-manager bandwidth_controller.py
    #
    # Then run this script:
    sudo python3 topologies.py --topo [linear|star|tree] [--bw <Mbps>]

    # Or use the interactive menu (no arguments):
    sudo python3 topologies.py
"""

#!/usr/bin/env python3

import sys
import argparse
import time
from mininet.net import Mininet
from mininet.node import RemoteController, OVSKernelSwitch
from mininet.topo import Topo
from mininet.link import TCLink
from mininet.log import setLogLevel, info
from mininet.cli import CLI


# ──────────────────────────────────────────────────────
# Topologies
# ──────────────────────────────────────────────────────

class LinearTopo(Topo):
    def build(self, bw=10):
        s1 = self.addSwitch('s1')
        s2 = self.addSwitch('s2')

        h1 = self.addHost('h1', ip='10.0.1.1/24')
        h2 = self.addHost('h2', ip='10.0.1.2/24')

        self.addLink(h1, s1, bw=bw, delay='5ms')
        self.addLink(s1, s2, bw=bw, delay='2ms')
        self.addLink(s2, h2, bw=bw, delay='5ms')


class StarTopo(Topo):
    def build(self, bw=10):
        s1 = self.addSwitch('s1')

        for i in range(1, 5):
            h = self.addHost(f'h{i}', ip=f'10.0.1.{i}/24')
            self.addLink(h, s1, bw=bw, delay='2ms')


class TreeTopo(Topo):
    def build(self, bw=10):
        s1 = self.addSwitch('s1')
        s2 = self.addSwitch('s2')
        s3 = self.addSwitch('s3')

        h1 = self.addHost('h1', ip='10.0.1.1/24')
        h2 = self.addHost('h2', ip='10.0.1.2/24')
        h3 = self.addHost('h3', ip='10.0.2.1/24')
        h4 = self.addHost('h4', ip='10.0.2.2/24')

        self.addLink(s1, s2, bw=bw*2, delay='1ms')
        self.addLink(s1, s3, bw=bw*2, delay='1ms')

        self.addLink(s2, h1, bw=bw, delay='5ms')
        self.addLink(s2, h2, bw=bw, delay='5ms')
        self.addLink(s3, h3, bw=bw, delay='5ms')
        self.addLink(s3, h4, bw=bw, delay='5ms')


# ──────────────────────────────────────────────────────
# Tests
# ──────────────────────────────────────────────────────

def run_iperf_test(net, src, dst, duration=10):
    h1 = net.get(src)
    h2 = net.get(dst)

    info(f"\n[IPERF] {src} → {dst}\n")

    h2.cmd('pkill iperf; iperf -s -D')
    time.sleep(1)

    result = h1.cmd(f'iperf -c {h2.IP()} -t {duration}')
    info(result)

    h2.cmd('pkill iperf')


def run_ping_test(net, src, dst):
    h1 = net.get(src)
    h2 = net.get(dst)

    info(f"\n[PING] {src} → {dst}\n")
    info(h1.cmd(f'ping -c 5 {h2.IP()}'))


def show_flows(net):
    info("\n[FLOW TABLES]\n")
    for sw in net.switches:
        info(f"\n--- {sw.name} ---\n")
        info(sw.cmd(f'ovs-ofctl dump-flows {sw.name}'))


# ──────────────────────────────────────────────────────
# Main Runner
# ──────────────────────────────────────────────────────

def run_topology(topo_name, bw):

    topo_map = {
        'linear': LinearTopo,
        'star': StarTopo,
        'tree': TreeTopo
    }

    if topo_name not in topo_map:
        print("Invalid topology")
        sys.exit(1)

    topo = topo_map[topo_name](bw=bw)

    net = Mininet(
        topo=topo,
        switch=OVSKernelSwitch,
        controller=None,
        link=TCLink,
        autoSetMacs=True
    )

    # Add POX controller (OpenFlow 1.0)
    net.addController('c0',
                      controller=RemoteController,
                      ip='127.0.0.1',
                      port=6633)

    net.start()

    # IMPORTANT: Force OpenFlow 1.0 for POX
    for sw in net.switches:
        sw.cmd(f'ovs-vsctl set bridge {sw.name} protocols=OpenFlow10')

    info("\n[INFO] Network started\n")
    time.sleep(2)

    # Connectivity
    net.pingAll()

    # Tests
    if topo_name == 'linear':
        run_iperf_test(net, 'h1', 'h2')
        run_ping_test(net, 'h1', 'h2')

    elif topo_name == 'star':
        run_iperf_test(net, 'h1', 'h2')
        run_iperf_test(net, 'h3', 'h4')

    elif topo_name == 'tree':
        run_iperf_test(net, 'h1', 'h2')
        run_iperf_test(net, 'h1', 'h3')

    show_flows(net)

    CLI(net)
    net.stop()


# ──────────────────────────────────────────────────────
# Entry
# ──────────────────────────────────────────────────────

if __name__ == '__main__':
    setLogLevel('info')

    parser = argparse.ArgumentParser()
    parser.add_argument('--topo', choices=['linear', 'star', 'tree'], default='linear')
    parser.add_argument('--bw', type=int, default=10)

    args = parser.parse_args()

    run_topology(args.topo, args.bw)
