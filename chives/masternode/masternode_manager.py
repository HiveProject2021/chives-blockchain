import sys
import asyncio
import aiosqlite
from pathlib import Path
import binascii
import sqlite3
import json
import logging
import time
import pathlib
import importlib
from decimal import Decimal
from typing import Dict, List, Set, Tuple, Optional, Union, Any
from blspy import AugSchemeMPL, G1Element, G2Element, PrivateKey

from chives.cmds.units import units
from chives.types.blockchain_format.coin import Coin
from chives.types.spend_bundle import SpendBundle
from chives.types.blockchain_format.program import Program, SerializedProgram
from chives.util.hash import std_hash
from clvm.casts import int_to_bytes, int_from_bytes
from chives.util.byte_types import hexstr_to_bytes
from chives.consensus.default_constants import DEFAULT_CONSTANTS
from chives.wallet.puzzles.load_clvm import load_clvm
from chives.wallet.util.wallet_types import AmountWithPuzzlehash, WalletType
from chives.wallet.transaction_record import TransactionRecord
from chives.util.keychain import Keychain, bytes_from_mnemonic, bytes_to_mnemonic, generate_mnemonic, mnemonic_to_seed, unlocks_keyring
from chives.util.condition_tools import ConditionOpcode
from chives.wallet.puzzles.p2_delegated_puzzle_or_hidden_puzzle import (  # standard_transaction
    puzzle_for_pk,
    calculate_synthetic_secret_key,
    DEFAULT_HIDDEN_PUZZLE_HASH,
)
from chives.util.db_wrapper import DBWrapper
from chives.full_node.coin_store import CoinStore
from chives.wallet.derive_keys import (
    master_sk_to_farmer_sk,
    master_sk_to_pool_sk,
    master_sk_to_wallet_sk,
    master_sk_to_wallet_sk_unhardened,
    _derive_path,
    _derive_path_unhardened,
    master_sk_to_singleton_owner_sk,
)
from chives.wallet.puzzles.puzzle_utils import (
    make_assert_absolute_seconds_exceeds_condition,
    make_assert_coin_announcement,
    make_assert_my_coin_id_condition,
    make_assert_puzzle_announcement,
    make_create_coin_announcement,
    make_create_coin_condition,
    make_create_puzzle_announcement,
    make_reserve_fee_condition,
)
from chives.wallet.derive_keys import master_sk_to_wallet_sk_unhardened
from chives.types.coin_spend import CoinSpend
from chives.wallet.sign_coin_spends import sign_coin_spends
from chives.wallet.lineage_proof import LineageProof
from chives.wallet.puzzles import singleton_top_layer
from chives.types.announcement import Announcement
from chives.types.blockchain_format.sized_bytes import bytes32
from chives.util.default_root import DEFAULT_ROOT_PATH
from chives.rpc.rpc_client import RpcClient
from chives.rpc.full_node_rpc_client import FullNodeRpcClient
from chives.rpc.wallet_rpc_client import WalletRpcClient
from chives.util.config import load_config
from chives.util.ints import uint16, uint64, uint32
from chives.util.bech32m import decode_puzzle_hash, encode_puzzle_hash
from chives.wallet.puzzles.p2_delegated_puzzle_or_hidden_puzzle import solution_for_conditions
from chives.wallet.secret_key_store import SecretKeyStore

from clvm_tools.clvmc import compile_clvm

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


ROOT = pathlib.Path(importlib.import_module("chives").__file__).absolute().parent.parent

log = logging.getLogger(__name__)
SINGLETON_MOD = load_clvm("singleton_top_layer.clvm")
SINGLETON_MOD_HASH = SINGLETON_MOD.get_tree_hash()
LAUNCHER_PUZZLE = load_clsp_relative(f"{ROOT}/chives/masternode/clsp/nft_launcher.clsp")
LAUNCHER_PUZZLE_HASH = LAUNCHER_PUZZLE.get_tree_hash()

INNER_MOD = load_clsp_relative(f"{ROOT}/chives/masternode/clsp/creator_nft.clsp")
ESCAPE_VALUE = -113
MELT_CONDITION = [ConditionOpcode.CREATE_COIN, 0, ESCAPE_VALUE]

config = load_config(Path(DEFAULT_ROOT_PATH), "config.yaml")
selected = config["selected_network"]
if config["selected_network"] =="testnet10":
    testnet_agg_sig_data = config["network_overrides"]["constants"][config["selected_network"]]["AGG_SIG_ME_ADDITIONAL_DATA"]
    DEFAULT_CONSTANTS = DEFAULT_CONSTANTS.replace_str_to_bytes(**{"AGG_SIG_ME_ADDITIONAL_DATA": testnet_agg_sig_data})

