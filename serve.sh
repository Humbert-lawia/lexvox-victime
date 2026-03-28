#!/bin/bash
export PATH="/tmp/node-v22.14.0-darwin-arm64/bin:$PATH"
cd "/Users/patricehumbert/Desktop/LANDING PAGE LAWIA SKILLS/lexvox-victime"
exec npx serve . --listen "tcp://0.0.0.0:${PORT:-8091}"
