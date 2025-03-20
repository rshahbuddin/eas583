#!/usr/bin/env python3
<<<<<<< HEAD
import random
import json
from hashlib import md5
from pathlib import Path


def validate(code_path):
    try:
        from reading_the_chain import is_ordered_block, connect_to_eth, connect_with_middleware, get_contract_values
    except Exception as e:
        print("Could not load methods from reading_the_chain.py")
        print(e)
        return 0

    # Setup tests block and contract info
    test_file = Path(__file__).parent.absolute()
    test_file = test_file / "block_data.json"
    if not test_file.is_file():  # if runtests_local
        test_file = Path(__file__).parent.absolute()
        test_file = test_file / '.guides' / 'tests' / 'block_data.json'
    try:
        with open(test_file, 'r') as json_file:
        # with open('block_data.json') as json_file:
            block_data = json.load(json_file)
    except Exception as e:
        print("Failed to load block_data -- please contact your instructor")
        return 0

    num_tests = 8  # Updated for each block checked in is_ordered.is_ordered_block()
    num_passed = 0
    contract_file = Path(__file__).parent.absolute()
    contract_file = contract_file / 'testing_contract_info.json'
    if not contract_file.is_file():  # if runtests_local
        contract_file = Path(__file__).parent.absolute()
        contract_file = contract_file / 'contract_info.json'

    blocks = random.sample(block_data, 4)

    # Test 1: Connect to correct chain
    print("Connecting to eth")
    try:
        eth_w3 = connect_to_eth()
        if eth_w3.eth.chain_id == 1:
            print("\tSuccessfully connected to the Ethereum chain")
            num_passed += 1
        else:
            print("\tDid not connect to the Ethereum chain")
    except Exception as e:
        print(f"Error: connect_to_eth failed\n{e}")

    # Test 2: Check for correctly identified ordered/unordered blocks
    print("\nChecking for correctly identified blocks")
    for block in blocks:
        num_tests += 1
        try:
            ordered = is_ordered_block(eth_w3, block['block_num'])
        except Exception as e:
            print("Error: is_ordered_block failed")
            print(e)
            continue
        if ordered == block['ordered']:
            if ordered:
                print(f"\tCorrectly identified block {block['block_num']} as ordered")
            else:
                print(f"\tCorrectly identified block {block['block_num']} as unordered")
            num_passed += 1
        else:
            if ordered:
                print(f"\t*Incorrectly* identified block {block['block_num']} as ordered")
            else:
                print(f"\t*Incorrectly* identified block {block['block_num']} as unordered")

    # Test 3: Connect to correct chain
    try:
        print("\nConnecting to the BNB testnet chain and the contract")
        cont_w3, contract = connect_with_middleware(contract_file)
        if cont_w3.eth.chain_id == 97:
            print("\tSuccessfully connected to the BNB testnet chain")
            num_passed += 1
        else:
            print("\tDid not connect to the BNB testnet chain")
    except Exception as e:
        print(f"Error: connect_with_middleware failed\n{e}")
        return int(100 * float(num_passed) / num_tests)

    # BNB Merkel contract values
    admin_address = "0xAC55e7d73A792fE1A9e051BDF4A010c33962809A"
    owner_address = "0x793A37a85964D96ACD6368777c7C7050F05b11dE"
    onchain = "3bd2af849ba5159ad82b8b074e14a45f"  # md5 hash hexdigest of onchain root
    mid_added = False

    try:
        onchain_root, has_role, prime = get_contract_values(contract, admin_address, owner_address)
        # Test 4: Check that the correct Merkle root was returned
        if onchain == md5(onchain_root).hexdigest():
            print("\tSuccessfully retrieved the Merkle root")
            num_passed += 1
        else:
            print("\tDid not retrieve the Merkle root")
        # Test 5: Check that middleware was added to the contract object
        mw_found = False
        try:
            for middleware in cont_w3.middleware_onion.middleware:
                m_ware, title = middleware
                if "<class 'web3.middleware.formatting.FormattingMiddlewareBuilder'>" in title:
                    print("\tSuccessfully injected middleware into the web3 object")
                    mid_added = True
        except Exception as e:
            print(f"\t{e}\nFailed to retrieve middleware layers on your contract object")

        if not mid_added:
            print("\t\tYou have not injected middleware or you have injected\n"
                  "\t\tthe incorrect type of middleware into the web3 object.\n"
                  "\t\tCheck the assignment guide")
        else:
            print("\tSuccessfully injected Middleware")
            num_passed += 1
        # Test 6: Check that admin address was validated as a contract admin
        if has_role:
            print("\tSuccessfully verified default admin")
            num_passed += 1
        else:
            print("\tDid not verify default admin address")
        # Test 7: Check for the correct prime ownership
        if prime == 65063:
            print("\tSuccessfully retrieved the correct prime for this owner")
            num_passed += 1
        else:
            print("\tDid not retrieve the correct prime")

        onchain_root, has_role, prime = get_contract_values(contract, owner_address, admin_address)
        # Test 8: Check that owner address was not validated as a contract admin
        if not has_role:
            print("\tSuccessfully rejected the incorrect default admin")
            num_passed += 1
        else:
            print("\tIncorrectly verified a non-default admin address")
        # Test 9: Check for the correct prime ownership (different address)
        if prime == 4099:
            print("\tSuccessfully returned the correct result for this owner")
            num_passed += 1
        else:
            print(prime)
            print("\tDid not return the correct result for this owner")
    except Exception as e:
        print(f"Error: there was a problem interacting with your contract object\n{e}")
