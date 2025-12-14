import argparse
import os
import sys
import ast
from collections import defaultdict
from itertools import chain as flatten, product as cartesian

import galois
import h5py
import numpy as np

from ..parameters import *
from ..helpers import *

sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)


class Coefficient:
    def __init__(self, v):
        self.value = v

    def __repr__(self):
        return f"Coefficient(v={self.value})"

    def __eq__(self, other):
        if not isinstance(other, Coefficient):
            raise NotImplementedError
        return self.value == other.value


def _recover_beta_literals(ciphertext_n__hdf5_file):
    if "expression" in ciphertext_n__hdf5_file:

        ciphertext = ciphertext_n__hdf5_file["expression"]
        ciphertext = np.array(ciphertext[:])
        ciphertext = map(tuple, ciphertext)

        lengths = map(len, ciphertext)

        ciphertext = zip(ciphertext, lengths)
        ciphertext, _ = zip(*filter(lambda x: x[1] > TERM_LENGTH_CUTOFF, ciphertext))
        ciphertext = set(ciphertext)

        groups = []

        while len(groups) < BETA and len(ciphertext) > 0:

            largest = max(ciphertext, key=len)
            group = set(largest)
            ciphertext.remove(largest)

            while True:

                if len(ciphertext) == 0:
                    groups.append(group)
                    group = set()
                    break

                closeness = np.fromiter(
                    map(lambda x: (x, len(group.difference(x))), ciphertext),
                    dtype=object,
                )

                closest = min(closeness, key=lambda x: x[1])

                MAX_DIFF_PCT = 0.5
                max_diff = math.floor(MAX_DIFF_PCT * len(group))

                if closest[1] <= max_diff:
                    group = group.union(closest[0])
                    ciphertext.remove(closest[0])
                else:
                    groups.append(group)
                    group = set()
                    break

        beta_literals_sets = []
        for s in groups:
            beta_literals_sets.append(sorted([int(l) for l in s]))
        return sorted(beta_literals_sets)


def _recover_plaintext(
    args,
    ciphertext_n__hdf5_file,
    clauses_n__txt_file,
    beta_literals_sets_n__txt_file,
):

    real_beta_literals_sets = ast.literal_eval(beta_literals_sets_n__txt_file.read())
    recovered_beta_literals_sets = _recover_beta_literals(ciphertext_n__hdf5_file)
    if real_beta_literals_sets != recovered_beta_literals_sets:
        return -1

    clauses = clauses_n__txt_file.read()
    all_clauses = ast.literal_eval(clauses)
    a_terms = defaultdict(list)

    coefficient_count = 0

    for beta_literals_set in recovered_beta_literals_sets:

        possible_clauses = np.fromiter(
            filter(
                lambda c: all(map(lambda l: l in beta_literals_set, list(zip(*c))[0])),
                all_clauses,
            ),
            dtype=list,
        )

        if len(possible_clauses) < ALPHA:
            return -2

        C = [cnf_to_neg_anf(c) for c in possible_clauses]
        for i, C_i in enumerate(C):

            C_i = list(C_i)
            C_i = np.fromiter(C_i, dtype=object)
            C_minus_C_i = list(possible_clauses[:i]) + list(possible_clauses[i + 1 :])
            R_i_literals_set = list(set([l[0] for l in flatten(*C_minus_C_i)]))
            R_terms = np.fromiter(distribute(R_i_literals_set), dtype=object)
            n = len(R_terms)
            coefficient_count += n

            R_i_terms = R_terms
            R_i_coefficients = np.fromiter(
                map(
                    lambda i: Coefficient(i),
                    range(coefficient_count - n, coefficient_count),
                ),
                dtype=object,
            )
            R_i = np.fromiter(zip(R_i_coefficients, R_i_terms), dtype=object)

            #####
            unformatted_C_iR_i = np.fromiter(cartesian(R_i, C_i), dtype=object)
            
            C_iR_i = []

            for term in unformatted_C_iR_i:

                coefficient = term[0][0]
                literals = tuple(sorted([int(x) for x in set(term[0][1] + term[1])]))
                full_term = (coefficient, literals)
                C_iR_i.append(full_term)

            for term in C_iR_i:

                coefficient = term[0]
                literals = term[1]
                a_terms[literals] = a_terms[literals] + [coefficient]
            
    def clause_vector(coefficients, cols):
        v = np.zeros(cols)
        for c in coefficients:
            v[c.value] = 1
        return v

    ciphertext = ciphertext_n__hdf5_file["expression"][:]
    ciphertext = set(map(lambda x: tuple([int(l) for l in x]), ciphertext))


    # if y=0 and const_term = 0: real ciphertext contains NOT contain ()
    # if y=0 and const_term = 1: real ciphertext contains contain ()
    # if y=1 and const_term = 0: real ciphertext contains contain ()
    # if y=1 and const_term = 1: real ciphertext contains NOT contain ()

    missing_terms = ciphertext - set(a_terms.keys())
    if len(missing_terms) > 0:
        if missing_terms == {tuple()}:
            return 1
        else:
            return -3

    rows = len(a_terms.keys())
    cols = coefficient_count

    a = np.zeros((rows, cols), dtype=np.int64)
    b = np.zeros(rows, dtype=np.int64)

    for i, term in enumerate(a_terms):
        
        a[i] = clause_vector(a_terms[term], cols)
        b[i] = int(term in ciphertext)
        if sum(a[i]) == 0 and b[i] == 1:
            return -4

    GF = galois.GF(2)
    a = GF(a)
    b = GF(b)

    rank_a = np.linalg.matrix_rank(a)
    augmented_matrix = np.hstack((a, b.reshape(-1, 1)))
    rank_augmented = np.linalg.matrix_rank(augmented_matrix)
    y = int(rank_a != rank_augmented)
    
    print(rank_a, file=sys.stderr)
    print(a.shape, file=sys.stderr)
    print(rank_augmented, file=sys.stderr)

    # print(f"codebreaking for cipher {args.n}:")
    # print(f"A:\n{a}\nb:\n{b}")
    # lhs = f"rank([A])={rank_a} \u2227 rank([A|b])={rank_augmented}"
    # rhs = f"y={y}"
    # print(f"{lhs}       =>      {rhs}")
    return y


def attack(args):

    CIPHERTEXT_DIRPATH = f"tests/cipher_{args.n}_dir"
    CIPHERTEXT_FILEPATH = f"{CIPHERTEXT_DIRPATH}/ciphertext_{args.n}.hdf5"
    CLAUSES_FILEPATH = f"{CIPHERTEXT_DIRPATH}/clauses_{args.n}.txt"
    BETA_LITERALS_SETS_FILEPATH = f"{CIPHERTEXT_DIRPATH}/beta_literals_sets_{args.n}.txt"

    with h5py.File(CIPHERTEXT_FILEPATH, "r") as CIPHERTEXT_FILE:
        with open(CLAUSES_FILEPATH, "r") as CLAUSES_FILE:
            with open(BETA_LITERALS_SETS_FILEPATH, "r") as BETA_LITERALS_SETS_FILE:
                y = _recover_plaintext(
                    args,
                    CIPHERTEXT_FILE,
                    CLAUSES_FILE,
                    BETA_LITERALS_SETS_FILE
                )
                return y


###


def main():
    parser = argparse.ArgumentParser(prog="Attack")

    parser.add_argument("n", type=int)
    args = parser.parse_args()

    y = attack(args)
    print(y)


if __name__ == "__main__":
    main()
