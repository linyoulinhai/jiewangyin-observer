线索收集工具：私有待核验队列原型
更新：2026-10-08；Python 3.9+；仅标准库，无需安装依赖。

这是可运行的本地收集后端，不是已上线的采集服务。原型不修改网站，
不自动发布，不定时运行，不发送消息，也没有手机录入界面。
所有记录均为 PRIVATE REVIEW / 未核验。来源陈述不等于事实。
example-import.json 只有模拟数据，不能作为任何机构的证据。

手机怎样用
手机可以先复制视频或评论的公开链接，记下来源文字和采集时间，之后
由可信维护人员整理成下列 JSON/JSONL 导入。抖音短链/B站短链不会被
本工具联网解析，必须另填公开 video_id；不能仅粘贴短链即自动采集。
现阶段仍需电脑运行 CLI；手机表单、手机上传、平台内实时抓取均未实现。

已实现
1. 导入自行合法取得的抖音、B站视频/评论 JSON 或 JSONL。
2. 规范化平台链接及 ID、移除链接跟踪参数、同平台同类来源 ID 去重。
   BV 号与 av 号之间不作推算转换；不同格式指向同一视频时需人工核对。
   抖音 sec_item_id 与公开 video_id 在同一视频记录中出现时会建立关联。
3. 关联所属视频和上级评论；找不到的父记录和来源 URL 会明确标记缺失。
4. 保存 UTC 采集时间、来源原发布时间、输入文件摘要、逐次最小化观察记录和翻页完整性。
   同来源多次出现会保留观察历史；最新采集正文用于队列，次数可见。
5. 导出未核验私有 JSON 队列。只有人工核实、编辑、必要脱敏后才能另行
   决定是否用于公开站点；本工具没有任何发布操作。
6. 可选抖音官方 API：关键词视频搜索、指定搜索视频的评论列表。
   适配器已用模拟响应测试，尚未用真实凭证联调；没有自动运行过平台采集。

未实现
B站网络/API自动采集；自动遍历关键词和所有视频；评论回复接口；登录、
OAuth 换 token、刷新 token；自动断点续跑；证据截图/音视频下载；事实
核查、自动脱敏、投稿审核界面和手机采集 UI。不存在任意 URL 抓取接口。

快速开始（在此目录打开终端）
  python3 -m unittest -v
  python3 collector.py import example-import.json
  python3 collector.py export

默认输出位于项目之外：
  ~/.local/share/jiewangyin-clues/intake.sqlite3
  ~/.local/share/jiewangyin-clues/review-queue.json

可选指定私有目录（--store 必须放在子命令前）：
  python3 collector.py --store "$HOME/私有线索" import /path/to/input.json
  python3 collector.py --store "$HOME/私有线索" export

目录权限 0700，数据库及队列文件 0600。程序拒绝将私有数据库或导出放到
此项目目录内，包括“概念展示站”、public、发布包素材等位置。不要把私有
目录加入静态网站、共享盘、代码仓库或站点压缩包。这是本地文件权限，
不是加密、权限管理服务或匿名化。目录所在设备/备份仍需由维护者管理。

导入格式
支持 UTF-8 JSON 数组，或 {"records": [...], "pagination": {...}}；
也支持 .jsonl 每行一个记录。一次最多 10 MiB / 10000 条；遇到无效记录
或 ID 冲突会回滚本次导入。不同平台可以混在一个文件里。

视频记录示意（以下均为虚构测试内容）：
  {"platform":"douyin","kind":"video","video_id":"123456789",
   "source_url":"https://www.douyin.com/video/123456789",
   "text":"模拟来源文字","captured_at":"2026-10-08T12:00:00+08:00"}

评论记录：
  {"platform":"bilibili","kind":"comment","video_id":"av123456789",
   "comment_id":"987654321","parent_comment_id":"987654320",
   "text":"模拟评论","captured_at":"2026-10-08T12:00:00+08:00"}

platform 为 douyin 或 bilibili；可省略并在 import 命令后加 --platform。
kind 为 video 或 comment，默认 video。video_id 为抖音数字 ID 或 B站
BV/av 号。也接受 aweme_id、bvid、aid 等常见导出字段。
评论需要 comment_id（也接受 cid/rpid）和所属视频 ID；回复可填写
parent_comment_id。没有父评论记录时仍保留关联，并在导出标明缺失。
source_url 可由完整公开视频链接提取 ID，或由公开 video_id 生成。
评论未提供可用定位链接时只链接所属视频，source_url_scope=video；
加密 ID 本身无法生成公开 URL。仅有加密 ID 时 missing_source_url=true，
若此前已导入对应视频，导出会沿父视频补上来源链接。
captured_at 需为带时区的 ISO 时间；省略时使用本次导入时间。
source_published_at 是来源原发布时间，独立于采集时间；导入接受带时区的
ISO 时间，或 create_time 的 Unix 秒（官方 API 使用此字段），统一转为 UTC。
缺失时保留 null，不用采集时间代替。非法发布时间会拒绝该次导入；API
出现非法发布时间时标为错误并停止，保留此前成功页，不猜测、不伪造。
正文接受 text/content/message/title/desc；B站 content.message 也支持。

