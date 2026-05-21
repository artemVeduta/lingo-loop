# Vocabulary Card Contract

## Card Types

### Standard

Standard cards show a prompt and grade against accepted answers.

```json
{
  "card_type": "standard",
  "target": "privit",
  "prompt": "hello",
  "accepted_answers": ["privit"],
  "tags": ["greetings"]
}
```

### Cloze

Cloze cards show sentence context with the hidden answer omitted.

```json
{
  "card_type": "cloze",
  "target": "privit",
  "prompt": "{{answer}} is a common greeting.",
  "accepted_answers": ["privit"],
  "tags": ["greetings", "cloze"]
}
```

## Normalization

One shared normalizer applies to duplicate identity and tag matching:

- Unicode NFKC normalization.
- `casefold` for case-insensitive matching.
- Trim and collapse whitespace.
- Normalize apostrophe variants.
- Trim boundary punctuation.

The normalizer must be unit-tested with case, whitespace, punctuation, and tag-order variants.

## Duplicate Rules

Duplicate identity uses only:

- `card_type`
- normalized `target`
- normalized `prompt`

The following fields never affect duplicate identity:

- `accepted_answers` variants beyond the canonical target
- `hint`
- `notes`
- `source`
- `tags`
- seed file path
- import order

## Metadata Merge Rules

When an imported card matches an existing card:

- accepted-answer variants are unioned by normalized value
- notes are unioned by normalized value
- sources are unioned by normalized value
- tags are unioned by normalized tag key
- existing values are not removed
- review state and review attempts are untouched

Manual duplicate adds are rejected by default and report the existing item id.

## Drill Rendering Rules

Standard drill prompt:

```text
Prompt: hello
```

Cloze drill prompt:

```text
Prompt: ____ is a common greeting.
```

Cloze feedback reveal:

```text
Sentence: privit is a common greeting.
Accepted answer: privit
```

Renderers must be deterministic and covered by golden tests.

## History Rules

Review history output includes:

- card id and card type
- prompt or cloze context
- current due status
- every review attempt in chronological order
- learner answer
- verdict
- reviewed time
- previous and next review state

Text rendering may summarize long histories for readability, but JSON output remains complete.