class MasterNodeManager:
    def __init__(
        self,
        wallet_client: WalletRpcClient = None,
        node_client: FullNodeRpcClient = None,
        db_name: str = str(Path(DEFAULT_ROOT_PATH))+"/db/masternode.db",
    ) -> None:
        self.wallet_client = wallet_client
        self.node_client = node_client
        self.db_name = db_name
        self.connection = None
        self.key_dict = {}
        self.mojo_per_unit = 100000000

    async def connect(self, wallet_index: int = 0) -> None:
        config = load_config(Path(DEFAULT_ROOT_PATH), "config.yaml")
        rpc_host = config["self_hostname"]
        full_node_rpc_port = config["full_node"]["rpc_port"]
        wallet_rpc_port = config["wallet"]["rpc_port"]
        if not self.node_client:
            self.node_client = await FullNodeRpcClient.create(
                rpc_host, uint16(full_node_rpc_port), Path(DEFAULT_ROOT_PATH), config
            )
        if not self.wallet_client:
            self.wallet_client = await WalletRpcClient.create(
                rpc_host, uint16(wallet_rpc_port), Path(DEFAULT_ROOT_PATH), config
            )
        self.connection = await aiosqlite.connect(Path(self.db_name))
        self.db_wrapper = DBWrapper(self.connection)
        self.masternode_wallet = await MasterNodeWallet.create(self.db_wrapper, self.node_client)
        self.fingerprints = await self.wallet_client.get_public_keys()
        fp = self.fingerprints[wallet_index]
        private_key = await self.wallet_client.get_private_key(fp)
        sk_data = binascii.unhexlify(private_key["sk"])
        self.master_sk = PrivateKey.from_bytes(sk_data)
        await self.derive_nft_keys()
        await self.derive_wallet_keys()
        await self.derive_unhardened_keys()

    async def checkSyncedStatus(self) -> None:
        checkSyncedStatus = 0
        blockchain_state = await self.node_client.get_blockchain_state()
        if blockchain_state is None:
            print("There is no blockchain found yet. Try again shortly")
            await self.close()
            return checkSyncedStatus
        peak: Optional[BlockRecord] = blockchain_state["peak"]
        node_id = blockchain_state["node_id"]
        difficulty = blockchain_state["difficulty"]
        sub_slot_iters = blockchain_state["sub_slot_iters"]
        synced = blockchain_state["sync"]["synced"]
        sync_mode = blockchain_state["sync"]["sync_mode"]
        total_iters = peak.total_iters if peak is not None else 0
        num_blocks: int = 10
        network_name = config["selected_network"]
        genesis_challenge = config["farmer"]["network_overrides"]["constants"][network_name]["GENESIS_CHALLENGE"]
        full_node_port = config["full_node"]["port"]
        full_node_rpc_port = config["full_node"]["rpc_port"]

        print(f"Network: {network_name}    Port: {full_node_port}   RPC Port: {full_node_rpc_port}")
        print(f"Node ID: {node_id}")
        if synced:
            print("Chives Blockchain Status: Full Node Synced")
            checkSyncedStatus += 1
        elif peak is not None and sync_mode:
            sync_max_block = blockchain_state["sync"]["sync_tip_height"]
            sync_current_block = blockchain_state["sync"]["sync_progress_height"]
            print(
                f"Chives Blockchain Status: Syncing {sync_current_block}/{sync_max_block} "
                f"({sync_max_block - sync_current_block} behind)."
            )
            print("Peak: Hash:", peak.header_hash if peak is not None else "")
            print("Masternode require blockchain synced.")
            await self.close()
            return checkSyncedStatus
        elif peak is not None:
            print(f"Chives Blockchain Status: Not Synced. Peak height: {peak.height}")
            await self.close()
            return checkSyncedStatus
        else:
            print("\nSearching for an initial chain\n")
            print("You may be able to expedite with 'chives show -a host:port' using a known node.\n")
            await self.close()
            return checkSyncedStatus
        
        #######################################################
        is_synced: bool = await self.wallet_client.get_synced()
        is_syncing: bool = await self.wallet_client.get_sync_status()

        print(f"Chives Wallet height: {await self.wallet_client.get_height_info()}")
        if is_syncing:
            print("Chives Wallet Sync Status: Syncing...")
            await self.close()
            return checkSyncedStatus
        elif is_synced:
            print("Chives Wallet Sync Status: Synced")
            checkSyncedStatus += 1
        else:
            print("Chives Wallet Sync Status: Not synced")
            await self.close()
            return checkSyncedStatus
        print('-'*64)
        return checkSyncedStatus


    async def close(self) -> None:
        if self.node_client:
            self.node_client.close()

        if self.wallet_client:
            self.wallet_client.close()

        if self.connection:
            await self.connection.close()

    async def sync(self) -> None:
        await self.masternode_wallet.sync_masternode()

    async def derive_nft_keys(self, index: int = 0) -> None:
        _sk = master_sk_to_singleton_owner_sk(self.master_sk, index)
        synth_sk = calculate_synthetic_secret_key(_sk, INNER_MOD.get_tree_hash())
        self.key_dict[bytes(synth_sk.get_g1())] = synth_sk
        self.nft_sk = synth_sk
        self.nft_pk = synth_sk.get_g1()

    async def derive_wallet_keys(self, index=0):
        _sk = master_sk_to_wallet_sk(self.master_sk, index)
        synth_sk = calculate_synthetic_secret_key(_sk, DEFAULT_HIDDEN_PUZZLE_HASH)
        self.key_dict[bytes(synth_sk.get_g1())] = synth_sk
        self.key_dict[bytes(_sk.get_g1())] = _sk
        self.wallet_sk = _sk

    async def derive_unhardened_keys(self, n=10):
        for i in range(n):
            #_sk = AugSchemeMPL.derive_child_sk_unhardened(self.master_sk, i) #  TESTING on main branch
            _sk = master_sk_to_wallet_sk_unhardened(self.master_sk, i)  # protocol_and_cats_branch
            synth_sk = calculate_synthetic_secret_key(_sk, DEFAULT_HIDDEN_PUZZLE_HASH)
            self.key_dict[bytes(_sk.get_g1())] = _sk
            self.key_dict[bytes(synth_sk.get_g1())] = synth_sk

    async def pk_to_sk(self, pk):
        return self.key_dict.get(bytes(pk))

    async def available_balance(self) -> int:
        balance_data = await self.wallet_client.get_wallet_balance(1)
        return balance_data["confirmed_wallet_balance"]

    async def choose_std_coin(self, amount: int) -> Tuple[Coin, Program]:
        # check that wallet_balance is greater than amount
        assert await self.available_balance() > amount
        for k in self.key_dict.keys():
            puzzle = puzzle_for_pk(k)
            my_coins = await self.node_client.get_coin_records_by_puzzle_hash(
                puzzle.get_tree_hash(), include_spent_coins=False
            )
            if my_coins:
                coin_record = next((cr for cr in my_coins if (cr.coin.amount >= amount) and (not cr.spent)), None)
                if coin_record:
                    assert not coin_record.spent
                    assert coin_record.coin.puzzle_hash == puzzle.get_tree_hash()
                    synth_sk = calculate_synthetic_secret_key(self.key_dict[k], DEFAULT_HIDDEN_PUZZLE_HASH)
                    self.key_dict[bytes(synth_sk.get_g1())] = synth_sk
                    return (coin_record.coin, puzzle)
        raise ValueError("No spendable coins found")

    async def launch_staking_storage(self) -> bytes:    
        blockchain_state = await self.node_client.get_blockchain_state()
        if blockchain_state is None:
            print("There is no blockchain found yet. Try again shortly")
            return None
        new_height = blockchain_state["peak"].height
        node_id = blockchain_state["node_id"]
        synced = blockchain_state["sync"]["synced"]
        sync_mode = blockchain_state["sync"]["sync_mode"]        
        
        #Create MasterNode NFT Must Have Staking Coin.            
        get_staking_address = self.masternode_wallet.get_staking_address();
        StakingData = {}
        StakingData['ReceivedAddress'] = get_staking_address['first_address'];
        StakingData['StakingAddress'] = get_staking_address['address'];
        StakingData['StakingAmount'] = get_staking_address['StakingAmount'];
        StakingData['NodeName'] = blockchain_state["node_id"];      
        IsStakingCoin = False;
        all_staking_coins = await self.node_client.get_coin_records_by_puzzle_hash(get_staking_address['puzzle_hash'],False)
        for coin_record in all_staking_coins:
            stakingAmount = coin_record.coin.amount;
            if stakingAmount == StakingData['StakingAmount'] * 100000000 :
                IsStakingCoin = True;
        if IsStakingCoin == False:
            return ("No finish staking coin","No finish staking coin");
        
        dataJsonText = json.dumps(StakingData)       
        nft_data = ("MasterNodeNFT", dataJsonText)
        
        amount = 101
        launch_state = [0, 9699]
        royalty = [0]
        
        addr = await self.wallet_client.get_next_address(1, False)
        puzzle_hash = decode_puzzle_hash(addr)
        launch_state += [puzzle_hash, self.nft_pk]
        royalty.insert(0, puzzle_hash)

        found_coin, found_coin_puzzle = await self.choose_std_coin(amount)

        launcher_coin = Coin(found_coin.name(), LAUNCHER_PUZZLE_HASH, amount)

        launcher_spend = make_launcher_spend(found_coin, amount, launch_state, royalty, nft_data)
        found_spend = make_found_spend(found_coin, found_coin_puzzle, launcher_spend, amount)
        eve_spend = make_eve_spend(launch_state, royalty, launcher_spend)

        sb = await sign_coin_spends(
            [launcher_spend, found_spend, eve_spend],
            self.pk_to_sk,
            DEFAULT_CONSTANTS.AGG_SIG_ME_ADDITIONAL_DATA,
            DEFAULT_CONSTANTS.MAX_BLOCK_COST_CLVM,
        )

        res = await self.node_client.push_tx(sb)
        if res["success"]:
            # add launcher_id and pk to masternode_list
            await self.masternode_wallet.save_launcher(launcher_coin.name(), self.nft_pk, 0, StakingData)
            tx_id = await self.get_tx_from_mempool(sb.name())
            return (tx_id, launcher_coin.name())

    async def get_tx_from_mempool(self, sb_name):
        # get mempool txn
        mempool_items = await self.node_client.get_all_mempool_items()
        for tx_id in mempool_items.keys():
            mem_sb_name = bytes32(hexstr_to_bytes(mempool_items[tx_id]["spend_bundle_name"]))
            if mem_sb_name == sb_name:
                return tx_id
        raise ValueError("No tx found in mempool. Check if confirmed")
    
    def check_unusual_transaction(self, amount: Decimal, fee: Decimal):
        return fee >= amount

    async def get_wallet_type(self, wallet_id: int, wallet_client: WalletRpcClient) -> WalletType:
        summaries_response = await wallet_client.get_wallets()
        for summary in summaries_response:
            summary_id: int = summary["id"]
            summary_type: int = summary["type"]
            if wallet_id == summary_id:
                return WalletType(summary_type)
        raise LookupError(f"Wallet ID not found: {wallet_id}")
        
    def print_masternode(self, nft,counter):
        print("-" * 64)
        if counter>0:
            print(f"ID:  {counter}")
        print(f"MasterNode NFT:  {nft.launcher_id.hex()}")
        print(f"Chialisp:        {str(nft.data[0].decode('utf-8'))}")
        StakingData = nft.StakingData
        StakingAmount = StakingData['stakingAmount']
        print(f"StakingAddress:  {StakingData['StakingAddress']}")
        if StakingAmount>0:
            print(f"StakingAmount:   {round(Decimal(StakingAmount/self.mojo_per_unit),8)}")
        else:
            print(f"StakingAmount:   0")

        print(f"ReceivedAddress: {StakingData['ReceivedAddress']}")
        #print(f"All Data:")
        print("-" * 64)
        print("\n")

    async def masternode_list(self, args: dict, wallet_client: WalletRpcClient, fingerprint: int) -> None:
        nfts = await self.get_all_masternodes()
        counter = 0
        for nft in nfts:
            counter += 1
            self.print_masternode(nft,counter)

    async def masternode_merge(self, args: dict, wallet_client: WalletRpcClient, fingerprint: int) -> None:
        wallet_id: int = 1
        mojo_per_unit = self.mojo_per_unit
        balances = await wallet_client.get_wallet_balance(wallet_id)
        if balances["max_send_amount"]>0:
            max_send_amount = round(Decimal(balances["max_send_amount"]/mojo_per_unit),8)
        else:
            max_send_amount = 0
        if balances["confirmed_wallet_balance"]>0:
            confirmed_wallet_balance = round(Decimal(balances["confirmed_wallet_balance"]/mojo_per_unit),8)
        else:
            confirmed_wallet_balance = 0
        fee = 1
        override = False
        memo = "Merge coin for MasterNode"
        get_staking_address_result = self.masternode_wallet.get_staking_address()
        address = get_staking_address_result['address']
        amount = max_send_amount
        #Staking Amount
        stakingCoinAmount = 100000
        #print(balances)
        #print(get_staking_address_result)
        #To check is or not have this staking coin record
        isHaveStakingCoin = False
        StakingAccountAmount = 0
        get_target_xcc_coin_result = await self.get_target_xcc_coin(args,wallet_client,fingerprint,mojo_per_unit,address)
        #print(get_target_xcc_coin_result)
        if get_target_xcc_coin_result is not None:
            for target_xcc_coin in get_target_xcc_coin_result:
                StakingAccountAmount += target_xcc_coin.coin.amount
                if target_xcc_coin.coin.amount == stakingCoinAmount * mojo_per_unit:
                    isHaveStakingCoin = True
        #print(balances);
        print(f"")
        print(f"Wallet Balance:             {confirmed_wallet_balance}");
        print(f"Wallet Max Sent:            {max_send_amount} (Must more than {stakingCoinAmount} XCC)");
        print(f"Wallet Address:             {get_staking_address_result['first_address']}");
        print(f"")
        
        if isHaveStakingCoin is True:
            print("You have staking coins. Not need to merge coin again.");
            print("")
            return None
        
        #Wallet balance must more than 100000 XCC
        if confirmed_wallet_balance < (stakingCoinAmount+fee):
            print(f"Wallet confirmed balance must more than {(stakingCoinAmount+fee)} XCC. Need extra {fee} xcc as miner fee.");
            print("")
            return None
        
        #最大发送金额超过100000 XCC
        if max_send_amount >= (stakingCoinAmount+fee):
            print(f"Wallet Max Sent Amount have more than {(stakingCoinAmount+fee)} XCC, not need to merge coins");
            print("")
            return None
            
        #Merge small amount coins
        #print(f"max_send_amount:{max_send_amount}")
        if max_send_amount>fee and max_send_amount < (stakingCoinAmount+fee) and isHaveStakingCoin == False:
            amount = max_send_amount-fee;
            address = get_staking_address_result['first_address']
            memos = ["Merge coin for MasterNode"]
            if not override and self.check_unusual_transaction(amount, fee):
                print(
                    f"A transaction of amount {amount} and fee {fee} is unusual.\n"
                    f"Pass in --override if you are sure you mean to do this."
                )
                return
            try:
                typ = await self.get_wallet_type(wallet_id=wallet_id, wallet_client=wallet_client)
            except LookupError:
                print(f"Wallet id: {wallet_id} not found.")
                print("")
                return
            final_fee = uint64(int(fee * units["chives"]))
            final_amount: uint64
            if typ == WalletType.STANDARD_WALLET:
                final_amount = uint64(int(amount * units["chives"]))
                print("Merge coin for MasterNode Submitting transaction...")
                print("")
                res = await wallet_client.send_transaction(str(wallet_id), final_amount, address, final_fee, memos)
            else:
                print("Only standard wallet is supported")
                print("")
                return
            tx_id = res.name
            start = time.time()
            while time.time() - start < 10:
                await asyncio.sleep(0.1)
                tx = await wallet_client.get_transaction(str(wallet_id), tx_id)
                if len(tx.sent_to) > 0:
                    print(f"Merge coin for MasterNode Transaction submitted to nodes: {tx.sent_to}")
                    print(f"fingerprint {fingerprint} tx 0x{tx_id} to address: {address}")
                    print("Waiting for block (180s). Do not quit.")
                    await asyncio.sleep(180)
                    print(f"finish to submit blockchain")
                    print("")
                    return None
            print("Merge coin for MasterNode not yet submitted to nodes")
            print(f"tx 0x{tx_id} ")
            print("")
    
    async def masternode_staking(self, args: dict, wallet_client: WalletRpcClient, fingerprint: int) -> None:
        jsonResult = await self.masternode_staking_json(args, wallet_client, fingerprint)
        self.printJsonResult(jsonResult)

    async def masternode_staking_json(self, args: dict, wallet_client: WalletRpcClient, fingerprint: int) -> None:
        wallet_id: int = 1
        mojo_per_unit = self.mojo_per_unit
        balances = await wallet_client.get_wallet_balance(wallet_id)
        if balances["max_send_amount"]>0:
            max_send_amount = round(Decimal(balances["max_send_amount"]/mojo_per_unit),8)
        else:
            max_send_amount = 0
        if balances["confirmed_wallet_balance"]>0:
            confirmed_wallet_balance = round(Decimal(balances["confirmed_wallet_balance"]/mojo_per_unit),8)
        else:
            confirmed_wallet_balance = 0
        fee = 1
        override = False
        memo = "Merge coin for MasterNode"
        get_staking_address_result = self.masternode_wallet.get_staking_address()
        address = get_staking_address_result['address']
        StakingAddress = address
        amount = max_send_amount
        #Staking Amount
        stakingCoinAmount = 100000
        #print(balances)
        #print(get_staking_address_result)
        # #################################################################
        # get mempool txn to check current staking address is or not in the txn.
        config = load_config(DEFAULT_ROOT_PATH, "config.yaml")
        self_hostname = config["self_hostname"]
        rpc_port = config["full_node"]["rpc_port"]
        selected = config["selected_network"]
        prefix = config["network_overrides"]["config"][selected]["address_prefix"]
        # All txn in mempool
        all_address_in_mempool = []
        mempool_items = await self.node_client.get_all_mempool_items()
        for tx_id in mempool_items.keys():
            mem_sb_name = bytes32(hexstr_to_bytes(mempool_items[tx_id]["spend_bundle_name"]))
            additions = mempool_items[tx_id]['additions']
            for coin in additions:
                address_mempool = encode_puzzle_hash(hexstr_to_bytes(coin['puzzle_hash']),prefix)
                all_address_in_mempool.append(address_mempool)
                #print(address_mempool)
                #print(coin['puzzle_hash'])
                #print(coin['amount'])
        #print("=====================================================")
        #print(all_address_in_mempool)
        #print(StakingAddress)
        #return None
        
        # To check is or not have this staking coin record
        isHaveStakingCoin = False
        StakingAccountAmount = 0
        StakingAccountAmountCoin = '0'

        if StakingAddress in all_address_in_mempool:
            isHaveStakingCoin = True
            StakingAccountAmountCoin = "Wait block to generate..."

        if isHaveStakingCoin is False:
            get_target_xcc_coin_result = await self.get_target_xcc_coin(args,wallet_client,fingerprint,mojo_per_unit,address)
            #print(get_target_xcc_coin_result)
            if get_target_xcc_coin_result is not None:
                for target_xcc_coin in get_target_xcc_coin_result:
                    StakingAccountAmount += target_xcc_coin.coin.amount
                    if target_xcc_coin.coin.amount == stakingCoinAmount * mojo_per_unit:
                        isHaveStakingCoin = True
                StakingAccountAmountCoin = StakingAccountAmount/mojo_per_unit
        #print(balances);
        jsonResult = {}
        jsonResult['status'] = "success"
        jsonResult['title'] = "Chvies Masternode Staking Information:"
        jsonResult['data'] = []
        jsonResult['data'].append({"":""})
        jsonResult['data'].append({"Wallet Balance":confirmed_wallet_balance})
        jsonResult['data'].append({"Wallet Max Sent":max_send_amount})
        jsonResult['data'].append({"Wallet Address":get_staking_address_result['first_address']})
        jsonResult['data'].append({"":""})
        jsonResult['data'].append({"Staking Address":get_staking_address_result['address']})
        jsonResult['data'].append({"Staking Account Balance":StakingAccountAmount/self.mojo_per_unit})
        jsonResult['data'].append({"Staking Account Status":isHaveStakingCoin})
        jsonResult['data'].append({"Staking Cancel Address":get_staking_address_result['first_address']})

        if isHaveStakingCoin is True:
            jsonResult['data'].append({"You have staking coins. Not need to stake coin again.":""})
            jsonResult['data'].append({"":""})
            return jsonResult
            
        #Wallet balance must more than 100000 XCC
        if confirmed_wallet_balance < (stakingCoinAmount+fee):
            jsonResult['data'].append({"Wallet confirmed balance must more than":{(stakingCoinAmount+fee)}})
            jsonResult['data'].append({"":""})
            return jsonResult
            
        #Merge small amount coins
        #print(f"max_send_amount:{max_send_amount}")
        if max_send_amount < (stakingCoinAmount+fee) and isHaveStakingCoin == False and 1:
            self.merge(args, wallet_client, fingerprint)
        
        #STAKING COIN
        if max_send_amount >= (stakingCoinAmount+fee) and isHaveStakingCoin == False and 1:
            amount = stakingCoinAmount
            address = get_staking_address_result['address']
            memos = ["Staking coin for MasterNode"]
            if not override and self.check_unusual_transaction(amount, fee):
                jsonResult['data'].append({"":""})
                jsonResult['data'].append({f"A transaction of amount {amount} and fee {fee} is unusual":""})
                jsonResult['data'].append({"Pass in --override if you are sure you mean to do this.":""})
                return jsonResult
            try:
                typ = await self.get_wallet_type(wallet_id=wallet_id, wallet_client=wallet_client)
            except LookupError:
                jsonResult['data'].append({"":""})
                jsonResult['data'].append({f"Wallet id: {wallet_id} not found.":""})
                return jsonResult
            final_fee = uint64(int(fee * units["chives"]))
            final_amount: uint64
            if typ == WalletType.STANDARD_WALLET:
                final_amount = uint64(int(amount * units["chives"]))
                jsonResult['data'].append({"Staking coin for MasterNode Submitting transaction...":""})
                res = await wallet_client.send_transaction(str(wallet_id), final_amount, address, final_fee, memos)
            else:
                jsonResult['data'].append({"":""})
                jsonResult['data'].append({"Only standard wallet is supported":""})
                return jsonResult

            tx_id = res.name
            start = time.time()
            while time.time() - start < 10:
                await asyncio.sleep(0.1)
                tx = await wallet_client.get_transaction(str(wallet_id), tx_id)
                if len(tx.sent_to) > 0:
                    jsonResult['data'].append({"":""})
                    jsonResult['data'].append({f"Staking coin for MasterNode Transaction submitted to nodes: {tx.sent_to}":""})
                    jsonResult['data'].append({f"fingerprint {fingerprint} tx 0x{tx_id} to address: {address}":""})
                    jsonResult['data'].append({"Waiting for block (180s).Do not quit...":""})                    
                    self.printJsonResult(jsonResult)
                    await asyncio.sleep(180)  
                    jsonResult = {}
                    jsonResult['status'] = "success"
                    jsonResult['title'] = "Chvies Masternode Staking Information:"
                    jsonResult['data'] = []
                    jsonResult['data'].append({f"finish to submit blockchain":""})
                    return jsonResult                
                else:
                    jsonResult = {}
                    jsonResult['status'] = "success"
                    jsonResult['title'] = "Chvies Masternode Staking Information:"
                    jsonResult['data'] = []
                    jsonResult['data'].append({"Waiting for block (180s).Do not quit...":""})
                    return jsonResult

            jsonResult['data'].append({"Staking coin for MasterNode not yet submitted to nodes":""})
            jsonResult['data'].append({"tx":{tx_id}})
            return jsonResult

    async def masternode_cancel(self, args: dict, wallet_client: WalletRpcClient, fingerprint: int) -> None:
        jsonResult = await self.masternode_cancel_json(args, wallet_client, fingerprint)
        self.printJsonResult(jsonResult)

    async def masternode_cancel_json(self, args: dict, wallet_client: WalletRpcClient, fingerprint: int) -> None:
        wallet_id: int = 1
        mojo_per_unit = self.mojo_per_unit        
        balances = await wallet_client.get_wallet_balance(wallet_id)
        if balances["max_send_amount"]>0:
            max_send_amount = round(Decimal(balances["max_send_amount"]/mojo_per_unit),8)
        else:
            max_send_amount = 0
        if balances["confirmed_wallet_balance"]>0:
            confirmed_wallet_balance = round(Decimal(balances["confirmed_wallet_balance"]/mojo_per_unit),8)
        else:
            confirmed_wallet_balance = 0
        fee = 1
        override = False
        memo = "Merge coin for MasterNode"
        get_staking_address_result = self.masternode_wallet.get_staking_address()
        address = get_staking_address_result['address']
        amount = max_send_amount
        
        #Staking Amount
        stakingCoinAmount = 100000
        
        #print(balances)
        #print(get_staking_address_result)
        
        #To check is or not have this staking coin record
        isHaveStakingCoin = False
        StakingAccountAmount = 0
        get_target_xcc_coin_result = await self.get_target_xcc_coin(args,wallet_client,fingerprint,mojo_per_unit,address)
        #print(get_target_xcc_coin_result)
        if get_target_xcc_coin_result is not None:
            for target_xcc_coin in get_target_xcc_coin_result:
                StakingAccountAmount += target_xcc_coin.coin.amount
                if target_xcc_coin.coin.amount == stakingCoinAmount * mojo_per_unit:
                    isHaveStakingCoin = True;
        
        jsonResult = {}
        jsonResult['status'] = "success"
        jsonResult['title'] = "Chvies Masternode Cancel Information:"
        jsonResult['data'] = []
        jsonResult['data'].append({"":""})
        jsonResult['data'].append({"Wallet Balance":confirmed_wallet_balance})
        jsonResult['data'].append({"Wallet Max Sent":max_send_amount})
        jsonResult['data'].append({"Wallet Address":get_staking_address_result['first_address']})
        jsonResult['data'].append({"":""})
        jsonResult['data'].append({"Staking Address":get_staking_address_result['address']})
        jsonResult['data'].append({"Staking Account Balance":StakingAccountAmount/self.mojo_per_unit})
        jsonResult['data'].append({"Staking Account Status":isHaveStakingCoin})
        jsonResult['data'].append({"Staking Cancel Address":get_staking_address_result['first_address']})
        jsonResult['data'].append({"":""})
        
        #取消质押
        if isHaveStakingCoin is True:
            jsonResult['data'].append({"Cancel staking coin for MasterNode Submitting transaction...":""})
            await self.cancel_masternode_staking_coins()
            jsonResult['data'].append({"Canncel staking coins for MasterNode have submitted to nodes":""})
            jsonResult['data'].append({"You have canncel staking coins. Waiting 1-3 minutes, will see your coins in wallet.":""})
            jsonResult['data'].append({"":""})
        else:
            jsonResult['data'].append({"You have not staking coins":""})
            jsonResult['data'].append({"":""})
        return jsonResult

    async def masternode_register(self, args: dict, wallet_client: WalletRpcClient, fingerprint: int) -> None:
        jsonResult = await self.masternode_register_json(args, wallet_client, fingerprint)
        self.printJsonResult(jsonResult)

    async def masternode_register_json(self, args: dict, wallet_client: WalletRpcClient, fingerprint: int) -> None:
        #First step to check staking address is or not in database
        get_staking_address_result = self.masternode_wallet.get_staking_address()
        staking_address = get_staking_address_result['address']

        print(staking_address)
        query = f"SELECT launcher_id FROM masternode_list WHERE StakingAddress = ?"
        cursor = await self.masternode_wallet.db_connection.execute(query, (staking_address,))
        rows = await cursor.fetchone()
        await cursor.close()
        staking_launcher_id = None
        if rows is not None and len(rows)>0 and rows[0] is not None and 0:
            staking_launcher_id = rows[0]
            await self.masternode_show(args, wallet_client, fingerprint)
        else:        
            #Second step: if staking address is not in database, will start a new nft mint process to finish the register
            tx_id, launcher_id = await self.launch_staking_storage()
            if tx_id is not None and len(tx_id)>=32:
                nft = await self.wait_for_confirmation(tx_id, launcher_id)
                self.print_masternode(nft,0)
                jsonResult = {}
                jsonResult['status'] = "success"
                jsonResult['title'] = "Chvies Masternode Register Success"
                jsonResult['data'] = []
                jsonResult['data'].append({"":""})
                jsonResult['data'].append({"Transaction id":tx_id})
                jsonResult['data'].append({"launcher_id":launcher_id})
                jsonResult['data'].append({"result":"stake NFT Launched!!"})
                return jsonResult
            else:
                print(f"Error: {tx_id}")
                jsonResult = {}
                jsonResult['status'] = "error"
                jsonResult['title'] = "Chvies Masternode Register Trip"
                jsonResult['data'] = []
                jsonResult['data'].append({"":""})
                jsonResult['data'].append({"Error":tx_id})
                return jsonResult

    async def get_target_xcc_coin(self, args: dict, wallet_client: WalletRpcClient, fingerprint: int, mojo_per_unit: int, address: str) -> None:
        get_staking_address_result = self.masternode_wallet.get_staking_address()
        staking_coins = await self.node_client.get_coin_records_by_puzzle_hash(get_staking_address_result['puzzle_hash'], include_spent_coins=False)       
        if staking_coins:
            return staking_coins
        else:
            return None

    async def masternode_show(self, args: dict, wallet_client: WalletRpcClient, fingerprint: int) -> None:
        jsonResult = await self.masternode_show_json(args, wallet_client, fingerprint)
        self.printJsonResult(jsonResult)

    async def masternode_show_json(self, args: dict, wallet_client: WalletRpcClient, fingerprint: int) -> None:
        mojo_per_unit = self.mojo_per_unit
        wallet_id: int = 1
        balances = await wallet_client.get_wallet_balance(wallet_id)
        if balances["max_send_amount"]>0:
            max_send_amount = round(Decimal(balances["max_send_amount"]/mojo_per_unit),8)
        else:
            max_send_amount = 0
        if balances["confirmed_wallet_balance"]>0:
            confirmed_wallet_balance = round(Decimal(balances["confirmed_wallet_balance"]/mojo_per_unit),8)
        else:
            confirmed_wallet_balance = 0
        fee = 1
        override = False
        get_staking_address_result = self.masternode_wallet.get_staking_address()
        address = get_staking_address_result['address']
        amount = max_send_amount
        
        #Staking Amount
        stakingCoinAmount = 100000
        
        #print(balances)
        #print(get_staking_address_result)
        
        #To check is or not have this staking coin record
        isHaveStakingCoin = False
        StakingAccountAmount = 0
        get_target_xcc_coin_result = await self.get_target_xcc_coin(args,wallet_client,fingerprint,self.mojo_per_unit,address)
        #print(get_target_xcc_coin_result)
        if get_target_xcc_coin_result is not None:
            for target_xcc_coin in get_target_xcc_coin_result:
                StakingAccountAmount += target_xcc_coin.coin.amount
                if target_xcc_coin.coin.amount == stakingCoinAmount * self.mojo_per_unit:
                    isHaveStakingCoin = True
        #print(balances);

        jsonResult = {}
        jsonResult['status'] = "success"
        jsonResult['title'] = "Chvies Masternode Staking Information:"
        jsonResult['data'] = []
        jsonResult['data'].append({"":""})
        jsonResult['data'].append({"Wallet Balance":confirmed_wallet_balance})
        jsonResult['data'].append({"Wallet Max Sent":max_send_amount})
        jsonResult['data'].append({"Wallet Address":get_staking_address_result['first_address']})
        jsonResult['data'].append({"":""})
        jsonResult['data'].append({"Staking Address":get_staking_address_result['address']})
        jsonResult['data'].append({"Staking Account Balance":StakingAccountAmount/self.mojo_per_unit})
        jsonResult['data'].append({"Staking Account Status":isHaveStakingCoin})
        jsonResult['data'].append({"Staking Cancel Address":get_staking_address_result['first_address']})
        return jsonResult
    
    def printJsonResult(self,jsonResult):
        if jsonResult:
            print("")
            print("Status:"+jsonResult['status'])
            print(jsonResult['title'])
            for item in jsonResult['data']:
                for left,right in item.items():
                    if right == "":
                        print(left)
                    elif right == "" and left == "":
                        print("")
                    else:
                        print(str(left) +" : "+ str(right))
            print("")

    async def wait_for_confirmation(self, tx_id, launcher_id):
        while True:
            item = await self.node_client.get_mempool_item_by_tx_id(tx_id)
            if not item:
                return await self.masternode_wallet.get_nft_by_launcher_id(launcher_id)
            else:
                print("Waiting for block (30s)")
                await asyncio.sleep(30)
    
    async def wait_tx_for_confirmation(self, tx_id):
        while True:
            item = await self.node_client.get_mempool_item_by_tx_id(tx_id)
            if not item:
                print(f"wait_tx_for_confirmation: {item}")
            else:
                print("Waiting for block (30s)")
                await asyncio.sleep(30)

    async def get_all_masternodes(self) -> List:
        launcher_ids = await self.masternode_wallet.get_all_nft_ids()
        get_all_masternodes = []
        for launcher_id in launcher_ids:            
            nft = await self.masternode_wallet.get_nft_by_launcher_id(hexstr_to_bytes(launcher_id))
            get_all_masternodes.append(nft)
        return get_all_masternodes
    
    async def cancel_masternode_staking_coins(self) -> List:
        cancel_staking_coins = await self.masternode_wallet.cancel_staking_coins()
        print(f"cancel_staking_coins:{cancel_staking_coins}")


