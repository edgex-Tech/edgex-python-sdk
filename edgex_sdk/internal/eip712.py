from typing import Dict, Any, List, Tuple

from eth_account import Account
from eth_account.messages import encode_typed_data


def derive_address_from_private_key(private_key_hex: str) -> str:
    private_key_hex = private_key_hex.strip()
    if not private_key_hex.startswith("0x"):
        private_key_hex = "0x" + private_key_hex
    acct = Account.from_key(private_key_hex)
    return acct.address


def sign_typed_data(private_key_hex: str, typed_data: Dict[str, Any]) -> str:
    private_key_hex = private_key_hex.strip()
    if not private_key_hex.startswith("0x"):
        private_key_hex = "0x" + private_key_hex

    domain_data = typed_data.get("domain", {})
    primary_type = typed_data.get("primaryType", "")
    types = typed_data.get("types", {})
    message = typed_data.get("message", {})

    full_message = {
        "types": types,
        "primaryType": primary_type,
        "domain": domain_data,
        "message": message,
    }

    signable = encode_typed_data(full_message=full_message)

    signed = Account.sign_message(signable, private_key_hex)
    return signed.signature.hex()


def build_eip712_domain(
    name: str,
    version: str,
    chain_id: str,
    verifying_contract: str
) -> Dict[str, Any]:
    domain = {
        "name": name.strip(),
        "version": version.strip(),
    }
    chain_id = chain_id.strip()
    if chain_id:
        domain["chainId"] = int(chain_id, 16) if chain_id.lower().startswith("0x") else int(chain_id)
    verifying_contract = verifying_contract.strip()
    if verifying_contract:
        domain["verifyingContract"] = verifying_contract
    return domain


EIP712_DOMAIN_TYPE = [
    {"name": "name", "type": "string"},
    {"name": "version", "type": "string"},
    {"name": "chainId", "type": "uint256"},
    {"name": "verifyingContract", "type": "address"},
]

ORDER_BASE_TYPE = [
    {"name": "nonce", "type": "uint256"},
    {"name": "signer", "type": "address"},
    {"name": "accountId", "type": "uint64"},
    {"name": "expirationTimestamp", "type": "uint256"},
]

LIMIT_ORDER_PARAMS_TYPE = [
    {"name": "base", "type": "OrderBase"},
    {"name": "amountSynthetic", "type": "int256"},
    {"name": "amountCollateral", "type": "int256"},
    {"name": "amountFee", "type": "uint256"},
    {"name": "assetIdSynthetic", "type": "uint64"},
    {"name": "assetIdCollateral", "type": "uint64"},
    {"name": "isBuyingSynthetic", "type": "bool"},
    {"name": "parentOrderHash", "type": "bytes32"},
    {"name": "subOrderIndex", "type": "uint256"},
]

TRANSFER_PARAMS_TYPE = [
    {"name": "from", "type": "uint64"},
    {"name": "to", "type": "uint64"},
    {"name": "assetId", "type": "uint64"},
    {"name": "amount", "type": "int256"},
    {"name": "nonce", "type": "uint256"},
    {"name": "deadline", "type": "uint256"},
    {"name": "signer", "type": "address"},
]

WITHDRAWAL_PARAMS_TYPE = [
    {"name": "from", "type": "uint64"},
    {"name": "toAddress", "type": "address"},
    {"name": "amount", "type": "int256"},
    {"name": "feeAmount", "type": "int256"},
    {"name": "nonce", "type": "uint256"},
    {"name": "expirationTimestamp", "type": "uint256"},
    {"name": "signer", "type": "address"},
]
