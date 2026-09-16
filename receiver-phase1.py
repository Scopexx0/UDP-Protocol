"""
CYB 410 - Data Communication & Computer Networks
Project: Reliable Data Transfer Protocol (RDT)
Team #1 | Ports: 12001-12005
Phase 1: The Handshake (Receiver side - runs on "Mars")

Description:
    Listens on the assigned Team 1 port for an incoming "HELLO" message
    from Moon. Once received, it sends back a "HELLO_ACK" to complete
    the handshake.
"""

import socket

# ─── Configuration ───────────────────────────────────────────────────────────
LISTEN_HOST = ""        # Empty string = listen on all available interfaces
LISTEN_PORT = 12001     # Team 1 assigned port
BUFFER_SIZE = 1024
# ─────────────────────────────────────────────────────────────────────────────


def main():
    # Step 1: Create a UDP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # Step 2: Bind the socket to our assigned port so we can receive packets
    # Binding tells the OS: "give me everything that arrives on port 12001"
    sock.bind((LISTEN_HOST, LISTEN_PORT))
    print(f"[Receiver/Mars] Listening on port {LISTEN_PORT} ...")

    try:
        # Step 3: Block and wait for an incoming packet
        # recvfrom() returns both the data and the sender's address
        data, client_addr = sock.recvfrom(BUFFER_SIZE)
        print(f"[Receiver/Mars] Received from {client_addr}: {data.decode()}")

        # Step 4: Check that the message is the expected handshake
        if data == b"HELLO":
            print("[Receiver/Mars] Valid HELLO received. Sending HELLO_ACK ...")

            # Step 5: Send the acknowledgment back to the sender
            ack_msg = b"HELLO_ACK"
            sock.sendto(ack_msg, client_addr)
            print(f"[Receiver/Mars] Sent: {ack_msg.decode()} → {client_addr}")
            print("[Receiver/Mars] Handshake complete!")
        else:
            print(f"[Receiver/Mars] Unexpected message: {data.decode()}")

    except KeyboardInterrupt:
        print("\n[Receiver/Mars] Interrupted by user.")

    finally:
        # Step 6: Close the socket
        sock.close()
        print("[Receiver/Mars] Socket closed.")


if __name__ == "__main__":
    main()