class MasterNodeCoin(Coin):
    def __init__(self, launcher_id: bytes32, coin: Coin, last_spend: CoinSpend = None, nft_data=None, royalty=None, StakingData=None):
        super().__init__(coin.parent_coin_info, coin.puzzle_hash, coin.amount)
        self.launcher_id = launcher_id
        self.last_spend = last_spend
        self.data = nft_data
        self.StakingData = StakingData
        self.royalty = royalty
        #MASTERNODE属性信息
        self.Height = 0
        self.StakingAmount = 0
        self.StakingAddress = ""
        self.ReceivedAddress = ""
        self.NodeName = ""
        self.NodeOnline = ""
        self.NodeStatus = ""
        self.NodeIPAddress = ""
        self.NodeIPPort = ""
        self.Memo = ""

    def conditions(self):
        if self.last_spend:
            return conditions_dict_for_solution(
                self.last_spend.puzzle_reveal.to_program(), self.last_spend.solution.to_program()
            )

    def as_coin(self):
        return Coin(self.parent_coin_info, self.puzzle_hash, self.amount)

    def state(self):
        mod, args = self.last_spend.solution.to_program().uncurry()
        return mod.as_python()[-1][0]
        
    def is_master_node(self):
        if int_from_bytes(self.state()[0]) == 0:
            return True
            
    def owner_pk(self):
        return self.state()[-1]

    def owner_fingerprint(self):
        return G1Element(self.owner_pk()).get_fingerprint()

    def owner_puzzle_hash(self):
        return self.state()[-2]

    def price(self):
        return int_from_bytes(self.state()[1])

