"""
CYB 410 - Data Communication & Computer Networks
Project: Reliable Data Transfer Protocol (RDT)
Team #1 | Ports: 12001-12005
Phase 3: RDT Logic - Lossy Network (Receiver side - runs on "Mars")

Description:
    The receiver is functionally identical to Phase 2. The lossy layer
    lives entirely on the sender side — the receiver simply waits for
    valid, in-order packets and ACKs them.

    If a packet is dropped by the sender's lossy layer, the receiver
    never sees it and sends no ACK. The sender's timer fires, and the
    packet is retransmitted. From the receiver's perspective, the
    protocol is unchanged.

    Steps for each arriving packet:
      1. Parse header (sequence number + checksum).
      2. Verify checksum — drop silently if corrupted.
      3. Accept if in-order; re-ACK last good packet if duplicate/out-of-order.
      4. Write accepted data to disk.
      5. Save file on END signal.
"""

import socket
import struct
import zlib

# ─── Configuration ───────────────────────────────────────────────────────────
LISTEN_HOST = ""
LISTEN_PORT = 12001                     # Team 1 port
BUFFER_SIZE = 2048
OUTPUT_FILE = "received_Hawks-IL.jpg"   # Output filename on Mars
# ─────────────────────────────────────────────────────────────────────────────


def parse_packet(raw: bytes):
    """Splits raw bytes into (seq_num, checksum, data)."""
    seq_num, checksum = struct.unpack("!II", raw[:8])
    return seq_num, checksum, raw[8:]


def verify_checksum(seq_num: int, data: bytes, recv_checksum: int) -> bool:
    """Returns True if the packet's checksum matches its contents."""
    seq_bytes = struct.pack("!I", seq_num)
    computed  = zlib.crc32(seq_bytes + data) & 0xFFFFFFFF
    return computed == recv_checksum


def send_ack(sock: socket.socket, seq_num: int, addr):
    """Sends a 4-byte ACK for the given sequence number."""
    sock.sendto(struct.pack("!I", seq_num), addr)


def receive_file(sock: socket.socket):
    """Main receive loop — identical to Phase 2."""
    expected_seq = 0
    file_chunks  = []

    print(f"[Receiver/Mars] Listening on port {LISTEN_PORT} for Phase 3 transfer ...")

    while True:
        raw, addr = sock.recvfrom(BUFFER_SIZE)
        seq_num, recv_checksum, data = parse_packet(raw)

        # Verify checksum integrity
        if not verify_checksum(seq_num, data, recv_checksum):
            print(f"[Receiver/Mars] CHECKSUM FAIL on packet {seq_num}. Dropping (no ACK).")
            continue

        # Check for END signal
        if data == b"END":
            print("[Receiver/Mars] END received. Saving file ...")
            send_ack(sock, seq_num, addr)
            break

        if seq_num == expected_seq:
            # Correct in-order packet
            file_chunks.append(data)
            print(f"[Receiver/Mars] Packet {seq_num} accepted ({len(data)} bytes). ACK sent.")
            send_ack(sock, seq_num, addr)
            expected_seq += 1
        else:
            # Duplicate or out-of-order — re-ACK the last accepted packet
            print(f"[Receiver/Mars] Unexpected seq {seq_num} (expected {expected_seq}). Re-ACKing {expected_seq - 1}.")
            if expected_seq > 0:
                send_ack(sock, expected_seq - 1, addr)

    # Reassemble and write to disk
    with open(OUTPUT_FILE, "wb") as f:
        for chunk in file_chunks:
            f.write(chunk)

    total = sum(len(c) for c in file_chunks)
    print(f"[Receiver/Mars] '{OUTPUT_FILE}' saved ({total} bytes). Transfer complete!")


def main():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((LISTEN_HOST, LISTEN_PORT))

    try:
        receive_file(sock)
    except KeyboardInterrupt:
        print("\n[Receiver/Mars] Interrupted.")
    finally:
        sock.close()
        print("[Receiver/Mars] Socket closed.")


if __name__ == "__main__":
    main()
