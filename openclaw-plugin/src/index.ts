import { execFile } from "node:child_process";
import { promisify } from "node:util";

import { defineToolPlugin } from "openclaw/plugin-sdk/tool-plugin";
import { Type } from "typebox";

const execFileAsync = promisify(execFile) as (
  file: string,
  args: readonly string[],
  options: {
    env?: Record<string, string | undefined>;
    maxBuffer?: number;
  },
) => Promise<{ stdout: string }>;
const TUTOR_BIN = process.env.LANGUAGE_TUTOR_TUTOR_BIN ?? "tutor";
const MAX_STDOUT_BYTES = 1024 * 1024;
const ALLOWED_ROOTS = new Set([
  "session-start",
  "checkpoint",
  "boot-context",
  "setup",
  "vocab",
  "writing",
  "reading",
  "lesson",
  "progress",
  "render",
  "host",
  "doctor",
]);

async function runTutor(command: string[], payload?: unknown): Promise<unknown> {
  if (command.length === 0) {
    throw new Error("language_tutor CLI command must not be empty");
  }
  const [root, ...args] = command;
  if (!ALLOWED_ROOTS.has(root)) {
    throw new Error(`Unsupported tutor command root: ${root}`);
  }
  const execArgs = [...command];
  if (payload !== undefined) {
    execArgs.push(JSON.stringify(payload));
  }
  const { stdout } = await execFileAsync(TUTOR_BIN, execArgs, {
    env: process.env,
    maxBuffer: MAX_STDOUT_BYTES,
  });
  return JSON.parse(stdout);
}

export default defineToolPlugin({
  id: "language-tutor",
  name: "Language Tutor",
  description:
    "Text-only language tutor adapter for OpenClaw. Builds boot context on the first tutor message and exposes core text-modality tutor tools.",
  tools: (tool) => [
    tool({
      name: "language_tutor.boot_context",
      description:
        "Assemble learner boot context (profile, preferences, focus) on the first tutor message.",
      parameters: Type.Object({
        hostConversationId: Type.Optional(Type.String()),
      }),
      async execute(params) {
        return runTutor(["session-start", "--json"], {
          host: "openclaw",
          host_conversation_id: params.hostConversationId,
        });
      },
    }),
    tool({
      name: "language_tutor.text_exercise",
      description:
        "Present and evaluate a text-only tutor exercise (reading, lesson, transcript, vocab, writing, progress).",
      parameters: Type.Object({
        command: Type.Array(Type.String()),
        payload: Type.Optional(Type.Record(Type.String(), Type.Unknown())),
      }),
      async execute(params) {
        return runTutor(params.command, params.payload);
      },
    }),
    tool({
      name: "language_tutor.run_cli",
      description:
        "Invoke the local language-tutor CLI. Binary-dependent and side-effectful; opt-in only.",
      optional: true,
      parameters: Type.Object({
        command: Type.Array(Type.String()),
        payload: Type.Optional(Type.Record(Type.String(), Type.Unknown())),
      }),
      async execute(params) {
        return runTutor(params.command, params.payload);
      },
    }),
  ],
});
