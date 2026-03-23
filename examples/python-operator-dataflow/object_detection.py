"""Object detection operator for dora-rs dataflow using YOLOv8.

This operator receives image frames, performs object detection using the
ultralytics YOLOv8 model, and emits bounding box coordinates, confidence
scores, and class labels for detected objects.
"""

import numpy as np
import pyarrow as pa
from dora import DoraStatus
from ultralytics import YOLO

CAMERA_WIDTH = 640
CAMERA_HEIGHT = 480


model = YOLO("yolov8n.pt")


class Operator:
    """Inferring object from images."""

    def on_event(
        self,
        dora_event,
        send_output,
    ) -> DoraStatus:
        """
        Run YOLOv8 inference on an incoming image event and emit flattened detection arrays.
        
        When `dora_event["type"] == "INPUT"`, the function expects `dora_event["value"]` to be a buffer that can be converted to a NumPy array and reshaped to (CAMERA_HEIGHT, CAMERA_WIDTH, 3). The image is converted from BGR to RGB, passed to the pretrained YOLOv8 model, and detected boxes are extracted. For each detection the output contains [x1, y1, x2, y2, confidence, class_label]; all detections are concatenated into a single NumPy array, flattened, converted to a PyArrow array, and emitted via `send_output` with the key "bbox" and the original `dora_event["metadata"]`.
        
        Parameters:
            dora_event (dict): Dora-rs event expected to include keys "type", "value" (raw image buffer convertible to NumPy), and "metadata".
            send_output (Callable): Callback used to emit results; invoked as send_output("bbox", <pyarrow.Array>, dora_event["metadata"]).
        
        Returns:
            DoraStatus: CONTINUE to allow further processing.
        """
        if dora_event["type"] == "INPUT":
            frame = (
                dora_event["value"].to_numpy().reshape((CAMERA_HEIGHT, CAMERA_WIDTH, 3))
            )
            frame = frame[:, :, ::-1]  # OpenCV image (BGR to RGB)
            results = model(frame, verbose=False)  # includes NMS
            # Process results
            boxes = np.array(results[0].boxes.xyxy.cpu())
            conf = np.array(results[0].boxes.conf.cpu())
            label = np.array(results[0].boxes.cls.cpu())
            # concatenate them together
            arrays = np.concatenate((boxes, conf[:, None], label[:, None]), axis=1)

            send_output("bbox", pa.array(arrays.ravel()), dora_event["metadata"])

        return DoraStatus.CONTINUE
