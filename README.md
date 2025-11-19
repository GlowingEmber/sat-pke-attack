## Getting Started

- Mac
```zsh
cd path/to/folder
direnv allow
python3 -m venv venv
source venv/bin/activate
pip install .
pip install '.[colors]' # optional (visual-only)
```

## Usage

- To modify parameters, edit `src/validator/parameters.py`

#### Encryption
To generate `n` ciphertexts, run
```zsh
generate n
```
You can view each of these in `tests`; for example, `ciphertext 3` would be at `tests/cipher_3_dir`

#### Decryption
To decrypt ciphertext `x`, run
```zsh
decrypt x
```

#### Attacks
(Recommended) To generate and automatically test attacks against `n` ciphertexts, run
```
evaluate n
```
Or to run an attack against a specific ciphertext `x`, run 
```
attack x
```
