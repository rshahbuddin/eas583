import requests
import json

INFURA_API_URL = "https://ipfs.infura.io:5001/api/v0"
INFURA_PROJECT_ID = "f9fe6790a9994ec691770bb63baeb4d4"
INFURA_PROJECT_SECRET = "dv98qgJwif3/AK1ZFedGS1HNwvATpg+PKIagZ1qIADj/qRWfZ4OZmQ"

def pin_to_ipfs(data):
	assert isinstance(data,dict), f"Error pin_to_ipfs expects a dictionary"
	#YOUR CODE HERE
	json_data = json.dumps(data)
	files = {'file': ('data.json', json_data)}
	auth = (INFURA_PROJECT_ID, INFURA_PROJECT_SECRET)
	response = requests.post(f"{INFURA_API_URL}/add", files=files, auth=auth)

	if response.status_code == 200:
		cid = response.json()["Hash"]
		return cid
	else:
		raise Exception(f"Failed to pin to IPFS:{response.text}")

def get_from_ipfs(cid,content_type="json"):
	assert isinstance(cid,str), f"get_from_ipfs accepts a cid in the form of a string"
	#YOUR CODE HERE	

	response = requests.get(f"{INFURA_API_URL}/cat?arg={cid}" auth=(INFURA_PROJECT_ID, INFURA_PROJECT_SECRET))

	if response.status_code == 200:
		data = json.loads(response.text)
		assert isinstance(data,dict), f"get_from_ipfs should return a dict"
		return data
	else:
		raise Exception(f"Failed to retrieve from IPFS: {response.text}")
