from web3 import Web3
import json

# Connect to Ganache (or another Ethereum node)
ganache_url = "http://127.0.0.1:8545"
web3 = Web3(Web3.HTTPProvider(ganache_url))

# Load contract ABI and address
with open('compiled_code.json', 'r') as file:
    compiled_sol = json.load(file)

abi = compiled_sol['contracts']['ClinicalTrials.sol']['ClinicalTrials']['abi']
contract_address = '0x497615B8bbf78A188870251a17565Fc038fAD45F'  # contract address

# Create contract instance
contract = web3.eth.contract(address=contract_address, abi=abi)

# Function to get accounts
def get_accounts():
    return web3.eth.accounts

# # Function to authorize researcher
# def authorize_researcher(account):
#     tx_hash = contract.functions.authorizeResearcher(account).transact({'from': account})
#     receipt = web3.eth.wait_for_transaction_receipt(tx_hash)
#     return receipt

# Function to create trial
def create_trial(patient_id, ipfs_hash, account):
    web3.eth.default_account = account  # Set the default account
    tx_hash = contract.functions.createTrial(patient_id, ipfs_hash).transact({'from': account})
    receipt = web3.eth.wait_for_transaction_receipt(tx_hash)
    return receipt

# Function to update trial
def update_trial(trial_id, additional_info, status, account):
    web3.eth.default_account = account  # Set the default account
    tx_hash = contract.functions.updateTrial(trial_id, additional_info, status).transact({'from': account})
    receipt = web3.eth.wait_for_transaction_receipt(tx_hash)
    return receipt

# Function to get trial
def get_trial(trial_id):
    trial = contract.functions.getTrial(trial_id).call()
    return trial

# Function to get trial count
def get_trial_count():
    count = contract.functions.trialCount().call()
    return count
