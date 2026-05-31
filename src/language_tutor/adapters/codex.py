"""Codex host adapter.

Codex discovers tutor skills from the user's personal skills hub and boots the
tutor on the first tutor-skill invocation. Setup is package-only. This module
exposes the host capability profile and leaves pedagogy, feedback, progress,
and learner state to the tutor core.
"""

from __future__ import annotations

from language_tutor.adapters.registry import capability_profile_for
from language_tutor.schemas import AdapterCapabilityProfile, HostId


def capability_profile() -> AdapterCapabilityProfile:
    return capability_profile_for(HostId.CODEX.value)
