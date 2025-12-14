from ..parameters import *
import subprocess
import os
import argparse
import random
from tqdm import tqdm

my_env = os.environ.copy()


def run_zsh(cmd, capture=False):
    return subprocess.run(
        cmd,
        env=my_env,
        shell=True,
        text=True,
        executable="/bin/zsh",
        capture_output=capture,
    )


def simulate(n, g, e):
    os.makedirs(my_env["DATA_DIRECTORY"], exist_ok=True)
    if GENERATE_CLEARS_DATA:
        if (
            os.path.isdir(my_env["DATA_DIRECTORY"])
            and len(os.listdir(my_env["DATA_DIRECTORY"])) > 0
        ):
            run_zsh("rm -rf $DATA_DIRECTORY/*")
            print(f"tests directory cleared")

    ciphers = []
    t = 0

    attack_results_counts = {"successes": 0, "failures": 0, "errors": 0}
    progress_bar = tqdm(
        range(n),
        unit="ciphertext",
        postfix=attack_results_counts,
        bar_format="{l_bar}{bar}|[{n_fmt}/{total_fmt}{postfix}]"
    )
    for _ in progress_bar:

        plaintext = PLAINTEXT
        if PLAINTEXT == "r":
            plaintext = random.getrandbits(1)

        #####

        next_n = 0
        next_dir = f"{my_env["DATA_DIRECTORY"]}/cipher_{next_n}_dir"
        while os.path.isdir(next_dir):
            next_n += 1
            next_dir = f"{my_env["DATA_DIRECTORY"]}/cipher_{next_n}_dir"
        os.mkdir(next_dir)

        #####

        cmd = f'time python3 -m validator.primitives.encrypt -n "{next_n}" -y "{plaintext}"'
        res = run_zsh(cmd, capture=True)

        ciphers.append(str(next_n))
        t += float(res.stderr[:-2])

        ### plaintext_n__txt
        path = f"{next_dir}/plaintext_{next_n}.txt"
        with open(path, "w") as file:
            file.write(str(plaintext))

        ### ciphertext_n__txt
        if INCLUDE_CIPHERTEXT_N__TXT:
            path = f"{next_dir}/ciphertext_{next_n}.txt"
            with open(path, "w") as file:
                cmd = f"h5dump --width=1 '{next_dir}/ciphertext_{next_n}.hdf5'"
                cipher = run_zsh(cmd, capture=True)
                file.write(cipher.stdout)

        if e:
            cmd = f"python3 -m validator.primitives.decrypt {next_n}"
            decryption = int(run_zsh(cmd, capture=True).stdout[:-1])

            cmd = f"python3 -m validator.attacks.attack {next_n}"
            attack = int(run_zsh(cmd, capture=True).stdout[:-1])

            code = attack
            if code >= 0:
                code = int(code == decryption)
            if code < 0:
                code = -1
            

            RESULT_STRINGS_PLURAL = {
                1: "successes",
                0: "failures",
                -1: "errors"
            }
            RESULT_STRINGS_SINGULAR = {
                1: "SUCCESS",
                0: "FAILURE",
                -1: "ERROR"
            }

            attack_results_counts[RESULT_STRINGS_PLURAL.get(code)] += 1
            s = f"ciphertext {next_n}: {RESULT_STRINGS_SINGULAR[code]:<10} y={decryption} \u2227 attack(pub,c)={attack}"
            progress_bar.write(s)
            progress_bar.set_postfix(attack_results_counts, refresh=True)


def main(g=False, e=False):
    parser = argparse.ArgumentParser(prog="Generate")
    parser.add_argument("n", type=int)
    args = parser.parse_args()
    simulate(args.n, g, e)


if __name__ == "__main__":
    main()


def generate():
    main(g=True)


def evaluate():
    main(e=True)
