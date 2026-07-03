/**
 * V10 选项 B · OpenAPI Codegen 校验脚本
 *
 * G1 contract gate:
 *  - 生成文件必须存在
 *  - 不允许旧占位 stub 文件假通过
 *  - TypeScript 声明必须包含 OpenAPI paths
 *  - Zod client 输出必须包含可导出 contract/schema 内容
 *
 * 注意: 后端 OpenAPI 文档里可能合法出现“占位密钥”等业务说明，
 * 不能把任意“占位”字样误判为生成文件仍是 stub。
 */
import { existsSync, readFileSync } from 'node:fs';

const TYPES_FILE = 'src/types/api-generated.d.ts';
const SCHEMAS_FILE = 'src/schemas/api-generated.ts';

function fail(message: string): never {
  console.error(`❌ ${message}`);
  process.exit(1);
}

function readRequired(path: string): string {
  if (!existsSync(path)) {
    fail(`Codegen 文件缺失: ${path}; 请运行 pnpm codegen`);
  }
  return readFileSync(path, 'utf-8');
}

function looksLikeStub(content: string): boolean {
  const trimmed = content.trim();
  const firstLines = trimmed.split(/\r?\n/).slice(0, 12).join('\n');
  if (trimmed === 'export {};') return true;
  if (/^\/\/\s*(占位类型|占位 schema|placeholder|stub)/i.test(firstLines)) return true;
  if (trimmed.length < 500 && /占位|placeholder|stub|真实后端启动后|后端 OpenAPI 联通后/i.test(trimmed)) return true;
  return false;
}

const typesContent = readRequired(TYPES_FILE);
const schemasContent = readRequired(SCHEMAS_FILE);

if (looksLikeStub(typesContent)) {
  fail(`${TYPES_FILE} 仍是占位/stub 输出`);
}

if (looksLikeStub(schemasContent)) {
  fail(`${SCHEMAS_FILE} 仍是占位/stub 输出`);
}

if (!/export interface paths\b/.test(typesContent)) {
  fail(`${TYPES_FILE} 未包含 openapi-typescript paths 接口`);
}

if (!/\/api\//.test(typesContent)) {
  fail(`${TYPES_FILE} 未包含任何 /api/ 路径`);
}

if (!/export const|export default|makeApi|z\.object/.test(schemasContent)) {
  fail(`${SCHEMAS_FILE} 未包含可用的 schema/client 导出`);
}

if (/: any\b/.test(typesContent)) {
  fail(`${TYPES_FILE} 包含 ': any'，G1 0-any 闸门失败`);
}

console.log('✅ Codegen contract gate passed: generated OpenAPI types/schemas are non-stub');
