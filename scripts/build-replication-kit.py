#!/usr/bin/env python3
"""Package the reproducible public data source and local export tools only."""
import argparse
import hashlib
from pathlib import Path
import json
import zipfile

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--output', required=True)
args = parser.parse_args()
output = Path(args.output).expanduser().resolve()
if output.is_relative_to(ROOT) or output.exists():
    parser.error('Choose a new ZIP outside the public repository')
paths = ['scripts/release-data.py', 'LICENSE', 'ACKNOWLEDGEMENTS.md',
         'docs/project-providers.json', 'docs/replicable-workflow.md', 'docs/domestic-primary.md',
         'docs/overseas-backup.md', 'docs/channel-catalog.json',
         'docs/deployment-options.md',
         'docs/channel-catalog-domestic.json', 'docs/channel-catalog-backup.json',
         'docs/channel-catalog-conditional.json', 'docs/private-index-example.json',
         'dist/source-catalog.json', 'dist/source-catalog.csv', 'dist/source-catalog.js',
         'dist/tools/build-local-library.py.txt',
         'dist/SOURCE-LICENSES.txt', 'dist/NCT-LICENSE.txt', 'dist/PanDefense-LICENSE.txt']
payload = {}
for name in paths:
    path = ROOT / name
    if not path.is_file() or path.is_symlink():
        parser.error('Missing regular public file: ' + name)
    payload[name] = path.read_bytes()
payload['先读我.txt'] = '''戒网瘾机构观察 · 可复制数据源起步包 / 2026-10-09

手机读者：进入dist查看source-catalog.csv；JSON是保留公开字段的资料源。
保管者：整包另存，不仅收藏链接；转交时保留作者、许可、版本与散列。
维护者：本包不需Node/npm，可用Python 3在电脑重建整理索引与公开数据包。

在解压目录执行：
python3 scripts/release-data.py init --from-public dist/source-catalog.json --destination ../my-private-index --date 2026-10-09 --accept-existing-public
python3 scripts/release-data.py export --source ../my-private-index/records.json --output ../my-public-copy --version my-copy-1
python3 scripts/release-data.py verify ../my-public-copy

这三条命令不联网、不上传、不发布；输出目录必须是新目录且在此包外。
新的未审核资料设为pending；不能冒充既有公开基线，审核后再公开。
私有索引和原件另存，不整体上传到公开库；手机提交资料仍通过原站已有入口。
这不是完整网站/论坛包，没有真实视频。下载展示站请找发行里的公开网站包。
机构目录待核对，不代表违法认定或当前经营状态。真实图片视频需单独授权。
docs有国内主用、跨境备用和全流程说明，旁边同名TXT方便手机阅读。
项目：https://github.com/linyoulinhai/jiewangyin-observer
原站：https://kanjian-archive-concept.chengbiliu3.chatgpt.site/
'''.encode()
for name in ['deployment-options', 'replicable-workflow', 'domestic-primary', 'overseas-backup']:
    payload[f'docs/{name}.txt'] = payload[f'docs/{name}.md']
payload['SHA256SUMS.txt'] = ''.join(hashlib.sha256(v).hexdigest() + '  ' + k + '\n'
                                  for k, v in sorted(payload.items())).encode()
output.parent.mkdir(parents=True, exist_ok=True)
with zipfile.ZipFile(output, 'x', zipfile.ZIP_DEFLATED) as archive:
    for name, data in sorted(payload.items()):
        info = zipfile.ZipInfo(name, date_time=(2026, 1, 1, 0, 0, 0))
        info.compress_type = zipfile.ZIP_DEFLATED
        info.external_attr = 0o100644 << 16
        archive.writestr(info, data)
print(json.dumps({'files': len(payload), 'bytes': output.stat().st_size,
                  'sha256': hashlib.sha256(output.read_bytes()).hexdigest()}))
