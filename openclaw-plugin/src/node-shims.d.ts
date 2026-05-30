declare const process: {
  env: Record<string, string | undefined>;
};

declare module "node:child_process" {
  export function execFile(
    file: string,
    args: readonly string[],
    options: {
      env?: Record<string, string | undefined>;
      maxBuffer?: number;
    },
    callback: (error: unknown, stdout: string, stderr: string) => void,
  ): unknown;
}

declare module "node:util" {
  export function promisify(fn: unknown): unknown;
}
