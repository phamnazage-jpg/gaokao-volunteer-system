/**
 * V10 Sprint 4 · T-B-24 · lhci 分数汇总脚本
 * 读 .lighthouseci/lhr-*.json，对每个 URL 计算 P/A/B/S 的 median
 */
const fs = require('fs');
const dir = '.lighthouseci';
const files = fs.readdirSync(dir).filter((f) => f.startsWith('lhr-') && f.endsWith('.json'));
const urlMap = {};
for (const f of files) {
  const j = JSON.parse(fs.readFileSync(`${dir}/${f}`, 'utf8'));
  if (!j.categories || !j.categories.performance) continue;
  const url = j.requestedUrl.replace('http://127.0.0.1:8080', '') || '/';
  if (!urlMap[url]) urlMap[url] = [];
  urlMap[url].push({
    p: Math.round(j.categories.performance.score * 100),
    a: Math.round(j.categories.accessibility.score * 100),
    b: Math.round(j.categories['best-practices'].score * 100),
    s: Math.round(j.categories.seo.score * 100),
  });
}
console.log('URL                perf  a11y  best  seo');
for (const k of Object.keys(urlMap)) {
  const runs = urlMap[k];
  const med = (x) => {
    const arr = runs.map((r) => r[x]).sort((a, b) => a - b);
    const m = Math.floor(arr.length / 2);
    return arr.length % 2 ? arr[m] : Math.round((arr[m - 1] + arr[m]) / 2);
  };
  const ok = (x) => med(x) >= 90 ? '✅' : '❌';
  console.log(
    `${k.padEnd(15)}  ${String(med('p')).padStart(4)}${ok('p')}  ${String(med('a')).padStart(4)}${ok('a')}  ${String(med('b')).padStart(4)}${ok('b')}  ${String(med('s')).padStart(4)}${ok('s')}`,
  );
}
