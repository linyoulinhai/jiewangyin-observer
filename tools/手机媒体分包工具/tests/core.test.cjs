'use strict';
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict'),crypto=require('node:crypto'),path=require('node:path'),os=require('node:os'),cp=require('node:child_process');
const html=fs.readFileSync(path.join(__dirname,'../index.html'),'utf8');
vm.runInThisContext(html.match(/<script id="media-core">([\s\S]*?)<\/script>/)[1]);
const C=MediaPackCore, digest=b=>crypto.createHash('sha256').update(b).digest('hex'),clone=x=>JSON.parse(JSON.stringify(x));
(async()=>{
 let assertions=0;function check(value){assert.ok(value);assertions++;}
 for(const length of [0,1,55,56,63,64,65,127,128,129,4096,1024*1024+3]){
  const input=crypto.randomBytes(length),h=new C.SHA256();for(let off=0;off<length;off+=37)h.update(input.subarray(off,off+37));assert.equal(h.hex(),digest(input));assertions++;
 }
 assert.equal(new C.SHA256().update(Buffer.from('abc')).hex(),'ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad');assertions++;
 const contents=[crypto.randomBytes(9904),crypto.randomBytes(1984),Buffer.alloc(0),Buffer.from('中文资料\n')];
 const names=['演示.mp4','同名.png','empty.jpg','同名.png'];
 const files=contents.map((b,i)=>new File([b],names[i],{type:i===0?'video/mp4':'image/png'}));
 const out=await C.pack(files,2048);for(const p of out.outputs)check(p.blob.size<=2048);
 out.manifest.files.forEach((f,i)=>{assert.equal(f.sha256,digest(contents[i]));assertions++;});
 const pieces=out.outputs.map(p=>new File([p.blob],p.name));
 const restored=await C.restore(out.manifest,[...pieces].reverse());
 for(const [i,f]of restored.entries()){assert.deepEqual(Buffer.from(await f.blob.arrayBuffer()),contents[i]);assert.equal(f.name,names[i]);assertions+=2;}
 const broken=Buffer.from(await pieces[0].arrayBuffer());broken[45]^=1;
 const bad=new File([broken],pieces[0].name);
 await assert.rejects(C.restore(out.manifest,[bad,...pieces.slice(1)]),/损坏|不符/);assertions++;
 await assert.rejects(C.restore(out.manifest,pieces.slice(1)),/缺少/);assertions++;
 const numbered=new File([pieces[0]],pieces[0].name.replace('.zip',' (1).zip'));
 const fallback=await C.restore(out.manifest,[bad,numbered,...pieces.slice(1)]);assert.deepEqual(Buffer.from(await fallback[0].blob.arrayBuffer()),contents[0]);assertions++;
 const wrong=clone(out.manifest);wrong.files[0].sha256='0'.repeat(64);await assert.rejects(C.restore(wrong,pieces),/完整文件校验失败/);assertions++;
 for(const name of ['../secret','a/b','a\\b','..','a\0b']){const m=clone(out.manifest);m.files[0].name=name;assert.throws(()=>C.validManifest(m),/不安全/);assertions++;}
 const mismatch=clone(out.manifest);mismatch.files[0].parts[0].size++;assert.throws(()=>C.validManifest(mismatch),/总长度/);assertions++;
 const controller=new AbortController();controller.abort();await assert.rejects(C.pack(files,2048,()=>{},controller.signal),/停止/);await assert.rejects(C.restore(out.manifest,pieces,()=>{},controller.signal),/停止/);assertions+=2;
 const temp=fs.mkdtempSync(path.join(os.tmpdir(),'media-core-'));try{for(const [i,p]of out.outputs.entries())fs.writeFileSync(path.join(temp,i+'.zip'),Buffer.from(await p.blob.arrayBuffer()));cp.execFileSync('python3',['-c',"import zipfile,glob; files=glob.glob('*.zip'); assert files; [zipfile.ZipFile(p).read('payload.bin') for p in files]; print('Python ZIP CRC validation passed')"],{cwd:temp,stdio:'inherit'});const app=new Blob([html]);const hash=await C.scan(app);fs.writeFileSync(path.join(temp,'app.zip'),Buffer.from(await C.zipStored(app,hash.crc32,'index.html').arrayBuffer()));cp.execFileSync('python3',['-c',"import zipfile; z=zipfile.ZipFile('app.zip'); assert z.namelist()==['index.html']; assert b'media-core' in z.read('index.html')"],{cwd:temp});assertions++;}finally{fs.rmSync(temp,{recursive:true,force:true});}
 console.log(`PASS: ${assertions} integrity assertions; SHA-256 independently checked with Node crypto; ZIP independently checked with Python.`);
})().catch(e=>{console.error(e);process.exitCode=1;});
