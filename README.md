🌐 SDN Bandwidth Measurement and Analysis

Orange Level Project – Computer Networks (UE24CS252B) | PES University

⸻

📌 Problem Statement

Modern networks must handle varying traffic loads across different topologies.
This project implements an SDN-based solution using Mininet and the Ryu OpenFlow controller to:
	•	Measure and compare bandwidth across three network topologies:
	•	Linear
	•	Star
	•	Tree
	•	Observe how network structure affects throughput and latency
	•	Install and monitor OpenFlow flow rules in real-time
	•	Analyze performance using iperf and ping with statistics logging

🏗️ Architecture Overview
┌─────────────────────────────────────┐
│         Ryu Controller              │
│  ┌─────────────────────────────┐   │
│  │  Learning Switch Logic      │   │
│  │  + Port Stats Polling (5s)  │   │
│  │  + Bandwidth Calculator     │   │
│  │  + CSV Logger               │   │
│  └─────────────────────────────┘   │
└──────────────┬──────────────────────┘
               │ OpenFlow 1.3
    ┌──────────┴──────────┐
    │   OVS Switches      │
    │  (Mininet Topology) │
    └─────────────────────┘

🌐 Network Topologies


🔹 Linear Topology
h1 ──── s1 ──── s2 ──── h2
         (5ms)  (2ms)

         

🔹 Star Topology
        h1
         │
h3 ───  s1  ─── h2
         │
        h4
        

🔹 Tree Topology (2-Level)
            s1 (core)
           /         \
         s2            s3
        /  \          /  \
       h1   h2       h3   h4

⚙️ Flow Rule Design


<img width="846" height="237" alt="image" src="https://github.com/user-attachments/assets/14153093-d5f3-4899-a0f0-641ac7bbb1b4" />

🛠️ Setup & Execution

📦 Prerequisites
	•	Ubuntu 20.04 / 22.04 VM
	•	Mininet
	•	Ryu Controller
	•	Open vSwitch

🔧 Step 1: Install Dependencies

sudo apt update && sudo apt upgrade -y
sudo apt install mininet openvswitch-switch iperf wireshark -y
pip3 install ryu

🧹 Step 2: Clean Mininet
sudo mn -c

🚀 Step 3: Start Ryu Controller (Terminal 1)
ryu-manager bandwidth_controller.py --observe-links


🌐 Step 4: Run Topologies (Terminal 2)

Linear
sudo python3 topologies.py --topo linear --bw 10

Star
sudo python3 topologies.py --topo star --bw 10

Tree
sudo python3 topologies.py --topo tree --bw 10

🧪 Test Scenarios

✅ Scenario 1 – Connectivity
mininet> pingall


📊 Scenario 2 – Single Flow (iperf)
mininet> h1 iperf -s &
mininet> h2 iperf -c 10.0.1.1 -t 10

🔁 Scenario 3 – Parallel Flows
mininet> h1 iperf -s -D
mininet> h3 iperf -s -D
mininet> h2 iperf -c 10.0.1.1 -t 10 &
mininet> h4 iperf -c 10.0.1.3 -t 10

🔍 Scenario 4 – Flow Table
mininet> sh ovs-ofctl dump-flows s1

📈 Expected Output
Controller Logs

10:23:01 [INFO] ─────────────────────────────────────────
Switch 0001 │ Port Statistics
Port │ RX (bps) │ TX (bps)
1    │ 9834201  │ 132
2    │ 131      │ 9834190

CSV Log

timestamp,datapath_id,port_no,rx_bps,tx_bps
10:23:01,0001,1,9834201,132

📊 Performance Analysis

Metric
Linear
Star (1 flow)
Star (2 flows)
Tree (intra)
Tree (inter)
Throughput
~9.5 Mbps
~9.5 Mbps
~4.7 Mbps
~9.5 Mbps
~9.5 Mbps
Latency
~12 ms
~4 ms
~4 ms
~10 ms
~11 ms
Bottleneck
Series links
Switch
Shared link
Edge link
Core link











