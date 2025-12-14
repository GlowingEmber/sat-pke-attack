import h5py
import numpy as np
import argparse


def g(args):

    PRIVATE_KEY_FILEPATH = f"tests/cipher_{args.n}_dir/private_key_{args.n}.txt"
    CIPHERTEXT_FILEPATH = f"tests/cipher_{args.n}_dir/ciphertext_{args.n}.hdf5"


    with open(PRIVATE_KEY_FILEPATH, "r") as file:
        priv = file.read()
        with h5py.File(CIPHERTEXT_FILEPATH, "r") as file:
            if "expression" in file:

                def assign(x):
                    x = int(x)
                    return int(priv[x - 2])

                v__assign = np.vectorize(assign)
                v__assign_conditional = lambda term: (
                    v__assign(term) if len(term) > 0 else []
                )

                expression = file["expression"]
                expression = np.array(expression[:])
                expression = [all(v__assign_conditional(term)) for term in expression]
                expression = filter(lambda term: term, expression)
                expression = list(expression)

                size = sum(1 for _ in expression)
                g_res = size % 2
                return g_res


def main():
    parser = argparse.ArgumentParser(prog="Decrypt")

    parser.add_argument("n", type=int)
    args = parser.parse_args()

    g_decryption = g(args)
    print(g_decryption)


if __name__ == "__main__":
    main()
