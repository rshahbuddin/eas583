from web3 import Web3
from web3.providers.rpc import HTTPProvider
from web3.middleware import ExtraDataToPOAMiddleware #Necessary for POA chains
from datetime import datetime
import json
import pandas as pd
import time


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


def get_contract_info(chain, contract_info="contract_info.json"):
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
    return contracts.get(chain, {})

def handle_deposit_event(event, destination_contract, destination_w3, contract_info):
    print("Deposit event detected:", event)
    deposit_data = event['args']
    print(f"Deposit Data: {deposit_data}")
    
    destination_contract.functions.wrap(deposit_data["amount"], deposit_data["receiver"]).transact({
        "from": contract_info["destination_chain_wallet_address"],
        "gas": 2000000
    })

def handle_unwrap_event(event, source_contract, source_w3, contract_info):
    print("Unwrap event detected:", event)
    unwrap_data = event['args']
    print(f"Unwrap Data: {unwrap_data}")
    
    source_contract.functions.withdraw(unwrap_data["amount"], unwrap_data["receiver"]).transact({
        "from": contract_info["source_chain_wallet_address"],
        "gas": 2000000
    })



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
    with open(contract_info, 'r') as f:
        all_contract_info = json.load(f)

    source_info = all_contract_info['source']
    destination_info = all_contract_info['destination']

    source_w3 = connect_to('source')
    destination_w3 = connect_to('destination')

    source_contract = source_w3.eth.contract(address=source_info['address'], abi=source_info['abi'])
    destination_contract = destination_w3.eth.contract(address=destination_info['address'], abi=destination_info['abi'])

    deposit_event_filter = source_contract.events.Deposit.createFilter(fromBlock='latest')
    unwrap_event_filter = destination_contract.events.Unwrap.createFilter(fromBlock='latest')

    while True:
        for event in deposit_event_filter.get_new_entries():
            handle_deposit_event(event, destination_contract, destination_w3, destination_info)

        for event in unwrap_event_filter.get_new_entries():
            handle_unwrap_event(event, source_contract, source_w3, source_info)

        time.sleep(5)
