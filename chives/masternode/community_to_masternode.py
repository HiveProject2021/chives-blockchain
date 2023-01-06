import sys
import asyncio
import aiosqlite
import binascii
import sqlite3
import json
import logging
import time
import pathlib
import importlib

from blspy import G2Element
import json

import time

from chives.rpc.full_node_rpc_client import FullNodeRpcClient
from chives.rpc.wallet_rpc_client import WalletRpcClient
from chives.types.blockchain_format.coin import Coin
from chives.types.blockchain_format.program import Program
from chives.types.blockchain_format.sized_bytes import bytes32
from chives.types.coin_spend import CoinSpend
from chives.types.spend_bundle import SpendBundle
from chives.util.bech32m import encode_puzzle_hash, decode_puzzle_hash
from chives.util.config import load_config
from chives.util.default_root import DEFAULT_ROOT_PATH
from chives.util.ints import uint16, uint64
from chives.wallet.transaction_record import TransactionRecord
from pathlib import Path
from chives.util.byte_types import hexstr_to_bytes
from chives.consensus.default_constants import DEFAULT_CONSTANTS
from typing import Dict, List, Set, Tuple, Optional, Union, Any
from clvm_tools.clvmc import compile_clvm
from chives.types.blockchain_format.program import Program, SerializedProgram

config = load_config(DEFAULT_ROOT_PATH, "config.yaml")
selected = config["selected_network"]
if config["selected_network"] =="testnet10":
    testnet_agg_sig_data = config["network_overrides"]["constants"][config["selected_network"]]["AGG_SIG_ME_ADDITIONAL_DATA"]
    DEFAULT_CONSTANTS = DEFAULT_CONSTANTS.replace_str_to_bytes(**{"AGG_SIG_ME_ADDITIONAL_DATA": testnet_agg_sig_data})
self_hostname = config["self_hostname"] # localhost
full_node_rpc_port = config["full_node"]["rpc_port"] # 8555
wallet_rpc_port = config["wallet"]["rpc_port"] # 9256
prefix = config["network_overrides"]["config"][selected]["address_prefix"]

ROOT = pathlib.Path(importlib.import_module("chives").__file__).absolute().parent.parent


def print_json(dict):
    print(json.dumps(dict, sort_keys=True, indent=4))

def load_clsp_relative(filename: str, search_paths: List[Path] = [Path("include/")]):
    base = Path().parent.resolve()
    source = base / filename
    target = base / f"{filename}.hex"
    searches = [base / s for s in search_paths]
    compile_clvm(source, target, searches)
    clvm = target.read_text()
    clvm_blob = bytes.fromhex(clvm)
    sp = SerializedProgram.from_bytes(clvm_blob)
    return Program.from_bytes(bytes(sp))

async def getAllUnspentCoins(STAKING_PUZZLE_HASH, STAKING_PUZZLE):  
    try:
        node_client = await FullNodeRpcClient.create(self_hostname, uint16(full_node_rpc_port), DEFAULT_ROOT_PATH, config)
        all_staking_coins = await node_client.get_coin_records_by_puzzle_hash(STAKING_PUZZLE_HASH,False,160000)
        #print(f"STAKING_PUZZLE_HASH: {STAKING_PUZZLE_HASH}")
        print(f"all_staking_coins: {len(all_staking_coins)}")
        for coin_record in all_staking_coins:
            coin_record = await node_client.get_coin_record_by_name(coin_record.coin.name())
            #print(f"unspend coin_record:{coin_record}")        
            #Spent Coin
            coin_spend = CoinSpend(
                coin_record.coin,
                STAKING_PUZZLE,
                Program.to([coin_record.coin.amount])
            )
            # empty signature i.e., c00000.....
            signature = G2Element()
            # SpendBundle
            spend_bundle = SpendBundle(
                    # coin spends
                    [coin_spend],
                    # aggregated_signature
                    signature,
                )
            #print_json(spend_bundle.to_json_dict())
            blockchain_state = await node_client.get_blockchain_state()
            if blockchain_state is not None and blockchain_state["sync"]["synced"] == True:
                try:
                    status = await node_client.push_tx(spend_bundle)
                    print_json(status['status'])  
                except Exception:
                    print(Exception)
            else:
                print("Not synced.")
                return None
                      
    finally:
        node_client.close()
        await node_client.await_closed()

# /home/wang/chives-blockchain/venv/bin/python3 /home/wang/chives-blockchain/chives/masternode/community_to_masternode.py

def MakeUserStakingAddressBaseOnStaking(COMMUNITY_ADDRESS, MASTERNODE_ADDRESS): 
    STAKING_MOD = load_clsp_relative(f"{ROOT}/chives/masternode/clsp/community_to_masternode.clsp")
    #print(f"decode_puzzle_hash(FIRST_ADDRESS):{decode_puzzle_hash(FIRST_ADDRESS)}")
    STAKING_PUZZLE = STAKING_MOD.curry(decode_puzzle_hash(COMMUNITY_ADDRESS), decode_puzzle_hash(MASTERNODE_ADDRESS))
    STAKING_PUZZLE_HASH = STAKING_PUZZLE.get_tree_hash()
    STAKING_ADDRESS = encode_puzzle_hash(STAKING_PUZZLE_HASH,prefix)
    #print(f"STAKING_PUZZLE:{STAKING_PUZZLE}")
    #print(f"STAKING_PUZZLE_HASH: {STAKING_PUZZLE_HASH}\n")
    #print(f"STAKING_ADDRESS: {STAKING_ADDRESS}\n")
    return STAKING_PUZZLE_HASH,STAKING_PUZZLE,STAKING_ADDRESS
    
if __name__ == "__main__":
    
    # This file is used for spend your staking smart coins.
    # Need full node support !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    
    # This is your first address (index=0, master_sk_to_wallet_sk_unhardened)
    MASTERNODE_ADDRESS = "txcc124dcndk6hawzk729j6cu84dalqkcptx57j33dnm3y4csufnwkgsqdkq0aa"
    COMMUNITY_ADDRESS = "xcc1fe7c0sm49s9558e9a3avtsg0x37rjsrwvafjyqzr728953gwqwyq2whe8f"
    STAKING_REQUIRED_HEIGHT = 5

    # Make the staking puzzle hash
    STAKING_PUZZLE_HASH,STAKING_PUZZLE,STAKING_ADDRESS = MakeUserStakingAddressBaseOnStaking(COMMUNITY_ADDRESS, MASTERNODE_ADDRESS)

    # Pls send coin to this address use cmd
    #print(f"Pls send coin to this address use cmd: chives wallet send -t {STAKING_ADDRESS} -a 1.234")

    # spend coins if coin can be spent
    asyncio.run(getAllUnspentCoins(STAKING_PUZZLE_HASH,STAKING_PUZZLE))
