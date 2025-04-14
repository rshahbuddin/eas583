from web3 import Web3
from web3.providers.rpc import HTTPProvider
from web3.middleware import ExtraDataToPOAMiddleware #Necessary for POA chains
from datetime import datetime
import json
import pandas as pd


def connect_to(chain):
    if chain == 'source':  # The source contract chain is avax
        api_url = f"https://api.avax-test.network/ext/bc/C/rpc" #AVAX C-chain testnet

    if chain == 'destination':  # The destination contract chain is bsc
        api_url = f"https://data-seed-prebsc-1-s1.binance.org:8545/" #BSC testnet

    if chain in ['source','destination']:
        w3 = Web3(Web3.HTTPProvider(api_url))
        # inject the poa compatibility middleware to the innermost layer
        w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)
    return w3


def get_contract_info(chain, contract_info):
    """
        Load the contract_info file into a dictionary
        This function is used by the autograder and will likely be useful to you
    """
    try:
        with open(contract_info, 'r')  as f:
            contracts = json.load(f)
    except Exception as e:
        print( f"Failed to read contract info\nPlease contact your instructor\n{e}" )
        return 0
    return contracts[chain]



def scan_blocks(chain, contract_info="contract_info.json"):
    """
        chain - (string) should be either "source" or "destination"
        Scan the last 5 blocks of the source and destination chains
        Look for 'Deposit' events on the source chain and 'Unwrap' events on the destination chain
        When Deposit events are found on the source chain, call the 'wrap' function the destination chain
        When Unwrap events are found on the destination chain, call the 'withdraw' function on the source chain
    """

    # This is different from Bridge IV where chain was "avax" or "bsc"
    if chain not in ['source','destination']:
        print( f"Invalid chain: {chain}" )
        return 0
    
        #YOUR CODE HERE
    from eth_account import Account 

    PRIVATE_KEY = "12d6299d39888e9d3f8d71ee143355a147d1ca4d7b5282116c597e21b93fa2a6"
    account = Account.from_key(PRIVATE_KEY)

    w3 = connect_to(chain)
    contract_data = get_contract_info(chain, contract_info)
    contract = w3.eth.contract(
        address=Web3.to_checksum_address(contract_data["address"]),
        abi=contract_data["abi"]
    )

    latest = w3.eth.block_number
    from_block = max(0, latest - 5)

    if chain == "source":
        print("Scanning source chain for Deposit events")
        events = contract.events.Deposit().get_logs(fromBlock=from_block, toBlock="latest")

        if not events:
            print("No Deposit events found.")
            return

        print(f"Found {len(events)} Deposit events.")

        w3_dest = connect_to("destination")
        dest_contract_data = get_contract_info("destination", contract_info)
        dest_contract = w3_dest.eth.contract(
            address=Web3.to_checksum_address(dest_contract_data["address"]),
            abi=dest_contract_data["abi"]
        )

        for event in events:
            token = event["args"]["token"]
            recipient = event["args"]["recipient"]
            amount = event["args"]["amount"]

            print(f"Relaying Deposit: token={token}, recipient={recipient}, amount={amount}")

            txn = dest_contract.functions.unwrap(token, recipient, amount).build_transaction({
                'chainId': 97,
                'from': account.address,
                'nonce': w3_dest.eth.get_transaction_count(account.address),
                'gas': 300000,
                'gasPrice': w3_dest.eth.gas_price
            })

            signed_txn = w3_dest.eth.account.sign_transaction(txn, PRIVATE_KEY)
            tx_hash = w3_dest.eth.send_raw_transaction(signed_txn.rawTransaction)
            print(f"Unwrap transaction sent: {tx_hash.hex()}")

    elif chain == "destination":
        print("Scanning destination chain for Unwrap events")
        events = contract.events.Unwrap().get_logs(fromBlock=from_block, toBlock="latest")

        if not events:
            print("No Unwrap events found.")
            return

        print(f"Found {len(events)} Unwrap events.")

        w3_source = connect_to("source")
        source_contract_data = get_contract_info("source", contract_info)
        source_contract = w3_source.eth.contract(
            address=Web3.to_checksum_address(source_contract_data["address"]),
            abi=source_contract_data["abi"]
        )

        for event in events:
            token = event["args"]["token"]
            recipient = event["args"]["recipient"]
            amount = event["args"]["amount"]

            print(f"Relaying Unwrap: token={token}, recipient={recipient}, amount={amount}")

            txn = source_contract.functions.withdraw(token, recipient, amount).build_transaction({
                'chainId': 43113,
                'from': account.address,
                'nonce': w3_source.eth.get_transaction_count(account.address),
                'gas': 300000,
                'gasPrice': w3_source.eth.gas_price
            })

            signed_txn = w3_source.eth.account.sign_transaction(txn, PRIVATE_KEY)
            tx_hash = w3_source.eth.send_raw_transaction(signed_txn.rawTransaction)
            print(f"Withdraw transaction sent: {tx_hash.hex()}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2 or sys.argv[1] not in ["source", "destination"]:
        print("Usage: python3 bridge.py [source|destination]")
    else:
        scan_blocks(sys.argv[1])
