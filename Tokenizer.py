import nltk
import os
import string

STEMMER = nltk.stem.porter.PorterStemmer()


def make_doc_read_generator(in_dir, docs_list):
    """
    Generator function for the next (term, doc_length, doc_id) tuple.
    Call this function to make the generator first, then use next() to generate the next tuple.
    Yields (None, None, None) when done.
    """
    for doc_name in docs_list:
        doc_path = os.path.join(in_dir, doc_name)
        doc = read_and_clean(doc_path)
        tokens = tokenize(doc)
        doc_length = len(tokens)
        # for this assignment, we can assume that document names are integers without exception
        # since we are using a generator, we only count the number of tokens once per file
        for tok in tokens:
            yield tok, doc_length, int(doc_name)
    yield None, None, None


def read_and_clean(doc_path):
    """
    Reads document at specified path, does case-folding and returns text.
    (All pre-processing before tokenization should go here)
    """
    with open(doc_path, "r") as f:
        return f.read().lower()


def tokenize(doc_text):
    """
    Takes in document text and tokenizes.
    Also does post-tokenization cleaning like stemming.
    """
    tokens = nltk.tokenize.word_tokenize(doc_text)
    tokens = [STEMMER.stem(tok) for tok in tokens]
    isNotOnlyPunct = lambda tok: any(char not in string.punctuation for char in tok)
    tokens = [tok for tok in tokens if isNotOnlyPunct(tok)]
    return tokens


def clean_operand(operand):
    """
    Case-folds and stems a single operand (token).
    For use in Parser, when parsing queries.
    """
    return STEMMER.stem(operand.lower())
