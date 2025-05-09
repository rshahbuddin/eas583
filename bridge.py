from web3 import Web3
import json
import time
import os
from web3.exceptions import ContractLogicError

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

    max_retries = 3
    retry_delay = 5
    for attempt in range(max_retries):
        try:
            nonce = destination_w3.eth.get_transaction_count(
                Web3.to_checksum_address(from_address), "pending"
            )
            
            gas_price_multiplier = 1.2 + (0.1 * attempt)
            
            tx = destination_contract.functions.wrap(
                deposit_data["token"],
                deposit_data["recipient"],
                deposit_data["amount"]
            ).build_transaction({
                "from": Web3.to_checksum_address(from_address),
                "nonce": nonce,
                "gas": 2000000,
                "gasPrice": int(destination_w3.eth.gas_price * gas_price_multiplier),
                "chainId": destination_info.get("chainId"),
            })

            signed_tx = destination_w3.eth.account.sign_transaction(tx, PRIVATE_KEY)
            tx_hash = destination_w3.eth.send_raw_transaction(signed_tx.raw_transaction)
            print(f"Sent wrap tx on destination chain: {tx_hash.hex()}")
            
            receipt = destination_w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
            print(f"Wrap transaction confirmed in block {receipt.blockNumber}, status: {receipt.status}")
            
            return  
        except Exception as e:
            print(f"Attempt {attempt+1}/{max_retries} failed: {str(e)}")
            if attempt < max_retries - 1:
                print(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
                retry_delay *= 2  
            else:
                print(f"Failed to send wrap transaction after {max_retries} attempts")


def handle_unwrap_event(event, source_contract, source_w3, source_info):
    unwrap_data = event['args']
    from_address = ADMIN_ADDRESS

    max_retries = 3
    retry_delay = 5
    for attempt in range(max_retries):
        try:
            nonce = source_w3.eth.get_transaction_count(
                Web3.to_checksum_address(from_address), "pending"
            )
            
            gas_price_multiplier = 1.2 + (0.1 * attempt)
            
            tx = source_contract.functions.withdraw(
                unwrap_data["underlying_token"],  
                unwrap_data["to"],                
                unwrap_data["amount"]
            ).build_transaction({
                "from": Web3.to_checksum_address(from_address),
                "nonce": nonce,
                "gas": 2000000,
                "gasPrice": int(source_w3.eth.gas_price * gas_price_multiplier),
                "chainId": source_info.get("chainId"),
            })

            signed_tx = source_w3.eth.account.sign_transaction(tx, PRIVATE_KEY)
            tx_hash = source_w3.eth.send_raw_transaction(signed_tx.raw_transaction)
            print(f"Sent withdraw tx on source chain: {tx_hash.hex()}")
            
            receipt = source_w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
            print(f"Withdraw transaction confirmed in block {receipt.blockNumber}, status: {receipt.status}")
            
            return  
        except Exception as e:
            print(f"Attempt {attempt+1}/{max_retries} failed: {str(e)}")
            if attempt < max_retries - 1:
                print(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
                retry_delay *= 2  
            else:
                print(f"Failed to send withdraw transaction after {max_retries} attempts")


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

    current_source_block = source_w3.eth.block_number
    current_destination_block = destination_w3.eth.block_number
    
    blocks_to_scan = 5
    from_source_block = max(1, current_source_block - blocks_to_scan)
    to_source_block = current_source_block
    
    from_destination_block = max(1, current_destination_block - blocks_to_scan)
    to_destination_block = current_destination_block

    print(f"Starting block scan from source: {from_source_block} to {to_source_block}, destination: {from_destination_block} to {to_destination_block}")

    print(f"Checking Deposit events from block {from_source_block} to {to_source_block}")
    try:
        deposit_filter = source_contract.events.Deposit.create_filter(
            from_block=from_source_block, 
            to_block=to_source_block
        )
        deposit_events = deposit_filter.get_all_entries()
        
        for event in deposit_events:
            print(f"Deposit event detected: {event}")
            handle_deposit_event(event, destination_contract, destination_w3, destination_info)
            
    except Exception as e:
        print(f"Error checking Deposit events: {e}")
        
    print(f"Checking Unwrap events from block {from_destination_block} to {to_destination_block}")
    try:
        unwrap_filter = destination_contract.events.Unwrap.create_filter(
            from_block=from_destination_block,
            to_block=to_destination_block
        )
        unwrap_events = unwrap_filter.get_all_entries()
        
        for event in unwrap_events:
            print(f"Unwrap event detected: {event}")
            handle_unwrap_event(event, source_contract, source_w3, source_info)
            
    except Exception as e:
        print(f"Error checking Unwrap events: {e}")
    
    print("Block scanning complete")
    return


if __name__ == "__main__":
    scan_blocks()