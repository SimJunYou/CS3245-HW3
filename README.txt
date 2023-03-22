This is the README file for A0200198L-A0199724M's submission
Email(s): e0407179@u.nus.edu e0406705@u.nus.edu

== Python Version ==

We're using Python Version 3.8.10 for this assignment.

== General Notes about this assignment ==

Some carry-over notes from HW2:
> Tokenization is simple, using NLTK's word_tokenize, case folding, and Porter stemming.
> Punctuation is left in place.
>
> The dictionary contains a mapping of terms to their position in the posting lists file
> in number of characters, which serves as a pointer for retrieval.
> 
> The final dictionary file contains:
> - Dictionary object, as mentioned above
> 
> Special characters:
> - '$' separates the number of items from the actual list
> - '*' entails the delimiter between the document ID and its respective term frequency
> - '|' terminates the posting list serialization
> 

The final posting list will have term frequencies written in it.
Each posting list has this format: "df$id1*tf1,id2*tf2,...,idn*tfn|"
...where df is document frequency, idn is the nth document ID, and tfn is the term frequency of the nth document.
Skip pointers have been disabled.

The search method only reads the necessary postings lists from the postings lists file, using the dictionary
which stores the location of each term's postings list in the file.

The get_doc_tfidf_dict and calc_query_tfidf methods in Searcher.py compute the cosine similarities
with the aid of the interface PostingReader in InputOutput.py to grab the document and term frequencies.

In the indexing step, document lengths are calculated and stored in lengths.txt as a dictionary 
mapping document ID to the document length. This is used in Searcher.py to normalize the document and query vectors
to calculate cosine similarity.

== Files included with this submission ==

- README.txt
- CS3245-hw3-check.sh
- index.py       > Main loop for indexing, calls helper functions from InputOutput and Tokenizer
- search.py      > Main loop for search, calls helper functions from InputOutput, Parser, and Searcher

- InputOutput.py > Helper functions for input/output operations
- Tokenizer.py   > Helper functions for tokenization operations
- Parser.py      > Helper functions for parsing queries
- Searcher.py    > Helper functions for computation of cosine similarities, and class definitions for calculation of lnc.ltc

- dictionary.txt > Dictionary file from indexing Reuters corpora 
- postings.txt   > Postings lists file from indexing Reuters corpora 
- length.txt     > File containing dictionary mapping document ID to document vector length from indexing Reuters corpora 

== Statement of individual work ==

Please put a "x" (without the double quotes) into the bracket of the appropriate statement.

[x] I/We, A0200198L-A0199724M, certify that we have followed the CS 3245 Information
Retrieval class guidelines for homework assignments.  In particular, we
expressly vow that we have followed the Facebook rule in discussing
with others in doing the assignment and did not take notes (digital or
printed) from the discussions.  

[ ] I/We, A0000000X, did not follow the class rules regarding homework
assignment, because of the following reason:

<Please fill in>

We suggest that we should be graded as follows:

<Please fill in>

== References ==

None
