#!/usr/bin/env python3
"""
wander.py — a generative text wanderer

Seed a word. Follow the drift.
Usage: python wander.py [seed] [--steps N] [--drift F] [--fast] [--trace]
"""

import random
import time
import sys

# ── the word graph ─────────────────────────────────────────────────────────────

FIELDS = {
    "water": ["rain", "river", "tide", "surface", "current", "still", "depth", "cold"],
    "light": ["shadow", "flicker", "pale", "dim", "dusk", "dawn", "glow", "fade"],
    "time":  ["moment", "before", "after", "wait", "linger", "return", "edge", "pass"],
    "body":  ["breath", "hand", "eye", "voice", "skin", "weight", "hollow", "pulse"],
    "earth": ["stone", "root", "dust", "ground", "seed", "crack", "layer", "dark"],
    "air":   ["wind", "open", "empty", "lift", "drift", "gone", "thin", "rise"],
    "mind":  ["echo", "dream", "forget", "strange", "wake", "lost", "word", "become"],
}

# words that naturally reach across field boundaries
BRIDGES = {
    "rain":    ["cold", "stone", "wait", "pale"],
    "still":   ["hollow", "moment", "empty", "dark"],
    "depth":   ["dark", "hollow", "before", "cold"],
    "cold":    ["stone", "empty", "fade", "skin"],
    "shadow":  ["dark", "hollow", "edge", "dream"],
    "dusk":    ["return", "stone", "breath", "wait"],
    "dawn":    ["breath", "pale", "before", "lift"],
    "fade":    ["linger", "still", "pale", "gone"],
    "moment":  ["breath", "edge", "flicker", "hand"],
    "before":  ["dream", "root", "wait", "cold"],
    "wait":    ["still", "breath", "shadow", "linger"],
    "linger":  ["shadow", "cold", "hollow", "echo"],
    "edge":    ["crack", "moment", "thin", "pale"],
    "breath":  ["wind", "moment", "pale", "voice"],
    "hollow":  ["echo", "dark", "empty", "stone"],
    "weight":  ["stone", "ground", "dark", "drift"],
    "pulse":   ["river", "moment", "breath", "flicker"],
    "stone":   ["cold", "root", "ground", "still"],
    "root":    ["dark", "ground", "before", "weight"],
    "dust":    ["gone", "drift", "pale", "forget"],
    "crack":   ["edge", "dark", "still", "thin"],
    "drift":   ["gone", "dream", "pale", "linger"],
    "gone":    ["before", "dust", "empty", "echo"],
    "rise":    ["dawn", "lift", "breath", "before"],
    "echo":    ["hollow", "voice", "return", "linger"],
    "dream":   ["drift", "shadow", "before", "strange"],
    "wake":    ["dawn", "breath", "moment", "cold"],
    "lost":    ["drift", "dark", "gone", "hollow"],
    "word":    ["echo", "voice", "breath", "strange"],
    "become":  ["return", "before", "strange", "drift"],
}

# ── fragment templates ─────────────────────────────────────────────────────────
# %w = current word   %f = a word from the same field

TEMPLATES = [
    "the %w",
    "%w",
    "%w, %f",
    "the %w of %f",
    "a kind of %w",
    "toward the %w",
    "where %f meets %w",
    "inside the %w",
    "not %f, but %w",
    "%f into %w",
    "the %f of %w",
    "what %w becomes",
    "%w without %f",
    "%w again",
    "there is %w here",
    "something like %w",
    "between %f and %w",
    "the %w holds",
    "%w, almost %f",
    "still %w",
    "how %w becomes %f",
    "the sound of %w",
    "before the %w",
    "%w returning",
    "like %f, like %w",
]

BREATH = ["", "", "", "...", "—"]  # occasional pauses, weighted toward silence

# ── graph navigation ───────────────────────────────────────────────────────────

WORD_FIELD = {word: field for field, words in FIELDS.items() for word in words}
ALL_WORDS = list(WORD_FIELD.keys())


def kin(word):
    """Words in the same field."""
    field = WORD_FIELD.get(word)
    return [w for w in FIELDS.get(field, []) if w != word]


def neighbors(word, drift):
    """Return candidate next words. drift ∈ [0,1]: low=stay close, high=leap."""
    close = kin(word)
    far = BRIDGES.get(word, [])

    if random.random() < drift and far:
        pool = close + far * 2  # weight bridges when drifting
    else:
        pool = close if close else ALL_WORDS

    return pool


def step(current, trail, drift):
    pool = neighbors(current, drift)
    pool = [w for w in pool if w not in trail[-4:]]  # avoid backtracking
    if not pool:
        pool = [w for w in ALL_WORDS if w != current]
    return random.choice(pool)


def make_fragment(word, trail):
    kin_words = [w for w in kin(word) if w not in trail[-3:]]
    if not kin_words:
        kin_words = kin(word) or ALL_WORDS

    template = random.choice(TEMPLATES)
    f_word = random.choice(kin_words)

    return template.replace("%w", word).replace("%f", f_word)


# ── the wanderer ───────────────────────────────────────────────────────────────

def wander(seed, steps=24, drift=0.3, delay=0.35, trace=False):
    if seed in WORD_FIELD:
        current = seed
    else:
        current = random.choice(ALL_WORDS)
        if seed:
            print(seed)
            print()
            time.sleep(delay)

    trail = [current]

    for _ in range(steps):
        # occasional breath
        if random.random() < 0.12:
            print(random.choice(BREATH))
            time.sleep(delay * 0.6)
            continue

        fragment = make_fragment(current, trail)

        if trace:
            field = WORD_FIELD.get(current, "?")
            print(f"{fragment}  \033[2m[{current} · {field}]\033[0m")
        else:
            print(fragment)

        time.sleep(delay)

        if random.random() < 0.18:
            print()

        current = step(current, trail, drift)
        trail.append(current)
        if len(trail) > 12:
            trail = trail[-12:]

    print()


# ── cli ────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse

    p = argparse.ArgumentParser(
        description="wander.py — seed a word, follow the drift",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"known words: {', '.join(sorted(ALL_WORDS))}",
    )
    p.add_argument("seed", nargs="?", default="drift",
                   help="starting word (default: drift)")
    p.add_argument("--steps", type=int, default=24,
                   help="how many steps to take (default: 24)")
    p.add_argument("--drift", type=float, default=0.3,
                   help="tendency to leap between fields, 0–1 (default: 0.3)")
    p.add_argument("--fast", action="store_true",
                   help="no delays, print all at once")
    p.add_argument("--trace", action="store_true",
                   help="show current word and field after each fragment")
    args = p.parse_args()

    wander(
        seed=args.seed,
        steps=args.steps,
        drift=args.drift,
        delay=0.0 if args.fast else 0.35,
        trace=args.trace,
    )
