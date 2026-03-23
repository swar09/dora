"""Main entry point for a dora-rs Python node.

This script demonstrates a basic dora-rs node implementation that listens
for events and optionally sends outputs back to the dataflow.
"""

import pyarrow as pa
from dora import Node


def main():
    """
    Initialize and run the dora-rs node event loop.
    
    Creates a Node, iterates over events from the runtime, prints details for INPUT events with id "TICK",
    and sends an output for INPUT events with id "my_input_id" (output_id "my_output_id").
    Expects INPUT events to include the keys "type", "id", "value", and "metadata".
    """
    node = Node()

    for event in node:
        if event["type"] == "INPUT":
            if event["id"] == "TICK":
                print(
                    f"""Node received:
                id: {event["id"]},
                value: {event["value"]},
                metadata: {event["metadata"]}""",
                )

            elif event["id"] == "my_input_id":
                # Warning: Make sure to add my_output_id and my_input_id within the dataflow.
                node.send_output(
                    output_id="my_output_id", data=pa.array([1, 2, 3]), metadata={},
                )


if __name__ == "__main__":
    main()
