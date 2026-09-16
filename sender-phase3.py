"""
CYB 410 - Data Communication & Computer Networks
Project: Reliable Data Transfer Protocol (RDT)
Team #1 | Ports: 12001-12005
Phase 3: RDT Logic - Lossy Network (Sender side - runs on "Moon")

Description:
    Identical to Phase 2, but adds a "Lossy Layer" function that randomly
    drops ~10% of outgoing packets before they are handed to the socket.

    This simulates real-world packet loss. The Stop-and-Wait protocol
    must still deliver every byte correctly by:
      - Detecting the loss via a retransmission timer (socket timeout).
      - Retransmitting the same packet until an ACK is received.

    The receiver (receiver-phase3.py) is unchanged from Phase 2 —
    the reliability logic lives entirely in the sender's timer/retransmit loop.
"""

import socket
import struct
import zlib
import os
import random

# ─── Configuration ───────────────────────────────────────────────────────────
MARS_HOST    = "mars"           # Replace with actual hostname/IP of Mars
MARS_PORT    = 12001            # Team 1 port
CHUNK_SIZE   = 1024             # Bytes of file data per packet
TIMEOUT_SEC  = 2                # Retransmission timeout in seconds
FILE_PATH    = "Hawks-IL.jpg"   # File to transfer (must exist on Moon)
LOSS_PROB    = 0.10             # 10% simulated packet loss probability
# ─────────────────────────────────────────────────────────────────────────────


def lossy_send(sock: socket.socket, packet: bytes, addr: tuple) -> bool:
    """
    Lossy Layer: simulates network packet loss.

    With probability LOSS_PROB, the packet is silently dropped (not sent).
    Otherwise it is forwarded to the real UDP socket.

    Returns True if the packet was actually sent, False if it was dropped.
    """
    if random.random() < LOSS_PROB:
        # Simulate packet loss — pretend it was sent but it was not
        print("[LossyLayer] *** PACKET DROPPED (simulated loss) ***")
        return False
    else:
        sock.sendto(packet, addr)
        return True


def build_packet(seq_num: int, data: bytes) -> bytes:
    """
    Constructs a packet with a custom header.

    Header (8 bytes):
      - Sequence number : 4 bytes unsigned int
      - CRC-32 Checksum : 4 bytes unsigned int  (over seq_bytes + data)
    """
    seq_bytes = struct.pack("!I", seq_num)
    checksum  = zlib.crc32(seq_bytes + data) & 0xFFFFFFFF
    return seq_bytes + struct.pack("!I", checksum) + data


def send_file(sock: socket.socket, filepath: str):
    """
    Reads the file in chunks and sends each using Stop-and-Wait.
    Packets pass through the Lossy Layer before hitting the network.
    The retransmission timer handles any dropped packets automatically.
    """
    file_size = os.path.getsize(filepath)
    print(f"[Sender/Moon] Sending '{filepath}' ({file_size} bytes) with {int(LOSS_PROB*100)}% simulated loss ...")

    with open(filepath, "rb") as f:
        seq_num    = 0
        total_sent = 0
        retransmits = 0     # Track how many retransmissions occurred

        while True:
            # Read next file chunk
            chunk = f.read(CHUNK_SIZE)
            if not chunk:
                break

            packet = build_packet(seq_num, chunk)

            # Stop-and-Wait loop with lossy layer
            while True:
                # Attempt to send (may be silently dropped by lossy layer)
                actually_sent = lossy_send(sock, packet, (MARS_HOST, MARS_PORT))

                if not actually_sent:
                    # Packet was dropped — timeout will trigger retransmission
                    # Simulate the timeout delay so behavior mirrors real loss
                    import time
                    time.sleep(TIMEOUT_SEC)
                    retransmits += 1
                    print(f"[Sender/Moon] Retransmitting packet {seq_num} ...")
                    continue

                try:
                    # Wait for ACK
                    ack_data, _ = sock.recvfrom(16)
                    ack_seq = struct.unpack("!I", ack_data[:4])[0]

                    if ack_seq == seq_num:
                        total_sent += len(chunk)
                        print(f"[Sender/Moon] Packet {seq_num} ACK'd | "
                              f"{total_sent}/{file_size} bytes transferred")
                        seq_num += 1
                        break
                    else:
                        print(f"[Sender/Moon] Stale ACK {ack_seq}, expected {seq_num}. Retransmitting...")
                        retransmits += 1

                except socket.timeout:
                    print(f"[Sender/Moon] Timeout on packet {seq_num}. Retransmitting...")
                    retransmits += 1

    # Send END signal (also goes through lossy layer — retry until ACK'd)
    end_packet = build_packet(seq_num, b"END")
    while True:
        lossy_send(sock, end_packet, (MARS_HOST, MARS_PORT))
        try:
            ack_data, _ = sock.recvfrom(16)
            break
        except socket.timeout:
            print("[Sender/Moon] Timeout on END signal. Retransmitting...")

    print(f"\n[Sender/Moon] Transfer complete!")
    print(f"[Sender/Moon] Total retransmissions due to loss: {retransmits}")


def main():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(TIMEOUT_SEC)

    try:
        send_file(sock, FILE_PATH)
    finally:
        sock.close()
        print("[Sender/Moon] Socket closed.")


if __name__ == "__main__":
    main()
