# chat80 — Session Notes (2026-05-23)

---

## /init — Generate CLAUDE.md

**User:** `/init`

**Assistant:** Analysed the codebase and created `CLAUDE.md` covering:

- What the project is (CHAT-80, a classic Pereira & Warren NLP system, packaged as a SWI-Prolog pack)
- How to run it (interactively via `hi/0`, programmatically via `chat_process/2`, test suite via `test_chat/0`)
- The four-stage pipeline architecture: Parse → Semantics → Optimize → Evaluate
- Key entry-point files and the role of each module
- The geographic database files

---

## Add and Commit

**User:** add and commit

**Assistant:** Staged `CLAUDE.md` and committed:

```
e50806c Add CLAUDE.md with architecture overview and usage guidance
```

---

## How the Parser Works

**User:** Explain how the parser works to someone who doesn't understand prolog (except for database access)

**Assistant:**

### Step 1: Tokenisation (`readin.pl`)

The raw text is read character-by-character and turned into a flat list of atoms:

```
"What is the capital of France?"
→  [what, is, the, capital, of, france, ?]
```

Everything is lowercased. Digit sequences become `nb(N)` terms (e.g. `nb(200)`). After this step the parser sees only that list.

---

### Step 2: The Grammar — Functions That Eat a Word List

The grammar in `newg.pl` is a collection of functions, each with this contract:

> *"Give me a word list. I will try to consume some words from the front that match my grammatical category, and return whatever's left over."*

For example, a simplified version of `noun` says: "I match if the first word in the list is a known noun." The result — the thing actually built — is a parse tree node. So matching doesn't just succeed/fail; it simultaneously builds structure.

These functions call each other recursively, forming a top-down parser:

```
sentence
 └─ wh_question
     ├─ variable_q       ("what")
     └─ question
         └─ s
             ├─ subj (np → "the capital")
             ├─ verb ("is")
             └─ verb_args (np → "of France")
```

Each level consumes its slice of the word list and passes the remainder to the next level.

---

### Step 3: The Dictionary — It Really Is a Database (`newdic.pl`)

Every leaf of that recursive descent ends in a dictionary lookup, and the dictionary is literally just a table of facts — exactly what you're used to:

```prolog
verb_form(borders,  border, pres+fin,  3+sin).
verb_form(bordered, border, past+fin,  _).
noun_sin(capital).
noun_plu(countries, country).
prep(of).
det(the, No, the(No), def).
```

When the grammar reaches a terminal (a single word), it queries this table: "is `borders` a verb form? What's its root and tense?" The grammar rules compose; the dictionary is flat data. This separation is deliberate — adding new vocabulary is adding rows, not changing the grammar.

---

### Step 4: The Gap Mechanism — Handling Moved Words (`xgrun.pl`)

This is the clever part. English lets words "move" away from where they belong syntactically:

> *"What does France border?"*

Here `what` appears at the front but is grammatically the **object** of `border`. The grammar needs to record that `what` is pending and fill it in later when it reaches the object position.

The mechanism is a **gap register** — a second list threaded through every single function call alongside the word list:

```
sentence(Tree, WordList_in, WordList_out, GapReg_in, GapReg_out)
```

The key is in `xgrun.pl`, the 35-line runtime kernel. There are only two ways to match a terminal word:

```prolog
% From the word list (normal case)
terminal(T, [T|S], S, X, X) :- gap(X).

% From the gap register (displaced word)
terminal(T, S, S, x(_, terminal, T, X), X).
```

When `what` is consumed as a wh-pronoun, the grammar doesn't discard it — it stores a "gap marker" saying *"there's an NP-shaped hole to be filled with `what` somewhere ahead."* That marker travels through the gap register until the grammar reaches the object position of `border`. At that point the grammar expects a noun phrase but finds an empty word list; it checks the gap register instead, finds `what` waiting there, and "fills" the gap. The grammar succeeds; the word `what` ends up structurally in the right place in the parse tree.

---

### What Comes Out

The output of `sentence/5` is a nested term — a parse tree:

```prolog
whq(3+sin,
  s(np(name(france),...),
    verb(border,...),
    [arg(dir, np(wh(what),...))],
    []))
```

That tree is then handed to the **semantics** stage (`chat_semantics/2`), which translates it into a Prolog query that gets run against the geographic database.

---

### Summary

| Component | Role | Analogous to |
|---|---|---|
| `readin.pl` | Tokeniser | Lexer / string split |
| `newg.pl` | Grammar rules | Recursive-descent parser functions |
| `newdic.pl` | Word categories and inflections | Database tables |
| `xgrun.pl` | Terminal matching + gap register | Parser engine / iterator |

The grammar and dictionary are cleanly separated: grammarians write rules, lexicographers add rows. The gap register is what lets a parser written in this style handle real English movement constructions without backtracking the whole parse.
