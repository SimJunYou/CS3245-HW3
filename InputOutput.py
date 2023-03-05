import pickle
from math import floor, sqrt

# === READING ===
# read_posting_list -> Reads a posting list out of a posting list block
# get_dictionary -> Reads the dictionary file and returns an dictionary


def read_posting_list(posting_fp, location):
    # TODO: To be edited for file cursor reading
    """
    Returns a posting list from a posting list file pointer,
    given its location (in characters from start) in the file.
    """
    posting_fp.seek(location, 0)
    posting_str = char = ""

    # move past the document frequency stored and reset char
    while char != "$":
        char = posting_fp.read(1)
    char = ""

    # read the entire posting list and stop at terminating char
    while char != "|":
        posting_str += char
        char = posting_fp.read(1)

    # convert to list of ints and return
    parse_list_item = (
        lambda item: tuple(map(int, item.split("^"))) if "^" in item else int(item)
    )
    posting_list = list(map(parse_list_item, posting_str.split(",")))
    return posting_list


def read_doc_freq(posting_fp, location):
    """
    Reads only the document frequency from the posting list file.
    For query optimization purposes.
    """
    posting_fp.seek(location, 0)
    doc_freq_str = char = ""
    while char != "$":
        doc_freq_str += char
        char = posting_fp.read(1)
    doc_freq = int(doc_freq_str)
    return doc_freq


def get_dict_and_doc_list(out_dict):
    """
    FOR SEARCHING ONLY!
    We assume that the full index does not fit in memory, so we only load the dictionary.
    The dictionary lets us read posting lists by their positions in the posting lists file.
    """
    return pickle.load(open(out_dict, "rb"))


# === WRITING ===
# write_block -> Writes in-memory dictionary into a block (dictionary + posting files)
# serialize_posting -> Turns a posting list into a formatted string
# add_skips_to_posting -> Adds skip pointers to an existing posting list


def write_block(
    dictionary, out_dict, out_postings, docs_list=[], block_num="", write_skips=False
):
    """
    For each (term, posting list) pair in the dictionary...

    We serialize each posting list using serialize_posting into a string.
    The serialized posting list is written into the postings file.
    We count the number of characters written so far as cumulative_ptr.

    As each term is written, we write the (term, cumulative_ptr) pair into index.
    The cumulative_ptr can be used to directly grab a posting list from the postings file.

    The (list of all documents, index) tuple is written into the dictionary file using pickle.
    """
    index = dict()
    cumulative_ptr = 0

    with open(str(block_num) + out_postings, "w") as postings_fp:
        for term, posting_list in dictionary.items():
            posting_list = posting_list[1]  # discard frequency for now
            posting_list_serialized = serialize_posting(posting_list, write_skips)
            index[term] = cumulative_ptr
            cumulative_ptr += len(posting_list_serialized)
            postings_fp.write(posting_list_serialized)

    # we want to store the docs_list with each doc as a set of integers
    if docs_list:
        docs_list = set(map(int, docs_list))
        pickle.dump((index, docs_list), open(str(block_num) + out_dict, "wb"))
    else:
        pickle.dump(index, open(str(block_num) + out_dict, "wb"))

    if block_num:
        print(f"Wrote {len(dictionary)} terms into block number {block_num}")
    else:
        print(f"Wrote {len(dictionary)} terms into final files")


def serialize_posting(posting_list, write_skips):
    """
    Turns a posting list into a string, and returns the string.
    The string format is: "(freq)$(id1),(id2^skip),(...),(idn)|".
    Skip denotes how many characters to skip to get to the next number.
    The "|" is the terminator character for the serialization.
    """
    posting_list = sorted(list(posting_list))
    doc_freq = str(len(posting_list))

    if write_skips:
        # convert to posting list with skips, then convert the skips to string form
        posting_list = add_skips_to_posting(posting_list)
        for i, item in enumerate(posting_list):
            if isinstance(item, tuple):
                posting_list[i] = f"{item[0]}^{item[1]}"

    doc_ids = ",".join(map(str, posting_list))
    output = f"{doc_freq}${doc_ids}|"
    return output


def add_skips_to_posting(posting_list):
    """
    Adds skip pointers to existing posting list.
    Changes existing doc id items into (doc id, skip interval) tuple.
    Returns new posting list.
    Does not do anything if list length is below 4!
    """
    # posting list should have at least 4 elements for skip pointers to be efficient
    if len(posting_list) < 4:
        return posting_list

    # calculate the last index which should contain a skip
    size = len(posting_list)
    skip_interval = floor(sqrt(size))
    last_skip = (size - 1) - skip_interval
    last_skip = last_skip - (last_skip % skip_interval)

    for i, doc_id in enumerate(posting_list):
        if i <= last_skip and i % skip_interval == 0:
            posting_list[i] = (doc_id, skip_interval)
    return posting_list
