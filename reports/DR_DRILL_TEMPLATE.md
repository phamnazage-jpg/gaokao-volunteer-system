# DR_DRILL_TEMPLATE

日期:
负责人:
目标主机:
备用/异机主机:
对应快照目录:
对应工单/变更号:

## 1. 演练目标

- 验证目标主机可生成真实快照
- 验证 `bash scripts/backup_verify.sh --from-backup <backup-dir>` 可在目标主机跑通
- 验证恢复副本最小服务链：
  - `health_status = 200`
  - `portal_status = 200`
  - `portal_report = 200`
  - `portal_pdf = 200`
- 记录密钥位置、恢复耗时、异常与补救动作

## 2. 前置条件

- 目标主机已部署当前版本代码
- 目标主机已配置 `.env` / secrets / backup root
- 目标主机存在可执行的 `bash scripts/backup_snapshot.sh`
- 若做异机演练，备用主机已具备读取快照与最小运行依赖

## 3. 执行记录

### 3.1 生成真实快照

命令:

```bash
bash scripts/backup_snapshot.sh <backup-root>
```

结果:

- 快照目录:
- manifest 是否生成:
- 失败/异常:

### 3.2 从快照执行 restore smoke

命令:

```bash
bash scripts/backup_verify.sh --from-backup <backup-dir>
```

结果:

- `manifest_ok`:
- `sqlite_ok`:
- `health_status`:
- `portal_status`:
- `portal_report`:
- `portal_pdf`:
- 耗时:
- 失败/异常:

### 3.3 异机恢复（如执行）

命令:

```bash
bash scripts/backup_verify.sh --from-backup <backup-dir>
```

结果:

- 主机:
- 是否成功:
- 差异/异常:

## 4. 密钥与配置核对

- JWT secret 位置:
- Portal token secret 位置:
- Fernet key 位置:
- Payment key/cert 位置:
- 负责人:

## 5. 结论

- [ ] 目标主机快照成功
- [ ] 目标主机 restore smoke 成功
- [ ] 异机恢复成功（若适用）
- [ ] 可归档为上线前灾备演练证据

## 6. 后续动作

- 待修复问题:
- 风险等级:
- 下一次演练时间:
