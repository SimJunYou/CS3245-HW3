#!/usr/bin/python3
import sys
import getopt

# SELF-WRITTEN MODULES
from Parser import read_and_parse_queries
from InputOutput import unpickle_file
from Searcher import process_query


def usage():
    print(
        "usage: "
        + sys.argv[0]
        + " -d dictionary-file -p postings-file -q file-of-queries -o output-file-of-results"
    )


def run_search(dict_file, postings_file, queries_file, results_file):
    """
    using the given dictionary file and postings file,
    perform searching on the given queries file and output the results to a file
    """
    print("running search on the queries...")

    dictionary = unpickle_file(dict_file)
    docs_len_dct = unpickle_file("lengths.txt")  # FIXME: Don't hardcode file name?
    queries = read_and_parse_queries(queries_file)

    with open(results_file, "w") as of:
        for query in queries:
            # if query is empty, print blank line and continue
            if not query:
                print("", file=of)
                continue
            # process query, convert to string
            # if there is an error, print an error line to the output file
            try:
                result = process_query(query, dictionary, docs_len_dct, postings_file)
                result = " ".join(map(str, result))
                print(result, file=of)
            except:
                print("Error processing query", file=of)


dictionary_file = postings_file = file_of_queries = output_file_of_results = None

try:
    opts, args = getopt.getopt(sys.argv[1:], "d:p:q:o:")
except getopt.GetoptError:
    usage()
    sys.exit(2)

for o, a in opts:
    if o == "-d":
        dictionary_file = a
    elif o == "-p":
        postings_file = a
    elif o == "-q":
        file_of_queries = a
    elif o == "-o":
        file_of_output = a
    else:
        assert False, "unhandled option"

if (
    dictionary_file == None
    or postings_file == None
    or file_of_queries == None
    or file_of_output == None
):
    usage()
    sys.exit(2)

run_search(dictionary_file, postings_file, file_of_queries, file_of_output)
