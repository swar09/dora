"""Webcam operator for dora-rs dataflow.

This operator captures video frames from a local webcam using OpenCV and
emits them as raw image buffers to the "image" output. It includes basic
error handling for cases where the camera is unavailable.
"""

import os
import time

import cv2
import numpy as np
import pyarrow as pa
from dora import DoraStatus

CAMERA_WIDTH = 640
CAMERA_HEIGHT = 480
CAMERA_INDEX = int(os.getenv("CAMERA_INDEX", 0))
CI = os.environ.get("CI")

font = cv2.FONT_HERSHEY_SIMPLEX


class Operator:
    """Sending image from webcam to the dataflow."""

    def __init__(self):
        """
        Create and configure the webcam capture for this operator.
        
        Initializes an OpenCV VideoCapture for the configured camera index, sets the capture resolution to the module's CAMERA_WIDTH and CAMERA_HEIGHT, records the operator start time, and initializes the consecutive read failure counter.
        """
        self.video_capture = cv2.VideoCapture(CAMERA_INDEX)
        self.start_time = time.time()
        self.video_capture.set(cv2.CAP_PROP_FRAME_WIDTH, CAMERA_WIDTH)
        self.video_capture.set(cv2.CAP_PROP_FRAME_HEIGHT, CAMERA_HEIGHT)
        self.failure_count = 0

    def on_event(
        self,
        dora_event: str,
        send_output,
    ) -> DoraStatus:
        """
        Handle an incoming Dora event by capturing a webcam frame (or a fallback image) and emitting it on the "image" output.
        
        Parameters:
            dora_event (dict): Dora-RS event object; expected to contain a "type" key ("INPUT", "STOP", etc.) and a "metadata" field used when emitting output.
            send_output (Callable): Callback used to emit output with signature send_output(channel: str, data, metadata).
        
        Returns:
            DoraStatus: `CONTINUE` to keep the operator running, `STOP` to request shutdown.
        """
        event_type = dora_event["type"]
        if event_type == "INPUT":
            ret, frame = self.video_capture.read()
            if ret:
                frame = cv2.resize(frame, (CAMERA_WIDTH, CAMERA_HEIGHT))
                self.failure_count = 0
            ## Push an error image in case the camera is not available.
            elif self.failure_count > 10:
                frame = np.zeros((CAMERA_HEIGHT, CAMERA_WIDTH, 3), dtype=np.uint8)
                cv2.putText(
                    frame,
                    f"No Webcam was found at index {CAMERA_INDEX}",
                    (30, 30),
                    font,
                    0.75,
                    (255, 255, 255),
                    2,
                    1,
                )
            else:
                self.failure_count += 1
                return DoraStatus.CONTINUE

            send_output(
                "image",
                pa.array(frame.ravel()),
                dora_event["metadata"],
            )
        elif event_type == "STOP":
            print("received stop")
        else:
            print("received unexpected event:", event_type)

        if time.time() - self.start_time < 20 or CI != "true":
            return DoraStatus.CONTINUE
        return DoraStatus.STOP

    def __del__(self):
        """
        Release the webcam capture device when the operator is destroyed.
        
        This frees the underlying OpenCV VideoCapture resource so the camera can be reused by other processes.
        """
        self.video_capture.release()
