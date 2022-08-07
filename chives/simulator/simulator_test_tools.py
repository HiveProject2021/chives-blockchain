import asyncio
import sys
import tempfile
from pathlib import Path
from typing import Any, AsyncGenerator, Dict, Optional, Tuple

from blspy import PrivateKey

from chives.cmds.init_funcs import create_all_ssl
from chives.consensus.coinbase import create_puzzlehash_for_pk
from chives.daemon.server import WebSocketServer, daemon_launch_lock_path
from chives.simulator.full_node_simulator import FullNodeSimulator
from chives.simulator.socket import find_available_listen_port
from chives.simulator.ssl_certs import get_next_nodes_certs_and_keys, get_next_private_ca_cert_and_key
from chives.simulator.start_simulator import async_main as start_simulator_main
from chives.types.blockchain_format.sized_bytes import bytes32
from chives.util.bech32m import encode_puzzle_hash
from chives.util.config import create_default_chives_config, load_config, save_config
from chives.util.ints import uint32
from chives.util.keychain import Keychain
from chives.util.lock import Lockfile
from chives.wallet.derive_keys import master_sk_to_wallet_sk

"""
These functions are used to test the simulator.
"""


def mnemonic_fingerprint() -> Tuple[str, int]:
    mnemonic = (
        "today grape album ticket joy idle supreme sausage "
        "oppose voice angle roast you oven betray exact "
        "memory riot escape high dragon knock food blade"
    )
    # add key to keychain
    sk = Keychain().add_private_key(mnemonic)
    fingerprint = sk.get_g1().get_fingerprint()
    return mnemonic, fingerprint


def get_puzzle_hash_from_key(fingerprint: int, key_id: int = 1) -> bytes32:
    priv_key_and_entropy = Keychain().get_private_key_by_fingerprint(fingerprint)
    if priv_key_and_entropy is None:
        raise Exception("Fingerprint not found")
    private_key = priv_key_and_entropy[0]
    sk_for_wallet_id: PrivateKey = master_sk_to_wallet_sk(private_key, uint32(key_id))
    puzzle_hash: bytes32 = create_puzzlehash_for_pk(sk_for_wallet_id.get_g1())
    return puzzle_hash


def create_config(chives_root: Path, fingerprint: int) -> Dict[str, Any]:
    # create chives directories
    create_default_chives_config(chives_root)
    create_all_ssl(
        chives_root,
        private_ca_crt_and_key=get_next_private_ca_cert_and_key(),
        node_certs_and_keys=get_next_nodes_certs_and_keys(),
    )
    # load config
    config = load_config(chives_root, "config.yaml")
    config["full_node"]["send_uncompact_interval"] = 0
    config["full_node"]["target_uncompact_proofs"] = 30
    config["full_node"]["peer_connect_interval"] = 50
    config["full_node"]["sanitize_weight_proof_only"] = False
    config["full_node"]["introducer_peer"] = None
    config["full_node"]["dns_servers"] = []
    config["logging"]["log_stdout"] = True
    config["selected_network"] = "testnet0"
    for service in [
        "harvester",
        "farmer",
        "full_node",
        "wallet",
        "introducer",
        "timelord",
        "pool",
        "simulator",
    ]:
        config[service]["selected_network"] = "testnet0"
    config["daemon_port"] = find_available_listen_port("BlockTools daemon")
    config["full_node"]["port"] = 0
    config["full_node"]["rpc_port"] = find_available_listen_port("Node RPC")
    # simulator overrides
    config["simulator"]["key_fingerprint"] = fingerprint
    config["simulator"]["farming_address"] = encode_puzzle_hash(get_puzzle_hash_from_key(fingerprint), "txch")
    config["simulator"]["plot_directory"] = "test-simulator/plots"
    # save config
    save_config(chives_root, "config.yaml", config)
    return config


async def start_simulator(chives_root: Path, automated_testing: bool = False) -> AsyncGenerator[FullNodeSimulator, None]:
    sys.argv = [sys.argv[0]]  # clear sys.argv to avoid issues with config.yaml
    service = await start_simulator_main(True, automated_testing, root_path=chives_root)
    await service.start()

    yield service._api

    service.stop()
    await service.wait_closed()


async def get_full_chives_simulator(
    automated_testing: bool = False, chives_root: Optional[Path] = None, config: Optional[Dict[str, Any]] = None
) -> AsyncGenerator[Tuple[FullNodeSimulator, Path, Dict[str, Any], str, int], None]:
    """
    A chives root directory can be provided, otherwise a temporary one is created.
    This test can either be run in automated mode or not, which determines which mode block tools run in.
    This test is fully interdependent and can be used without the rest of the chives test suite.
    Please refer to the documentation for more information.
    """
    # Create and setup temporary chives directories.
    if chives_root is None:
        chives_root = Path(tempfile.TemporaryDirectory().name)
    mnemonic, fingerprint = mnemonic_fingerprint()
    if config is None:
        config = create_config(chives_root, fingerprint)
    crt_path = chives_root / config["daemon_ssl"]["private_crt"]
    key_path = chives_root / config["daemon_ssl"]["private_key"]
    ca_crt_path = chives_root / config["private_ssl_ca"]["crt"]
    ca_key_path = chives_root / config["private_ssl_ca"]["key"]
    with Lockfile.create(daemon_launch_lock_path(chives_root)):
        shutdown_event = asyncio.Event()
        ws_server = WebSocketServer(chives_root, ca_crt_path, ca_key_path, crt_path, key_path, shutdown_event)
        await ws_server.start()  # type: ignore[no-untyped-call]

        async for simulator in start_simulator(chives_root, automated_testing):
            yield simulator, chives_root, config, mnemonic, fingerprint

        await ws_server.stop()
        await shutdown_event.wait()  # wait till shutdown is complete
