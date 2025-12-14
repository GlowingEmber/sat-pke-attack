import numpy as np

from itertools import chain as flatten, combinations as subset, product as cartesian

CONSTANT_MONOMIAL = tuple() # empty tuple

def distribute(iterable):  # from itertools powerset recipe
    return flatten.from_iterable(subset(iterable, r) for r in range(len(iterable) + 1))

def product_simplify(clause, random):
    clause = np.fromiter(clause, dtype=tuple)
    random = np.fromiter(random, dtype=tuple)
    x_array, y_array = np.meshgrid(clause, random)
    product = np.fromiter(zip(x_array.ravel(), y_array.ravel()), dtype=tuple)
    product = [set(flatten(*t)) for t in product]
    return product

def cnf_to_neg_anf(term):
    # print(term)
    term = term + [(1,)]
    term = cartesian(*term)
    term = filter(lambda t: 0 not in t, term)  # a*0 = 0
    term = map(lambda t: tuple(filter(lambda t: t != 1, t)), term)  # a*1 = a
    term = map(lambda t: tuple(set(t)), term)  # a*a = a
    return term