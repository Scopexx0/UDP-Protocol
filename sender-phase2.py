"""
CYB 410 - Data Communication & Computer Networks
Project: Reliable Data Transfer Protocol (RDT)
Team #1 | Ports: 12001-12005
Phase 2: Data Transfer - Perfect Network (Sender side - runs on "Moon")

Description:
    Reads a file, breaks it into fixed-size chunks, and sends each chunk
    to Mars using a Stop-and-Wait protocol over UDP.

    Each packet has a custom header:
        [SEQ_NUM (4 bytes)] [CHECKSUM (4 bytes)] [DATA (up to CHUNK_SIZE bytes)]

    The sender waits for an ACK after every packet before sending the next.
    If no ACK arrives within TIMEOUT_SEC, the packet is retransmitted.

    Phase 2 assumes 0% packet loss (no lossy layer).
"""

import socket
import struct
import zlib
import os

# ─── Configuration ───────────────────────────────────────────────────────────
MARS_HOST   = "mars"        # Replace with actual hostname/IP of Mars
MARS_PORT   = 12001         # Team 1 port
CHUNK_SIZE  = 1024          # Bytes of file data per packet
TIMEOUT_SEC = 2             # Retransmission timeout in seconds
FILE_PATH   = "Hawks-IL.jpg"  # File to transfer (must exist on Moon)
# ─────────────────────────────────────────────────────────────────────────────


def build_packet(seq_num: int, data: bytes) -> bytes:
    """
    Constructs a custom packet with a header.

    Header format (8 bytes total):
      - Sequence number : 4 bytes, unsigned int  (I)
      - Checksum        : 4 bytes, unsigned int  (I)

    The checksum is computed over (seq_num bytes + data) using CRC-32,
    which detects accidental bit-level corruption in transit.
    """
    # Pack the sequence number into 4 bytes (big-endian)
    seq_bytes = struct.pack("!I", seq_num)

    # Compute CRC-32 checksum over the sequence number + payload
    checksum = zlib.crc32(seq_bytes + data) & 0xFFFFFFFF

    # Pack the checksum into 4 bytes
    checksum_bytes = struct.pack("!I", checksum)

    # Final packet = header + payload
    return seq_bytes + checksum_bytes + data


def send_file(sock: socket.socket, filepath: str):
    """
    Reads the file in chunks and sends each chunk reliably
    using Stop-and-Wait: send → wait for ACK → send next.
    """
    file_size = os.path.getsize(filepath)
    print(f"[Sender/Moon] Sending file: {filepath} ({file_size} bytes)")

    with open(filepath, "rb") as f:
        seq_num   = 0       # Sequence number starts at 0
        total_sent = 0      # Track progress

        while True:
            # Step 1: Read the next chunk of the file
            chunk = f.read(CHUNK_SIZE)
            if not chunk:
                break   # End of file reached

            # Step 2: Build the packet (header + data)
            packet = build_packet(seq_num, chunk)

            # Step 3: Stop-and-Wait loop — keep retransmitting until ACK received
            while True:
                # Send the packet
                sock.sendto(packet, (MARS_HOST, MARS_PORT))

                try:
                    # Wait for an ACK from Mars
                    ack_data, _ = sock.recvfrom(16)

                    # Unpack the ACK sequence number (4 bytes)
                    ack_seq = struct.unpack("!I", ack_data[:4])[0]

                    if ack_seq == seq_num:
                        # Correct ACK received — move to next packet
                        total_sent += len(chunk)
                        print(f"[Sender/Moon] Packet {seq_num} ACK'd | "
                              f"Progress: {total_sent}/{file_size} bytes")
                        seq_num += 1
                        break   # Exit the retransmit loop
                    else:
                        print(f"[Sender/Moon] Wrong ACK {ack_seq}, expected {seq_num}. Retransmitting...")

                except socket.timeout:
                    # No ACK within timeout — retransmit the same packet
                    print(f"[Sender/Moon] Timeout on packet {seq_num}. Retransmitting...")

    # Step 4: Send an END signal so Mars knows the transfer is complete
    end_packet = build_packet(seq_num, b"END")
    sock.sendto(end_packet, (MARS_HOST, MARS_PORT))
    print(f"[Sender/Moon] END signal sent. Transfer complete!")


def main():
    # Create UDP socket and set retransmission timeout
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(TIMEOUT_SEC)

    try:
        send_file(sock, FILE_PATH)
    finally:
        sock.close()
        print("[Sender/Moon] Socket closed.")


if __name__ == "__main__":
    main()
