#!/bin/bash

set -euo pipefail

SCRIPT_DIR="$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")"

apt-get update
apt-get install -y --no-install-recommends software-properties-common python3.8  python3.8-venv  python3.8-dev build-essential python3-pip
python3.8 -m pip install virtualenv
curl -L https://get.docker.com/ | bash
gpasswd -a vagrant docker
