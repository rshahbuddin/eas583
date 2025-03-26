from web3 import Web3
#from web3.middleware.proof_of_authority import POAMiddleware
import json
import os
from eth_utils import to_bytes

#Connect to avalanche fuji testnet
AVALANCHE_RPC_URL = "https://api.avax-test.network/ext/bc/C/rpc"
w3 = Web3(Web3.HTTPProvider(AVALANCHE_RPC_URL))

#Proof of authority middleware
#w3.middleware_onion.inject(POAMiddleware, layer=0)

assert w3.is_connected(), "Failed to connect to Avalanche Fuji Testnet"

#Wallet private key
PRIVATE_KEY = "12d6299d39888e9d3f8d71ee143355a147d1ca4d7b5282116c597e21b93fa2a6"
ACCOUNT = w3.eth.account.from_key(PRIVATE_KEY)
MY_ADDRESS = ACCOUNT.address

CONTRACT_ADDRESS = "0x85ac2e065d4526FBeE6a2253389669a12318A412"

with open("NFT.abi", "r") as abi_file:
	CONTRACT_ABI = json.load(abi_file)
CONTRACT_ABI = json.load(open("NFT.abi"))

#Load contract 
contract = w3.eth.contract(address=CONTRACT_ADDRESS, abi=CONTRACT_ABI)

#Generate random nonce
import random
nonce = random.randint(1, 1_000_000)

#Estimate gas and send transaction
tx = contract.functions.claim(
	MY_ADDRESS,
	to_bytes(hexstr=w3.keccak(text=str(nonce)).hex())
).build_transaction({
	'from': MY_ADDRESS,
	'gas': 200000,
	'gasPrice': w3.to_wei('50', 'gwei'),
	'nonce': w3.eth.get_transaction_count(MY_ADDRESS)
})

#Sign and send transaction
signed_tx = w3.eth.account.sign_transaction(tx, PRIVATE_KEY)
tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)

print(f"Transaction send! Hash: {tx_hash.hex()}")

#Wait for receipt
receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
if receipt.status == 1:
	print("NFT claimed successfully")
else:
	print("Transaction failed")
