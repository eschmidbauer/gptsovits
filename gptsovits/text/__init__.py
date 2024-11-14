import os

from gptsovits.text import symbols2 as symbols_v2

# if os.environ.get("version","v1")=="v1":
#   from text.symbols import symbols
# else:
#   from text.symbols2 import symbols


_symbol_to_id_v2 = {s: i for i, s in enumerate(symbols_v2.symbols)}


def cleaned_text_to_sequence(cleaned_text, version=None):
    phones = [_symbol_to_id_v2[symbol] for symbol in cleaned_text]
    return phones
