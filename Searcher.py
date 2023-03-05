from InputOutput import read_posting_list, add_skips_to_posting


def process_query(query, dictionary, all_doc_ids, postings_file):
    """
    Generates an in-memory index, containing only terms found in the query.
    Converts the query into a nested operator form (see below).
    Then, uses the generated index to resolve the query starting from the outermost operator.
    """
    index = dict()
    with open(postings_file, "r") as pf:
        for op in query:
            if isinstance(op, tuple):
                term, _ = op
                if term in dictionary:
                    index[term] = read_posting_list(pf, dictionary[term])
                else:
                    index[term] = []

    wrapped = wrap_query(query)

    # if it is an operator, call resolve on the outermost operator
    # to recursively resolve all inner operators
    if isinstance(wrapped, Operator):
        return wrapped.resolve(index, all_doc_ids)

    # otherwise, it will be a (term, doc freq) tuple
    # just return the posting list
    else:
        term, _ = wrapped
        return index[term]


def wrap_query(query):
    """
    Converts query from postfix form to nested Operator form.
    e.g., [a, b, c, d, 1, 1, 0] -> OR(a, AND(b, c, d))
    """
    stack = []
    for op in query:
        if isinstance(op, tuple):
            stack.append(op)
        else:
            if op == 2:
                newOperator = Not()
                newOperator.add(stack.pop())
                stack.append(newOperator)
            elif op == 1:
                newOperator = And()
                newOperator.add(stack.pop())
                newOperator.add(stack.pop())
                stack.append(newOperator)
            elif op == 0:
                newOperator = Or()
                newOperator.add(stack.pop())
                newOperator.add(stack.pop())
                stack.append(newOperator)
    # the size of the stack at the end should be 1; otherwise, our postfix conversion failed
    assert (
        len(stack) == 1
    ), f"Nested Operator conversion failed! Stack size is {len(stack)}"
    return stack[0]


class Operator:
    """
    Parent class for all operators.
    Operands are stored in tuples to avoid this weird memory glitch where lists get duplicated.
    As such, list methods like 'append' are replaced with tuple equivalents.
    """

    def __init__(self):
        self.operands = tuple()
        self.type = None

    def add(self, operand, debug=""):
        # if new operand is an operator of the same type (e.g. OR and OR),
        # just add the operator's operands into this operator's operands
        if isinstance(operand, Operator):
            if self.type == operand.type:
                self.operands = (*self.operands, *operand.operands)
            else:
                self.operands = (*self.operands, operand)
        else:
            self.operands = (*self.operands, operand)

    def __repr__(self):
        operator = {0: "OR", 1: "AND", 2: "NOT"}[self.type]
        if self.type == 2:
            return f"{operator}({self.operands})"
        else:
            return f"{operator}({','.join(map(str, self.operands))})"


class Or(Operator):
    def __init__(self):
        super().__init__()
        self.type = 0

    def resolve(self, index, all_doc_ids):
        """
        Resolves the operands stored in the current operator using the given index.
        Returns a posting list.
        """
        # first, recursively resolve all unresolved operands in the operand list
        # self.operands should only contain (term, doc freq) tuples
        self.operands = [
            (
                operand.resolve(index, all_doc_ids)
                if isinstance(operand, Operator)
                else operand
            )
            for operand in self.operands
        ]
        # at this point, self.operands only contains either term-freq tuples or posting lists

        posting_lists = []
        for op in self.operands:
            # if op is a (term, doc freq) tuple, convert it to a posting list
            if isinstance(op, tuple):
                term, _ = op
                posting_lists.append(index[term])
            # otherwise, it is a posting list and we append it directly
            else:
                posting_lists.append(op)
        # at this point, self.operands only contains posting lists

        final_list = posting_lists[0]
        for next_list in posting_lists[1:]:
            final_list = self.union(final_list, next_list)

        return final_list

    def union(self, list1, list2):
        """
        Custom union algorithm NOT using skip pointers.
        """
        get_terms = lambda x: x[0] if isinstance(x, tuple) else x

        ptr1 = ptr2 = 0
        output = []
        while ptr1 < len(list1) and ptr2 < len(list2):
            val1, val2 = get_terms(list1[ptr1]), get_terms(list2[ptr2])
            if val1 == val2:
                output.append(val1)
                ptr1 += 1
                ptr2 += 1
            elif val1 > val2:
                output.append(val2)
                ptr2 += 1
            else:
                output.append(val1)
                ptr1 += 1

        # after the above while loop, one list will be exhausted
        # therefore, only one of the following while loops will run
        # to add the remaining items from the non-exhausted list
        while ptr1 < len(list1):
            output.append(get_terms(list1[ptr1]))
            ptr1 += 1
        while ptr2 < len(list2):
            output.append(get_terms(list2[ptr2]))
            ptr2 += 1

        output = add_skips_to_posting(output)
        return output


