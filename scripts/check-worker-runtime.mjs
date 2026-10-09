// Integration check for a LOCAL Wrangler instance only. Simulated forwarded identity.
import {readFile} from 'node:fs/promises';
const base='http://127.0.0.1:8772',user='runtime-test-'+crypto.randomUUID();
const headers={Origin:base,'X-Kanjian-Request':'1','oai-authenticated-user-id':user,'oai-authenticated-user-email':'runtime@testing.invalid'};
async function api(path,method='GET',data){const r=await fetch(base+path,{method,headers:{...headers,...(data?{'Content-Type':'application/json'}:{})},body:data?JSON.stringify(data):undefined});const result=await r.json();if(!r.ok)throw Error(r.status+' '+JSON.stringify(result));return result}
const root=await fetch(base+'/');if(root.status!==200||!(await root.text()).includes('community.js'))throw Error('Static assets unavailable');
await api('/api/community/profile','POST',{nickname:'运行环境测试',acceptRules:true});const t=await api('/api/community/topics','POST',{title:'运行环境自检',body:'仅存在本机Cloudflare模拟环境，不发布真实资料。',category:'资料整理'});
const file=await readFile(new URL('../dist/assets/demo-film.mp4',import.meta.url));
const up=await fetch(base+'/api/community/topics/'+t.id+'/attachments?name=runtime-video.mp4',{method:'POST',headers:{...headers,'Content-Type':'video/mp4','X-File-Size':String(file.length),'X-Media-Consent':'confirmed'},body:file});const a=await up.json();if(up.status!==201)throw Error('R2 upload failed '+JSON.stringify(a));
const read=await fetch(base+'/api/attachments/'+a.id,{headers:{...headers,Range:'bytes=0-31'}});if(read.status!==206||(await read.arrayBuffer()).byteLength!==32)throw Error('Range read failed');
const own=await api('/api/community/topics/'+t.id);if(own.attachments.length!==1)throw Error('D1 attachment metadata mismatch');const unsigned=await fetch(base+'/api/attachments/'+a.id);if(unsigned.status!==404)throw Error('Private file escaped');
console.log(JSON.stringify({cloudflareRuntime:true,assets:200,d1:'persisted',r2FixedLengthStream:'saved',videoRange:206,privateReadDenied:404}));
