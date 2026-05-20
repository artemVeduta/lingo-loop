from __future__ import annotations

from language_tutor.dal.paths import resolve_paths
from language_tutor.schemas import LearnerProfile
from language_tutor.setup import read_setup, write_setup


def test_setup_round_trip(tutor_home) -> None:  # type: ignore[no-untyped-def]
    paths = resolve_paths(tutor_home)
    write_setup(paths, LearnerProfile(native_language="en", target_language="uk"))
    state = read_setup(paths)
    assert state.profile.target_language == "uk"
    assert state.preferences.session_length == 10
