# MIT License
#
# Copyright (c) 2023 CNRS
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.


from pyannote.audio import Pipeline, Audio
import torch
import base64
import traceback


class EndpointHandler:
    def __init__(self, path=""):
        # initialize pretrained pipeline
        self._pipeline = Pipeline.from_pretrained("pyannote/speaker-diarization-3.1")

        # send pipeline to GPU if available
        if torch.cuda.is_available():
            self._pipeline.to(torch.device("cuda"))

        # initialize audio reader
        self._io = Audio()

    def __call__(self, data):
        try:
            inputs = data.pop("inputs", data)
            if not isinstance(inputs, str):
                # Handle cases where "inputs" key is missing or its value isn't a string
                err_msg = "Request JSON must contain 'inputs' key with a base64 encoded string."
                print(f"HANDLER ERROR: {err_msg} - Received data type: {type(inputs)}")
                return {"error": err_msg}
    
            audio_bytes = base64.b64decode(inputs.encode('utf-8'))
            audio_io = io.BytesIO(audio_bytes)
    
            waveform, sample_rate = self._io({"audio": audio_io})
    
            parameters = data.pop("parameters", dict())
            diarization = self.pipeline(
                {"waveform": waveform, "sample_rate": sample_rate}, **parameters
            )
    
            processed_diarization = [
                {
                    "speaker": speaker,
                    "start": f"{turn.start:.3f}",
                    "end": f"{turn.end:.3f}",
                }
                for turn, _, speaker in diarization.itertracks(yield_label=True)
            ]
    
            return {"diarization": processed_diarization}
        except Exception as e:
            print(f"HANDLER ERROR: Exception during processing: {e}")
            traceback.print_exc() # Print full traceback to endpoint logs
            return {"error": f"Failed during processing: {str(e)}"}
