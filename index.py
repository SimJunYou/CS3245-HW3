#!/usr/bin/python3
import os
import sys
import getopt
from math import log10

# SELF-WRITTEN MODULES
from InputOutput import write_block
from Tokenizer import make_doc_read_generator


def build_index(in_dir, out_dict, out_postings):
    """
    Build index from documents stored in the input directory,
    then output the dictionary file and postings file
    """
    print("indexing...")

    docs_list = [
        f for f in os.listdir(in_dir) if os.path.isfile(os.path.join(in_dir, f))
    ]

    # we want to capture all document IDs and each document's length
    # we can do that using a dictionary mapping doc_id to doc_length
    docs_len_dct = {}

    # === Indexing happens here! ===
    dictionary = dict()
    pair_generator = make_doc_read_generator(in_dir, docs_list)

    current_doc = None
    term_freq_counter = dict()
    while True:
        term, doc_length, doc_id = next(pair_generator)

        # if we have run out of terms, we stop building index
        if term is None and doc_id is None:
            # we have one last document's length to calculate!
            # calc length and save to old doc's ID in docs_len_dct
            doc_length = 0
            for count in term_freq_counter.values():
                doc_length += (1 + log10(count)) ** 2
            docs_len_dct[current_doc] = doc_length**0.5
            break

        # if we encounter a new document, update docs_len_dct with the calculated
        # doc length and reset term_freq_counter
        if current_doc != doc_id:
            # calc length and save to old doc's ID in docs_len_dct
            doc_length = 0
            for count in term_freq_counter.values():
                doc_length += (1 + log10(count)) ** 2
            docs_len_dct[current_doc] = doc_length**0.5
            # then, reset counter and update current_doc
            current_doc = doc_id
            term_freq_counter = dict()

        # count occurrences of each term in each document
        if term in term_freq_counter:
            term_freq_counter[term] += 1
        else:
            term_freq_counter[term] = 1

        # update our dictionary of term -> posting lists
        if term in dictionary:
            # posting_list contains a mapping of doc_id -> term_freq
            # one posting_list is held for each term
            posting_list = dictionary[term]
            if doc_id in posting_list:
                dictionary[term][doc_id] += 1
            else:
                dictionary[term][doc_id] = 1
        else:
            dictionary[term] = {doc_id: 1}

    # we write the final posting list and dictionary to disk
    # since we have no more intersects, we will not use skip pointers anymore
    write_block(dictionary, out_dict, out_postings, docs_len_dct, write_skips=False)


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
