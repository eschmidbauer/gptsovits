import os

from gptsovits.text import cleaned_text_to_sequence
from gptsovits.text import symbols2 as symbols_v2

special = [
    ("￥", "zh", "SP2"),
    ("^", "zh", "SP3"),
]


def clean_text(text, language, version=None):
    symbols = symbols_v2.symbols
    language = "en"
    language_module_map = {"en": "english"}
    for special_s, special_l, target_symbol in special:
        if special_s in text and language == special_l:
            return clean_special(text, language, special_s, target_symbol, version)
    language_module = __import__("gptsovits.text." + language_module_map[language], fromlist=[language_module_map[language]])
    if hasattr(language_module, "text_normalize"):
        norm_text = language_module.text_normalize(text)
    else:
        norm_text = text
    phones = language_module.g2p(norm_text)
    if len(phones) < 4:
        phones = [','] + phones
    word2ph = None
    phones = ['UNK' if ph not in symbols else ph for ph in phones]
    return phones, word2ph, norm_text


def clean_special(text, language, special_s, target_symbol, version=None):
    symbols = symbols_v2.symbols
    language_module_map = {"en": "english"}
    text = text.replace(special_s, ",")
    language_module = __import__("gpt.text." + language_module_map[language], fromlist=[language_module_map[language]])
    norm_text = language_module.text_normalize(text)
    phones = language_module.g2p(norm_text)
    new_ph = []
    for ph in phones[0]:
        assert ph in symbols
        if ph == ",":
            new_ph.append(target_symbol)
        else:
            new_ph.append(ph)
    return new_ph, phones[1], norm_text


def text_to_sequence(text, language, version=None):
    version = os.environ.get('version', version)
    if version is None:
        version = 'v2'
    phones = clean_text(text)
    return cleaned_text_to_sequence(phones, version)
