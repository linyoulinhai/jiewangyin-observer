import json,hashlib,zipfile,pathlib
p=pathlib.Path(__file__).resolve().parents[1]/'dist'
d=json.loads((p/'public-data.json').read_text())
package_dir=p/'packages';package_dir.mkdir(exist_ok=True)
material={m['id']:m for m in d['materials']};stories={s['id']:s for s in d['stories']}
def pack(name,record,items,story_items=[]):
 files={}
 text='看见 · 虚构演示资料 v'+d['version']+'\n\n'+record.get('name',record.get('title',''))+'\n\n本包所有机构、经历与讨论均为虚构演示；媒体为AI生成示意，不是事实证据。\n\n'
 for m in items:
  text+=m['title']+'\n'+m['summary']+'\n来源：'+m['source']+'\n编号：'+m['id']+' · v'+m['version']+'\n'+'\n'.join(m['body'])+'\n\n'
  for f in {m['file'],m['image']}:files[f]=(p/f).read_bytes()
 for s in story_items:text+=s['title']+'\n'+s['author']+' · 虚构示例\n'+'\n\n'.join(s['paragraphs'])+'\n\n'
 files['先读我.txt']=text.encode();files['public-record.json']=json.dumps(dict(format='kanjian-public-package-v1',isDemo=True,isPublic=True,version=d['version'],record=record,materials=items,stories=story_items),ensure_ascii=False,indent=2).encode()
 files['SHA256SUMS.txt']=''.join(hashlib.sha256(b).hexdigest()+'  '+n+'\n' for n,b in files.items()).encode()
 with zipfile.ZipFile(package_dir/name,'w',zipfile.ZIP_DEFLATED) as z:
  for n,b in files.items():z.writestr(n,b)
for m in material.values():pack(m['id']+'.zip',m,[m])
for i in d['institutions']:pack('institution-'+i['id']+'.zip',i,[material[n] for n in i['materials']],[stories[n] for n in i['stories']])
for s in stories.values():pack('story-'+s['id']+'.zip',s,[material[n] for n in s['attachments']],[s])
files=[f for f in p.rglob('*') if f.is_file() and f.name not in {'site-copy.zip','public-files.json'} and not any(x.startswith('.') for x in f.relative_to(p).parts)]
# Keep a stable explicit public allowlist; no browser drafts, local originals, credentials or sources.
allowed={'index.html','styles.css','icons.js','community.js','app.js','views.js','drafts.js','actions.js','data.js','map-data.js','public-data.json','README.txt','LICENSE.txt','assets/linyi-exterior-2016.jpg','assets/real-photo-credit.txt','assets/campus.webp','assets/documents.webp','assets/dormitory.webp','assets/demo-film.mp4','assets/china-regions.geojson','tools/media-pack.html'}|{'packages/'+f.name for f in package_dir.glob('*.zip')}
allowed|={'assets/icons/'+f.name for f in (p/'assets/icons').iterdir() if f.is_file()}
allowed|={'source-catalog.js','source-catalog.json','source-catalog.csv','sha256.js','intake.js','archive-ui.js','backup-ui.js','pwa.js','service-worker.js','manifest.webmanifest','access-points.json','assets/brand.svg','tools/intake-offline.html','tools/restore-private.mjs','tools/recovery-schema.sql','tools/恢复私人备份说明.txt','SOURCE-LICENSES.txt','tools/source-directory.html'}
allowed|={'ACKNOWLEDGEMENTS.txt','MULTIPLATFORM-GUIDE.txt','NCT-LICENSE.txt','PanDefense-LICENSE.txt','tools/build-local-library.py.txt'}
files=[f for f in files if f.relative_to(p).as_posix() in allowed]
manifest=dict(format='kanjian-public-files-v1',version='2026-10-09-source-library',demoVersion=d['version'],isDemo=False,sourceRecords=1251,files=[dict(path=f.relative_to(p).as_posix(),size=f.stat().st_size,sha256=hashlib.sha256(f.read_bytes()).hexdigest()) for f in sorted(files)])
(p/'public-files.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
with zipfile.ZipFile(p/'site-copy.zip','w',zipfile.ZIP_DEFLATED) as z:
 for f in sorted(files):z.write(f,f.relative_to(p))
 z.write(p/'public-files.json','public-files.json')
print(json.dumps(dict(publicFiles=len(files)+1,siteZipBytes=(p/'site-copy.zip').stat().st_size,mediaBytes=sum((p/'assets'/f).stat().st_size for f in ['campus.webp','documents.webp','dormitory.webp','demo-film.mp4']),packageCount=len(list(package_dir.glob('*.zip'))))))
