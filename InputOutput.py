import pickle
from math import floor, sqrt

# === READING ===
# PostingReader class -> An interface for posting list reading.
# (All other methods removed in favor of this new class)


class PostingReader:
    """
    An interface for a posting list reading.
    Automatically grabs the doc frequency (the first entry) upon init.
    Has helper methods like .read_entry(), .skip(), etc.
    Should be used with a context manager (i.e. 'with' blocks) for
    automatic initialisation and closing of files.
    """

    def __init__(self, file, location):
        self.file = file
        self.location = location

    def __enter__(self):
        self._f = open(self.file, "r")
        self._f.seek(self.location, 0)

        # get document frequency
        doc_freq_str = char = ""
        while char != "$":
            doc_freq_str += char
            char = self._f.read(1)
        self._docfreq = int(doc_freq_str)

        # flag for completing the reading of the given posting list
        self._done = False

        # since text files don't support relative seeks,
        # we need to store our previous location!
        # save location after reading the document frequency
        self._loc = self._f.tell()

        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        # parameters here are required by Python, we won't use them
        self._f.close()

    def read_entry(self):
        """
        Using the current position of the instance's file pointer,
        read the next entry in the posting list and return it as a tuple:
        >> (doc_id, term_freq, skip)
        Skip will be -1 if there is no skip pointer.
        """
        # throw error if we're trying to read a completely read posting list
        assert not self._done, "Reading of posting list is already complete!"

        self._f.seek(self._loc, 0)

        entry = ""
        char = ""
        while char != "," and char != "|":
            entry += char
            char = self._f.read(1)
        if char == "|":
            self._done = True  # update flag if the posting list is done

        doc_id, term_freq = entry.split("*")
        skip = -1
        if "^" in term_freq:
            term_freq, skip = term_freq.split("^")

        self._loc = self._f.tell()

        # return a integer tuple
        return (int(doc_id), int(term_freq), int(skip))

    def skip(self, skip_amt):
        self._f.seek(self._loc + skip_amt, 0)
        self._loc = self._f.tell()

    def get_doc_freq(self):
        return self._docfreq

    def is_done(self):
        return self._done


def unpickle_dict_file(out_dict):
    """
    Returns the (dictionary, docs_dict) tuple.
    dictionary is the dictionary mapping term to location in postings file.
    docs_dict is the dictionary mapping doc_id to doc_length.
    """
    return pickle.load(open(out_dict, "rb"))


# === WRITING ===
# write_block -> Writes in-memory dictionary into a block (dictionary + posting files)
# serialize_posting -> Turns a posting list into a formatted string


def write_block(dictionary, out_dict, out_postings, docs_dict, write_skips=False):
    """
    For each (term, posting list) pair in the dictionary...

    Each posting list is in the following format: [Dict[doc_id -> term_freq], doc_length]
    We extract the Dict and pass it to serialize_posting, which returns a string.
    The serialized posting list is written into the postings file.
    We count the number of characters written so far as cumulative_ptr.

    As each term is written, we write the (term -> cumulative_ptr) pair into final_dict.
    The cumulative_ptr can be used to directly grab a posting list from the postings file.

    The dictionary mapping doc_id to doc_length is made in the top-level index.py entry method,
    and is passed in here via docs_dict.

    The (final_dict, docs_dict) tuple is written into the dictionary file using pickle.
    """
    final_dict = dict()
    cumulative_ptr = 0

    with open(out_postings, "w") as postings_fp:
        for term, posting_list in dictionary.items():
            posting_list_serialized = serialize_posting(posting_list, write_skips)
            final_dict[term] = cumulative_ptr
            cumulative_ptr += len(posting_list_serialized)
            print(posting_list_serialized)
            postings_fp.write(posting_list_serialized)

    # we want to store the docs_list with each doc as a set of integers
    docs_list = set(map(int, docs_list))
    pickle.dump((final_dict, docs_dict), open(out_dict, "wb"))

    print(f"Wrote {len(dictionary)} terms into final files")


def serialize_posting(posting_list, write_skips):
    """
    Turns a posting list into a string, and returns the string.
    The string format is: "(freq)$(id1*tf1),(id2*tf2^skip),(...),(idn*tfn)|".
    Skip denotes how many characters to skip to get to the next skip number.
    The "|" is the terminator character for the serialization.
    """
    # convert the dictionary into a list of tuples (doc_id, term_freq)
    posting_list = list(posting_list.items())

    # we take the 2nd element (term_freq) to sort by descending term frequency
    posting_list = sorted(posting_list, key=lambda x: -x[1])

    # serialize each tuple first, before we add skip pointers
    posting_list = [f"{doc_id}*{term_freq}" for doc_id, term_freq in posting_list]

    output = ""

    # posting list should have at least 4 elements for skip pointers to be efficient
    if write_skips and len(posting_list) >= 4:
        # calculate the last index which should contain a skip
        size = len(posting_list)
        skip_interval = floor(sqrt(size))
        last_skip = (size - 1) - skip_interval
        last_skip = last_skip - (last_skip % skip_interval)
    else:
        # setting these to these values will stop skip pointers from being added
        last_skip = -1
        skip_interval = 1

    # since our skip pointers encode the number of characters to the next item with skip,
    # we build the serialization from back to front, so we can count the number of
    # characters between a later skip and an earlier skip more easily

    # if last_skip or skip_interval are set to 0, then skip pointers will not be added

    prev_skip_len = len(posting_list[-1])
    for i, item in list(enumerate(posting_list))[::-1]:
        if i <= last_skip and i % skip_interval == 0:  # if current item has skip,
            output = f"{item}^{len(output) - prev_skip_len}," + output
            prev_skip_len += len(output) - prev_skip_len
        else:
            output = f"{item}," + output
        output = output[:-1] + "|"  # finally, replace ending comma with |

    output = f"{str(len(posting_list))}${output}"  # add in doc freq
    return output


with PostingReader("postings.txt", 41) as tmp:
    while not tmp.is_done():
        print(tmp.read_entry())
