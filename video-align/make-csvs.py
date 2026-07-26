import json
import csv
from pathlib import Path

input_json = Path("output/input.json")  # adjust if your file has a different name
utterances_csv = Path("utterances.csv")
words_csv = Path("words.csv")

with input_json.open("r", encoding="utf-8") as f:
    data = json.load(f)

segments = data.get("segments", [])

with utterances_csv.open("w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(
        f,
        fieldnames=["utterance_id", "start", "end", "text"]
    )
    writer.writeheader()

    for i, seg in enumerate(segments):
        writer.writerow({
            "utterance_id": i,
            "start": seg.get("start"),
            "end": seg.get("end"),
            "text": seg.get("text", "").strip(),
        })

with words_csv.open("w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(
        f,
        fieldnames=["utterance_id", "word_index", "start", "end", "word"]
    )
    writer.writeheader()

    for i, seg in enumerate(segments):
        for j, word in enumerate(seg.get("words", [])):
            writer.writerow({
                "utterance_id": i,
                "word_index": j,
                "start": word.get("start"),
                "end": word.get("end"),
                "word": word.get("word", "").strip(),
            })

print(f"Wrote {utterances_csv}")
print(f"Wrote {words_csv}")
