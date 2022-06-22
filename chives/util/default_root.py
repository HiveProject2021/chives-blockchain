import os
from pathlib import Path

DEFAULT_ROOT_PATH = Path(os.path.expanduser(os.getenv("CHIVES_ROOT", "~/.chives/mainnet"))).resolve()
STANDALONE_ROOT_PATH = Path(
    os.path.expanduser(os.getenv("CHIVES_STANDALONE_WALLET_ROOT", "~/.chives/standalone_wallet"))
).resolve()

DEFAULT_KEYS_ROOT_PATH = Path(os.path.expanduser(os.getenv("CHIVES_KEYS_ROOT", "~/.chives_keys"))).resolve()
