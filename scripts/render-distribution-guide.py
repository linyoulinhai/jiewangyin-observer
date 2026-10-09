#!/usr/bin/env python3
"""Render all preserved channels in data/deployment-first publication order."""
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / 'docs'
catalog = json.loads((DOCS / 'channel-catalog.json').read_text())
groups = [
 ('国内网站部署与已有空间', ['公益组织已有网站栏目', 'EdgeOne Makers / Pages', 'CloudBase静态托管', '阿里云ESA']),
 ('国内公开目录与收件', ['腾讯文档', '飞书文档 / 知识库', 'WPS云文档', '石墨文档', '语雀', '问卷星', '金数据']),
 ('国内资料下载与源码保存', ['123云盘', '蓝奏云', '中国移动云盘', '天翼云盘', '百度网盘', '夸克网盘', '阿里云盘', '腾讯微云', '坚果云', '小飞机网盘', '115', '文叔叔', '奶牛快传', 'Gitee', 'GitCode', 'CNB']),
 ('手机文件与独立接力', ['手机文件 / SD卡 / USB存储', '另一位维护者独立副本', 'LocalSend', 'PairDrop / ShareDrop', 'Syncthing', 'BitTorrent / Web Seed', '邮件附件 / 邮件列表']),
 ('国内文字与图文传播', ['微信好友与群', 'QQ好友与QQ群', '微信公众号', '微博', '百度贴吧', '知乎', '小红书', '豆瓣', '今日头条', 'CSDN / 掘金']),
 ('跨境与特殊网络条件备用', ['现有Sites原站', 'GitHub Pages', 'Cloudflare Pages', 'Netlify Drop / Netlify', 'Vercel Hobby', 'Codeberg Pages', 'GitLab Pages', 'Neocities', 'Surge', 'GitHub仓库与Fork', 'GitHub Releases', 'Git LFS', 'GitLab', 'Codeberg', 'Internet Archive', 'Notion', 'Proton Drive', 'Google Drive', 'OneDrive', 'Dropbox', 'MEGA', 'Reddit', 'Mastodon / Bluesky', 'Telegram', 'Discord']),
 ('依部署地点选择的Wiki论坛与保存工具', ['TiddlyWiki / Tiddlyhost', 'FeatherWiki', 'DokuWiki', 'MediaWiki', 'Miraheze', 'Discourse免费托管', 'Forumotion', 'IPFS']),
 ('视频平台、媒体存储与渲染层', ['微信视频号', '哔哩哔哩', '抖音', '快手', 'YouTube', 'PeerTube', 'R2 / 其他对象存储'])]
lookup = {c['name']: c for c in catalog['channels']}
names = [name for _, items in groups for name in items]
if len(names) != 84 or len(set(names)) != 84 or set(names) != set(lookup):
    raise ValueError('Publication order must preserve all 84 channels once')
text = (DOCS / 'distribution-introduction.md').read_text().rstrip() + '\n\n'
number = 0
for stage, (title, names) in enumerate(groups, 1):
    text += f'## {stage}. {title}\n\n'
    if stage == 8:
        text += '本层放在资料库、部署和复制流程之后。播放版、原件与可再分发版分别保存；当前没有自动转码或新媒体索引UI。\n\n'
    for name in names:
        number += 1
        c = lookup[name]
        c.setdefault('channel_id', f"channel-{catalog['channels'].index(c)+1:03d}")
        c.update(display_stage=stage, display_order=number)
        heading = f"[{name}]({c['url']})" if c.get('url') else name
        text += f'<a id="{c["channel_id"]}"></a>\n\n### {number}. {heading}\n\n{c["action"]}\n\n条件与保存：{c["limit"]} 状态：{c["status"]}。\n\n'
text += (DOCS / 'distribution-notes.md').read_text().rstrip() + '\n'
catalog['display_order_notice'] = '先资料库名称与来源，再国内部署、国内保存/接力、传播、跨境备用，最后视频与渲染。channel_id不随排序改变。'
catalog['channels'].sort(key=lambda c: c['display_order'])
(DOCS / 'channel-catalog.json').write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + '\n')
(DOCS / 'multiplatform-distribution.md').write_text(text)
print(json.dumps({'channels': number, 'display_groups': len(groups), 'video_stage': 8}))
