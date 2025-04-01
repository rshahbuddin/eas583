import eth_account
import random
import string
import json
from pathlib import Path
from web3 import Web3
from web3.middleware import ExtraDataToPOAMiddleware  # Necessary for POA chains
from eth_account.messages import encode_defunct

def merkle_assignment():
    num_of_primes = 8192
    primes = generate_primes(num_of_primes)
    leaves = convert_leaves(primes)
    tree = build_merkle(leaves)

    while True:
        random_leaf_index = random.randint(0, num_of_primes - 1)  # (0 is already claimed)
        proof = prove_merkle(tree, random_leaf_index)
        if proof:
            break

    challenge = ''.join(random.choice(string.ascii_letters) for i in range(32))

    addr, sig = sign_challenge(challenge)

    if sign_challenge_verify(challenge, addr, sig):
        tx_hash = send_signed_msg(proof, leaves[random_leaf_index])
        print(f"Transaction submitted: {tx_hash}")


def generate_primes(num_primes):
    primes_list = []
    num = 2  # Start from 2 (first prime)
    while len(primes_list) < num_primes:
        is_prime = all(num % p != 0 for p in primes_list if p * p <= num)
        if is_prime:
            primes_list.append(num)
        num += 1
    return primes_list


def convert_leaves(primes_list):
    return [p.to_bytes(32, 'big') for p in primes_list]


def build_merkle(leaves):
    tree = [leaves]
    while len(tree[-1]) > 1:
        parent_layer = []
        for i in range(0, len(tree[-1]), 2):
            if i + 1 < len(tree[-1]):
                parent_layer.append(hash_pair(tree[-1][i], tree[-1][i + 1]))
            else:
                parent_layer.append(tree[-1][i])  # Carry last node up if odd count
        tree.append(parent_layer)
    return tree


def prove_merkle(merkle_tree, random_indx):
    merkle_proof = []
    index = random_indx
    for layer in merkle_tree[:-1]:
        sibling_index = index ^ 1  # Find sibling index
        if sibling_index < len(layer):
            merkle_proof.append(layer[sibling_index])
        index //= 2
    return merkle_proof


def sign_challenge(challenge):
    acct = get_account()
    message = encode_defunct(text=challenge)
    eth_sig_obj = eth_account.Account.sign_message(message, acct.key)
    return acct.address, eth_sig_obj.signature.hex()


def send_signed_msg(proof, random_leaf):
    chain = 'bsc'
    acct = get_account()
    address, abi = get_contract_info(chain)
    w3 = connect_to(chain)
    contract = w3.eth.contract(address=address, abi=abi)

    tx = contract.functions.claimPrime(random_leaf, proof).build_transaction({
        'from': acct.address,
        'nonce': w3.eth.get_transaction_count(acct.address),
        'gas': 250000,
        'gasPrice': int(w3.eth.gas_price * 1.2)
    })

    signed_tx = w3.eth.account.sign_transaction(tx, acct.key)
    return w3.eth.send_raw_transaction(signed_tx.rawTransaction).hex()


# Helper functions that do not need to be modified
def connect_to(chain):
    """
        Takes a chain ('avax' or 'bsc') and returns a web3 instance
        connected to that chain.
    """
    if chain not in ['avax','bsc']:
        print(f"{chain} is not a valid option for 'connect_to()'")
        return None
    if chain == 'avax':
        api_url = f"https://api.avax-test.network/ext/bc/C/rpc"  # AVAX C-chain testnet
    else:
        api_url = f"https://data-seed-prebsc-1-s1.binance.org:8545/"  # BSC testnet
    w3 = Web3(Web3.HTTPProvider(api_url))
    # inject the poa compatibility middleware to the innermost layer
    w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)

    return w3


def get_account():
    """
        Returns an account object recovered from the secret key
        in "sk.txt"
    """
    cur_dir = Path(__file__).parent.absolute()
    with open(cur_dir.joinpath('sk.txt'), 'r') as f:
        sk = f.readline().rstrip()
    if sk[0:2] == "0x":
        sk = sk[2:]
    return eth_account.Account.from_key(sk)


def get_contract_info(chain):
    """
        Returns a contract address and contract abi from "contract_info.json"
        for the given chain
    """
    contract_file = Path(__file__).parent.absolute() / "contract_info.json"
    if not contract_file.is_file():
        contract_file = Path(__file__).parent.parent.parent / "tests" / "contract_info.json"
    with open(contract_file, "r") as f:
        d = json.load(f)
        d = d[chain]
    return d['address'], d['abi']


def sign_challenge_verify(challenge, addr, sig):
    """
        Helper to verify signatures, verifies sign_challenge(challenge)
        the same way the grader will. No changes are needed for this method
    """
    eth_encoded_msg = eth_account.messages.encode_defunct(text=challenge)

    if eth_account.Account.recover_message(eth_encoded_msg, signature=sig) == addr:
        print(f"Success: signed the challenge {challenge} using address {addr}!")
        return True
    else:
        print(f"Failure: The signature does not verify!")
        print(f"signature = {sig}\naddress = {addr}\nchallenge = {challenge}")
        return False


def hash_pair(a, b):
    """
        The OpenZeppelin Merkle Tree Validator we use sorts the leaves
        https://github.com/OpenZeppelin/openzeppelin-contracts/blob/master/contracts/utils/cryptography/MerkleProof.sol#L217
        So you must sort the leaves as well

        Also, hash functions like keccak are very sensitive to input encoding, so the solidity_keccak function is the function to use

        Another potential gotcha, if you have a prime number (as an int) bytes(prime) will *not* give you the byte representation of the integer prime
        Instead, you must call int.to_bytes(prime,'big').
    """
    if int.from_bytes(a, 'big') < int.from_bytes(b, 'big'):
        return Web3.solidity_keccak(['bytes32', 'bytes32'], [a, b])
    else:
        return Web3.solidity_keccak(['bytes32', 'bytes32'], [b, a])


if __name__ == "__main__":
    merkle_assignment()
