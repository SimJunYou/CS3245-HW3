from Tokenizer import tokenize


def read_and_parse_queries(queries_file):
    """
    Reads and tokenizes queries. Within the tokenization step, preprocessing
    like case folding and stemming is also done.
    Returns a list of queries, where each query is a list of tokens.
    """

    queries = read_queries(queries_file)

    queries = [tokenize(query) for query in queries]

    # # query string -> list of operators/operands
    # queries = [parse_query(query) for query in queries]

    # # operator/operand list -> operator/cleaned operand list
    # queries = [
    #     [(clean_operand(op) if type(op) == str else op) for op in query]
    #     for query in queries
    # ]

    # # operator/operand list -> postfixed list
    # queries = [postfix_conversion(query) for query in queries]

    # # operator/operand list -> operator/(cleaned operand, operand freq) list
    # queries = [
    #     add_document_freqs(query, postings_file, dictionary) for query in queries
    # ]

    return queries


def read_queries(queries_file):
    """
    Reads each line of queries file and strips whitespace.
    """
    with open(queries_file, "r") as f:
        queries = f.readlines()
    # remove trailing whitespace
    queries = list(map(lambda x: x.rstrip(), queries))
    return queries