=======
import hashlib
from pathlib import Path


class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def validate(code_path):
    try:
        import connect_to_eth
    except ImportError as e:
        print(f"Could not import homework file 'connect_to_eth.py'\n\n{e}")
        return 0

    required_methods = ["connect_to_eth", "connect_with_middleware"]
    for m in required_methods:
        if m not in dir(connect_to_eth):
            print("%s not defined" % m)
            return 0

    num_tests = 6
    num_passed = 0

    # Tests to verify connecting to ethereum node
    try:
        w3 = connect_to_eth.connect_to_eth()
    except Exception as e:

        print("Unable to connect to Ethereum node")
        print(e)
        return 0

    try:
        if w3.is_connected() and 1 == w3.eth.chain_id:
            print("You connected to an Ethereum Main net node")
            num_passed += 1
        else:
            print("w3 instance is not connected")
    except Exception as e:
        print(e)
        return 0

    try:
        block = w3.eth.get_block('latest')
    except Exception as e:
        block = None
        print(e)

    try:
        if block.number > 10 ** 7:
            print(f"\tSuccessfully retrieved block {block.number}")
            num_passed += 1
        else:
            print("\tFailed to get a block")
    except Exception as e:
        print(e)

    # Tests to verify connecting to BSC testnet
    json_file = Path(__file__).parent.absolute()
    json_file = json_file / 'test_contract_info.json'
    try:
        w3, contract = connect_to_eth.connect_with_middleware(json_file)
    # LOCAL CODE VERSION
    # try:
    #     w3, contract = connect_to_eth.connect_with_middleware("test_contract_info.json")
    except Exception as e:
        print("Unable to connect to BSC node")
        print(e)
        return 0

    try:
        if w3.is_connected() and 97 == w3.eth.chain_id:
            print("You connected to a BSC testnet node")
            num_passed += 1
        else:
            print("\tw3 instance is not connected")
    except Exception as e:
        print(e)
        return 0

    try:
        block = w3.eth.get_block('latest')
        if block.number > 10 ** 7:
            print(f"\tSuccessfully retrieved block {block.number}")
            num_passed += 1
        else:
            print(f"\tFailed to get a block")
    except Exception as e:
        print(f"\tThere was an error communicating with the chain\n\t\t{e}")

    # Middleware and contract connection checks
    hroot = '3bd2af849ba5159ad82b8b074e14a45f'
    try:
        if hroot == hashlib.md5(contract.functions.merkleRoot().call()).hexdigest():
            print("\tSuccessfully connected to contract")
            num_passed += 1
        else:
            print("\tFailed to interact with contract, check your contract() call")
    except Exception as e:
        print(e)

    mw_found = False
    try:
        for middleware in w3.middleware_onion.middleware:  # TEST 4
            m_ware, title = middleware
            if "<class 'web3.middleware.formatting.FormattingMiddlewareBuilder'>" in title:
                print("\tSuccessfully injected middleware into the web3 object")
                num_passed += 1
                mw_found = True
    except Exception as e:
        print(f"\t{e}\nFailed to retrieve middleware layers on your contract object")

    if not mw_found:
        print("\t\tYou have not injected middleware or you have injected\n"
              "\t\tthe incorrect type of middleware into the web3 object.\n"
              "\t\tCheck the assignment guide")

    run_score = int(num_passed * (100 / num_tests))
    print(f"\nRun Tests Score : {run_score}")
>>>>>>> 9657b38c4c96fbec93b1c12ed0cfdb05593694a7

    return int(100 * float(num_passed) / num_tests)


<<<<<<< HEAD
if __name__ == '__main__':
    print(validate(""))
=======
# if __name__ == '__main__':
#     print(f"Score = {validate(code_path)}")
>>>>>>> 9657b38c4c96fbec93b1c12ed0cfdb05593694a7
