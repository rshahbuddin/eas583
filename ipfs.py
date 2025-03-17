import requests
import json

PINATA_API_URL = "https://api.pinata.cloud"
PINATA_PROJECT_ID = "2521c0ed06a4f4408d5b"
PINATA_PROJECT_SECRET = "3bf4d9632ed6f63d8e9ee6bbf0f14bd256c2ea33538af46aba9a0c493deff1e3"

headers = {
	"pinata_api_key": PINATA_PROJECT_ID,
	"pinata_secret_api_key": PINATA_PROJECT_SECRET
}

def pin_to_ipfs(data):
	assert isinstance(data,dict), f"Error pin_to_ipfs expects a dictionary"
	
	#YOUR CODE HERE

	response = requests.post(f"{PINATA_API_URL}/pinning/pinJSONToIPFS", json=data, headers=headers)

	if response.status_code == 200:
		cid = response.json()["IpfsHash"]
		return cid
	else:
		raise Exception(f"Failed to pin to IPFS:{response.text}")

def get_from_ipfs(cid,content_type="json"):
	assert isinstance(cid,str), f"get_from_ipfs accepts a cid in the form of a string"
	#YOUR CODE HERE	

	response = requests.get(f"https://gateway.pinata.cloud/ipfs/{cid}")

	if response.status_code == 200:
		data = json.loads(response.text)
		assert isinstance(data,dict), "Error: get_from_ipfs should return a dict"
		return data
	else:
		raise Exception(f"Failed to retrieve from IPFS: {response.text}")
