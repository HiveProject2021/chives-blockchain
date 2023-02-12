import asyncio
import time
import logging
import pathlib
from multiprocessing import freeze_support
from typing import Dict

from chives.consensus.constants import ConsensusConstants
from chives.consensus.default_constants import DEFAULT_CONSTANTS
from chives.server.outbound_message import NodeType
from chives.server.start_service import run_service
from chives.util.config import load_config_cli
from chives.util.config import load_config
from chives.util.default_root import DEFAULT_ROOT_PATH
from chives.util.chives_logging import initialize_logging
import datetime
import requests
import json
import binascii
from pathlib import Path
from chives.rpc.rpc_client import RpcClient
from chives.rpc.full_node_rpc_client import FullNodeRpcClient
from chives.rpc.wallet_rpc_client import WalletRpcClient
from chives.util.ints import uint16, uint64, uint32
from blspy import AugSchemeMPL, G1Element, G2Element, PrivateKey
from chives.util.bech32m import decode_puzzle_hash, encode_puzzle_hash
from chives.wallet.derive_keys import (
    master_sk_to_farmer_sk,
    master_sk_to_pool_sk,
    master_sk_to_wallet_sk,
    master_sk_to_wallet_sk_unhardened,
    _derive_path,
    _derive_path_unhardened,
    master_sk_to_singleton_owner_sk,
)
from chives.wallet.puzzles.p2_delegated_puzzle_or_hidden_puzzle import (  # standard_transaction
    puzzle_for_pk,
    calculate_synthetic_secret_key,
    DEFAULT_HIDDEN_PUZZLE_HASH,
)
from chives.masternode.masternode_manager import MasterNodeManager


# See: https://bugs.python.org/issue29288
"".encode("idna")

SERVICE_NAME = "full_node"
log = logging.getLogger(__name__)


async def masternode_update_status_interval(selected_network, config) -> None:

    while True:
        x = datetime.datetime.now()

        config = load_config(Path(DEFAULT_ROOT_PATH), "config.yaml")
        rpc_host = config["self_hostname"]
        full_node_rpc_port = config["full_node"]["rpc_port"]
        wallet_rpc_port = config["wallet"]["rpc_port"]

        try:
            node_client = await FullNodeRpcClient.create(
                rpc_host, uint16(full_node_rpc_port), Path(DEFAULT_ROOT_PATH), config
            )
            wallet_client = await WalletRpcClient.create(
                rpc_host, uint16(wallet_rpc_port), Path(DEFAULT_ROOT_PATH), config
            )
            log.warning("*" * 64)
            log.warning(f"[{selected_network}] Masternode heartbeat {x} ")
            fingerprint = await wallet_client.get_logged_in_fingerprint()
            private_key = await wallet_client.get_private_key(fingerprint)
            sk_data = binascii.unhexlify(private_key["sk"])
            master_sk = PrivateKey.from_bytes(sk_data)

            selected = config["selected_network"]
            prefix = config["network_overrides"]["config"][selected]["address_prefix"]

            result = {}
            result['selected_network'] = selected_network
            result['fingerprint'] = fingerprint
            privateKey = _derive_path_unhardened(master_sk, [12381, 9699, 2, 0])
            publicKey = privateKey.get_g1()
            puzzle = puzzle_for_pk(bytes(publicKey))
            puzzle_hash = puzzle.get_tree_hash()
            first_address = encode_puzzle_hash(puzzle_hash, prefix)
            result['first_address'] = first_address

            # Standard wallet keys
            privateKey = _derive_path_unhardened(master_sk, [12381, 9699, 2, 10])
            publicKey = privateKey.get_g1()
            puzzle = puzzle_for_pk(bytes(publicKey))
            puzzle_hash = puzzle.get_tree_hash()
            ReceivedAddress = encode_puzzle_hash(puzzle_hash, prefix)
            result['ReceivedAddress'] = ReceivedAddress

            # node id
            blockchain_state = await node_client.get_blockchain_state()
            if blockchain_state is not None and blockchain_state["sync"]["synced"] == True:
                result['difficulty'] = blockchain_state["difficulty"]
                result['node_id'] = blockchain_state["node_id"]
                result['space'] = blockchain_state["space"]
                result['sub_slot_iters'] = blockchain_state["sub_slot_iters"]

            if node_client:
                node_client.close()
            if wallet_client:
                wallet_client.close()

            MasterNodeHeartBeat = json.dumps(result, indent=4, sort_keys=True)

            try:
                content = requests.post('https://community.chivescoin.org/masternode/',
                                        data={'MasterNodeHeartBeat': MasterNodeHeartBeat}, timeout=3)
                log.warning(content.text)
            except requests.exceptions.ConnectionError:
                log.warning('ConnectionError -- please wait 600 seconds............................')
            except requests.exceptions.ChunkedEncodingError:
                log.warning('ChunkedEncodingError -- please wait 600 seconds............................')
            except:
                log.warning('Unfortunitely -- An Unknow Error Happened, Please wait 600 seconds............................')
            # update masternode data from blockchain
            try:
                manager = MasterNodeManager()
                await manager.connect()
                checkSyncedStatus, checkSyncedStatusText, fingerprint = await manager.checkSyncedStatus()
                await manager.chooseWallet(fingerprint)
                # for item in checkSyncedStatusText:
                #    print(item)
                if checkSyncedStatus == 2:
                    await manager.sync_masternode_from_blockchain()
                await manager.close()
            except:
                pass
        except:
            log.warning('Unfortunitely -- An Unknow except Happened, Please wait 600 seconds............................')
            pass

        log.warning("begin sleep ***** " * 5)
        time.sleep(600)


def main():
    try:
        config = load_config_cli(DEFAULT_ROOT_PATH, "config.yaml", "seeder")
        selected_network = config["selected_network"]
        root_path = DEFAULT_ROOT_PATH
        net_config = load_config(root_path, "config.yaml")
        config = net_config["timelord_launcher"]
        initialize_logging("masternode", config["logging"], DEFAULT_ROOT_PATH)
        log = logging.getLogger(__name__)
        asyncio.run(masternode_update_status_interval(selected_network, config))
    except:
        log.warning(
            'Unfortunitely -- An Unknow except Happened in main function, Please wait 600 seconds............................')
        pass


if __name__ == "__main__":
    main()
