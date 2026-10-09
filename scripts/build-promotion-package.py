#!/usr/bin/env python3
"""Build the public phone promotion/cloud handoff ZIP; never upload or send it."""
from pathlib import Path
import argparse, hashlib, json, zipfile

ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--output',required=True)
args=parser.parse_args();output=Path(args.output).expanduser().resolve()
if output.is_relative_to(ROOT):parser.error('Output must be outside repository')
if output.exists():parser.error('Output exists; choose a new version/path')
base=ROOT/'docs/promotion-kit'
names=['README.md','先读我.txt','index.html','评论区与短介绍.txt','图文发布稿.txt','视频口播.txt',
       '视频字幕.srt','志愿协作任务.txt','网盘上传步骤.txt','接下来由你完成.txt','渠道验收记录.csv',
       '公开链接登记模板.json','site-qr.png','visual-manifest.json','验收说明.txt',
       'cards/01-introduction.png','cards/01-introduction.svg','cards/02-sources.png',
       'cards/02-sources.svg','cards/03-save-and-share.png','cards/03-save-and-share.svg']
files={name:base/name for name in names}
files.update({
 '接力流程/国内主用.txt':ROOT/'docs/domestic-primary.md',
 '接力流程/跨境与特殊网络条件备用.txt':ROOT/'docs/overseas-backup.md',
 '接力流程/公私两库与资料源复制.txt':ROOT/'docs/replicable-workflow.md',
 '公开资料/公开网站包.zip':ROOT/'dist/site-copy.zip',
 '公开资料/公开来源目录.csv':ROOT/'dist/source-catalog.csv',
 '公开资料/公开来源目录.json':ROOT/'dist/source-catalog.json',
 '来源与许可/项目提供者与致谢.txt':ROOT/'ACKNOWLEDGEMENTS.md',
 '来源与许可/多平台传播与保存.txt':ROOT/'docs/multiplatform-distribution.md',
 '来源与许可/本站代码许可.txt':ROOT/'LICENSE',
 '来源与许可/SOURCE-LICENSES.txt':ROOT/'dist/SOURCE-LICENSES.txt',
 '来源与许可/NCT-LICENSE.txt':ROOT/'dist/NCT-LICENSE.txt',
 '来源与许可/PanDefense-LICENSE.txt':ROOT/'dist/PanDefense-LICENSE.txt',
 '来源与许可/照片署名.txt':ROOT/'dist/assets/real-photo-credit.txt',
 '来源与许可/图标许可.txt':ROOT/'dist/assets/icons/LICENSE.txt',
})
payload={}
for name,path in files.items():
 if path.is_symlink() or not path.is_file():raise ValueError('Missing regular public file: '+name)
 payload[name]=path.read_bytes()
payload['SHA256SUMS.txt']=''.join(hashlib.sha256(data).hexdigest()+'  '+name+'\n' for name,data in sorted(payload.items())).encode()
output.parent.mkdir(parents=True,exist_ok=True)
with zipfile.ZipFile(output,'x',zipfile.ZIP_DEFLATED) as z:
 for name,data in sorted(payload.items()):z.writestr(name,data)
print(json.dumps({'zip':str(output),'files':len(payload),'bytes':output.stat().st_size,
                  'sha256':hashlib.sha256(output.read_bytes()).hexdigest()},ensure_ascii=False))
