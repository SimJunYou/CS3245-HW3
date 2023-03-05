from Tokenizer import clean_operand
from InputOutput import read_doc_freq

OPERATOR_ORDER = {"OR": 0, "AND": 1, "NOT": 2, "(": 3, ")": 4}


def read_and_parse_queries(queries_file, postings_file, dictionary):
    """
    Entry point for all the query reading/parsing functions.
    Also cleans operands by case-folding and stemming them.
    Dictionary and postings file are included so we can get the document frequencies.
    Takes in queries file, returns list of cleaned parsed queries each in postfix order.

    The final list contains either operators (in integer order form),
    or operands in the following tuple: (operand, freq)
    """

    queries = read_queries(queries_file)

    # query string -> list of operators/operands
    queries = [parse_query(query) for query in queries]

    # operator/operand list -> operator/cleaned operand list
    queries = [
        [(clean_operand(op) if type(op) == str else op) for op in query]
        for query in queries
    ]

    # operator/operand list -> postfixed list
    queries = [postfix_conversion(query) for query in queries]

    # operator/operand list -> operator/(cleaned operand, operand freq) list
    queries = [
        add_document_freqs(query, postings_file, dictionary) for query in queries
    ]

    return queries


def add_document_freqs(query, postings_file, dictionary):
    """
    Turns each operand in the query into a tuple of operand and doc freq.
    Leaves operators unchanged.
    Returns a new list.
    """
    output = []
    with open(postings_file, "r") as pf:
        for op in query:
            if type(op) is str:
                if op in dictionary:
                    output.append((op, read_doc_freq(pf, dictionary[op])))
                else:
                    output.append((op, 0))
            else:
                output.append(op)
    return output


def read_queries(queries_file):
    """
    Reads each line of queries file and strips whitespace.
    """
    with open(queries_file, "r") as f:
        queries = f.readlines()
    # remove trailing whitespace
    queries = list(map(lambda x: x.rstrip(), queries))
    return queries


def parse_query(query_string):
    """
    'Tokenizes' a given query string by splitting it into operands and operators.
    Cleans each operand using Tokenizer module's clean_token function.
    Does operator conversion before returning the final list.
    """
    query_string = query_string.replace("(", " ( ")
    query_string = query_string.replace(")", " ) ")
    tokens = query_string.split(" ")

    query = []
    # split parantheses from the tokens
    for tok in tokens:
        if tok == "(":
            query.append("(")
        elif tok == ")":
            query.append(")")
        elif tok:
            query.append(tok)

    # given original input "bill OR Gates AND (vista OR XP) AND NOT mac"...
    # the output list here should be in this form:
    # [bill, OR, Gates, AND, (, vista, OR, XP, ), AND, NOT, mac]
    query = operator_conversion(query)
    return query


def operator_conversion(query):
    """
    Converts a operand in string form (e.g. "AND") to its integer order (e.g. 1).
    """
    return [(q if q not in OPERATOR_ORDER else OPERATOR_ORDER[q]) for q in query]


def postfix_conversion(query):
    """
    Shunting yard algorithm, with no error handling because we assume all inputs are perfect.
    Operands and operators are distinguished by type, since operators are converted to their integer order.
    Takes in list of operands + operators in infix order, returns them in postfix order.
    """
    stack = []
    output = []

    for symbol in query:

        # if it is an operand, just add to output queue
        if not type(symbol) is int:
            output.append(symbol)

        # if it is an operator, push onto stack
        elif type(symbol) is int:
            # if symbol is not a parenthesis,
            if symbol in (0, 1, 2):
                # we pop operators if the conditions are fulfilled:
                # 1. stack is not empty
                # 2. top of stack is not a left paren
                # 3. top of stack has higher precedence than incoming operator
                while stack and stack[-1] != 3 and stack[-1] > symbol:
                    output.append(stack.pop())
                stack.append(symbol)

            # if symbol is a left parenthesis,
            elif symbol == 3:
                stack.append(symbol)

            # if the symbol is a right parenthesis,
            else:
                # we pop operators if the conditions are fulfilled:
                # 1. stack is not empty
                # 2. top of stack is not a left paren
                while stack and stack[-1] != 3:
                    output.append(stack.pop())
                stack.pop()  # remove the left parenthesis

    # pop all remaining operators onto the output queue
    while stack:
        output.append(stack.pop())
    return output
