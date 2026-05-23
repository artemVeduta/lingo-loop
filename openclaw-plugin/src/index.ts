// Language Tutor plugin entry for the OpenClaw host.
//
// Uses focused SDK subpath imports (NOT a whole-SDK wildcard import) per the
// OpenClaw plugin model: https://docs.openclaw.ai/plugins
//
// Capability stance (mirrors src/language_tutor/adapters/registry.py OpenClaw
// defaults): text supported; lifecycle start = first_message; lifecycle end =
// not_available; boot context is built on the first tutor message. Any
// side-effectful / binary-dependent tool is registered opt-in only.

import { defineToolPlugin } from "openclaw/plugin-sdk/tool-plugin";
import { Type } from "typebox";

export default defineToolPlugin({
  id: "language-tutor",
  name: "Language Tutor",
  description:
    "Text-only language tutor adapter for OpenClaw. Builds boot context on the first tutor message and exposes core text-modality tutor tools.",
  tools: (tool) => [
    // First-message boot trigger: OpenClaw has no SessionStart-style hook, so
    // the tutor assembles boot context the first time the learner messages
    // the tutor.
    tool({
      name: "language_tutor.boot_context",
      description:
        "Assemble learner boot context (profile, preferences, focus) on the first tutor message.",
      parameters: Type.Object({
        sessionId: Type.Optional(Type.String()),
      }),
      async execute(_params, _config, _context) {
        // Pure text assembly only. No persistence or host-specific behavior
        // here; the core tutor owns boot-context generation.
        return { sections: [] as string[] };
      },
    }),
    // Text-modality tutor tool (reading / lesson / transcript / vocab /
    // writing / progress are all text-only flows). No side effects beyond
    // returning text.
    tool({
      name: "language_tutor.text_exercise",
      description:
        "Present and evaluate a text-only tutor exercise (reading, lesson, transcript, vocab, writing, progress).",
      parameters: Type.Object({
        modality: Type.String(),
        payload: Type.Optional(Type.Record(Type.String(), Type.Unknown())),
      }),
      async execute(params, _config, _context) {
        return { modality: params.modality, text: "" };
      },
    }),
    // Side-effectful / binary-dependent tool. Shells out to the local tutor
    // CLI, so it is OPT-IN ONLY and gated behind a user allowlist.
    tool({
      name: "language_tutor.run_cli",
      description:
        "Invoke the local language-tutor CLI. Binary-dependent and side-effectful; opt-in only.",
      optional: true,
      parameters: Type.Object({
        command: Type.Array(Type.String()),
      }),
      async execute(params, _config, _context) {
        // Execution is performed by the host only after the user allowlists
        // it.
        return { command: params.command };
      },
    }),
  ],
});