翻页说明
本地导入的 pagination 可包含 complete、has_more、next_cursor、pages_fetched。
默认 complete=false。用户声明 complete=true 且未声明 has_more=true 才
记录为完成，并注明“由导出提供，未经独立验证”；这不等于资料全面。
API 仅在 has_more=false 时记本次接口列表完成。达到页数/请求上限、
重复游标、网络/业务错误或无效响应都会保持 complete=false。
next_cursor 保存便于人工核对；当前再次运行从首页开始，会按来源去重。
评论列表完成不代表包含子回复、删除内容、私密内容或历史全部内容；
程序不抓取回复接口，不能把一页或接口完成标为“完整评论档案”。

数据最小化与审阅
结构化头像、昵称、联系方式、个人简介等字段不保存；不做账号画像或
个人资料补充。保留视频/评论/上级评论 ID、可用来源账号 ID 用于审核。
只接收白名单字段，不复制完整本地原始文件，也不落盘完整 API 响应。
SQLite 的 observations 表保存逐次最小化来源观察；runs 保存采集范围。
这会舍弃一些原始字段，并不是完整取证系统或证据保全认证。
正文仍可能包含姓名、联系方式、健康信息或未成年人信息，来源 ID 和
链接也能关联个人，所以本工具不声称已匿名化或自动脱敏。私有队列不能
直接作为公开数据源；删除记录及留存周期目前需维护者人工管理。

可选抖音官方接口：先自行获得相应应用权限
官方接口不是开放任意爬虫入口。公益、研究或机构监督用途并不保证获批。
关键词须由应用后台创建并审核，仅限符合平台规则的自身业务范围，
不能据此承诺可搜索任意机构。文档说明关键词上限 20，替换需审核；
关键词视频搜索只返回最近 1 天内容，不是历史搜索库。

1. 关键词视频搜索
   GET https://open.douyin.com/video/search/
   Scope: video.search；需要申请权限和用户授权。
   access-token 请求头使用用户 token（由 /oauth/access_token/ 获得）。
   Query: open_id、keyword、count；cursor 首页为 0。

2. 指定搜索视频评论列表
   GET https://open.douyin.com/video/search/comment/list/
   Scope: video.search.comment；该接口不需要用户授权。
   access-token 请求头使用应用 client token（由 /oauth/client_token/ 获得）。
   Query: sec_item_id、count；cursor 首页为 0。
   sec_item_id 必须来自关键词视频搜索；工具通过 urlencode 正确编码。
   只有存在且公开的视频才可能返回评论，删除/好友可见/私密视频会失败。

官方文档（2026-10-08核对）：
https://open.douyin.com/platform/resource/docs/openapi/search-management/keywords-video-list/keywords-video/
https://open.douyin.com/platform/resource/docs/openapi/search-management/keywords-video-comment-management/comment-list/

凭证仅从当前进程环境变量读取，不接受 token 命令行参数或配置文件，
不保存、不输出 token，不记录 API 错误正文。两种 token 不能混用。
可在 Bash 中交互输入，避免把真实 token 写入 shell 历史：
  read -rsp '用户 access token: ' DOUYIN_USER_ACCESS_TOKEN
  export DOUYIN_USER_ACCESS_TOKEN
  read -rp 'open_id: ' DOUYIN_OPEN_ID
  export DOUYIN_OPEN_ID

使用已获批且适用于自己业务范围的关键词：
  python3 collector.py douyin-search --keyword '替换为已审核的业务关键词' --pages 2 --max-requests 2

为评论接口另外交互输入应用 client token：
  read -rsp '应用 client token: ' DOUYIN_CLIENT_ACCESS_TOKEN
  export DOUYIN_CLIENT_ACCESS_TOKEN
  python3 collector.py douyin-comments --sec-item-id '替换为搜索返回的sec_item_id' --pages 2 --max-requests 2
  python3 collector.py export

使用完可清除当前 shell 变量：
  unset DOUYIN_USER_ACCESS_TOKEN DOUYIN_CLIENT_ACCESS_TOKEN DOUYIN_OPEN_ID

每条命令的默认上限为 2 页 / 2 次请求，每页 count 默认 10，工具人为
限制为 1–20（不是声称平台文档最大值）。pages 最多 10，max-requests
最多 50。--interval 默认 1 秒且不可低于 1 秒；不自动重试错误。
首次请求立即发出，后续请求起始时间至少间隔 1 秒。
只连接上述固定官方 HTTPS 地址；TLS 使用系统验证；不走环境代理，
不跟随重定向，不读取 cookies，不模拟登录，不逆向平台接口、不绕过
验证码、不做代理轮换。未配置 token 会在发出请求前报错。

检查结果
测试使用临时目录、虚构记录和模拟 HTTP 响应，不访问真实平台。
覆盖：URL/ID规范化与冲突、来源去重、视频/评论/回复关联、私有文件权限、
JSONL、时间格式、最小化字段、缺失父记录、完整性声明、分页和请求上限、
原发布时间与采集时间区分、重复导入保留评论定位链接、禁止导出覆盖数据库、
至少一秒间隔、重复游标停止、错误停止且保留此前成功页、令牌类型选择、
令牌不进入队列、加密ID URL编码、无代理及阻止重定向。
