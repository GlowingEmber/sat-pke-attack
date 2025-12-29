## Getting Started

Mac
```
cd path/to/folder
direnv allow
python3 -m venv venv
source venv/bin/activate
pip install -e .
```

## Usage

- To change encryption or attack parameters, modify `src/validator/parameters.py`

- To create and test against `n` ciphertexts, run
```
evaluate n
```
these ciphertexts can then be found in `tests/`. 

You may also test against any previously-created ciphertext `i` using
```
attack i
```
