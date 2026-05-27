# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

CHAT-80: the classic Pereira & Warren (1980s) natural language question-answering system, packaged as a SWI-Prolog pack. It answers English questions about geography (countries, capitals, rivers, cities, etc.) by parsing them into Prolog queries and running those against a built-in database.

## Running

Load from the project root:

```prolog
swipl -g "use_module(prolog/chat80)"
```

Interactive session:

```prolog
?- hi.
Question: what is the capital of france?
```

Process a question programmatically (input is a list of atoms):

```prolog
?- chat_process([what, is, the, capital, of, france, ?], A).
A = [paris].
```

Run the standard 23-question test suite with timing:

```prolog
?- test_chat.
```

Run the suite N times for performance profiling:

```prolog
?- time(rtest_chats(20)).
```

Demo queries from inside a session:

```prolog
?- demo(mini).   % small set of yes/no questions
?- demo(main).   % full 23-question set
```

## Architecture

The pipeline has four stages, each exposed individually in `prolog/chat80.pl`:

| Stage | Predicate | Key module |
|---|---|---|
| Parse | `chat_parse/2` | `newg.pl`, `xgrun.pl` (DCG grammar + runtime) |
| Semantics | `chat_semantics/2` | `scopes.pl`, `slots.pl`, `templa.pl` |
| Optimize | `chat_optimize/2` | `qplan.pl` |
| Evaluate | `chat_answer/2` | `talkr.pl`, `aggreg.pl` |

`chat_process/2` runs all four in sequence.

**Entry points:**
- `prolog/chat80.pl` — the SWI-Prolog module that exports the public API and loads everything.
- `prolog/chat80/chat.pl` — the internal loader; consults all submodules in dependency order.
- `prolog/chat80/chattop.pl` — top-level control predicates (`hi/0`, `test_chat/0`, `process/2`, `ed/3` test examples, `eg/1` mini demos).

**Database files** (geographic facts): `world0.pl`, `rivers.pl`, `cities.pl`, `countr.pl`, `contai.pl`, `border.pl`.

**Linguistic modules**: `newdic.pl` (syntactic dictionary), `clotab.pl` (attachment tables), `readin.pl` (tokeniser), `ptree.pl` (parse tree pretty-printer).

**Operator definitions** (`chatops.pl`): defines `~=`, `=+`, `=:`, `:`, `&`, `~`, `--`, `ject` — load this first if working on any submodule.

## Python reimplementation (`chat80.py`)

A self-contained Python/NLTK reimplementation of CHAT-80 in a single file (~1240 lines).

**Run:**
```bash
python3 chat80.py                 # interactive REPL
python3 chat80.py --demo          # run the 24 canonical demo questions
python3 chat80.py "What is the capital of France?"
```

Inside the REPL, prefix a question with `debug ` to see normalisation and pattern matching.

**Architecture:**

| Layer | Lines | Description |
|---|---|---|
| Knowledge base | 73–455 | Static dicts: countries (name, capital, area, pop, continent), land borders, sea/ocean borders, rivers, cities — circa-1980 values |
| Lexicon / normalisation | 461–656 | Multi-word glueing, contraction expansion, genitive stripping, adjectival continent forms (`european` → `in_europe`), plural lemmatisation via WordNet |
| Pattern handlers | 725–970 | ~40 functions, one per query type (capital lookup, borders, superlatives, aggregates, filtered population, landlocked, etc.) |
| Pattern table | 977–1115 | Ordered `(regex, handler)` pairs tried with `re.fullmatch` against the normalised question; more-specific patterns first |
| `ask()` | 1122–1137 | Normalises input, tries each pattern in order, calls matched handler |
| Demo / REPL | 1144–1238 | 24 demo questions, interactive REPL, CLI entry point |

Key trade-off vs. the Prolog original: no DCG/unification — regex pattern matching after normalisation.

## SWI-Prolog pack metadata

`pack.pl` declares this as a redistributable pack named `chat80` version `1.1`. The pack home is `https://github.com/JanWielemaker/chat80.git`.
