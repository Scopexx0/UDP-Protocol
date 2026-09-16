"""
CYB 410 - Data Communication & Computer Networks
Project: Reliable Data Transfer Protocol (RDT)
Team #1 | Ports: 12001-12005
Phase 2: Data Transfer - Perfect Network (Receiver side - runs on "Mars")

Description:
    Listens on the assigned port for incoming data packets from Moon.
    For each packet received:
      1. Parses the custom header (sequence number + checksum).
      2. Verifies the checksum to detect any bit errors.
      3. Sends an ACK back to the sender.
      4. Writes the payload to disk in order.

    When the special "END" payload is received, the file is saved.

    Phase 2 assumes 0% packet loss.
"""

import socket
import struct
import zlib

# ─── Configuration ───────────────────────────────────────────────────────────
LISTEN_HOST  = ""           # Listen on all interfaces
LISTEN_PORT  = 12001        # Team 1 port
BUFFER_SIZE  = 2048         # Must be larger than CHUNK_SIZE + header (8 bytes)
OUTPUT_FILE  = "received_Hawks-IL.jpg"   # Where to save the reconstructed file
# ─────────────────────────────────────────────────────────────────────────────


def parse_packet(raw: bytes):
    """
    Parses a raw UDP payload into its header fields and data.

    Returns: (seq_num, received_checksum, data_payload)
    """
    # Header is 8 bytes: 4 for seq_num + 4 for checksum
    seq_num, received_checksum = struct.unpack("!II", raw[:8])
    data = raw[8:]
    return seq_num, received_checksum, data


def verify_checksum(seq_num: int, data: bytes, received_checksum: int) -> bool:
    """
    Recomputes the CRC-32 checksum on arrival and compares it
    to the checksum embedded in the packet header.

    Returns True if the packet is intact, False if corrupted.
    """
    seq_bytes = struct.pack("!I", seq_num)
    computed  = zlib.crc32(seq_bytes + data) & 0xFFFFFFFF
    return computed == received_checksum


def send_ack(sock: socket.socket, seq_num: int, addr):
    """
    Sends a 4-byte ACK packet containing the acknowledged sequence number.
    """
    ack = struct.pack("!I", seq_num)
    sock.sendto(ack, addr)


def receive_file(sock: socket.socket):
    """
    Main receive loop. Collects ordered chunks and writes them to disk.
    """
    expected_seq = 0        # Next expected sequence number
    file_chunks  = []       # Buffer to hold received data in order
    sender_addr  = None     # Will be set on first packet

    print(f"[Receiver/Mars] Waiting for data on port {LISTEN_PORT} ...")

    while True:
        # Step 1: Wait for a packet
        raw, addr = sock.recvfrom(BUFFER_SIZE)
        if sender_addr is None:
            sender_addr = addr

        # Step 2: Parse the header
        seq_num, recv_checksum, data = parse_packet(raw)

        # Step 3: Verify the checksum — detect bit errors
        if not verify_checksum(seq_num, data, recv_checksum):
            print(f"[Receiver/Mars] CHECKSUM FAIL on packet {seq_num}. Dropping.")
            # Do NOT send ACK — sender will timeout and retransmit
            continue

        # Step 4: Check if this is the END signal
        if data == b"END":
            print("[Receiver/Mars] END signal received. Saving file ...")
            send_ack(sock, seq_num, addr)
            break

        # Step 5: Check for correct sequence order
        if seq_num == expected_seq:
            # In-order packet — accept and ACK
            file_chunks.append(data)
            print(f"[Receiver/Mars] Received packet {seq_num} ({len(data)} bytes). Sending ACK.")
            send_ack(sock, seq_num, addr)
            expected_seq += 1
        else:
            # Out-of-order or duplicate — re-ACK the last in-order packet
            print(f"[Receiver/Mars] Out-of-order packet {seq_num} (expected {expected_seq}). Re-ACKing {expected_seq - 1}.")
            if expected_seq > 0:
                send_ack(sock, expected_seq - 1, addr)

    # Step 6: Reassemble and save the file
    with open(OUTPUT_FILE, "wb") as f:
        for chunk in file_chunks:
            f.write(chunk)

    total_bytes = sum(len(c) for c in file_chunks)
    print(f"[Receiver/Mars] File saved as '{OUTPUT_FILE}' ({total_bytes} bytes). Transfer complete!")


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
