"""Receiver node for the queue size and timeout test in dora-rs.

This script validates that messages are received within an acceptable
latency (less than 1 second) under specific queue and timeout
configurations. It calculates and prints the difference between the
sent and received timestamps for each message.
"""

import time

from dora import Node


def main() -> None:
    """
    Receive messages from a Dora node and assert message latency is under 1 second.
    
    Processes incoming messages from a Node until a message with type "STOP" is received.
    Ignores messages whose type is not "INPUT". For each "INPUT" message, reads the
    sent timestamp and message index, computes the received timestamp, prints a line
    with [counter, index], sent time, received time, and their difference, asserts the
    difference is less than 1.0 second, and sleeps 0.1 seconds before continuing.
    """
    dora_node = Node()

    i = 0
    for message in dora_node:
        message_type = message["type"]
        if message_type == "STOP":
            break

        if message_type != "INPUT":
            continue
        sent = message["value"][0].as_py()
        j = message["value"][1].as_py()
        sent_in_s = sent / 1_000_000_000
        received = time.perf_counter_ns()
        received_in_s = received / 1_000_000_000

        i += 1
        print(
            f"[{i}, {j}] Sent: {sent_in_s}, Received: {received_in_s}, Difference: {received_in_s - sent_in_s}",
        )
        assert received_in_s - sent_in_s < 1.0
        time.sleep(0.1)


if __name__ == "__main__":
    main()
