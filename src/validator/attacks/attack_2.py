import argparse
import os
import sys
import h5py
import numpy as np
from itertools import combinations
from ..parameters import *
from ..helpers import *
from functools import partial

sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)


def _literals_sets(ciphertext_file, clauses_file):

    if "ciphertext" in ciphertext_file:

        #########
        # 1
        #########

        c = [set(x) for x in ciphertext_file["ciphertext"][:]]
        s = [set().union(*subset) for subset in combinations(c, 2)]

        #########
        # 2
        #########

        def contained(monomial, literal):
            return literal in monomial

        r = np.arange(2, N + 2)
        shared = dict(
            zip(
                r,
                [set().union(*filter(partial(contained, literal=l), c)) for l in r],
            )
        )

        # s2 = [[subset.union(shared.get(v, set())) for v in subset] for subset in s]
        print(len(s))
        s2 = [[subset.union(shared.get(v, set())) for v in subset] for subset in s]
        for subset in s2:
            print(subset, "\n")

        # For each variable in s,
        # for each clause from the public key that shares a variable with s,
        # union the variables in that clause with s.

        # s2 = [
        #     set(np.concatenate(x))  # .union()
        #     # a         ->
        #     # b         ->
        #     # c         ->
        #     for x in combinations(s, 2)
        # ]


def _recover_plaintext(ciphertext_file, clauses_file):

    clauses = _literals_sets(ciphertext_file, clauses_file)

    # rows = len(a_terms.keys())
    # cols = coefficient_count

    # a = np.zeros((rows, cols), dtype=np.int64)
    # b = np.zeros(rows, dtype=np.int64)

    # for i, term in enumerate(a_terms):

    #     a[i] = clause_vector(a_terms[term], cols)
    #     b[i] = int(term in ciphertext)
    #     if sum(a[i]) == 0 and b[i] == 1:
    #         return -4

    # GF = galois.GF(2)
    # a = GF(a)
    # b = GF(b)

    # rank_a = np.linalg.matrix_rank(a)
    # augmented_matrix = np.hstack((a, b.reshape(-1, 1)))
    # rank_augmented = np.linalg.matrix_rank(augmented_matrix)
    # y = int(rank_a != rank_augmented)

    # return y


def attack(args):

    CIPHERTEXT_DIRPATH = f"tests/c_{args.i}"
    CIPHERTEXT_FILEPATH = f"{CIPHERTEXT_DIRPATH}/ciphertext_{args.i}.hdf5"
    CLAUSES_FILEPATH = f"{CIPHERTEXT_DIRPATH}/clauses_{args.i}.txt"

    with h5py.File(CIPHERTEXT_FILEPATH, "r") as CIPHERTEXT_FILE:
        with open(CLAUSES_FILEPATH, "r") as CLAUSES_FILE:
            y = _recover_plaintext(CIPHERTEXT_FILE, CLAUSES_FILE)
            return y


def main():
    parser = argparse.ArgumentParser(prog="Attack")
    parser.add_argument("i", type=int)
    args = parser.parse_args()
    y = attack(args)
    print(y)


if __name__ == "__main__":
    main()
