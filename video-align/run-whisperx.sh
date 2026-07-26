#!/bin/bash
uv run whisperx $1 \
  --model medium.en \
  --language en \
  --output_format json \
  --output_dir output
  

