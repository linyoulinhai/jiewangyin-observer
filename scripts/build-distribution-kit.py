#!/usr/bin/env python3
"""Build an explicitly public handoff bundle; never post or upload it."""
from pathlib import Path
import argparse, hashlib, json, zipfile
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--output',required=True,help='New ZIP path outside the source repository')
args=p.parse_args();target=Path(args.output).expanduser().resolve()
if target.is_relative_to(ROOT):p.error('Keep generated handoff bundles outside this repository')
if target.exists():p.error('Output exists; choose a new version/path')
files={
 '国内主用.md':ROOT/'docs/domestic-primary.md',
 '跨境与特殊网络条件备用.md':ROOT/'docs/overseas-backup.md',
 '公私两库与资料源复制.md':ROOT/'docs/replicable-workflow.md',
 '项目说明.md':ROOT/'README.md',
 '详细项目说明.md':ROOT/'docs/project-guide.md',
 '项目提供者与致谢.md':ROOT/'ACKNOWLEDGEMENTS.md',
 '各平台传播与保存办法.md':ROOT/'docs/multiplatform-distribution.md',
 '渠道清单.json':ROOT/'docs/channel-catalog.json',
 '平台发布模板.txt':ROOT/'docs/distribution-templates/平台发布模板.txt',
 '公开来源目录.csv':ROOT/'dist/source-catalog.csv',
 '公开来源目录.json':ROOT/'dist/source-catalog.json',
 '公开网站包.zip':ROOT/'dist/site-copy.zip',
 '来源与许可/SOURCE-LICENSES.txt':ROOT/'dist/SOURCE-LICENSES.txt',
 '来源与许可/NCT-LICENSE.txt':ROOT/'dist/NCT-LICENSE.txt',
 '来源与许可/PanDefense-LICENSE.txt':ROOT/'dist/PanDefense-LICENSE.txt',
 '来源与许可/本站代码许可.txt':ROOT/'LICENSE',
 '来源与许可/真实照片署名.txt':ROOT/'dist/assets/real-photo-credit.txt',
 '来源与许可/图标许可.txt':ROOT/'dist/assets/icons/LICENSE.txt',
}
intro='''先读我：戒网瘾机构观察 · 公开传播导读包
版本：2026-10-09

普通读者：先看平台发布模板.txt与项目提供者致谢；公开来源CSV/JSON适合保存和查阅。
需要展示网站：解压公开网站包.zip，按包内README.txt操作；手机文件预览器未必运行网页脚本，另用目录或CSV阅读。
想转发：可直接转交此ZIP，保留作者、来源、许可和版本；不要夹入私人信息、回执或原件。
开发者：源码与详细说明见 https://github.com/linyoulinhai/jiewangyin-observer
原站：https://kanjian-archive-concept.chengbiliu3.chatgpt.site/

此包不含账号、私人投稿、回执、原始媒体或后台运行数据库。目录待核对，机构收录不等于违法认定。
84项渠道/形式是路线清单，不是已上线平台数量；模板未自动发送。与制作/下载副本有关的权限和费用仍需验证。
此包不是完整论坛备份。公开媒体的旧副本不能保证完全撤回，更正后请重新取得版本。
'''
payload={'先读我.txt':intro.encode()}
for name,path in files.items():
 if path.is_symlink() or not path.is_file():raise ValueError('Missing regular public file: '+name)
 payload[name]=path.read_bytes()
checks=''.join(hashlib.sha256(data).hexdigest()+'  '+name+'\n' for name,data in sorted(payload.items()))
payload['SHA256SUMS.txt']=checks.encode()
target.parent.mkdir(parents=True,exist_ok=True)
with zipfile.ZipFile(target,'x',compression=zipfile.ZIP_DEFLATED) as z:
 for name,data in sorted(payload.items()):z.writestr(name,data)
print(json.dumps({'zip':str(target),'files':len(payload),'bytes':target.stat().st_size,'sha256':hashlib.sha256(target.read_bytes()).hexdigest()},ensure_ascii=False))
