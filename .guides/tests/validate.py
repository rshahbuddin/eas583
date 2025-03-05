#!/usr/bin/env python3
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

    return int(100 * float(num_passed) / num_tests)


# if __name__ == '__main__':
#     print(f"Score = {validate(code_path)}")
