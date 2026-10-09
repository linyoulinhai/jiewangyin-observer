import json,urllib.request,tarfile,io,pathlib,xml.etree.ElementTree as E
root=pathlib.Path(__file__).resolve().parents[1];dst=root/'dist';out=dst/'assets/icons';out.mkdir(parents=True,exist_ok=True)
metadata=json.load(urllib.request.urlopen('https://registry.npmjs.org/lucide-static/latest',timeout=20))
tar=tarfile.open(fileobj=io.BytesIO(urllib.request.urlopen(metadata['dist']['tarball'],timeout=30).read()),mode='r:gz')
chosen=['building-2','files','users-round','info','map-pin','search','image','video','file-text','camera','folder-open','share-2','download','copy','save','message-circle','history','clock','lock-keyhole','circle-help','pencil-line','package','play','x']
icons={};members={m.name:m for m in tar.getmembers() if m.isfile()}
allowed={'svg','path','circle','ellipse','rect','line','polyline','polygon','g'}
for name in chosen:
 candidates=[n for n in members if n.endswith('/icons/'+name+'.svg')]
 if len(candidates)!=1:raise RuntimeError('Icon not found: '+name)
 source=tar.extractfile(members[candidates[0]]).read().decode();element=E.fromstring(source)
 for node in element.iter():
  if node.tag.split('}')[-1] not in allowed or any(k.startswith('on') or k in {'href','src'} for k in node.attrib):raise RuntimeError('Unexpected SVG content')
 source=source[source.index('<svg'):].strip();source=source.replace('width="24"','width="20"').replace('height="24"','height="20"').replace('stroke-width="2"','stroke-width="1.8"')
 import re
 source=re.sub(r'class="[^"]*"','class="ui-icon"',source,count=1)
 if 'class="ui-icon"' not in source:source=source.replace('<svg','<svg class="ui-icon"',1)
 source=source.replace('<svg','<svg aria-hidden="true" focusable="false"',1)
 icons[name]=source;(out/(name+'.svg')).write_text(source+'\n')
licenses=[n for n in members if n.lower()=='package/license']
if not licenses:raise RuntimeError('Missing upstream license')
(out/'LICENSE.txt').write_bytes(tar.extractfile(members[licenses[0]]).read())
(out/'来源与使用说明.txt').write_text('图标：Lucide，lucide-static '+metadata['version']+'\n官方：https://lucide.dev/\n许可：https://lucide.dev/license\n保留完整上游许可于 LICENSE.txt。图标采用文字配合的用途标记，不表示身份核验或真实性背书。\n图标随整站公开包保存，无需访问外部图标服务。\n')
(dst/'icons.js').write_text('// Lucide icons. See assets/icons/LICENSE.txt for ISC and Feather MIT notices.\nconst UI_ICONS='+json.dumps(icons,separators=(',',':'))+';\nfunction icon(name){return UI_ICONS[name]||UI_ICONS["file-text"];}\nfunction kindIcon(kind){return icon(kind==="视频"?"video":kind==="图片"?"image":"file-text");}\n')
print(json.dumps({'icons':len(icons),'version':metadata['version'],'bytes':(dst/'icons.js').stat().st_size}))
