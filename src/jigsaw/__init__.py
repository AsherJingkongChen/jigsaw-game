"""Patch-shuffle jigsaw: assemble hides a permutation in an image, dessemble scores a guess."""

import argparse
import json
import random
import sys

from PIL import Image, ImageDraw, ImageFont
from PIL.PngImagePlugin import PngInfo

PATCH = 112
SHUFFLED_FRACTION_INVERSE = 5
GRID_COLOR = (255, 0, 255)
LABEL_COLOR = (255, 255, 0)
LABEL_BACKGROUND = (0, 0, 0)
GT_KEY = "jigsaw-gt"


def assemble():
    parser = argparse.ArgumentParser(description="Shuffle k patches of an image and embed the answer.")
    parser.add_argument("origin")
    parser.add_argument("-o", "--output", required=True)
    parser.add_argument("-k", "--shuffled", type=int, help=f"number of patches to shuffle (default: 1/{SHUFFLED_FRACTION_INVERSE} of the cells)")
    args = parser.parse_args()

    image = Image.open(args.origin).convert("RGB")
    cols, rows = image.width // PATCH, image.height // PATCH
    shuffled = args.shuffled or max(2, round(cols * rows / SHUFFLED_FRACTION_INVERSE))
    if shuffled < 2 or shuffled > cols * rows:
        sys.exit(f"shuffled must be in [2, {cols * rows}]")

    rng = random.SystemRandom()
    sources = rng.sample(range(cols * rows), shuffled)
    targets = sources[:]
    while any(s == t for s, t in zip(sources, targets)):
        rng.shuffle(targets)
    gt = dict(zip(sources, targets))

    def box(patch_id):
        row, col = divmod(patch_id, cols)
        return (col * PATCH, row * PATCH, (col + 1) * PATCH, (row + 1) * PATCH)

    jigsaw = image.copy()
    for source, target in gt.items():
        jigsaw.paste(image.crop(box(source)), box(target)[:2])

    draw = ImageDraw.Draw(jigsaw)
    for col in range(cols + 1):
        draw.line([(col * PATCH, 0), (col * PATCH, rows * PATCH)], fill=GRID_COLOR)
    for row in range(rows + 1):
        draw.line([(0, row * PATCH), (cols * PATCH, row * PATCH)], fill=GRID_COLOR)

    font = ImageFont.load_default(size=11)
    for patch_id in range(cols * rows):
        left, top = box(patch_id)[:2]
        anchor = (left + 2, top + 1)
        draw.rectangle(draw.textbbox(anchor, str(patch_id), font=font), fill=LABEL_BACKGROUND)
        draw.text(anchor, str(patch_id), fill=LABEL_COLOR, font=font)

    info = PngInfo()
    info.add_itxt(GT_KEY, json.dumps({"cols": cols, "rows": rows, "gt": gt}))
    jigsaw.save(args.output, pnginfo=info)
    print(f"{cols}x{rows} patches of {PATCH}px, {shuffled} shuffled, patch id = row * {cols} + col")


def dessemble():
    parser = argparse.ArgumentParser(description="Score a guessed {source: target} map against the embedded answer.")
    parser.add_argument("jigsaw")
    parser.add_argument("-d", "--dict", required=True, help='JSON map from source id to target id, e.g. \'{"3": 17}\'')
    args = parser.parse_args()

    answer = json.loads(Image.open(args.jigsaw).text[GT_KEY])
    gt = {int(s): t for s, t in answer["gt"].items()}
    guess = {int(s): int(t) for s, t in json.loads(args.dict).items()}
    correct = sum(guess.get(source) == target for source, target in gt.items())
    print(json.dumps({"score": correct, "of": len(gt), "submitted": len(guess)}))
    for source in sorted(gt.keys() | guess.keys()):
        verdict = "ok" if guess.get(source) == gt.get(source) else "x"
        print(f"{verdict:2} {source:>4} -> guess {guess.get(source, '-')!s:>4}, answer {gt.get(source, 'not shuffled')}")
