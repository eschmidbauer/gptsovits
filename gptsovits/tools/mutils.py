import os
import traceback
import ffmpeg
import numpy as np


def load_audio(file: str, sr: int):
    try:
        file = clean_path(file)
        if os.path.exists(file) == False:
            raise RuntimeError("You input a wrong audio path that does not exists, please fix it!")
        out, _ = (ffmpeg.input(file, threads=0).output("-", format="f32le", acodec="pcm_f32le", ac=1, ar=sr).run(cmd=["ffmpeg", "-nostdin"], capture_stdout=True, capture_stderr=True))
    except Exception as e:
        traceback.print_exc()
        raise RuntimeError(e)
    return np.frombuffer(out, np.float32).flatten()


def clean_path(path_str: str):
    if path_str.endswith(('\\', '/')):
        return clean_path(path_str[0:-1])
    path_str = path_str.replace('/', os.sep).replace('\\', os.sep)
    return path_str.strip(" ").strip('\'').strip("\n").strip('"').strip(" ").strip("\u202a")
