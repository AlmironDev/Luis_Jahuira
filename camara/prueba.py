from scapy.all import ARP, Ether, srp

target_ip = "192.168.1.0/24"  # adapta tu red
arp = ARP(pdst=target_ip)
ether = Ether(dst="ff:ff:ff:ff:ff:ff")
packet = ether/arp

result = srp(packet, timeout=2, verbose=False)[0]

for sent, received in result:
    print(received.psrc, received.hwsrc)
