import sys
import asyncio
import aiosqlite
from pathlib import Path
import binascii
import sqlite3
import json
import logging
from typing import Dict, List, Tuple, Optional, Union, Any
from blspy import AugSchemeMPL, G1Element, G2Element, PrivateKey

from chives.types.blockchain_format.coin import Coin
from chives.types.spend_bundle import SpendBundle
from chives.types.blockchain_format.program import Program, SerializedProgram
from chives.util.hash import std_hash
from clvm.casts import int_to_bytes, int_from_bytes
from chives.util.byte_types import hexstr_to_bytes
from chives.consensus.default_constants import DEFAULT_CONSTANTS
from chives.wallet.puzzles.load_clvm import load_clvm
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
    
    
log = logging.getLogger(__name__)
SINGLETON_MOD = load_clvm("singleton_top_layer.clvm")
SINGLETON_MOD_HASH = SINGLETON_MOD.get_tree_hash()
LAUNCHER_PUZZLE = load_clsp_relative("clsp/nft_launcher.clsp")
LAUNCHER_PUZZLE_HASH = LAUNCHER_PUZZLE.get_tree_hash()

INNER_MOD = load_clsp_relative("clsp/creator_nft.clsp")
ESCAPE_VALUE = -113
MELT_CONDITION = [ConditionOpcode.CREATE_COIN, 0, ESCAPE_VALUE]

config = load_config(Path(DEFAULT_ROOT_PATH), "config.yaml")
selected = config["selected_network"]
testnet_agg_sig_data = config["network_overrides"]["constants"][selected]["AGG_SIG_ME_ADDITIONAL_DATA"]
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
        all_staking_coins = await self.node_client.get_coin_records_by_puzzle_hash(get_staking_address['puzzle_hash'],True)
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

    async def wait_for_confirmation(self, tx_id, launcher_id):
        while True:
            item = await self.node_client.get_mempool_item_by_tx_id(tx_id)
            if not item:
                return await self.masternode_wallet.get_nft_by_launcher_id(launcher_id)
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


class MasterNodeCoin(Coin):
    def __init__(self, launcher_id: bytes32, coin: Coin, last_spend: CoinSpend = None, nft_data=None, royalty=None):
        super().__init__(coin.parent_coin_info, coin.puzzle_hash, coin.amount)
        self.launcher_id = launcher_id
        self.last_spend = last_spend
        self.data = nft_data
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
        print(Path(DEFAULT_ROOT_PATH))
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
                        print(NftDataJson)
                        if "ReceivedAddress" in NftDataJson and "StakingAddress" in NftDataJson and "StakingAmount" in NftDataJson and "NodeName" in NftDataJson:
                            await self.save_launcher(launcher_id, state[-1], eve_cr[0].spent_block_index, NftDataJson)
                            MasterNode = MasterNodeCoin(launcher_id, launcher_rec.coin, launcher_spend, nft_data, 0)
                            return MasterNode
                        #else:
                        #    print("NftDataJson Json Format Error.")
                    except Exception as e:
                        print(e)
 
    async def sync_masternode(self):
        all_nfts = await self.node_client.get_coin_records_by_puzzle_hash(LAUNCHER_PUZZLE_HASH)
        await self.filter_singletons(all_nfts)

    async def save_launcher(self, launcher_id, pk, Height, StakingData):
        cursor = await self.db_connection.execute(
            "INSERT OR REPLACE INTO masternode_list (launcher_id, owner_pk, Height, ReceivedAddress, StakingAddress, StakingAmount, NodeName) VALUES (?,?,?,?,?,?,?)", (
            str(bytes(launcher_id).hex()), 
            str(bytes(pk).hex()),
            int(Height),
            str(StakingData['ReceivedAddress']),
            str(StakingData['StakingAddress']),
            int(StakingData['StakingAmount']),
            str(StakingData['NodeName'])
            )
        )
        print(f"save_launcher:{StakingData}")
        await cursor.close()
        await self.db_connection.commit()

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
        for sk, seed in private_keys:   
            privateKey = _derive_path_unhardened(sk, [12381, 9699, 2, 0])
            publicKey = privateKey.get_g1()
            puzzle = puzzle_for_pk(bytes(publicKey))
            puzzle_hash = puzzle.get_tree_hash()
            #print(puzzle_hash)
            first_address = encode_puzzle_hash(puzzle_hash, prefix)
            result['first_address'] = first_address;      
            result['first_puzzle_hash'] = puzzle_hash;      
        for sk, seed in private_keys:   
            privateKey = _derive_path(sk, [12381, 9699, 99, 0])
            publicKey = privateKey.get_g1()
            puzzle = puzzle_for_pk(bytes(publicKey))
            puzzle_hash = puzzle.get_tree_hash()
            #print(puzzle_hash)
            address = encode_puzzle_hash(puzzle_hash, prefix)
            #print(address)        
            result['privateKey'] = privateKey;
            result['publicKey'] = publicKey;
            result['puzzle_hash'] = puzzle_hash;
            result['address'] = address;
            result['StakingAmount'] = 100000;
            return result;



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