class MasterNodeWallet:
    db_connection: aiosqlite.Connection
    db_wrapper: DBWrapper
    _state_transitions_cache: Dict[int, List[Tuple[uint32, CoinSpend]]]

    key_dict = {}
    key_dict_synth_sk = {}
    puzzle_for_puzzle_hash = {}
    puzzlehash_to_privatekey = {}
    puzzlehash_to_publickey = {}
    secret_key_store = SecretKeyStore()

    @classmethod
    async def create(cls, wrapper: DBWrapper, node_client):
        self = cls()

        self.db_connection = wrapper.db
        self.db_wrapper = wrapper
        self.node_client = node_client

        await self.db_connection.execute(
            """CREATE TABLE IF NOT EXISTS
                 nft_state_transitions(transition_index integer,
                                       wallet_id integer,
                                       height bigint,
                                       coin_spend blob,
                                       PRIMARY KEY(transition_index, wallet_id))"""
        )
        
        await self.db_connection.execute(
            """CREATE TABLE IF NOT EXISTS
                 masternode_rewards (
                            launcher_id char(64),
                            owner_pk char(96),
                            Height bigint,
                            TotalAmount bigint,
                            TotalNodes bigint,
                            RewardCoinname char(64) PRIMARY KEY,
                            StakingAddress varchar(96),
                            ReceivedAddress varchar(96),
                            IncludeMySelf int,
                            Memo text
                           )"""
        )
        await self.db_connection.execute(
            """CREATE INDEX IF NOT EXISTS launcher_id_index on masternode_rewards(launcher_id)"""
        )
        await self.db_connection.execute(
            """CREATE INDEX IF NOT EXISTS owner_pk_index on masternode_rewards(owner_pk)"""
        )
        await self.db_connection.execute(
            """CREATE INDEX IF NOT EXISTS ReceivedAddress_index on masternode_rewards(ReceivedAddress)"""
        )
        await self.db_connection.execute(
            """CREATE INDEX IF NOT EXISTS StakingAddress_index on masternode_rewards(StakingAddress)"""
        )
        await self.db_connection.execute(
            """CREATE INDEX IF NOT EXISTS IncludeMySelf_index on masternode_rewards(IncludeMySelf)"""
        )

        await self.db_connection.execute(
            """CREATE TABLE IF NOT EXISTS
                 masternode_list (
                            launcher_id varchar(64),
                            owner_pk varchar(96),
                            Height bigint,
                            StakingAmount bigint,
                            StakingAddress varchar(96) PRIMARY KEY,
                            ReceivedAddress varchar(96),
                            NodeName varchar(96),
                            NodeOnline varchar(96),
                            NodeStatus varchar(96),
                            NodeLastReceivedAmount bigint,
                            NodeLastReceivedTime varchar(64),
                            NodeIPAddress varchar(64),
                            NodeIPPort varchar(6),
                            Memo text
                           )"""
        )
        await self.db_connection.execute(
            """CREATE INDEX IF NOT EXISTS owner_pk_index on masternode_list(owner_pk)"""
        )
        await self.db_connection.execute(
            """CREATE INDEX IF NOT EXISTS StakingAmount_index on masternode_list(StakingAmount)"""
        )
        await self.db_connection.execute(
            """CREATE INDEX IF NOT EXISTS ReceivedAddress_index on masternode_list(ReceivedAddress)"""
        )
        await self.db_connection.execute(
            """CREATE INDEX IF NOT EXISTS NodeOnline_index on masternode_list(NodeOnline)"""
        )
        await self.db_connection.execute(
            """CREATE INDEX IF NOT EXISTS NodeStatus_index on masternode_list(NodeStatus)"""
        )

        await self.db_connection.commit()

        return self

    async def _clear_database(self):
        cursor = await self.db_connection.execute("DELETE FROM masternode_rewards")
        cursor = await self.db_connection.execute("DELETE FROM masternode_list")
        await cursor.close()
        await self.db_connection.commit()

    async def get_current_height_from_node(self):
        blockchain_state = await self.node_client.get_blockchain_state()
        new_height = blockchain_state["peak"].height
        return new_height
        
    async def filter_singletons(self, singletons: List):
        print(f"Updating {len(singletons)} CreatorNFTs")
        #print(Path(DEFAULT_ROOT_PATH))
        for cr in singletons:
            await self.get_nft_by_launcher_id(cr.coin.name())
                        
    async def get_nft_by_launcher_id(self, launcher_id: bytes32):
        eve_cr = await self.node_client.get_coin_records_by_parent_ids([launcher_id])
        assert len(eve_cr) > 0
        if eve_cr[0].spent:
            eve_spend = await self.node_client.get_puzzle_and_solution(
                eve_cr[0].coin.name(), eve_cr[0].spent_block_index
            )
            # uncurry the singletons inner puzzle
            _, args = eve_spend.puzzle_reveal.to_program().uncurry()
            _, inner_puzzle = list(args.as_iter())
            mod, _ = inner_puzzle.uncurry()
            if mod.get_tree_hash() == INNER_MOD.get_tree_hash():
                mod, _ = eve_spend.solution.to_program().uncurry()
                state = mod.as_python()[-1][0]
                #launcher_id = cr.coin.name()
                launcher_rec = await self.node_client.get_coin_record_by_name(launcher_id)
                if launcher_rec is None:
                    return None;
                launcher_spend = await self.node_client.get_puzzle_and_solution(
                    launcher_rec.coin.name(), launcher_rec.spent_block_index
                )
                nft_data = launcher_spend.solution.to_program().uncurry()[0].as_python()[-1]
                if nft_data is not None and len(nft_data)==2 and nft_data[0]==b"MasterNodeNFT":
                    try:
                        NftDataJson = json.loads(nft_data[1].decode("utf-8"))
                        #print(NftDataJson)
                        if "ReceivedAddress" in NftDataJson and "StakingAddress" in NftDataJson and "StakingAmount" in NftDataJson and "NodeName" in NftDataJson:
                            StakingData = await self.save_launcher(launcher_id, state[-1], eve_cr[0].spent_block_index, NftDataJson)
                            MasterNode = MasterNodeCoin(launcher_id, launcher_rec.coin, launcher_spend, nft_data, 0, StakingData)
                            return MasterNode
                        #else:
                        #    print("NftDataJson Json Format Error.")
                    except Exception as e:
                        print(e)
 
    async def sync_masternode(self):
        all_nfts = await self.node_client.get_coin_records_by_puzzle_hash(LAUNCHER_PUZZLE_HASH)
        await self.filter_singletons(all_nfts)

    async def save_launcher(self, launcher_id, pk, Height, StakingData):
        if "StakingAddress" in StakingData and StakingData['StakingAddress'] is not None:
            all_staking_coins = await self.node_client.get_coin_records_by_puzzle_hash(decode_puzzle_hash(StakingData['StakingAddress']),False)
            stakingAmount = 0
            for coin_record in all_staking_coins:
                stakingAmount += coin_record.coin.amount
        #print(f"stakingAmount:{stakingAmount}")
        #print(f"stakingAmount:{StakingData['StakingAddress']}")
        
        cursor = await self.db_connection.execute(
            "INSERT OR REPLACE INTO masternode_list (launcher_id, owner_pk, Height, ReceivedAddress, StakingAddress, StakingAmount, NodeName) VALUES (?,?,?,?,?,?,?)", (
            str(bytes(launcher_id).hex()), 
            str(bytes(pk).hex()),
            int(Height),
            str(StakingData['ReceivedAddress']),
            str(StakingData['StakingAddress']),
            int(stakingAmount),
            str(StakingData['NodeName'])
            )
        )
        #print(f"save_launcher:{StakingData}")
        await cursor.close()
        await self.db_connection.commit()

        StakingData['stakingAmount'] = stakingAmount
        return StakingData

    async def get_all_nft_ids(self):
        query = "SELECT launcher_id FROM masternode_list"
        cursor = await self.db_connection.execute(query)
        rows = await cursor.fetchall()
        await cursor.close()
        return list(map(lambda x: x[0], rows))

    async def get_nft_ids_by_pk(self, pk: G1Element = None):
        query = f"SELECT launcher_id FROM masternode_list WHERE owner_pk = ?"
        cursor = await self.db_connection.execute(query, (bytes(pk),))
        rows = await cursor.fetchall()
        await cursor.close()
        return list(map(lambda x: x[0], rows))
        
    def get_staking_address(self):
        non_observer_derivation = False
        root_path = DEFAULT_ROOT_PATH
        config = load_config(root_path, "config.yaml")
        private_keys = Keychain().get_all_private_keys()
        selected = config["selected_network"]
        prefix = config["network_overrides"]["config"][selected]["address_prefix"]
        if len(private_keys) == 0:
            print("There are no saved private keys")
            return None
        result = {}
        # Standard wallet keys
        for sk, seed in private_keys:   
            privateKey = _derive_path_unhardened(sk, [12381, 9699, 2, 0])
            publicKey = privateKey.get_g1()
            puzzle = puzzle_for_pk(bytes(publicKey))
            puzzle_hash = puzzle.get_tree_hash()
            #print(puzzle_hash)
            first_address = encode_puzzle_hash(puzzle_hash, prefix)
            result['first_address'] = first_address;      
            result['first_puzzle_hash'] = puzzle_hash;   
        # Masternode wallet keys   
        for sk, seed in private_keys:   
            privateKey = _derive_path(sk, [12381, 9699, 99, 0])
            publicKey = privateKey.get_g1()
            puzzle = puzzle_for_pk(bytes(publicKey))
            puzzle_hash = puzzle.get_tree_hash()
            #print(puzzle_hash)
            address = encode_puzzle_hash(puzzle_hash, prefix)
            #print(address)        
            result['privateKey'] = privateKey
            result['publicKey'] = publicKey
            result['puzzle_hash'] = puzzle_hash
            result['address'] = address
            result['StakingAmount'] = 100000
            self.puzzle_for_puzzle_hash[puzzle_hash] = puzzle
            self.puzzlehash_to_privatekey[puzzle_hash] = privateKey
            self.puzzlehash_to_publickey[puzzle_hash] = publicKey
            self.key_dict[bytes(publicKey)] = privateKey
            return result;

    async def cancel_staking_coins(self) -> Tuple[Coin, Program]:
        get_staking_address = self.get_staking_address()
        staking_coins = await self.node_client.get_coin_records_by_puzzle_hashes(
            [get_staking_address['puzzle_hash']], include_spent_coins=False
        )
        #print(f"cancel_staking_select_coins: {staking_coins}")
        
        totalAmount = 0
        for coin in staking_coins:
            totalAmount += coin.coin.amount
        self.get_max_send_amount = totalAmount
        Memos = "Cancel Masternode Staking Amount."
        #print(totalAmount)
        spend_bundle = await self.generate_signed_transaction(
            totalAmount, get_staking_address['first_puzzle_hash'], uint64(0), memos=[Memos]
        )
        #print(spend_bundle)
        if spend_bundle is not None:
            #print(f"res:{get_staking_address['first_puzzle_hash']}")
            res = await self.node_client.push_tx(spend_bundle)
            #print(f"res:{res}")
            if res["success"]:
                tx_id = await self.get_tx_from_mempool(spend_bundle.name())
                #print(f"coin name: {coin.coin.name()}")
                #print(f"Cancel Masternode Staking Amount Successful. tx_id: {tx_id}")
                res["tx_id"] = tx_id
                return res
            else:
                #print(f"Cancel Masternode Staking Amount Failed. push_tx res: {res}")
                return res
        return None

    async def get_tx_from_mempool(self, sb_name):
        # get mempool txn
        mempool_items = await self.node_client.get_all_mempool_items()
        for tx_id in mempool_items.keys():
            mem_sb_name = bytes32(hexstr_to_bytes(mempool_items[tx_id]["spend_bundle_name"]))
            if mem_sb_name == sb_name:
                return tx_id
        raise ValueError("No tx found in mempool. Check if confirmed")
        
    # ###############################################################################
    # 标准钱包功能
    def make_solution(
        self,
        primaries: List[AmountWithPuzzlehash],
        min_time=0,
        me=None,
        coin_announcements: Optional[Set[bytes]] = None,
        coin_announcements_to_assert: Optional[Set[bytes32]] = None,
        puzzle_announcements: Optional[Set[bytes]] = None,
        puzzle_announcements_to_assert: Optional[Set[bytes32]] = None,
        fee=0,
    ) -> Program:
        assert fee >= 0
        condition_list = []
        if len(primaries) > 0:
            for primary in primaries:
                if "memos" in primary:
                    memos: Optional[List[bytes]] = primary["memos"]
                    if memos is not None and len(memos) == 0:
                        memos = None
                else:
                    memos = None
                condition_list.append(make_create_coin_condition(primary["puzzlehash"], primary["amount"], memos))
        if min_time > 0:
            condition_list.append(make_assert_absolute_seconds_exceeds_condition(min_time))
        if me:
            condition_list.append(make_assert_my_coin_id_condition(me["id"]))
        if fee:
            condition_list.append(make_reserve_fee_condition(fee))
        if coin_announcements:
            for announcement in coin_announcements:
                condition_list.append(make_create_coin_announcement(announcement))
        if coin_announcements_to_assert:
            for announcement_hash in coin_announcements_to_assert:
                condition_list.append(make_assert_coin_announcement(announcement_hash))
        if puzzle_announcements:
            for announcement in puzzle_announcements:
                condition_list.append(make_create_puzzle_announcement(announcement))
        if puzzle_announcements_to_assert:
            for announcement_hash in puzzle_announcements_to_assert:
                condition_list.append(make_assert_puzzle_announcement(announcement_hash))
        return solution_for_conditions(condition_list)

    def add_condition_to_solution(self, condition: Program, solution: Program) -> Program:
        python_program = solution.as_python()
        python_program[1].append(condition)
        return Program.to(python_program)
    
    def get_max_send_amount() -> int:
        return self.get_max_send_amount

    async def _generate_unsigned_transaction(
        self,
        amount: uint64,
        newpuzzlehash: bytes32,
        fee: uint64 = uint64(0),
        origin_id: bytes32 = None,
        coins: Set[Coin] = None,
        primaries_input: Optional[List[AmountWithPuzzlehash]] = None,
        ignore_max_send_amount: bool = False,
        coin_announcements_to_consume: Set[Announcement] = None,
        puzzle_announcements_to_consume: Set[Announcement] = None,
        memos: Optional[List[bytes]] = None,
        negative_change_allowed: bool = False,
    ) -> List[CoinSpend]:
        """
        Generates a unsigned transaction in form of List(Puzzle, Solutions)
        Note: this must be called under a wallet state manager lock
        """
        if primaries_input is None:
            primaries: Optional[List[AmountWithPuzzlehash]] = None
            total_amount = amount + fee
        else:
            primaries = primaries_input.copy()
            primaries_amount = 0
            for prim in primaries:
                primaries_amount += prim["amount"]
            total_amount = amount + fee + primaries_amount

        if not ignore_max_send_amount:
            max_send = self.get_max_send_amount
            if total_amount > max_send:
                print(f"get_max_send_amount:{self.get_max_send_amount} Actual to tx:{total_amount} Failed.")
                return None
            #self.log.debug("Got back max send amount: %s", max_send)
        if coins is None:
            coins = await self.select_coins(uint64(total_amount))
        if coins is None:
            return None
        #self.log.info(f"coins is not None {coins}")
        spend_value = sum([coin.amount for coin in coins])

        change = spend_value - total_amount
        if negative_change_allowed:
            change = max(0, change)

        #assert change >= 0

        if coin_announcements_to_consume is not None:
            coin_announcements_bytes: Optional[Set[bytes32]] = {a.name() for a in coin_announcements_to_consume}
        else:
            coin_announcements_bytes = None
        if puzzle_announcements_to_consume is not None:
            puzzle_announcements_bytes: Optional[Set[bytes32]] = {a.name() for a in puzzle_announcements_to_consume}
        else:
            puzzle_announcements_bytes = None

        spends: List[CoinSpend] = []
        primary_announcement_hash: Optional[bytes32] = None

        # Check for duplicates
        if primaries is not None:
            all_primaries_list = [(p["puzzlehash"], p["amount"]) for p in primaries] + [(newpuzzlehash, amount)]
            if len(set(all_primaries_list)) != len(all_primaries_list):
                raise ValueError("Cannot create two identical coins")
        if memos is None:
            memos = []
        assert memos is not None
        for coin in coins:
            # Only one coin creates outputs
            if origin_id in (None, coin.name()):
                origin_id = coin.name()
                if primaries is None:
                    if amount > 0:
                        primaries = [{"puzzlehash": newpuzzlehash, "amount": uint64(amount), "memos": memos}]
                    else:
                        primaries = []
                else:
                    primaries.append({"puzzlehash": newpuzzlehash, "amount": uint64(amount), "memos": memos})
                if change > 0:
                    change_puzzle_hash: bytes32 = self.first_puzzle_hash
                    primaries.append({"puzzlehash": change_puzzle_hash, "amount": uint64(change), "memos": []})
                message_list: List[bytes32] = [c.name() for c in coins]
                for primary in primaries:
                    message_list.append(Coin(coin.name(), primary["puzzlehash"], primary["amount"]).name())
                message: bytes32 = std_hash(b"".join(message_list))
                #print(self.puzzle_for_puzzle_hash)
                if coin.puzzle_hash not in self.puzzle_for_puzzle_hash:
                    print(f"Not found puzzle_hash {coin.puzzle_hash} in kv pairs. Need to enlarge address numbers")
                    print("")
                    return None
                puzzle: Program = self.puzzle_for_puzzle_hash[coin.puzzle_hash]
                solution: Program = self.make_solution(
                    primaries=primaries,
                    fee=fee,
                    coin_announcements={message},
                    coin_announcements_to_assert=coin_announcements_bytes,
                    puzzle_announcements_to_assert=puzzle_announcements_bytes,
                )
                primary_announcement_hash = Announcement(coin.name(), message).name()

                spends.append(
                    CoinSpend(
                        coin, SerializedProgram.from_bytes(bytes(puzzle)), SerializedProgram.from_bytes(bytes(solution))
                    )
                )
                break
        else:
            raise ValueError("origin_id is not in the set of selected coins")

        # Process the non-origin coins now that we have the primary announcement hash
        for coin in coins:
            if coin.name() == origin_id:
                continue

            puzzle = self.puzzle_for_puzzle_hash[coin.puzzle_hash]
            solution = self.make_solution(coin_announcements_to_assert={primary_announcement_hash}, primaries=[])
            spends.append(
                CoinSpend(
                    coin, SerializedProgram.from_bytes(bytes(puzzle)), SerializedProgram.from_bytes(bytes(solution))
                )
            )

        #self.log.debug(f"Spends is {spends}")
        return spends

    async def sign_transaction(self, coin_spends: List[CoinSpend]) -> SpendBundle:
        return await sign_coin_spends(
            coin_spends,
            self.secret_key_store.secret_key_for_public_key,
            DEFAULT_CONSTANTS.AGG_SIG_ME_ADDITIONAL_DATA,
            DEFAULT_CONSTANTS.MAX_BLOCK_COST_CLVM,
        )
        
    async def hack_populate_secret_key_for_puzzle_hash(self, puzzle_hash: bytes32) -> G1Element:
        secret_key = self.puzzlehash_to_privatekey[puzzle_hash]
        public_key = self.puzzlehash_to_publickey[puzzle_hash]
        # HACK
        synthetic_secret_key = calculate_synthetic_secret_key(secret_key, DEFAULT_HIDDEN_PUZZLE_HASH)
        self.secret_key_store.save_secret_key(synthetic_secret_key)
        return public_key

    async def hack_populate_secret_keys_for_coin_spends(self, coin_spends: List[CoinSpend]) -> None:
        """
        This hack forces secret keys into the `_pk2sk` lookup. This should eventually be replaced
        by a persistent DB table that can do this look-up directly.
        """
        for coin_spend in coin_spends:
            await self.hack_populate_secret_key_for_puzzle_hash(coin_spend.coin.puzzle_hash)
        
    async def generate_signed_transaction(
        self,
        amount: uint64,
        puzzle_hash: bytes32,
        fee: uint64 = uint64(0),
        origin_id: bytes32 = None,
        coins: Set[Coin] = None,
        primaries: Optional[List[AmountWithPuzzlehash]] = None,
        ignore_max_send_amount: bool = False,
        coin_announcements_to_consume: Set[Announcement] = None,
        puzzle_announcements_to_consume: Set[Announcement] = None,
        memos: Optional[List[bytes]] = None,
        negative_change_allowed: bool = False,
    ) -> TransactionRecord:
        """
        Use this to generate transaction.
        Note: this must be called under a wallet state manager lock
        The first output is (amount, puzzle_hash, memos), and the rest of the outputs are in primaries.
        """
        if primaries is None:
            non_change_amount = amount
        else:
            non_change_amount = uint64(amount + sum(p["amount"] for p in primaries))

        #self.log.debug("Generating transaction for: %s %s %s", puzzle_hash, amount, repr(coins))
        transaction = await self._generate_unsigned_transaction(
            amount,
            puzzle_hash,
            fee,
            origin_id,
            coins,
            primaries,
            ignore_max_send_amount,
            coin_announcements_to_consume,
            puzzle_announcements_to_consume,
            memos,
            negative_change_allowed,
        )
        if transaction is None:
            return None
        assert len(transaction) > 0
        #self.log.info("About to sign a transaction: %s", transaction)
        #合成密钥已经在初始化的时候生成,所以不需要调用此函数.
        await self.hack_populate_secret_keys_for_coin_spends(transaction)
        spend_bundle: SpendBundle = await sign_coin_spends(
            transaction,
            self.secret_key_store.secret_key_for_public_key,
            DEFAULT_CONSTANTS.AGG_SIG_ME_ADDITIONAL_DATA,
            DEFAULT_CONSTANTS.MAX_BLOCK_COST_CLVM,
        )

        now = uint64(int(time.time()))
        add_list: List[Coin] = list(spend_bundle.additions())
        rem_list: List[Coin] = list(spend_bundle.removals())

        output_amount = sum(a.amount for a in add_list) + fee
        input_amount = sum(r.amount for r in rem_list)
        if negative_change_allowed:
            assert output_amount >= input_amount
        else:
            assert output_amount == input_amount
        
        return spend_bundle
    
    async def select_coins(self, amount: int) -> Tuple[Coin, Program]:
        # check that wallet_balance is greater than amount
        # assert await self.available_balance() > amount
        select_coins = []
        for k in self.key_dict.keys():
            puzzle = puzzle_for_pk(k)
            my_coins = await self.node_client.get_coin_records_by_puzzle_hash(
                puzzle.get_tree_hash(), include_spent_coins=False
            )
            if my_coins:
                #coin_record = next((cr for cr in my_coins if (cr.coin.amount >= amount) and (not cr.spent)), None)
                for coin_record in my_coins:
                    if coin_record.spent == False and coin_record.coin.puzzle_hash == puzzle.get_tree_hash():
                        if True:
                            synth_sk = calculate_synthetic_secret_key(self.key_dict[k], DEFAULT_HIDDEN_PUZZLE_HASH)
                            self.key_dict_synth_sk[bytes(synth_sk.get_g1())] = synth_sk
                            select_coins.append(coin_record.coin)
                if self.get_max_send_amount >= amount:
                    return select_coins
        print(f"No spendable coins found !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! Need Select: {amount}")
        print(f"select_coins:{select_coins}")
        return None
    


