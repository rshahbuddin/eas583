from web3 import Web3
import json
import time
import os

try:
  from dotenv import load_dotenv
  load_dotenv()
except ImportError:
  pass

ADMIN_ADDRESS = os.getenv("ADMIN_ADDRESS")
PRIVATE_KEY = os.getenv("PRIVATE_KEY")
AVAX_RPC = os.getenv("AVAX_RPC")
BSC_RPC = os.getenv("BSC_RPC")

#print(f"ADMIN_ADDRESS={ADMIN_ADDRESS}")
#print(f"PRIVATE_KEY={'set' if PRIVATE_KEY else 'not set'}")
#print(f"AVAX_RPC={AVAX_RPC}")
#print(f"BSC_RPC={BSC_RPC}")


def connect_to(chain):
    if chain == 'source':
        api_url = AVAX_RPC
    elif chain == 'destination':
        api_url = BSC_RPC
    else:
        raise ValueError(f"Unknown chain: {chain}")

    w3 = Web3(Web3.HTTPProvider(api_url))

    try:
        from web3.middleware import geth_poa_middleware
        w3.middleware_onion.inject(geth_poa_middleware, layer=0)
    except ImportError:
        pass

    if not w3.is_connected():
        raise ConnectionError(f"Failed to connect to {chain} RPC at {api_url}")

    return w3


def get_contract_info(chain, contract_info_file="contract_info.json"):
    try:
        with open(contract_info_file, 'r') as f:
            contracts = json.load(f)
    except Exception as e:
        print(f"Failed to read contract info: {e}")
        return {}
    return contracts.get(chain, {})


def handle_deposit_event(event, destination_contract, destination_w3, destination_info):
    deposit_data = event['args']

    from_address = ADMIN_ADDRESS

    tx = destination_contract.functions.wrap(
        deposit_data["token"],
        deposit_data["recipient"],
        deposit_data["amount"]
    ).buildTransaction({
        "from": Web3.to_checksum_address(from_address),
        "nonce": destination_w3.eth.get_transaction_count(Web3.to_checksum_address(from_address)),
        "gas": 2000000,
        "gasPrice": destination_w3.eth.gas_price,
        "chainId": destination_info.get("chainId"),
    })

    signed_tx = destination_w3.eth.account.sign_transaction(tx, PRIVATE_KEY)
    tx_hash = destination_w3.eth.send_raw_transaction(signed_tx.rawTransaction)
    print(f"Sent wrap tx on destination chain: {tx_hash.hex()}")


def handle_unwrap_event(event, source_contract, source_w3, source_info):
    unwrap_data = event['args']

    from_address = ADMIN_ADDRESS

    tx = source_contract.functions.withdraw(
        unwrap_data["token"],
        unwrap_data["recipient"],
        unwrap_data["amount"]
    ).buildTransaction({
        "from": Web3.to_checksum_address(from_address),
        "nonce": source_w3.eth.get_transaction_count(Web3.to_checksum_address(from_address)),
        "gas": 2000000,
        "gasPrice": source_w3.eth.gas_price,
				"chainId": source_info.get("chainId"),
    })

    signed_tx = source_w3.eth.account.sign_transaction(tx, PRIVATE_KEY)
    tx_hash = source_w3.eth.send_raw_transaction(signed_tx.rawTransaction)
    print(f"Sent withdraw tx on source chain: {tx_hash.hex()}")


def scan_blocks(chain=None, contract_info_file="contract_info.json"):
    with open(contract_info_file, 'r') as f:
        all_contract_info = json.load(f)

    source_info = all_contract_info['source']
    destination_info = all_contract_info['destination']

    source_w3 = connect_to('source')
    destination_w3 = connect_to('destination')

    source_contract = source_w3.eth.contract(
        address=Web3.to_checksum_address(source_info['address']),
        abi=source_info['abi']
    )
    destination_contract = destination_w3.eth.contract(
        address=Web3.to_checksum_address(destination_info['address']),
        abi=destination_info['abi']
    )

    last_source_block = source_w3.eth.block_number
    last_destination_block = destination_w3.eth.block_number

    print(f"Starting block scan from source: {last_source_block}, destination: {last_destination_block}")

    while True:
        try:
            latest_source_block = source_w3.eth.block_number
            from_source_block = max(last_source_block, latest_source_block - 5)

            if from_source_block <= latest_source_block:
              deposit_filter = source_contract.events.Deposit.create_filter(from_block=from_source_block, to_block=latest_source_block)
              deposit_events = deposit_filter.get_all_entries()
            else:
              deposit_events = []

            for event in deposit_events:
                print(f"Deposit event detected: {event}")
                handle_deposit_event(event, destination_contract, destination_w3, destination_info)

            last_source_block = latest_source_block + 1

            latest_destination_block = destination_w3.eth.block_number
            from_destination_block = max(last_destination_block, latest_destination_block - 5)

            if from_destination_block <= latest_destination_block:
              unwrap_filter = destination_contract.events.Unwrap.create_filter(from_block=from_destination_block, to_block=latest_destination_block)
              unwrap_events = unwrap_filter.get_all_entries()
            else:
              unwrap_events = []

            for event in unwrap_events:
                print(f"Unwrap event detected: {event}")
                handle_unwrap_event(event, source_contract, source_w3, source_info)

            last_destination_block = latest_destination_block + 1

        except Exception as e:
            print(f"Error during block scanning or event handling: {e}")

        time.sleep(5)


if __name__ == "__main__":
    scan_blocks()
