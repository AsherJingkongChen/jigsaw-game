# jigsaw-game

A patch-shuffle puzzle for testing how well an agent recovers a permutation by sight.

`assemble` cuts an image into 112x112 patches, swaps k of them so that none stays in place, draws a magenta grid with each cell's id in its top-left corner, and stores the answer in a PNG iTXt chunk.
`dessemble` reads that answer back and scores a guess.
The output has the same size as the input; the strip past the last full patch is left as it is.

## Protocol

The agent's shell starts in this repository, and the agent may make exactly four tool calls:

1. `Read({dir}/origin.png)`
2. `Bash(uv run assemble {dir}/origin.png -o {dir}/jigsaw.png)`
3. `Read({dir}/jigsaw.png)`
4. `Bash(uv run dessemble {dir}/jigsaw.png -d '{submission}')`

Score = `-abs(tool_calls - 4) + step4.score`.
The Read tool shows only pixels, so the answer in iTXt stays hidden; any other tool call costs a point.

## Format

Patch id is `row * cols + col`, counted from the top left.
The submission maps where a patch was in the origin to where it sits in the jigsaw: `{"31": 247, "247": 31}`.
`dessemble` prints `{"score": correct, "of": k, "submitted": n}`, then one line per id with its verdict, the guess, and the answer.

`assemble -k N` sets how many patches are shuffled (default: one fifth of the cells, at least 2).
