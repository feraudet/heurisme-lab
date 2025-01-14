import socket
import time
import can

print("python-can", can.__version__)
# 1. Does this kernel have SocketCAN?
try:
    s = socket.socket(socket.PF_CAN, socket.SOCK_RAW, socket.CAN_RAW)
    print("socket PF_CAN/CAN_RAW : ouvert")
    s.close()
except OSError as e:
    print("socket PF_CAN/CAN_RAW :", e)

# 2. python-can virtual bus: three transmitters, one receiver, same channel
rx = can.Bus(interface="virtual", channel="deck", receive_own_messages=False)
noeuds = {n: can.Bus(interface="virtual", channel="deck") for n in "ABC"}
trames = {"A": (0x245, [0x10]), "B": (0x241, [0x0F, 0xA0]), "C": (0x2C0, [0x01])}
# Timestamps are printed relative to t0 (just before the first send), not as wall-clock epoch
t0 = time.time()
for n, (i, d) in trames.items():
    noeuds[n].send(can.Message(arbitration_id=i, data=d, is_extended_id=False))
for _ in trames:
    m = rx.recv(timeout=1)
    m.timestamp -= t0
    print(m)
for b in [rx, *noeuds.values()]:
    b.shutdown()
