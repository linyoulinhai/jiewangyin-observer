# 资料库、下载、复制与部署

先看[主要资料库名称、数据库用途与部署优先级](deployment-options.md)：已有可用国内空间、国内静态候选、国内目录/下载、跨境备用，最后视频与渲染。原始私人SQLite不随部署包发布，静态公开目录无需新开数据库。

**现在可复制的资料源**：公开`source-catalog.json/csv`；**维护端私有索引**：`jiewangyin-observer-private/records.json`；**完整互助后台数据库**：D1绑定`DB`，本机`.preview/community.sqlite3`。详见部署核对页。

## 各平台与普通人接力

具体84项路线见[多平台传播保存指南](multiplatform-distribution.md)。不是每位用户都要学Git：可下载公开传播导读包，先读TXT，按需要转发、另存表格或解压网站包。包内同时保留[原作者与提供者署名](../ACKNOWLEDGEMENTS.md)。

微信/QQ传文件，图文和视频平台展示，国内文档放目录，国内网盘与Release放下载副本，不同维护者与运营方保存独立版本。传播清单与实测结果分开；尚未开通的平台不登记为真实备用网址。

## 只想保存或转发

在[最新Releases](https://github.com/linyoulinhai/jiewangyin-observer/releases/latest)下载标注“公开网站包”的ZIP，解压后查看 `README.txt` 与 `index.html`。浏览器本地文件策略和手机文件预览器存在差异；独立 `tools/source-directory.html`、CSV与JSON是备用阅读办法。

上传公开包内文件到静态托管根目录即可展示档案。保留许可证、来源、演示标记和更正入口。静态副本不包含线上互助、服务器收件和审核服务，这些入口不能因为页面存在便当成已可用。

也可单独保存 `source-catalog.json` 和 `source-catalog.csv`；这比整份源码更适合普通资料查阅。下载后记录版本日期，公开来源目录和私人审核原件不要混在一起。

## 开发者运行完整本机试用

```sh
git clone https://github.com/linyoulinhai/jiewangyin-observer.git
cd jiewangyin-observer
npm ci
npm run dev
```

Node.js需24，Python需3。本机地址为 `http://127.0.0.1:8770/`，终端显示模拟用户和管理员入口。测试数据库与附件在 `.preview/`，被Git忽略。服务器只绑定127.0.0.1，不适合作为公网服务器。

检查和打包：

```sh
npm test
node scripts/check-concept.cjs
python3 scripts/package-public.py
npm run build
```

构建生成 `dist/client/` 与 `dist/server/index.js`。公开ZIP使用文件白名单，不能把真实附件放入 `dist/assets/` 再误当作演示素材发布。静态发布时可使用公开ZIP或 `dist/client/`；完整后台不是静态托管功能。

## 完整后台的部署条件

仓库未配置一键生产部署，也不携带原站项目ID或任何生产数据库、桶、管理员邮箱。

1. 配置自己的可信身份层；平台登录仅在支持该身份验证的托管分发器后可用。外部部署需要另接认证，剥离并覆盖客户端伪造的身份头。
2. 创建自己的D1数据库，按顺序应用 `drizzle/` 迁移；不要修改已上线的旧迁移。
3. 创建自己的R2桶，绑定 `BUCKET`；D1绑定名是 `DB`，静态文件绑定名是 `ASSETS`。
4. 管理员邮箱通过运行时secret `MODERATOR_EMAIL` 设置，不能填入前端、GitHub或构建静态目录。
5. 绑定自己的资源ID和域名，检查作者、回执与管理员权限以及上传、导出、撤回行为。
6. 在公开运行前做真机网络和上传测试，确认备份、恢复、配额及审核维护能力。

`dist/server/wrangler.json` 是构建生成的本机占位配置，数据库和桶名称不是已创建的线上资源；不能直接照搬上线。`.openai/hosting.example.json` 只展示绑定名称，没有可用项目ID。使用Sites时应在自己的新项目中生成 `.openai/hosting.json`，而不是复用原站ID；该实际绑定文件被本仓库忽略。

## 配套工具

媒体分包：打开 `tools/手机媒体分包工具/index.html`，浏览器本地操作，详见同目录手机操作说明。核心测试可运行 `node tools/手机媒体分包工具/tests/core.test.cjs`。浏览器测试还需Playwright、浏览器与FFmpeg，没有作为主项目默认依赖安装。

线索导入：进入 `tools/线索收集工具/`，运行 `python3 -m unittest -v`。README说明JSON/JSONL格式和可选接口；默认数据库保存在用户数据目录，真实输出不能提交Git。示例输入仅为虚构数据，接口未进行真实凭证联调。

## 更新副本

重新生成公开ZIP后保留版本日期和SHA256，重新发布新的Release；不要假称旧下载会自动被召回。GitHub源码不自动发布到原站，也不会包含线上新增投稿；公开动态档案需另外用获准导出功能保存。
