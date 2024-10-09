from nltk.corpus import stopwords
import spacy
from sentence_transformers import SentenceTransformer, util
import os

nlp = spacy.load("en_core_web_sm")
text_model = SentenceTransformer(
    'sentence-transformers/clip-ViT-B-32-multilingual-v1')


def get_surrounding_text(file_path, index, num_symbols=50):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            text = file.read()
            start = max(0, index - num_symbols)
            end = min(len(text), index + num_symbols)
            return text[start:end]
    except FileNotFoundError:
        print(f"File not found: {file_path}")
    except Exception as e:
        print(f"An error occurred: {e}")


def parse_query(query):
    doc = nlp(query)

    include_terms = []
    exclude_terms = []
    stop_words = set(stopwords.words("english"))
    for token in doc:
        include_terms.append(token.text)

    include_terms = [
        term for term in include_terms if term not in exclude_terms]
    stop_words = set(stopwords.words("english"))
    include_terms = [term for term in include_terms if term not in stop_words]
    return include_terms


def compare_results(snippets, user_request):
    snippets_embeddings = text_model.encode(snippets)
    user_requests_embeding = text_model.encode(
        user_request)
    cos_sim = util.cos_sim(user_requests_embeding, snippets_embeddings)
    return cos_sim


def get_best_snippet(file_names: list[str, list[int]], user_request: str):
    best_values = dict()
    for pair in file_names:
        list_of_snippets = []
        for coordinates_list in pair[1]:
            for coordinates in coordinates_list:
                list_of_snippets.append(get_surrounding_text(os.getcwd().removesuffix('\\src') +
                                                             '\\storage\\' + pair[0], coordinates))
        list_of_weights = list(compare_results(list_of_snippets, user_request))
        best_values[pair[0]] = list_of_snippets[list_of_weights.index(
            max(list_of_weights))]
    return best_values
