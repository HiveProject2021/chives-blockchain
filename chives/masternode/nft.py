import click
import asyncio
import json
from functools import wraps
from pathlib import Path

from chives.util.byte_types import hexstr_to_bytes

from masternode_manager import MasterNodeManager


CONTEXT_SETTINGS = dict(help_option_names=["-h", "--help"])


def coro(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        return asyncio.run(f(*args, **kwargs))

    return wrapper


def print_nft(nft):
    print("\n")
    print("-" * 64)
    print(f"MasterNode ID:  {nft.launcher_id.hex()}")
    print(f"Chialisp:        {str(nft.data[0].decode('utf-8'))}")
    StakingJson = json.loads(nft.data[1].decode("utf-8"))
    print(f"StakingAddress:  {StakingJson['StakingAddress']}")
    print(f"StakingAmount:   {StakingJson['StakingAmount']}")
    print(f"ReceivedAddress: {StakingJson['ReceivedAddress']}")
    print(f"All Data:")
    print(StakingJson)
    print("-" * 64)
    print("\n")

@click.group(
    help=f"\n  MasterNodeNFT v0.1\n",
    epilog="Try 'nft list' or 'nft sale' to see some NFTs",
    context_settings=CONTEXT_SETTINGS,
)
@click.pass_context
def cli(ctx: click.Context):
    ctx.ensure_object(dict)


@cli.command("init", short_help="Start the nft database")
@coro
async def init_cmd():
    manager = MasterNodeManager()
    await manager.connect()
    await manager.sync_masternode_from_blockchain()
    await manager.close()


@cli.command("view", short_help="View a single NFT by id")
@click.option("-n", "--nft-id", required=True, type=str)
@click.pass_context
@coro
async def view_cmd(ctx, nft_id):
    manager = MasterNodeManager()
    await manager.connect()
    nft = await manager.view_nft(hexstr_to_bytes(nft_id))
    if nft:
        print_nft(nft)
    else:
        print(f"\nNo record found for:\n{nft_id}")
    await manager.close()


@cli.command("get-all-masternodes", short_help="Show All Master Nodes")
@click.pass_context
@coro
async def sale_cmd(ctx) -> None:
    manager = MasterNodeManager()
    await manager.connect()
    nfts = await manager.get_all_masternodes()
    for nft in nfts:
        print_nft(nft)
    await manager.close()


@cli.command("stake", short_help="Launch a new NFT")
@click.pass_context
@coro
async def launch_cmd(ctx) -> None:
    manager = MasterNodeManager()
    await manager.connect()
    tx_id, launcher_id = await manager.launch_staking_storage()
    print(f"Transaction id: {tx_id}")
    nft = await manager.wait_for_confirmation(tx_id, launcher_id)
    print("\n\n !!")
    print_nft(nft)
    await manager.close()


@cli.command("cancel", short_help="Cancel Masternode Staking Amount.")
@click.pass_context
@coro
async def launch_cmd(ctx) -> None:
    manager = MasterNodeManager()
    await manager.connect()
    tx_id = await manager.cancel_masternode_staking_coins()
    print(f"Transaction id: {tx_id}")
    print("\n\n cancel_masternode_staking_coins!!")
    await manager.close()

@cli.command("update", short_help="Update one of your NFTs")
@click.option("-n", "--nft-id", required=True, type=str)
@click.option("-p", "--price", required=True, type=int)
@click.option("--for-sale/--not-for-sale", required=True, type=bool, default=False)
@click.pass_context
@coro
async def update_cmd(ctx, nft_id, price, for_sale):
    assert price > 0
    manager = MasterNodeManager()
    await manager.connect()
    if for_sale:
        new_state = [10, price]
    else:
        new_state = [0, price]
    tx_id = await manager.update_nft(hexstr_to_bytes(nft_id), new_state)
    print(f"Transaction id: {tx_id}")
    nft = await manager.wait_for_confirmation(tx_id, hexstr_to_bytes(nft_id))
    print("\n\n NFT Updated!!")
    print_nft(nft)
    await manager.close()


@cli.command("buy", short_help="Update one of your NFTs")
@click.option("-n", "--nft-id", required=True, type=str)
@click.option("-p", "--price", required=True, type=int)
@click.option("--for-sale/--not-for-sale", required=True, type=bool, default=False)
@click.pass_context
@coro
async def buy_cmd(ctx, nft_id, price, for_sale):
    assert price > 0
    manager = MasterNodeManager()
    await manager.connect()
    if for_sale:
        new_state = [10, price]
    else:
        new_state = [0, price]
    tx_id = await manager.buy_nft(hexstr_to_bytes(nft_id), new_state)
    print(f"Transaction id: {tx_id}")
    nft = await manager.wait_for_confirmation(tx_id, hexstr_to_bytes(nft_id))
    print("\n\n NFT Purchased!!")
    print_nft(nft)
    await manager.close()


def monkey_patch_click() -> None:
    import click.core

    click.core._verify_python3_env = lambda *args, **kwargs: 0  # type: ignore[attr-defined]


def main() -> None:
    monkey_patch_click()
    asyncio.run(cli())


if __name__ == "__main__":
    main()
