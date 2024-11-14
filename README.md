# gptsovits

## setup

```bash
conda create python=3.9 --prefix ./venv
conda activate ./venv
conda install pytorch==2.1.1 torchvision==0.16.1 torchaudio==2.1.1 pytorch-cuda=11.8 -c pytorch -c nvidia
pip install 'git+https://github.com/eschmidbauer/gptsovits.git'

git lfs install
git clone https://huggingface.co/eschmidbauer/gptsovits
mv gptsovits/pretrained_models .
mv gptsovits/configs .
rm -rf gptsovits
```

## tts

```python
from io import BytesIO
from typing import List

import nltk
import numpy as np
import soundfile as sf

from gptsovits.tts import TTS, TTS_Config

nltk.download('averaged_perceptron_tagger_eng')


tts_config = TTS_Config("configs/tts_infer.yaml")
tts_pipeline = TTS(tts_config)

req = {
    "text": "[output text goes here]",
    "text_lang": "en",
    "ref_audio_path": "[file path of reference wav]",
    "aux_ref_audio_paths": [],
    "prompt_text": "[text of reference wav]",
    "prompt_lang": "en",
    "top_k": 5,
    "top_p": 1,
    "temperature": 1,
    "text_split_method": "cut0",
    "batch_size": 1,
    "batch_threshold": 0.75,
    "split_bucket": True,
    "return_fragment": False,
    "speed_factor": 1.0,
    "fragment_interval": 0.3,
    "seed": -1,
    "parallel_infer": True,
    "repetition_penalty": 1.35
}
tts_generator = tts_pipeline.run(req)
e: List[np.ndarray] = []
rate: int
for sr, audio_data in tts_generator:
    rate = sr
    e.append(audio_data)

sf.write(io_buffer := BytesIO(), np.concatenate(e), sr, format='wav')
io_buffer.seek(0)
with open("output.wav", "wb") as f:
    f.write(io_buffer.read())

```
