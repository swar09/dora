"""Python operator template for dora-rs.

Provides a skeleton for implementing custom dataflow operators in Python.
"""

from dora import DoraStatus


class Operator:
    """Template docstring."""

    def __init__(self):
        """Perform initialization tasks."""

    def on_event(
        self,
        dora_event,
        send_output,
    ) -> DoraStatus:
        """
        Handle a dora-rs event and optionally emit outputs via the provided callback.
        
        Parameters:
            dora_event (dict): Event from dora-rs expected to include keys such as
                "type" (e.g., "INPUT"), "id", "value", and "metadata".
            send_output (Callable): Callback to emit outputs. Called with
                (output_id: str, value: bytes or pa.Array, metadata: dict|None).
        
        Returns:
            DoraStatus: `CONTINUE` to keep the operator running or `STOP` to terminate it.
        """
        if dora_event["type"] == "INPUT":
            print(
                f"Received input {dora_event['id']}, with data: {dora_event['value']}",
            )

        return DoraStatus.CONTINUE

    def __del__(self):
        """Perform actions before being deleted."""
