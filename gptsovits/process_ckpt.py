import os
import shutil
import traceback
from collections import OrderedDict
from time import time as ttime

import torch


def m_save(fea, path):
    dir = os.path.dirname(path)
    name = os.path.basename(path)
    tmp_path = f"{ttime()}.pth"
    torch.save(fea, tmp_path)
    shutil.move(tmp_path, f"{dir}/{name}")


def savee(ckpt, name, epoch, steps, hps):
    try:
        opt = OrderedDict()
        opt["weight"] = {}
        for key in ckpt.keys():
            if "enc_q" in key:
                continue
            opt["weight"][key] = ckpt[key].half()
        opt["config"] = hps
        opt["info"] = f"{epoch}epoch_{steps}iteration"
        os.makedirs(hps.save_weight_dir, exist_ok=True)
        m_save(opt, f"{hps.save_weight_dir}/{name}.pth")
        return "Success."
    except:
        return traceback.format_exc()
