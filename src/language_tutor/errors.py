from __future__ import annotations

import json
from typing import NoReturn

import click


class TutorError(Exception):
    def __init__(self, code: str, message: str, repair_hint: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.repair_hint = repair_hint


def error_payload(error: TutorError) -> dict[str, dict[str, str]]:
    return {
        "error": {
            "code": error.code,
            "message": error.message,
            "repair_hint": error.repair_hint,
        }
    }


def fail_json(error: TutorError) -> NoReturn:
    click.echo(json.dumps(error_payload(error), ensure_ascii=False, sort_keys=True))
    raise click.exceptions.Exit(1)
