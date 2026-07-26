
## Setup the project

```
  mkdir video-align
  cd video-align

  uv init
  uv add whisperx
```
## Run WhisperX through uv:
```
  uv run whisperx /path/to/input.mp4 \
    --model medium.en \
    --language en \
    --output_format json \
    --output_dir output
```
## Run the converter
```
  uv run python make_csvs.py
```
