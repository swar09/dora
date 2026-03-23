"""Speech-to-text operator for dora-rs dataflow using OpenAI Whisper.

This operator receives audio data, transcribes it into text using the
OpenAI Whisper 'base' model, and emits the resulting text to the "text"
output.
"""

import pyarrow as pa
import whisper
from dora import DoraStatus

model = whisper.load_model("base")


class Operator:
    """Transforming Speech to Text using OpenAI Whisper model."""

    def on_event(
        self,
        dora_event,
        send_output,
    ) -> DoraStatus:
        """
        Transcribe incoming audio contained in a dora_event and emit the resulting text on the "text" output.
        
        Parameters:
            dora_event (dict): Event dictionary. When dora_event["type"] == "INPUT" expects:
                - "value": an object with a .to_numpy() method that yields audio samples,
                - "metadata": dictionary forwarded to the output.
            send_output (Callable[[str, pa.Array, dict], None]): Callback used to emit output; invoked as send_output("text", pa.array([transcript]), metadata).
        
        Returns:
            DoraStatus: DoraStatus.CONTINUE to indicate processing should continue.
        """
        if dora_event["type"] == "INPUT":
            audio = dora_event["value"].to_numpy()
            audio = whisper.pad_or_trim(audio)
            result = model.transcribe(audio, language="en")
            send_output("text", pa.array([result["text"]]), dora_event["metadata"])
        return DoraStatus.CONTINUE
