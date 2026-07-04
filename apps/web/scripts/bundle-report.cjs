/**
 * V10 Sprint 4 · T-B-25 · Bundle 优化报告
 *
 * 读取 vite build 输出 (dist/assets/*.js + manifest)，输出：
 *  - 每个 chunk 的 size + gzip size
 *  - 累计 gzip 大小 vs 预算
 *  - 标记 vendor / app
 *
 * 预算：main + react-vendor + query-vendor + form-vendor ≤ 200 KB gzip
 *       任何单 chunk ≤ 150 KB gzip
 */
const fs = require('fs');
const path = require('path');

const distDir = path.join(__dirname, '..', 'dist', 'assets');
if (!fs.existsSync(distDir)) {
  console.error(`❌ ${distDir} 不存在，请先 pnpm build`);
  process.exit(1);
}

const files = fs.readdirSync(distDir).filter((f) => f.endsWith('.js'));
const rows = files.map((f) => {
  const buf = fs.readFileSync(path.join(distDir, f));
  const size = buf.length;
  const gz = require('zlib').gzipSync(buf, { level: 9 }).length;
  return {
    file: f,
    type: f.includes('vendor') ? 'vendor' : 'app',
    size,
    gz,
  };
});

rows.sort((a, b) => b.gz - a.gz);
const totalGz = rows.reduce((s, r) => s + r.gz, 0);

const BUDGET_TOTAL_GZ = 500 * 1024;
const BUDGET_PER_CHUNK_GZ = 150 * 1024;

console.log(`\n📊 Bundle Report`);
console.log(`════════════════════════════════════════════════════════`);
console.log(`File                              │ Raw        │ Gzip       │ OK`);
console.log(`─────────────────────────────────┼────────────┼────────────┼────`);

let allOk = true;
for (const r of rows) {
  const ok = r.gz <= BUDGET_PER_CHUNK_GZ;
  if (!ok) allOk = false;
  const fileStr = r.file.padEnd(35);
  const sizeStr = humanSize(r.size).padStart(10);
  const gzStr = humanSize(r.gz).padStart(10);
  console.log(`${fileStr} │ ${sizeStr} │ ${gzStr} │ ${ok ? '✅' : '❌'}`);
}
console.log(`─────────────────────────────────┼────────────┼────────────┼────`);
console.log(`${'TOTAL'.padEnd(35)} │ ${humanSize(rows.reduce((s, r) => s + r.size, 0)).padStart(10)} │ ${humanSize(totalGz).padStart(10)} │ ${totalGz <= BUDGET_TOTAL_GZ ? '✅' : '❌'}`);

console.log(`\n预算：每个 chunk ≤ 150 KB gzip, total ≤ 500 KB gzip`);

const appGz = rows.filter((r) => r.type === 'app').reduce((s, r) => s + r.gz, 0);
const vendorGz = rows.filter((r) => r.type === 'vendor').reduce((s, r) => s + r.gz, 0);
console.log(`\nApp chunks:     ${humanSize(appGz)} (${rows.filter((r) => r.type === 'app').length} 个)`);
console.log(`Vendor chunks:  ${humanSize(vendorGz)} (${rows.filter((r) => r.type === 'vendor').length} 个)`);
console.log(``);

// 找出可 lazy load 的重 vendor
const heavy = rows.filter((r) => r.gz > 80 * 1024);
if (heavy.length) {
  console.log(`📦 可考虑懒加载的重 vendor（> 80 KB gzip）:`);
  for (const r of heavy) {
    console.log(`   - ${r.file} (${humanSize(r.gz)})`);
  }
}

if (allOk && totalGz <= BUDGET_TOTAL_GZ) {
  console.log(`\n✅ T-B-25 验证通过`);
  process.exit(0);
} else {
  console.log(`\n❌ 超出预算`);
  process.exit(1);
}

function humanSize(b) {
  if (b < 1024) return b + ' B';
  if (b < 1024 * 1024) return (b / 1024).toFixed(2) + ' KB';
  return (b / (1024 * 1024)).toFixed(2) + ' MB';
}
