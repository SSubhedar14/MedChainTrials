# deploy_contract.py
import json
from web3 import Web3
from solcx import compile_standard, install_solc, set_solc_version, get_installed_solc_versions

# Install and set the specific version of Solidity compiler
install_solc('0.8.0')
set_solc_version('0.8.0')
# Solidity source code
contract_source_code = '''
pragma solidity ^0.8.0;

contract ClinicalTrials {
    struct Trial {
        uint256 id;
        string patientId;
        string dataHash;
        TrialStatus status;
        address researcher;
        uint256 startDate;
        uint256 lastUpdated;
    }

    enum TrialStatus { Active, Completed, Suspended }

    uint256 public trialCount = 0;
    mapping(uint256 => Trial) public trials;
    mapping(address => bool) public authorizedResearchers;

    event TrialCreated(uint256 id, string patientId, string dataHash, TrialStatus status, address researcher);
    event TrialUpdated(uint256 id, string newDataHash, TrialStatus newStatus);
    event ResearcherAuthorized(address researcher);
    event ResearcherDeauthorized(address researcher);

    modifier onlyAuthorizedResearcher() {
        require(authorizedResearchers[msg.sender], "Not an authorized researcher");
        _;
    }

    constructor() {
        authorizedResearchers[msg.sender] = true;
        emit ResearcherAuthorized(msg.sender);
    }

    function authorizeResearcher(address _researcher) public onlyAuthorizedResearcher {
        authorizedResearchers[_researcher] = true;
        emit ResearcherAuthorized(_researcher);
    }

    function deauthorizeResearcher(address _researcher) public onlyAuthorizedResearcher {
        authorizedResearchers[_researcher] = false;
        emit ResearcherDeauthorized(_researcher);
    }

    function createTrial(string memory _patientId, string memory _dataHash) public onlyAuthorizedResearcher {
        trialCount++;
        trials[trialCount] = Trial(
            trialCount,
            _patientId,
            _dataHash,
            TrialStatus.Active,
            msg.sender,
            block.timestamp,
            block.timestamp
        );
        emit TrialCreated(trialCount, _patientId, _dataHash, TrialStatus.Active, msg.sender);
    }

    function updateTrial(uint256 _id, string memory _newDataHash, TrialStatus _newStatus) public onlyAuthorizedResearcher {
        require(_id > 0 && _id <= trialCount, "Invalid trial ID");
        Trial storage trial = trials[_id];
        trial.dataHash = _newDataHash;
        trial.status = _newStatus;
        trial.lastUpdated = block.timestamp;
        emit TrialUpdated(_id, _newDataHash, _newStatus);
    }

    function getTrial(uint256 _id) public view returns (Trial memory) {
        require(_id > 0 && _id <= trialCount, "Invalid trial ID");
        return trials[_id];
    }
}
'''

# Compile the contract
compiled_sol = compile_standard({
    "language": "Solidity",
    "sources": {
        "ClinicalTrials.sol": {
            "content": contract_source_code
        }
    },
    "settings": {
        "outputSelection": {
            "*": {
                "*": ["abi", "metadata", "evm.bytecode", "evm.sourceMap"]
            }
        }
    }
})

# Save compiled contract into a json file
with open("compiled_code.json", "w") as file:
    json.dump(compiled_sol, file)

# Connect to Ganache
ganache_url = "http://127.0.0.1:8545"
web3 = Web3(Web3.HTTPProvider(ganache_url))

# Check connection and account list
if not web3.is_connected():
    raise Exception("Failed to connect to Ganache. Check if it's running.")

# Set default account
accounts = web3.eth._accounts()
if not accounts:
    raise Exception("No accounts found. Make sure Ganache is running and providing accounts.")

web3.eth.defaultAccount = accounts[0]

# Get bytecode and ABI
bytecode = compiled_sol['contracts']['ClinicalTrials.sol']['ClinicalTrials']['evm']['bytecode']['object']
abi = json.loads(compiled_sol['contracts']['ClinicalTrials.sol']['ClinicalTrials']['metadata'])['output']['abi']

# Deploy contract
ClinicalTrials = web3.eth.contract(abi=abi, bytecode=bytecode)
tx_hash = ClinicalTrials.constructor().transact({'from': web3.eth.defaultAccount})
tx_receipt = web3.eth.wait_for_transaction_receipt(tx_hash)

# Contract address
contract_address = tx_receipt.contractAddress
print(f'Contract deployed at address: {contract_address}')
