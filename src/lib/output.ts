import { spawnSync } from 'node:child_process';

export function printWithOptionalPager(content: string, usePager: boolean): void {
  if (!usePager) {
    console.log(content);
    return;
  }

  try {
    const pagerResult = spawnSync('less', ['-R'], {
      input: content,
      stdio: ['pipe', 'inherit', 'inherit'],
      encoding: 'utf-8'
    });

    if (pagerResult.error || pagerResult.status !== 0) {
      console.log(content);
    }
  } catch {
    console.log(content);
  }
}
