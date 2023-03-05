#!/usr/bin/python3
import os
import sys
import getopt

# SELF-WRITTEN MODULES
from InputOutput import write_block
from Tokenizer import make_pair_generator


def build_index(in_dir, out_dict, out_postings):
    """
    Build index from documents stored in the input directory,
    then output the dictionary file and postings file
    """
    print("indexing...")

    docs_list = [
        f for f in os.listdir(in_dir) if os.path.isfile(os.path.join(in_dir, f))
    ]
    docs_list = docs_list[:5]

    # === Indexing happens here! ===
    dictionary = dict()
    pair_generator = make_pair_generator(in_dir, docs_list)

    while True:
        term, doc_id = next(pair_generator)

        # if we have run out of terms, we stop building index
        if term is None and doc_id is None:
            break

        if term in dictionary:
            # term_dict contains a mapping of doc_id -> term_freq
            # one term_dict is held for each term
            term_dict = dictionary[term]
            if doc_id in term_dict:
                dictionary[term][doc_id] += 1
            else:
                dictionary[term][doc_id] = 1
        else:
            dictionary[term] = {doc_id: 1}

    # we write the final posting list and dictionary to disk
    # we will write skip pointers also into the posting list at this step
    write_block(
        dictionary, out_dict, out_postings, docs_list=docs_list, write_skips=True
    )


def usage():
    print(
        "usage: "
        + sys.argv[0]
        + " -i directory-of-documents -d dictionary-file -p postings-file"
    )


input_directory = output_file_dictionary = output_file_postings = None

try:
    opts, args = getopt.getopt(sys.argv[1:], "i:d:p:")
except getopt.GetoptError:
    usage()
    sys.exit(2)

for o, a in opts:
    if o == "-i":  # input directory
        input_directory = a
    elif o == "-d":  # dictionary file
        output_file_dictionary = a
    elif o == "-p":  # postings file
        output_file_postings = a
    else:
        assert False, "unhandled option"

if (
    input_directory == None
    or output_file_postings == None
    or output_file_dictionary == None
):
    usage()
    sys.exit(2)

build_index(input_directory, output_file_dictionary, output_file_postings)
