import json
from typing import Dict, Any, List, Tuple

from eth_account import Account
from eth_account.messages import encode_typed_data


def derive_address_from_private_key(private_key_hex: str) -> str:
    private_key_hex = private_key_hex.strip()
    if not private_key_hex.startswith("0x"):
        private_key_hex = "0x" + private_key_hex
    acct = Account.from_key(private_key_hex)
    return acct.address


def sign_typed_data(private_key_hex: str, typed_data: Dict[str, Any], include_0x: bool = False) -> str:
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
    signature = signed.signature.hex()
    if include_0x and not signature.startswith("0x"):
        return "0x" + signature
    if not include_0x and signature.startswith("0x"):
        return signature[2:]
    return signature


def build_typed_data_from_server_response(eip712_response: Dict[str, Any]) -> Dict[str, Any]:
    if "primaryType" not in eip712_response and isinstance(eip712_response.get("data"), dict):
        eip712_response = eip712_response["data"]

    domain = eip712_response.get("domain") or {}

    raw_types = eip712_response.get("types") or {}
    types: Dict[str, List[Dict[str, str]]] = {}
    for name, entry in raw_types.items():
        fields = entry.get("fields") if isinstance(entry, dict) else entry
        if fields is None:
            continue
        types[name] = [{"name": field["name"], "type": field["type"]} for field in fields]

    if "EIP712Domain" not in types:
        domain_fields: List[Dict[str, str]] = []
        if domain.get("name"):
            domain_fields.append({"name": "name", "type": "string"})
        if domain.get("version"):
            domain_fields.append({"name": "version", "type": "string"})
        if domain.get("chainId") not in (None, ""):
            domain_fields.append({"name": "chainId", "type": "uint256"})
        if domain.get("verifyingContract"):
            domain_fields.append({"name": "verifyingContract", "type": "address"})
        types["EIP712Domain"] = domain_fields

    normalized_domain: Dict[str, Any] = {}
    if domain.get("name"):
        normalized_domain["name"] = domain["name"]
    if domain.get("version"):
        normalized_domain["version"] = domain["version"]
    if domain.get("chainId") not in (None, ""):
        chain_id = str(domain["chainId"])
        normalized_domain["chainId"] = int(chain_id, 16) if chain_id.lower().startswith("0x") else int(chain_id)
    if domain.get("verifyingContract"):
        normalized_domain["verifyingContract"] = domain["verifyingContract"]

    if "messageJson" in eip712_response:
        message = json.loads(eip712_response["messageJson"])
    else:
        message = eip712_response.get("message") or {}

    return {
        "types": types,
        "primaryType": eip712_response["primaryType"],
        "domain": normalized_domain,
        "message": message,
    }


def build_eip712_domain(name: str, version: str, chain_id: str, verifying_contract: str) -> Dict[str, Any]:
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

SET_MARGIN_MODE_PARAMS_TYPE = [
    {"name": "accountId", "type": "uint64"},
    {"name": "assetId", "type": "uint64"},
    {"name": "marginMode", "type": "uint8"},
    {"name": "nonce", "type": "uint256"},
    {"name": "signer", "type": "address"},
]
