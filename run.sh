#!/usr/bin/env bash
# Sambhota Tibetan Schools Society (STSS) Teaching Repository Startup Script

set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

echo "=================================================================="
echo " བོད་མིའི་སྒྲིག་འཛུགས་ཤེས་རིག་ལས་ཁུངས། སམ་བྷོ་ཊ་བོད་སློབ་ཚོགས་པ།"
echo " Sambhota Tibetan Schools Society (STSS) Teaching Repository"
echo "=================================================================="

# Ensure database is initialized
python3 database.py

# Launch HTTP server
PORT="${1:-8080}"
echo "Starting STSS Teaching Repository on port $PORT..."
python3 server.py "$PORT"
