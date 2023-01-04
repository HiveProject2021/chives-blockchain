
import asyncio
from pathlib import Path
from chives.util.byte_types import hexstr_to_bytes
from masternode_manager import MasterNodeManager


async def init_cmd():

    manager = MasterNodeManager()
    await manager.connect()
    await manager.find_all_fullnode()
    await manager.close()

def main() -> None:
    asyncio.run(init_cmd())

if __name__ == "__main__":
    main()
