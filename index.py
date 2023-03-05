#!/usr/bin/python3
import os
import sys
import getopt

# SELF-WRITTEN MODULES
from InputOutput import merge_blocks, write_block
from Tokenizer import make_pair_generator

# CONSTANTS:
# SPIMI threshold -> Set to 200,000 based on our own testing
THRESHOLD = 200_000


def build_index(in_dir, out_dict, out_postings):
    """
    Build index from documents stored in the input directory,
    then output the dictionary file and postings file
    """
    print("indexing...")

    docs_list = [
        f for f in os.listdir(in_dir) if os.path.isfile(os.path.join(in_dir, f))
    ]
    # docs_list = docs_list[:10]  # TODO: Remove this

    # === SPIMI-Invert implementation ===
    # dictionary: Term -> [Term frequency, Set<Doc Ids>]
    dictionary = dict()
    pairs_processed = 0
    block_num = 1
    pair_generator = make_pair_generator(in_dir, docs_list)

    while True:
        term, doc_id = next(pair_generator)

        # if we have run out of terms, we stop building index
        if term is None and doc_id is None:
            break

        if term in dictionary:
            dictionary[term][0] += 1
            dictionary[term][1].add(doc_id)
        else:
            dictionary[term] = [1, set([doc_id])]
        pairs_processed += 1

        # if memory full, write dictionary to disk and reset in-memory index
        if pairs_processed >= THRESHOLD:
            write_block(
                dictionary,
                out_dict,
                out_postings,
                block_num=block_num,
                write_skips=False,
            )
            block_num += 1
            dictionary = dict()
            pairs_processed = 0

    # all blocks should be written at this point
    # now we need to merge all blocks into one
    # (if there is only one 'block', don't merge since it's still in memory)
    if block_num > 1:
        final_dict = merge_blocks(out_dict, out_postings, block_num)
    else:
        final_dict = dictionary

    # finally, we write the final posting list and dictionary to disk
    # at this step, we will write skip pointers also into the posting list
    write_block(
        final_dict, out_dict, out_postings, docs_list=docs_list, write_skips=True
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
