import tempfile
import json
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
import re


def find_all_indexes(input_str, substring):
    return [match.start() for match in re.finditer(re.escape(substring), input_str)]


def get_raw_text(file, path: str):
    stop_words = set(stopwords.words("english"))

    def process_text(text):
        print('working on file:', path)
        words = word_tokenize(text)
        filtered_words = [
            {"word": word, "pos": find_all_indexes(text, word)}
            for word in words
            if word.lower() not in stop_words
        ]
        print('finihed working on file:', path)
        return filtered_words

    filecontent = file.read()
    return process_text(filecontent.decode("utf-8"))