#Driver Section
def run_singleton(full_puzzle: Program, solution: Program) -> List:
    k = full_puzzle.run(solution)
    conds = []
    for x in k.as_iter():
        code = int.from_bytes(x.first(), "big")

        if code == 51:
            ph = x.rest().first().as_python()
            amt = int.from_bytes(x.rest().rest().first().as_python(), "big")
            conds.append([code, ph, amt])
        elif code == 50:
            pk = x.rest().first().as_python()
            msg = x.rest().rest().first().as_python()
            conds.append([code, pk, msg])
        elif code == 61:
            a_id = x.rest().first().as_python().hex()
            conds.append([code, a_id])
        elif code in [60, 62, 63, 70]:
            msg = x.rest().first().as_python()
            conds.append([code, msg])

    return conds


def make_inner(state: List, royalty: List) -> Program:
    args = [INNER_MOD.get_tree_hash(), state, royalty]
    return INNER_MOD.curry(*args)


def make_solution(new_state, payment_info):
    return [new_state, payment_info]


def get_eve_coin_from_launcher(launcher_spend):
    conds = run_singleton(launcher_spend.puzzle_reveal.to_program(), launcher_spend.solution.to_program())
    create_cond = next(c for c in conds if c[0] == 51)
    return Coin(launcher_spend.coin.name(), create_cond[1], create_cond[2])


