# Debug Mode (`chat80.py`)

Prefix any question with `debug ` in the REPL to see how it is processed:

```
Question: debug what is the capital of france?
  normalised: 'what is the capital of france'
  matched:    what is the capital of (?P<country>...)
paris
```

## Output lines

### `normalised:`

The question after `normalize()` runs. This includes:

- Multi-word glueing (e.g. `south america` → `south_america`)
- Contraction expansion (e.g. `what's` → `what is`)
- Genitive stripping (e.g. `france's` → `france`)
- Adjectival continent forms (e.g. `european` → `in_europe`)
- Plural lemmatisation via WordNet (e.g. `countries` → `country`)

### `matched:`

The specific regex pattern string from the `PATTERNS` table that `re.fullmatch` succeeded against the normalised text. This also identifies which handler function will be called to produce the answer.

Patterns are tried in order; the first match wins. If no pattern matches, only `normalised:` is printed and the response is `I don't understand that question.`
