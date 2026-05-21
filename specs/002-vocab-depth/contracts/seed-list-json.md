# Seed List JSON Contract

Seed lists are human-editable `.json` files containing a top-level list of card objects. They are import inputs only; the canonical learning record after import is SQLite.

## Top-Level Shape

```json
[
  {
    "card_type": "standard",
    "target": "privit",
    "prompt": "hello",
    "accepted_answers": ["privit"],
    "tags": ["greetings"],
    "notes": ["informal greeting"],
    "source": "uk-basic"
  },
  {
    "card_type": "cloze",
    "target": "privit",
    "prompt": "{{answer}} is a common greeting.",
    "accepted_answers": ["privit"],
    "tags": ["greetings", "cloze"],
    "source": "uk-basic"
  }
]
```

## Fields

| Field | Required | Type | Notes |
|-------|----------|------|-------|
| `card_type` | no | `standard` or `cloze` | Defaults to `standard` when omitted. |
| `target` | yes | string | Target-language content for standard cards; hidden answer for cloze cards. |
| `prompt` | yes | string | Cue for standard cards; sentence context with exactly one `{{answer}}` marker for cloze. |
| `accepted_answers` | yes | list of strings | Must contain at least one non-empty value. Variants merge additively on import. |
| `hint` | no | string | User-visible hint. |
| `tags` | no | list of strings | Normalized for matching; display values remain learner-visible. |
| `notes` | no | string or list of strings | Merged additively for matching cards. |
| `source` | no | string or list of strings | Merged additively for matching cards. |

Unknown fields are invalid.

## Import Semantics

- The import validates each list entry independently.
- A valid new duplicate identity creates one card.
- A valid matching duplicate identity updates only additive metadata: notes, source, tags, and accepted-answer variants.
- `created` means a new card was stored.
- `updated` means a matching card received at least one new additive value.
- `skipped` means a matching card already had all supplied additive values.
- `invalid` means the entry failed validation; the entry result includes `index`, stable error code, message, and repair hint.
- Existing metadata is never removed by import.
- Existing review state and review history are never reset by import.
- Invalid entries return repair hints and do not block other entries.
- Interrupted entries roll back their own transaction.
- Malformed JSON, non-list top-level JSON, empty lists, unreadable paths, non-`.json` paths, unknown fields, unsupported card types, empty metadata values, and invalid cloze markers must produce deterministic repair feedback.

## Duplicate Identity

Duplicate identity is:

```text
card_type + normalized(target) + normalized(prompt)
```

Metadata fields do not participate in identity.

Normalization applies Unicode NFKC, `casefold`, trimmed/collapsed whitespace, apostrophe variant folding, and leading/trailing Unicode punctuation trimming. Internal punctuation remains part of identity.

## Validation Examples

Invalid: cloze prompt with no marker.

```json
[
  {
    "card_type": "cloze",
    "target": "privit",
    "prompt": "A common greeting.",
    "accepted_answers": ["privit"]
  }
]
```

Invalid: cloze prompt with two markers.

```json
[
  {
    "card_type": "cloze",
    "target": "privit",
    "prompt": "{{answer}} and {{answer}} again.",
    "accepted_answers": ["privit"]
  }
]
```

Valid duplicate update: adds a tag and source without deleting prior metadata.

```json
[
  {
    "card_type": "standard",
    "target": "privit",
    "prompt": "hello",
    "accepted_answers": ["privit"],
    "tags": ["daily"],
    "source": "review-list"
  }
]
```