def make_launcher_spend(found_coin: Coin, amount: int, state: List, royalty: List, key_value_list: Tuple):
    # key_value_list must be a tuple, which can contain lists, but the top-level
    # must be 2 elements
    launcher_coin = Coin(found_coin.name(), LAUNCHER_PUZZLE_HASH, amount)
    args = [INNER_MOD.get_tree_hash(), state, royalty]
    curried = INNER_MOD.curry(*args)
    full_puzzle = SINGLETON_MOD.curry((SINGLETON_MOD_HASH, (launcher_coin.name(), LAUNCHER_PUZZLE_HASH)), curried)

    solution = Program.to(
        [
            full_puzzle.get_tree_hash(),
            SINGLETON_MOD_HASH,
            launcher_coin.name(),
            LAUNCHER_PUZZLE_HASH,
            INNER_MOD.get_tree_hash(),
            state,
            royalty,
            amount,
            key_value_list,
        ]
    )

    return CoinSpend(launcher_coin, LAUNCHER_PUZZLE, solution)


def make_found_spend(
    found_coin: Coin, found_coin_puzzle: Program, launcher_coin_spend: CoinSpend, amount: int
) -> CoinSpend:
    launcher_announcement = Announcement(launcher_coin_spend.coin.name(), launcher_coin_spend.solution.get_tree_hash())

    conditions = [
        [
            ConditionOpcode.ASSERT_COIN_ANNOUNCEMENT,
            std_hash(launcher_coin_spend.coin.name() + launcher_announcement.message),
        ],
        [ConditionOpcode.CREATE_COIN, launcher_coin_spend.coin.puzzle_hash, amount],
        [ConditionOpcode.CREATE_COIN, found_coin.puzzle_hash, found_coin.amount - amount],
    ]
    delegated_puzzle = Program.to((1, conditions))
    found_coin_solution = Program.to([[], delegated_puzzle, []])
    return CoinSpend(found_coin, found_coin_puzzle, found_coin_solution)


def make_eve_spend(state: List, royalty: List, launcher_spend: CoinSpend):
    eve_coin = get_eve_coin_from_launcher(launcher_spend)
    args = [INNER_MOD.get_tree_hash(), state, royalty]
    eve_inner_puzzle = INNER_MOD.curry(*args)
    full_puzzle = SINGLETON_MOD.curry(
        (SINGLETON_MOD_HASH, (launcher_spend.coin.name(), LAUNCHER_PUZZLE_HASH)), eve_inner_puzzle
    )

    assert full_puzzle.get_tree_hash() == eve_coin.puzzle_hash

    eve_solution = [state, [], 0]  # [state, pmt_id, fee]
    eve_proof = LineageProof(launcher_spend.coin.parent_coin_info, None, launcher_spend.coin.amount)
    # eve_proof = singleton_top_layer.lineage_proof_for_coinsol(launcher_spend)
    solution = singleton_top_layer.solution_for_singleton(eve_proof, eve_coin.amount, eve_solution)
    eve_spend = CoinSpend(eve_coin, full_puzzle, solution)
    return eve_spend



