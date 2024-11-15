import os
import re
import sys
from typing import Dict, List, Tuple

import LangSegment
import torch
from tqdm import tqdm
from transformers import AutoModelForMaskedLM, AutoTokenizer

from gptsovits.text import cleaned_text_to_sequence
from gptsovits.text.cleaner import clean_text
from gptsovits.text_segmentation_method import get_method as get_seg_method
from gptsovits.text_segmentation_method import split_big_text, splits
from gptsovits.tools.i18n.i18n import I18nAuto, scan_language_list

now_dir = os.getcwd()
sys.path.append(now_dir)


language = os.environ.get("language", "Auto")
language = sys.argv[-1] if sys.argv[-1] in scan_language_list() else language
i18n = I18nAuto(language=language)
punctuation = set(['!', '?', '…', ',', '.', '-', " "])


def get_first(text: str) -> str:
    pattern = "[" + "".join(re.escape(sep) for sep in splits) + "]"
    text = re.split(pattern, text)[0].strip()
    return text


def merge_short_text_in_array(texts: str, threshold: int) -> list:
    if (len(texts)) < 2:
        return texts
    result = []
    text = ""
    for ele in texts:
        text += ele
        if len(text) >= threshold:
            result.append(text)
            text = ""
    if (len(text) > 0):
        if len(result) == 0:
            result.append(text)
        else:
            result[len(result) - 1] += text
    return result


class TextPreprocessor:
    def __init__(self, bert_model: AutoModelForMaskedLM,
                 tokenizer: AutoTokenizer, device: torch.device):
        self.bert_model = bert_model
        self.tokenizer = tokenizer
        self.device = device

    def preprocess(self, text: str, lang: str, text_split_method: str, version: str = "v2") -> List[Dict]:
        text = self.replace_consecutive_punctuation(text)
        texts = self.pre_seg_text(text, lang, text_split_method)
        result = []
        for text in tqdm(texts):
            phones, bert_features, norm_text = self.segment_and_extract_feature_for_text(text, lang, version)
            if phones is None or norm_text == "":
                continue
            res = {"phones": phones, "bert_features": bert_features, "norm_text": norm_text}
            result.append(res)
        return result

    def pre_seg_text(self, text: str, lang: str, text_split_method: str):
        text = text.strip("\n")
        if len(text) == 0:
            return []
        if (text[0] not in splits and len(get_first(text)) < 4):
            text = "。" + text if lang != "en" else "." + text
        print(text)
        seg_method = get_seg_method(text_split_method)
        text = seg_method(text)
        while "\n\n" in text:
            text = text.replace("\n\n", "\n")

        _texts = text.split("\n")
        _texts = self.filter_text(_texts)
        _texts = merge_short_text_in_array(_texts, 5)
        texts = []

        for text in _texts:
            if (len(text.strip()) == 0):
                continue
            if not re.sub("\W+", "", text):
                continue
            if (text[-1] not in splits):
                text += "。" if lang != "en" else "."
            if (len(text) > 510):
                texts.extend(split_big_text(text))
            else:
                texts.append(text)
        print(texts)
        return texts

    def segment_and_extract_feature_for_text(self, text: str, language: str, version: str = "v1") -> Tuple[list, torch.Tensor, str]:
        return self.get_phones_and_bert(text, language, version)

    def get_phones_and_bert(self, text: str, language: str, version: str, final: bool = False):
        LangSegment.setfilters(["en"])
        formattext = " ".join(tmp["text"] for tmp in LangSegment.getTexts(text))
        while "  " in formattext:
            formattext = formattext.replace("  ", " ")
        phones, word2ph, norm_text = self.clean_text_inf(formattext, language, version)
        bert = torch.zeros((1024, len(phones)), dtype=torch.float32).to(self.device)
        if not final and len(phones) < 6:
            return self.get_phones_and_bert("." + text, language, version, final=True)
        return phones, bert, norm_text

    def get_bert_feature(self, text: str, word2ph: list) -> torch.Tensor:
        with torch.no_grad():
            inputs = self.tokenizer(text, return_tensors="pt")
            for i in inputs:
                inputs[i] = inputs[i].to(self.device)
            res = self.bert_model(**inputs, output_hidden_states=True)
            res = torch.cat(res["hidden_states"][-3:-2], -1)[0].cpu()[1:-1]
        assert len(word2ph) == len(text)
        phone_level_feature = []
        for i in range(len(word2ph)):
            repeat_feature = res[i].repeat(word2ph[i], 1)
            phone_level_feature.append(repeat_feature)
        phone_level_feature = torch.cat(phone_level_feature, dim=0)
        return phone_level_feature.T

    def clean_text_inf(self, text: str, language: str, version: str = "v2"):
        phones, word2ph, norm_text = clean_text(text, language, version)
        phones = cleaned_text_to_sequence(phones, version)
        return phones, word2ph, norm_text

    def get_bert_inf(self, phones: list, word2ph: list, norm_text: str, language: str):
        language = language.replace("all_", "")
        if language == "zh":
            feature = self.get_bert_feature(norm_text, word2ph).to(self.device)
        else:
            feature = torch.zeros(
                (1024, len(phones)),
                dtype=torch.float32,
            ).to(self.device)

        return feature

    def filter_text(self, texts):
        _text = []
        if all(text in [None, " ", "\n", ""] for text in texts):
            raise ValueError(i18n("请输入有效文本"))
        for text in texts:
            if text in [None, " ", ""]:
                pass
            else:
                _text.append(text)
        return _text

    def replace_consecutive_punctuation(self, text):
        punctuations = ''.join(re.escape(p) for p in punctuation)
        pattern = f'([{punctuations}])([{punctuations}])+'
        result = re.sub(pattern, r'\1', text)
        return result
