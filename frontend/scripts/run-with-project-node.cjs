const { existsSync } = require('node:fs');
const { join } = require('node:path');
const { spawnSync } = require('node:child_process');

const projectRoot = join(__dirname, '..');
const candidates = [
  join(projectRoot, 'node_modules', 'node', 'bin', 'node.exe'),
  join(projectRoot, 'node_modules', 'node', 'bin', 'node'),
];
const runtime = candidates.find(existsSync);
if (!runtime) {
  console.error('Project-local Node runtime is missing. Run npm install.');
  process.exit(1);
}
const [, , entry, ...args] = process.argv;
const result = spawnSync(runtime, [join(projectRoot, entry), ...args], {
  cwd: projectRoot,
  stdio: 'inherit',
  env: process.env,
});
process.exit(result.status ?? 1);
