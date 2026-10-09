# 数据库与资料源 → 部署 → 保存传播 → 视频与渲染

核对日期：2026-10-09。排序采用此前确认的优先级：**国内手机可访问优先 → 免费优先 → 发布步骤简单 → 文件可复制 → 多份备用**。免费套餐和国内厂商不自动等于长期可用入口。这里只更新发布说明，没有开通、购买或部署新服务。

## 先认清资料库名称和用途

- **NCT 全国矫正机构资料档案 / nct-archive**：现有公开目录的来源之一，[原项目](https://github.com/goodpsychologistclaw/nct-archive)，原作者goodpsychologistclaw，许可Unlicense。
- **PanDefenseProject**：公开机构目录来源，[原项目](https://github.com/FunctionSir/PanDefenseProject)，FunctionSir及贡献者，许可AGPL-3.0。它们是上游资料项目名称，不是本站线上数据库名称。
- **本站机构资料库 / SQLite**：本地文件名`机构资料库.sqlite3`，保存原始来源与整理记录；属于本地私人库，不随公开包发布。
- **私有整理库 / jiewangyin-observer-private**：以`records.json`保存公开字段候选和审核进度，是JSON索引而非SQL数据库；频繁整理，审核后才导出到公有库。
- **公开来源目录 / source-catalog.json、source-catalog.csv**：当前1251条待核对来源记录，供手机查找、下载和重建；静态复制不需要开通在线数据库。
- **互助与收件数据库 / Cloudflare D1**：代码绑定名`DB`，本机预览文件`.preview/community.sqlite3`。线上数据库实际名称由部署者创建，仓库没有公开生产资源ID；可另取`jiewangyin-community`作为新资源名称示例，不能当成已创建资源。

视频文件另放对象存储或媒体保管区，`BUCKET`是附件存储绑定，不是数据库。来源许可、个人授权与核对状态分别保留；收录不等于事实认定。完整流程见[公私两库与可复制资料源](replicable-workflow.md)。

## 第一顺位：有可用国内空间就发布同一份静态包

若你或自愿合作方**已有**可用域名和网站空间，优先上传公开网站包解压后的文件，不另买服务器；无现成空间就继续下一项。保留根目录`index.html`、JSON/CSV、许可和校验清单。合作方同意、域名、空间费用与国内实际可达均需确认，目前没有已确认合作方。

静态目录只展示已公开资料；论坛发帖、登录、私人收件和审核需要另行部署可信后台。不要把私人SQLite、私有索引、回执或原件加入静态目录。

## 第二顺位：国内静态部署候选，逐项核对免费与域名条件

### 1. EdgeOne Makers / Pages：ZIP直接上传较简单

下载发行中标注“公开网站包”的ZIP → 控制台创建项目并选择直接上传 → 选择加速区域 → 上传ZIP → 部署 → 配置适用域名 → 用国内手机测试。上传的是已生成的静态包，不是源码ZIP；`index.html`须在ZIP最外层。官方当前直接上传限20000文件、单文件25MB，见[直接上传文档](https://pages.edgeone.ai/zh/document/direct-upload)。

**长期发布条件**：官方默认项目/部署域名在大陆网络须通过3小时有效预览链接访问。大陆/全球含大陆区域的自定义域名需按该服务要求完成备案；不含大陆区域的自定义域名没有这一要求，但访问效果仍须实测。预览链接不适合作为长期宣传入口。见[域名与区域说明](https://pages.edgeone.ai/zh/document/domain-overview)。免费计划的当期额度与账号资格另查控制台，域名取得和续费另算。

### 2. CloudBase静态托管：已有环境时优先试文件上传

使用已有合适环境 → 静态网站托管 → 文件管理/上传文件夹 → 上传解压后的公开网站文件 → 检查首页及目录下载。官方支持现成静态文件直接上传、不需要构建，见[静态部署](https://docs.cloudbase.net/hosting/web-hosting-static)。

默认域名主要用于开发测试且有频率限制；正式入口应核对自定义域名、环境有效期、当前免费资格、存储/流量费用。见[域名管理](https://docs.cloudbase.net/hosting/manage)。不沿用旧教程的“一直免费”结论，不新开付费环境；尚未用你的账号核验是否符合预算。

### 3. 阿里云ESA函数和Pages：保留，免费路线有条件

官方支持静态网站与Git工作流，见[函数和Pages](https://help.aliyun.com/zh/edge-security-acceleration/esa/user-guide/what-is-functions-and-pages/)。需要技术维护者确认构建输出、项目域名与区域，不把加速套餐直接当成完整站点。

国际站Entrance免费方案默认不含中国内地加速，官方另提供活动解锁办法；中国站在ESA控制台注册域名的免费套餐路线包含域名购买步骤。两种路线的账号、取得条件和费用不同，不混成“注册就永久免费国内托管”。见[国际站活动](https://www.alibabacloud.com/help/zh/edge-security-acceleration/esa/product-overview/how-to-get-esa-for-free)、[中国站域名路线](https://help.aliyun.com/zh/edge-security-acceleration/esa/user-guide/register-a-domain-name)。活动是否适用于你的账号及实际节点仍待核验，本项目未参加或购买。

## 第三顺位：先保留国内可读目录和文件下载

没有合适网站空间时，腾讯文档/飞书/WPS之一承载公开目录，国内网盘承载完整可下载包，微信/QQ转交TXT和小ZIP。在线文档是资料入口，网盘是下载入口，均不冒充完整论坛部署。按[国内主用流程](domestic-primary.md)测试无会员手机下载、真正另存、另一设备转交和更正更新。

## 第四顺位：跨境部署与特殊网络条件备用

原Sites站、GitHub Pages、Cloudflare Pages、Netlify、Vercel、Codeberg Pages、GitLab Pages等继续保留，按[备用说明](overseas-backup.md)记录域名、免费资格和国内可达性。GitHub仍承载代码与公开发行；不要求普通国内读者必须先访问GitHub。现有完整Worker后端采用D1/R2，上传静态包到另一厂商不能自动迁移后台、身份与数据库。

## 最后安排：视频存储、转码与页面渲染

资料编号、出处、数据库和复制途径先落实，再设计视频播放器、缩略图、懒加载与转码。原件、公开视频播放版、允许转交版分别保存；平台转码不是原件备份。渲染层只读取已经审核的公开数据，不能让它直接连接私有整理库。

当前字节分包、文件核验与公开媒体小包可用；可独立播放的切段/合成、自动转码与新媒体索引的页面展示仍未完成。静音宣传MP4只是自制示例，放在发行附件后部，不作为资料库主体。
