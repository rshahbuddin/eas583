from web3 import Web3
from web3.middleware import geth_poa_middleware
from dotenv import load_dotenv
import os
import json
import time

load_dotenv()
ADMIN_ADDRESS = os.getenv("ADMIN_ADDRESS")
PRIVATE_KEY = os.getenv("PRIVATE_KEY")

if ADMIN_ADDRESS is None or PRIVATE_KEY is None:
    raise Exception("ADMIN_ADDRESS or PRIVATE_KEY not set in .env")

def connect_to(chain):
    if chain == 'source':  
        api_url = "https://api.avax-test.network/ext/bc/C/rpc"
    elif chain == 'destination':  
        api_url = "https://data-seed-prebsc-1-s1.binance.org:8545/"
    else:
        raise ValueError(f"Unknown chain: {chain}")

    w3 = Web3(Web3.HTTPProvider(api_url))
    w3.middleware_onion.inject(geth_poa_middleware, layer=0)
    return w3

def get_contract_info(chain, contract_info="contract_info.json"):
    try:
        with open(contract_info, 'r') as f:
            contracts = json.load(f)
    except Exception as e:
        print(f"Failed to read contract info\nPlease contact your instructor\n{e}")
        return {}
    return contracts.get(chain, {})

def send_signed_transaction(w3, txn, private_key):
    signed_txn = w3.eth.account.sign_transaction(txn, private_key=private_key)
    tx_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    return receipt

def handle_deposit_event(event, destination_contract, destination_w3):
    deposit_data = event['args']
    nonce = destination_w3.eth.get_transaction_count(ADMIN_ADDRESS)
    txn = destination_contract.functions.wrap(
        deposit_data["token"],
        deposit_data["recipient"],
        deposit_data["amount"]
    ).build_transaction({
        "from": ADMIN_ADDRESS,
        "nonce": nonce,
        "gas": 2000000,
        "gasPrice": destination_w3.eth.gas_price,
        "chainId": 97  
    })
    receipt = send_signed_transaction(destination_w3, txn, PRIVATE_KEY)
    print(f"Wrap tx sent: {receipt.transactionHash.hex()}")

def handle_unwrap_event(event, source_contract, source_w3):
    unwrap_data = event['args']
    nonce = source_w3.eth.get_transaction_count(ADMIN_ADDRESS)
    txn = source_contract.functions.withdraw(
        unwrap_data["token"],
        unwrap_data["recipient"],
        unwrap_data["amount"]
    ).build_transaction({
        "from": ADMIN_ADDRESS,
        "nonce": nonce,
        "gas": 2000000,
        "gasPrice": source_w3.eth.gas_price,
        "chainId": 43113  
    })
    receipt = send_signed_transaction(source_w3, txn, PRIVATE_KEY)
    print(f"Withdraw tx sent: {receipt.transactionHash.hex()}")

def scan_blocks(chain, contract_info="contract_info.json"):
    if chain not in ['source', 'destination']:
        print(f"Invalid chain: {chain}")
        return 0

    with open(contract_info, 'r') as f:
        all_contract_info = json.load(f)

    source_info = all_contract_info['source']
    destination_info = all_contract_info['destination']

    source_w3 = connect_to('source')
    destination_w3 = connect_to('destination')

    source_contract = source_w3.eth.contract(address=source_info['address'], abi=source_info['abi'])
    destination_contract = destination_w3.eth.contract(address=destination_info['address'], abi=destination_info['abi'])

    print(f"Starting event scanner for {chain}...")

    while True:
        if chain == 'source':
            latest_source_block = source_w3.eth.block_number
            from_source_block = max(latest_source_block - 5, 0)

            deposit_filter = source_contract.events.Deposit.create_filter(from_block=from_source_block)
            deposit_events = deposit_filter.get_all_entries()

            for event in deposit_events:
                handle_deposit_event(event, destination_contract, destination_w3)

        if chain == 'destination':
            latest_destination_block = destination_w3.eth.block_number
            from_destination_block = max(latest_destination_block - 5, 0)

            unwrap_filter = destination_contract.events.Unwrap.create_filter(from_block=from_destination_block)
            unwrap_events = unwrap_filter.get_all_entries()

            for event in unwrap_events:
                handle_unwrap_event(event, source_contract, source_w3)

        time.sleep(5)
