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


# See: https://bugs.python.org/issue29288
"".encode("idna")

SERVICE_NAME = "full_node"
log = logging.getLogger(__name__)


async def masternode_update_status_interval(selected_network, config) -> None:
    while True:
        x = datetime.datetime.now()
        log.warning("*"*64)
        log.warning(f"[{selected_network}] Masternode heartbeat {x} ")
        MasterNodeHeartBeat = {}
        MasterNodeHeartBeat['selected_network'] = selected_network
        MasterNodeHeartBeat['Address'] = "Address"
        MasterNodeHeartBeat['MasterNodeId'] = "MasterNodeId"
        MasterNodeHeartBeat['FingerPrint'] = "FingerPrint"
        MasterNodeHeartBeatText = json.dumps(MasterNodeHeartBeat, indent=4, sort_keys=True)
        try:
            content = requests.post('https://community.chivescoin.org/masternode/', data={'MasterNodeHeartBeat':MasterNodeHeartBeatText}, timeout=3)
            log.warning(content.text) 
        except requests.exceptions.ConnectionError:
            log.warning('ConnectionError -- please wait 600 seconds............................')
        except requests.exceptions.ChunkedEncodingError:
            log.warning('ChunkedEncodingError -- please wait 600 seconds............................')
        except:
            log.warning('Unfortunitely -- An Unknow Error Happened, Please wait 600 seconds............................')
        
        time.sleep(10)
        
def main():
    config = load_config_cli(DEFAULT_ROOT_PATH, "config.yaml", "seeder")
    selected_network = config["selected_network"]
    root_path = DEFAULT_ROOT_PATH
    net_config = load_config(root_path, "config.yaml")
    config = net_config["timelord_launcher"]
    initialize_logging("masternode", config["logging"], DEFAULT_ROOT_PATH)
    return asyncio.run(masternode_update_status_interval(selected_network, config))


if __name__ == "__main__":
    main()
