"""
Bandwidth Measurement and Analysis - Ryu SDN Controller
=======================================================
Project: Orange Level - SDN Mininet Simulation
Course: Computer Networks - UE24CS252B
PES University

Description:
    This pox controller implements a learning switch with:
    - Packet_in event handling for flow rule installation
    - Per-port and per-flow statistics polling (every 5 seconds)
    - Bandwidth calculation from byte counters
    - Flow table management with idle/hard timeouts
    - Logging of throughput metrics for analysis
"""

# POX Bandwidth Controller (OpenFlow 1.0)

from pox.core import core
import pox.openflow.libopenflow_01 as of
from pox.lib.recoco import Timer
import time
import logging

log = core.getLogger()

POLL_INTERVAL = 5  # seconds


class BandwidthController(object):
    def __init__(self):
        self.mac_to_port = {}       # {dpid: {mac: port}}
        self.prev_stats = {}        # {(dpid, port): (rx_bytes, tx_bytes, time)}
        self.connections = []       # active switches

        # CSV logging
        self.log_file = open("bandwidth_log.csv", "w")
        self.log_file.write("timestamp,dpid,port,rx_bps,tx_bps,rx_pkts,tx_pkts\n")

        # Start periodic monitoring
        Timer(POLL_INTERVAL, self._monitor, recurring=True)

        core.openflow.addListeners(self)

        log.info("╔══════════════════════════════════╗")
        log.info("║  POX Bandwidth Controller       ║")
        log.info("║  Poll interval: %ds             ║", POLL_INTERVAL)
        log.info("╚══════════════════════════════════╝")

    # ──────────────────────────────────────────
    # Switch Connection
    # ──────────────────────────────────────────
    def _handle_ConnectionUp(self, event):
        dpid = event.dpid
        self.connections.append(event.connection)
        self.mac_to_port.setdefault(dpid, {})

        log.info("[SWITCH %s] Connected", dpid)

        # Install table-miss (send to controller)
        msg = of.ofp_flow_mod()
        msg.priority = 0
        msg.actions.append(of.ofp_action_output(port=of.OFPP_CONTROLLER))
        event.connection.send(msg)

    def _handle_ConnectionDown(self, event):
        self.connections.remove(event.connection)
        log.info("[SWITCH %s] Disconnected", event.dpid)

    # ──────────────────────────────────────────
    # Packet-In (Learning Switch)
    # ──────────────────────────────────────────
    def _handle_PacketIn(self, event):
        packet = event.parsed
        if not packet.parsed:
            return

        dpid = event.dpid
        in_port = event.port

        src = packet.src
        dst = packet.dst

        # Learn MAC
        self.mac_to_port[dpid][src] = in_port
        log.info("[SW %s] Learned %s on port %s", dpid, src, in_port)

        # Decide output port
        if dst in self.mac_to_port[dpid]:
            out_port = self.mac_to_port[dpid][dst]
        else:
            out_port = of.OFPP_FLOOD

        # Install flow if known
        if out_port != of.OFPP_FLOOD:
            msg = of.ofp_flow_mod()
            msg.match.in_port = in_port
            msg.match.dl_src = src
            msg.match.dl_dst = dst
            msg.idle_timeout = 30
            msg.hard_timeout = 120
            msg.actions.append(of.ofp_action_output(port=out_port))
            event.connection.send(msg)

        # Send packet out
        msg = of.ofp_packet_out()
        msg.data = event.ofp
        msg.in_port = in_port
        msg.actions.append(of.ofp_action_output(port=out_port))
        event.connection.send(msg)

    # ──────────────────────────────────────────
    # Monitoring (Stats Request)
    # ──────────────────────────────────────────
    def _monitor(self):
        for conn in self.connections:
            req = of.ofp_port_stats_request()
            conn.send(req)

    # ──────────────────────────────────────────
    # Stats Reply
    # ──────────────────────────────────────────
    def _handle_PortStatsReceived(self, event):
        dpid = event.dpid
        now = time.time()

        log.info("─" * 60)
        log.info(" Switch %s - Port Stats", dpid)
        log.info(" Port | RX (bps) | TX (bps) | RX pkts | TX pkts")
        log.info("─" * 60)

        for stat in event.stats:
            port = stat.port_no
            key = (dpid, port)

            rx_bytes = stat.rx_bytes
            tx_bytes = stat.tx_bytes
            rx_pkts = stat.rx_packets
            tx_pkts = stat.tx_packets

            if key in self.prev_stats:
                prev_rx, prev_tx, prev_time = self.prev_stats[key]
                dt = now - prev_time

                if dt > 0:
                    rx_bps = (rx_bytes - prev_rx) * 8 / dt
                    tx_bps = (tx_bytes - prev_tx) * 8 / dt
                else:
                    rx_bps = tx_bps = 0
            else:
                rx_bps = tx_bps = 0

            self.prev_stats[key] = (rx_bytes, tx_bytes, now)

            log.info(" %s   | %.1f | %.1f | %d | %d",
                     port, rx_bps, tx_bps, rx_pkts, tx_pkts)

            # Write CSV
            self.log_file.write("%s,%s,%s,%.2f,%.2f,%d,%d\n" % (
                time.strftime("%H:%M:%S"),
                dpid, port,
                rx_bps, tx_bps,
                rx_pkts, tx_pkts
            ))
            self.log_file.flush()

    def _handle_ConnectionDown(self, event):
        log.info("Switch %s disconnected", event.dpid)

    def __del__(self):
        self.log_file.close()


# ──────────────────────────────────────────
# Launch
# ──────────────────────────────────────────
def launch():
    BandwidthController()
