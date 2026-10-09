# 本次导出验证（2026-10-09）

在新建的GitHub发布目录中安装锁定依赖，并执行以下检查：

- `npm test`：20项后端、权限、附件、导出和恢复测试通过。
- `node scripts/check-concept.cjs`：22路由及筛选、草稿检查通过。
- `npm run build`：可构建静态文件与Worker；没有原站项目绑定时给出明确提示。
- 媒体分包核心测试：48项断言通过，SHA256以Node crypto交叉核验，ZIP以Python核验。
- 线索收集工具：22项单元测试通过，使用虚构输入和模拟接口，不访问真实平台。
- Git暂存文件检查：不包含生产托管绑定、环境凭证、SQLite库、私有原件或回执；常见凭证格式扫描未命中。这是有限检查，不代替完整安全审计。
- 公开文件清单逐项核验Git暂存内容的SHA256，公开ZIP CRC验证通过；CSV保留原始字节，避免Git换行转换使公开清单失配。

`npm audit`报告4项moderate告警，涉及开发用drizzle-kit及其旧esbuild/loader依赖链；自动修复建议涉及主要版本变动，本次未执行强制降级或破坏性升级。现有运行测试通过，不表示依赖不存在风险。后续在单独变更中升级并复验数据库生成流程。

未在本次验证：真实平台采集、真机上传、外部认证部署、独立镜像灾备、全国运营负载。CI模板保存在 `docs/check-workflow.example.yml`。当前GitHub OAuth授权不包含workflow权限，仓库尚未启用Actions自动检查；拥有相应权限后可将模板放入 `.github/workflows/check.yml`。网页体验仍需人工检查。
