# 资料库、部署、传播与备用办法

更新：2026-10-09。排列原则：国内手机可访问优先、免费优先、部署简单、可复制、保留备用。视频与渲染层放后面；84项渠道全部保留。

## 先列主要资料库名称和数据库用途

1. **NCT 全国矫正机构资料档案 / nct-archive**：[goodpsychologistclaw原项目](https://github.com/goodpsychologistclaw/nct-archive)，当前公开目录来源之一，保留Unlicense。
2. **PanDefenseProject**：[FunctionSir及贡献者原项目](https://github.com/FunctionSir/PanDefenseProject)，公开机构目录来源，保留AGPL-3.0。
3. **本站机构资料库 / SQLite**：本地`机构资料库.sqlite3`保存原始来源和整理记录，是私人资料库，不随公开包上传。
4. **私有整理库 / jiewangyin-observer-private**：`records.json`是JSON审核索引，频繁整理；公有库只接收审核导出，不能把私有Git历史合并公开。
5. **公开来源目录 / source-catalog.json、source-catalog.csv**：1251条待核对来源记录，手机可保存、接力者可重建；不是1251家已确认违法的机构。
6. **互助与收件数据库 / Cloudflare D1**：代码绑定名`DB`；本机预览为`.preview/community.sqlite3`。线上数据库由部署者另建，未提供生产资源ID。附件绑定`BUCKET`是存储，不是数据库。

数据提供者完整署名见[致谢](../ACKNOWLEDGEMENTS.md)，可复制审核流程见[公私两库说明](replicable-workflow.md)。来源项目名、JSON索引和SQL数据库分别说明，避免混在一起。

## 再选部署办法

1. **已有可用国内网站空间**：自己或自愿合作方已有域名/空间时，先上传同一份公开静态包；目前没有已确认合作方，不新购服务器。
2. **国内静态部署候选**：依次核对EdgeOne ZIP直接上传、CloudBase已有环境上传文件、ESA函数和Pages；免费资格、域名/区域与正式访问条件详见[最新部署核对](deployment-options.md)。
3. **没有合适网站空间时的手机入口**：腾讯文档/飞书/WPS放公开目录，国内网盘放完整下载包；这是目录/下载入口，不冒充完整论坛。
4. **跨境/特殊网络条件备用**：原Sites、GitHub Pages、Cloudflare Pages等继续保留并单列；GitHub承载维护和发行，但不能是普通国内用户唯一入口。
5. **之后才安排视频与渲染层**：原件、公开播放版和允许转交版分开；播放器、缩略图与转码后置。

EdgeOne默认项目/部署域名在大陆使用的预览链接有效期3小时，不能当作长期宣传链接，见[官方域名说明](https://pages.edgeone.ai/zh/document/domain-overview)。CloudBase默认域名以测试为主且有限频，见[官方管理说明](https://docs.cloudbase.net/hosting/manage)。上传成功与长期访问合格分别验收。

## 再组织普通人的复制与传播

先拿到包 → 另存到手机文件目录 → 转交完整副本 → 回报访问问题并更新版本。每份保留JSON/CSV源、编号、出处、作者、许可、版本和散列；只收藏链接不算另存。小包不要求用户先学习GitHub。

[国内主用](domestic-primary.md)和[跨境备用](overseas-backup.md)分别执行。已有的原站、GitHub公私库/Release和本地公开包继续保留；其他列出的平台仍是候选，没有代你登录网盘、发帖或创建镜像。预算优先0元，后续总支出上限仍为50元/月，未购买服务。

[宣传与网盘交接材料](promotion-kit/README.md)提供可复制文案和图文；维护者用`scripts/build-distribution-kit.py`生成公开导读包，用`scripts/build-replication-kit.py`生成资料源起步包，均不自动上传。视频脚本和预览另在后部使用。

以下84项按部署、保存、接力、传播、备用、视频顺序展示；稳定channel_id不随展示序号改变。原9组来源分类保存在机器目录，正文改为8个执行分组。数量不是已建立平台或独立备份数量；无会员手机和实际网络验证仍待完成。
