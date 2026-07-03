/**
 * V10 选项 B · OpenAPI Codegen 脚本
 *
 * 生成真实后端 OpenAPI contract:
 *  - 默认从 API_BASE/openapi.json 拉取
 *  - BACKEND_OPENAPI_FROM_APP=1 时直接用后端 FastAPI app.openapi() 生成 spec
 *
 * 失败即失败: 不再写入占位文件假通过。
 */
import { execFileSync } from 'node:child_process';
import { existsSync, mkdirSync, writeFileSync, rmSync } from 'node:fs';
import { readFile } from 'node:fs/promises';

const API_BASE = process.env.API_BASE ?? 'http://localhost:8000';
const TYPES_OUTPUT = 'src/types/api-generated.d.ts';
const SCHEMAS_OUTPUT = 'src/schemas/api-generated.ts';
const SPEC_OUTPUT = '.openapi-tmp.json';

function ensureOutputDirs(): void {
  if (!existsSync('src/types')) mkdirSync('src/types', { recursive: true });
  if (!existsSync('src/schemas')) mkdirSync('src/schemas', { recursive: true });
}

async function fetchOpenApiSpec(): Promise<unknown> {
  if (process.env.BACKEND_OPENAPI_FROM_APP === '1') {
    console.log('📡 从后端 FastAPI app.openapi() 生成 OpenAPI spec ...');
    const stdout = execFileSync(
      'uv',
      [
        'run',
        '--python',
        '3.11',
        '--with-requirements',
        'requirements-admin.txt',
        '--with-requirements',
        'requirements-dev.txt',
        'python',
        '-c',
        "import json; from admin.app import create_app; app=create_app(); print(json.dumps(app.openapi(), ensure_ascii=False))",
      ],
      { encoding: 'utf-8', cwd: '../..' },
    );
    return JSON.parse(stdout);
  }

  const url = `${API_BASE}/openapi.json`;
  console.log(`📡 拉取 OpenAPI spec: ${url}`);
  const res = await fetch(url);
  if (!res.ok) {
    throw new Error(`Failed to fetch ${url}: HTTP ${res.status}`);
  }
  return res.json();
}

function generateTypes(specPath: string): void {
  console.log('🔧 生成 src/types/api-generated.d.ts ...');
  execFileSync('npx', ['openapi-typescript', specPath, '-o', TYPES_OUTPUT], { stdio: 'inherit', shell: true });
}

function generateSchemas(specPath: string): void {
  console.log('🔧 生成 src/schemas/api-generated.ts ...');
  execFileSync('npx', ['openapi-zod-client', specPath, '-o', SCHEMAS_OUTPUT], { stdio: 'inherit', shell: true });
}

function looksLikeStub(content: string): boolean {
  const trimmed = content.trim();
  const firstLines = trimmed.split(/\r?\n/).slice(0, 12).join('\n');
  if (trimmed === 'export {};') return true;
  if (/^\/\/\s*(占位类型|占位 schema|placeholder|stub)/i.test(firstLines)) return true;
  if (trimmed.length < 500 && /占位|placeholder|stub|真实后端启动后|后端 OpenAPI 联通后/i.test(trimmed)) return true;
  return false;
}

async function verifyGeneratedFiles(): Promise<void> {
  const typesContent = await readFile(TYPES_OUTPUT, 'utf-8');
  const schemasContent = await readFile(SCHEMAS_OUTPUT, 'utf-8');

  if (looksLikeStub(typesContent) || looksLikeStub(schemasContent)) {
    throw new Error('Codegen 输出仍是占位/stub 文件');
  }
  if (!/export interface paths\b/.test(typesContent)) {
    throw new Error(`${TYPES_OUTPUT} 未包含 openapi-typescript paths 接口`);
  }
  if (!/\/api\//.test(typesContent)) {
    throw new Error(`${TYPES_OUTPUT} 未包含任何 /api/ 路径`);
  }
  if (!/export const|export default|makeApi|z\.object/.test(schemasContent)) {
    throw new Error(`${SCHEMAS_OUTPUT} 未包含可用 schema/client 导出`);
  }
  if (/: any\b/.test(typesContent)) {
    throw new Error(`${TYPES_OUTPUT} 包含 ': any'，G1 0-any 闸门失败`);
  }
}

async function generate(): Promise<void> {
  ensureOutputDirs();
  const spec = await fetchOpenApiSpec();
  writeFileSync(SPEC_OUTPUT, JSON.stringify(spec, null, 2));
  try {
    generateTypes(SPEC_OUTPUT);
    generateSchemas(SPEC_OUTPUT);
    await verifyGeneratedFiles();
    console.log('✅ Codegen 完成: OpenAPI 类型/schema 已生成且通过 G1 contract gate');
  } finally {
    if (existsSync(SPEC_OUTPUT)) rmSync(SPEC_OUTPUT);
  }
}

void generate().catch((err: unknown) => {
  const message = err instanceof Error ? err.message : String(err);
  console.error(`❌ Codegen 失败: ${message}`);
  process.exit(1);
});
