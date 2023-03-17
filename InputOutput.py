import pickle
from math import floor, sqrt

# === READING ===
# PostingReader class -> An interface for posting list reading.
# (All other methods removed in favor of this new class)


class PostingReader:
    """
    An interface for a posting list reading.
    Keeps the dictionary within itself, so accessing the posting list of
    any given term is as easy as ".seek_term('term')".
    Automatically grabs the doc frequency (the first entry) upon seeking.
    Has helper methods like .read_entry(), .is_done(), etc.
    Should be used with a context manager (i.e. 'with' blocks) for
    automatic initialisation and closing of files.
    """

    def __init__(self, file, dct):
        self._fname = file
        self._dct = dct
        self._loc = 0

    def __enter__(self):
        self._f = open(self._fname, "r")
        return self

    def seek_term(self, term):
        """
        To be used right after entering the context manager!
        Seeks file to the desired term and returns the document frequency.
        """

        # we should be checking that terms are in dictionary in process_query
        assert term in self._dct, "Term not found in dictionary!"

        self._f.seek(self._dct[term], 0)

        # get document frequency
        doc_freq_str = char = ""
        while char != "$":
            doc_freq_str += char
            char = self._f.read(1)
        doc_freq = int(doc_freq_str)

        # flag for completing the reading of the given posting list
        self._done = False

        # since text files don't support relative seeks,
        # we need to store our previous location!
        # save location after reading the document frequency
        self._loc = self._f.tell()

        return doc_freq

    def __exit__(self, exc_type, exc_value, exc_traceback):
        # parameters here are required by Python, we won't use them
        self._f.close()

    def read_entry(self):
        """
        Using the current position of the instance's file pointer,
        read the next entry in the posting list and return it as a tuple:
        >> (doc_id, term_freq)
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

        self._loc = self._f.tell()

        # return a integer tuple
        return (int(doc_id), int(term_freq))

    def is_done(self):
        return self._done


def unpickle_file(filename):
    """
    Just unpickles a file. Putting this here since I don't want to import
    pickle elsewhere!
    """
    return pickle.load(open(filename, "rb"))


# === WRITING ===
# write_block -> Writes in-memory dictionary into a block (dictionary + posting files)
# serialize_posting -> Turns a posting list into a formatted string


def write_block(dictionary, out_dict, out_postings, docs_len_dct, write_skips=False):
    """
    For each (term, posting list) pair in the dictionary...

    Each posting list is in the following format: [Dict[doc_id -> term_freq], doc_length]
    We extract the Dict and pass it to serialize_posting, which returns a string.
    The serialized posting list is written into the postings file.
    We count the number of characters written so far as cumulative_ptr.

    As each term is written, we write the (term -> cumulative_ptr) pair into final_dict.
    The cumulative_ptr can be used to directly grab a posting list from the postings file.

    The dictionary mapping doc_id to doc_length is made in the top-level index.py entry method,
    and is passed in here via docs_len_dct.

    The (final_dict, docs_len_dct) tuple is written into the dictionary file using pickle.
    """
    final_dict = dict()
    cumulative_ptr = 0

    with open(out_postings, "w") as postings_fp:
        for term, posting_list in dictionary.items():
            posting_list_serialized = serialize_posting(posting_list, write_skips)
            final_dict[term] = cumulative_ptr
            cumulative_ptr += len(posting_list_serialized)
            postings_fp.write(posting_list_serialized)

    pickle.dump(final_dict, open(out_dict, "wb"))
    pickle.dump(
        docs_len_dct, open("lengths.txt", "wb")
    )  # FIXME: Don't hardcode file name?

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
