"""
CYB 410 - Data Communication & Computer Networks
Project: Reliable Data Transfer Protocol (RDT)
Team #1 | Ports: 12001-12005
Phase 1: The Handshake (Sender side - runs on "Moon")

Description:
    Establishes a simple "Hello" exchange with the receiver on "Mars"
    using a UDP socket. The sender initiates the handshake and waits
    for a confirmation reply.
"""

import socket

# ─── Configuration ───────────────────────────────────────────────────────────
MARS_HOST = "mars"          # Replace with the actual hostname or IP of Mars
MARS_PORT = 12001           # Team 1 assigned port
BUFFER_SIZE = 1024
TIMEOUT_SEC = 5             # Seconds to wait for a reply before giving up
# ─────────────────────────────────────────────────────────────────────────────


def main():
    # Step 1: Create a UDP socket
    # AF_INET  = IPv4
    # SOCK_DGRAM = UDP (datagram, connectionless)
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # Step 2: Set a timeout so we don't block forever waiting for a reply
    sock.settimeout(TIMEOUT_SEC)

    print(f"[Sender/Moon] Sending handshake to {MARS_HOST}:{MARS_PORT} ...")

    try:
        # Step 3: Send the "HELLO" message to Mars
        hello_msg = b"HELLO"
        sock.sendto(hello_msg, (MARS_HOST, MARS_PORT))
        print(f"[Sender/Moon] Sent: {hello_msg.decode()}")

        # Step 4: Wait for the receiver's reply
        data, server_addr = sock.recvfrom(BUFFER_SIZE)
        print(f"[Sender/Moon] Received reply from {server_addr}: {data.decode()}")

        # Step 5: Confirm handshake success
        if data == b"HELLO_ACK":
            print("[Sender/Moon] Handshake successful! Connection established.")
        else:
            print(f"[Sender/Moon] Unexpected reply: {data.decode()}")

    except socket.timeout:
        # No reply was received within the timeout window
        print("[Sender/Moon] ERROR: No reply from Mars. Timeout exceeded.")

    finally:
        # Step 6: Always close the socket when done
        sock.close()
        print("[Sender/Moon] Socket closed.")


if __name__ == "__main__":
    main()
