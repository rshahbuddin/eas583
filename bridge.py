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

print(f"ADMIN_ADDRESS={ADMIN_ADDRESS}")
print(f"PRIVATE_KEY={'set' if PRIVATE_KEY else 'not set'}")
print(f"AVAX_RPC={AVAX_RPC}")
print(f"BSC_RPC={BSC_RPC}")


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
    ).build_transaction({
        "from": Web3.to_checksum_address(from_address),
        "nonce": destination_w3.eth.get_transaction_count(Web3.to_checksum_address(from_address), "pending"),
        "gas": 2000000,
        "gasPrice": int(destination_w3.eth.gas_price * 1.2),
        "chainId": destination_info.get("chainId"),
    })

    signed_tx = destination_w3.eth.account.sign_transaction(tx, PRIVATE_KEY)

    print("Type of signed_tx:", type(signed_tx))
    print("signed_tx fields:", dir(signed_tx))

    tx_hash = destination_w3.eth.send_raw_transaction(signed_tx.raw_transaction)
    print(f"Sent wrap tx on destination chain: {tx_hash.hex()}")


def handle_unwrap_event(event, source_contract, source_w3, source_info):
    unwrap_data = event['args']

    from_address = ADMIN_ADDRESS

    tx = source_contract.functions.withdraw(
        unwrap_data["token"],
        unwrap_data["recipient"],
        unwrap_data["amount"]
    ).build_transaction({
        "from": Web3.to_checksum_address(from_address),
        "nonce": source_w3.eth.get_transaction_count(Web3.to_checksum_address(from_address), "pending"),
        "gas": 2000000,
        "gasPrice": int(source_w3.eth.gas_price * 1.2),
        "chainId": source_info.get("chainId"),
    })

    signed_tx = source_w3.eth.account.sign_transaction(tx, PRIVATE_KEY)
    tx_hash = source_w3.eth.send_raw_transaction(signed_tx.raw_transaction)
    print(f"Sent withdraw tx on source chain: {tx_hash.hex()}")


def scan_blocks():
    with open('contract_info.json') as f:
        info = json.load(f)

    admin = info["admin"]
    private_key = info["private_key"]

    source_w3 = Web3(Web3.HTTPProvider(info["source_rpc"]))
    dest_w3 = Web3(Web3.HTTPProvider(info["dest_rpc"]))

    source = source_w3.eth.contract(address=info["source_contract"]["address"], abi=info["source_contract"]["abi"])
    dest = dest_w3.eth.contract(address=info["destination_contract"]["address"], abi=info["destination_contract"]["abi"])

    source_block = source_w3.eth.block_number - 10
    dest_block = dest_w3.eth.block_number - 10

    deposit_events = source.events.Deposit.get_logs(fromBlock=source_block, toBlock='latest')
    for event in deposit_events:
        token = event.args.token
        recipient = event.args.recipient
        amount = event.args.amount

        nonce = dest_w3.eth.get_transaction_count(admin)
        tx = dest.functions.wrap(token, recipient, amount).build_transaction({
            "from": admin,
            "nonce": nonce,
            "gas": 500_000,
            "gasPrice": dest_w3.eth.gas_price,
        })
        signed = dest_w3.eth.account.sign_transaction(tx, private_key)
        dest_w3.eth.send_raw_transaction(signed.rawTransaction)

    unwrap_events = dest.events.Unwrap.get_logs(fromBlock=dest_block, toBlock='latest')
    for event in unwrap_events:
        token = event.args.token
        recipient = event.args.recipient
        amount = event.args.amount

        nonce = source_w3.eth.get_transaction_count(admin)
        tx = source.functions.withdraw(token, recipient, amount).build_transaction({
            "from": admin,
            "nonce": nonce,
            "gas": 500_000,
            "gasPrice": source_w3.eth.gas_price,
        })
        signed = source_w3.eth.account.sign_transaction(tx, private_key)
        source_w3.eth.send_raw_transaction(signed.rawTransaction)

if __name__ == "__main__":
    scan_blocks()
