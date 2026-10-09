#!/usr/bin/env python3
"""Keep all options, with separate domestic/offline and backup inventories."""
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1] / 'docs'
path = ROOT / 'channel-catalog.json'
catalog = json.loads(path.read_text())
domestic_groups = {'国内传播', '国内文件保存与下载'}
domestic_names = {'Gitee', 'GitCode', 'CNB', '腾讯文档', '飞书文档 / 知识库', 'WPS云文档',
                  '石墨文档', '语雀', '问卷星', '金数据', 'EdgeOne Makers / Pages',
                  'CloudBase静态托管', '阿里云ESA'}
offline = {'手机文件 / SD卡 / USB存储', '另一位维护者独立副本', 'LocalSend'}
backup_groups = {'境外传播与社群', '境外文件备用'}
backup_names = {'GitHub仓库与Fork', 'GitHub Releases', 'Git LFS', 'GitLab', 'Codeberg',
                'Internet Archive', 'Notion', '现有Sites原站', 'GitHub Pages',
                'Cloudflare Pages', 'Netlify Drop / Netlify', 'Vercel Hobby',
                'Codeberg Pages', 'GitLab Pages', 'Neocities', 'Surge', 'R2 / 其他对象存储'}
for channel in catalog['channels']:
    name, group = channel['name'], channel['group']
    tier = ('domestic-candidate' if group in domestic_groups or name in domestic_names else
            'offline-primary' if name in offline else
            'cross-border-backup' if group in backup_groups or name in backup_names else
            'deployment-dependent')
    channel.update(access_tier=tier, domestic_mobile_test='not-tested',
                   access_note='使用分层，不是必须VPN/保证直连结论；需按地区、网络和账号实测。')
catalog['access_tiers'] = {
    'domestic-candidate': '国内主用候选，尚需账号与手机验收',
    'offline-primary': '文件另存/独立维护者/局域网交接，安装来源另测',
    'cross-border-backup': '跨境或特殊网络条件备用；原Sites和GitHub已建立但国内可达性待测',
    'deployment-dependent': '开源工具/混合服务取决于部署地点和实际节点'}
def write(file, value):
    file.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')
write(path, catalog)
for suffix, tiers in [('domestic', {'domestic-candidate', 'offline-primary'}),
                      ('backup', {'cross-border-backup'}),
                      ('conditional', {'deployment-dependent'})]:
    subset = dict(catalog, channels=[c for c in catalog['channels'] if c['access_tier'] in tiers])
    write(ROOT / f'channel-catalog-{suffix}.json', subset)
    print(suffix, len(subset['channels']))