class And(Operator):
    def __init__(self):
        super().__init__()
        self.type = 1

    def resolve(self, index, all_doc_ids):
        """
        Resolves the operands stored in the current operator using the given index.
        Returns a posting list.
        """
        # first, recursively resolve all unresolved operands in the operand list
        # self.operands should only contain (term, doc freq) tuples
        self.operands = [
            (
                operand.resolve(index, all_doc_ids)
                if isinstance(operand, Operator)
                else operand
            )
            for operand in self.operands
        ]

        # at this point, self.operands only contains either term-freq tuples or posting lists

        # ONLY FOR AND OPERATOR: sort by ascending doc freq order
        self.operands.sort(key=lambda x: x[1] if isinstance(x, tuple) else len(x))

        posting_lists = []
        for op in self.operands:
            # if op is a (term, doc freq) tuple, convert it to a posting list
            if isinstance(op, tuple):
                term, _ = op
                posting_lists.append(index[term])
            # otherwise, it is a posting list and we append it directly
            else:
                posting_lists.append(op)
        # at this point, self.operands only contains posting lists

        # if there is only one posting list, return it
        if len(posting_lists) == 1:
            return posting_lists[0]

        final_list = posting_lists[0]
        for next_list in posting_lists[1:]:
            final_list = self.intersect(final_list, next_list)
        return final_list

    def intersect(self, list1, list2):
        """
        Custom intersect algorithm using skip pointers.
        Skip pointers tell the algorithm how many indices to jump ahead by.
        Otherwise, pretty standard merging algorithm.
        """
        get_terms = lambda x: x[0] if isinstance(x, tuple) else x
        get_skips = lambda x: x[1] if isinstance(x, tuple) else None

        ptr1 = ptr2 = 0
        output = []
        while ptr1 < len(list1) and ptr2 < len(list2):
            val1, val2 = get_terms(list1[ptr1]), get_terms(list2[ptr2])
            skp1, skp2 = get_skips(list1[ptr1]), get_skips(list2[ptr2])
            if val1 == val2:
                output.append(val1)
                ptr1 += 1
                ptr2 += 1
            elif val1 > val2:
                if skp2 and get_terms(list2[ptr2 + skp2]) <= val1:
                    ptr2 += skp2
                else:
                    ptr2 += 1
            else:
                if skp1 and get_terms(list1[ptr1 + skp1]) <= val2:
                    ptr1 += skp1
                else:
                    ptr1 += 1

        output = add_skips_to_posting(output)
        return output


class Not(Operator):
    def __init__(self):
        super().__init__()
        self.type = 2

    def resolve(self, index, all_doc_ids):
        """
        Resolves the operands stored in the current operator using the given index.
        Returns a posting list.
        """

        # ONLY FOR NOT OPERATOR: self.operands should only contain a single operand
        assert len(self.operands) == 1, "NOT operator has the wrong number of operands!"

        # first, recursively resolve all unresolved operands in the operand list
        # self.operands should only contain (term, doc freq) tuples
        if isinstance(self.operands[0], Operator):
            self.operands[0] = self.operands[0].resolve(index, all_doc_ids)

        posting_list = index[self.operands[0][0]]

        return self.invert(posting_list, all_doc_ids)

    def invert(self, list1, full_list):
        """
        This method should only take in a single posting list, assuming our queries are properly formed.
        all_doc_ids should already be a set, so we just do set difference.
        Return list after adding skip pointers.
        """
        total_set = set(posting_list)
        output = list(all_doc_ids - total_set)
        return add_skips_to_posting(output)
