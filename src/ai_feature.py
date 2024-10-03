from nltk.corpus import stopwords
import spacy

nlp = spacy.load("en_core_web_sm")


def parse_query(query):
    doc = nlp(query)

    include_terms = []
    exclude_terms = []
    stop_words = set(stopwords.words("english"))
    for token in doc:
        if token.text.lower() == "and":
            continue
        elif token.text.lower() in ["without", "no", "but", "not"]:
            exclude_terms.append(doc[token.i + 1].text)
        else:
            include_terms.append(token.text)

    include_terms = [term for term in include_terms if term not in exclude_terms]
    stop_words = set(stopwords.words("english"))
    include_terms = [term for term in include_terms if term not in stop_words]
    exclude_terms = [term for term in exclude_terms if term not in stop_words]
    return include_terms, exclude_terms
