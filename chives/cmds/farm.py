from typing import Optional

import click


@click.group("farm", short_help="Manage your farm")
def farm_cmd() -> None:
    pass


@farm_cmd.command("summary", short_help="Summary of farming information")
@click.option(
    "-p",
    "--rpc-port",
    help=(
        "Set the port where the Full Node is hosting the RPC interface. "
        "See the rpc_port under full_node in config.yaml"
    ),
    type=int,
    default=None,
    show_default=True,
)
@click.option(
    "-wp",
    "--wallet-rpc-port",
    help="Set the port where the Wallet is hosting the RPC interface. See the rpc_port under wallet in config.yaml",
    type=int,
    default=None,
    show_default=True,
)
@click.option(
    "-hp",
    "--harvester-rpc-port",
    help=(
        "Set the port where the Harvester is hosting the RPC interface"
        "See the rpc_port under harvester in config.yaml"
    ),
    type=int,
    default=None,
    show_default=True,
)
@click.option(
    "-fp",
    "--farmer-rpc-port",
    help=(
        "Set the port where the Farmer is hosting the RPC interface. " "See the rpc_port under farmer in config.yaml"
    ),
    type=int,
    default=None,
    show_default=True,
)
def summary_cmd(
    rpc_port: Optional[int],
    wallet_rpc_port: Optional[int],
    harvester_rpc_port: Optional[int],
    farmer_rpc_port: Optional[int],
) -> None:
    from .farm_funcs import summary
    import asyncio

    asyncio.run(summary(rpc_port, wallet_rpc_port, harvester_rpc_port, farmer_rpc_port))


@farm_cmd.command("challenges", short_help="Show the latest challenges")
@click.option(
    "-fp",
    "--farmer-rpc-port",
    help="Set the port where the Farmer is hosting the RPC interface. See the rpc_port under farmer in config.yaml",
    type=int,
    default=None,
    show_default=True,
)
@click.option(
    "-l",
    "--limit",
    help="Limit the number of challenges shown. Use 0 to disable the limit",
    type=click.IntRange(0),
    default=20,
    show_default=True,
)
def challenges_cmd(farmer_rpc_port: Optional[int], limit: int) -> None:
    from .farm_funcs import challenges
    import asyncio

    asyncio.run(challenges(farmer_rpc_port, limit))


@farm_cmd.command("uploadfarmerdata", short_help="Upload the farm summary and challenges data to community.chivescoin.org, and you can query the data in this site.")
@click.option(
    "-p",
    "--rpc-port",
    help=(
        "Set the port where the Full Node is hosting the RPC interface. "
        "See the rpc_port under full_node in config.yaml"
    ),
    type=int,
    default=None,
    show_default=True,
)
@click.option(
    "-wp",
    "--wallet-rpc-port",
    help="Set the port where the Wallet is hosting the RPC interface. See the rpc_port under wallet in config.yaml",
    type=int,
    default=None,
    show_default=True,
)
@click.option(
    "-hp",
    "--harvester-rpc-port",
    help=(
        "Set the port where the Harvester is hosting the RPC interface"
        "See the rpc_port under harvester in config.yaml"
    ),
    type=int,
    default=None,
    show_default=True,
)
@click.option(
    "-fp",
    "--farmer-rpc-port",
    help=(
        "Set the port where the Farmer is hosting the RPC interface. " "See the rpc_port under farmer in config.yaml"
    ),
    type=int,
    default=None,
    show_default=True,
)
def uploadfarmerdata_cmd(rpc_port: int, wallet_rpc_port: int, harvester_rpc_port: int, farmer_rpc_port: int) -> None:
    print("Ready to upload harvester data to community.chivescoin.org...")
    from .farm_funcs import summary,challenges,uploadfarmerdata
    import asyncio
    import requests
    import time
    import json
    from datetime import datetime
    while 1==1:
        FarmerSatus = asyncio.run(uploadfarmerdata(rpc_port, wallet_rpc_port, harvester_rpc_port, farmer_rpc_port))
        FarmerSatusJson = json.dumps(FarmerSatus)
        print('------------------------------------------------------------------')
        print(datetime.fromtimestamp(time.time()).strftime("%Y-%m-%d %H:%M:%S"))
        print(f"Upload the farm summary and challenges data to community.chivescoin.org, and you can query the data in this site.")
        try:
            content = requests.post('https://community.chivescoin.org/farmerinfor/uploaddata.php', data={'FarmerSatus':FarmerSatusJson})
            try:
                content = content.json()
                print(content)
            except json.JSONDecodeError as e:
                # No nothing  
                print("https://community.chivescoin.org no respone. Json parse failed.")  
        except requests.exceptions.ConnectionError:
            print('ConnectionError -- please wait 600 seconds')
        except requests.exceptions.ChunkedEncodingError:
            print('ChunkedEncodingError -- please wait 600 seconds')
        except:
            print('Unfortunitely -- An Unknow Error Happened, Please wait 600 seconds')
        time.sleep(600)

