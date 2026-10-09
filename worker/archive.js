// Intake receipts are bearer credentials. Only their SHA-256 hashes are stored.
import {SHA256} from './sha256.js';
const MAX=50*1024*1024;
export const BACKUP_TABLES=['profiles','topics','replies','attachments','subscriptions','notices','cases','audit','limits','intake','intake_files','intake_events','archive_records','archive_media'];
const hex=bytes=>Array.from(new Uint8Array(bytes),x=>x.toString(16).padStart(2,'0')).join('');
const digest=async value=>hex(await crypto.subtle.digest('SHA-256',typeof value==='string'?new TextEncoder().encode(value):value));

export async function archiveAPI(request,env,h) {
 const {db,user,fail,json,clean,id,source,body,first,all,run,statement,rate,now,uid}=h;
 const url=new URL(request.url),path=url.pathname,method=request.method;
 const fileFields=f=>({id:f.id,name:f.name,mime:f.mime,size:f.size,sha256:f.sha256,publicAllowed:!!f.public_allowed,exportAllowed:!!f.export_allowed,status:f.status});
 const intakeFields=r=>({id:r.id,kind:r.kind,title:r.title,institution:r.institution,region:r.region,body:r.body,sourceNote:r.source_note,scope:r.scope,rights:!!r.rights,allowExport:!!r.allow_export,status:r.status,decision:r.decision,version:r.version,created:r.created,updated:r.updated});
 const receipt=async()=>{const value=request.headers.get('X-Intake-Receipt')||'';if(!/^[a-f0-9]{64}$/.test(value))fail(404,'回执不正确或记录不存在。');return digest(value)};
 const access=async (iid,admin=false)=>{const r=await first(db,'SELECT * FROM intake WHERE id=?',id(iid));if(!r)fail(404,'回执不正确或记录不存在。');if(user?.id&&r.owner===user.id)return r;if(admin&&user?.moderator&&r.status!=='draft')return r;if(r.receipt_hash===await receipt())return r;fail(404,'回执不正确或记录不存在。')};
 const event=(iid,action,message)=>statement(db,'INSERT INTO intake_events (id,intake,action,message,created) VALUES (?,?,?,?,?)',uid(),iid,action,message,now());
 const moderator=()=>{if(!user?.moderator)fail(403,'只有管理员可以处理资料或备份。')};
 function input(b){
  const kind=b.kind||'material',scope=b.scope||'review';
  if(!['material','feedback'].includes(kind)||!['review','public'].includes(scope))fail(400,'请选择资料核对或反馈，及提交范围。');
  return {kind,title:clean(b.title||'',150),institution:clean(b.institution||'',150),region:clean(b.region||'',60),body:clean(b.body||'',20000),sourceNote:clean(b.sourceNote||'',4000),scope,rights:b.rights===true?1:0,allowExport:b.allowExport===true&&scope==='public'?1:0};
 }
 async function publicRecord(r){
  const files=await all(db,"SELECT f.* FROM intake_files f JOIN archive_media m ON m.file=f.id WHERE m.record=? AND f.status='ready' AND f.public_allowed=1 ORDER BY f.created,f.id",r.id);
  return {id:r.id,name:r.name,aliases:r.aliases,region:r.region,city:r.city,summary:r.summary,body:r.body,sources:JSON.parse(r.sources),verification:r.verification,allowExport:!!r.allow_export,version:r.version,created:r.created,updated:r.updated,attachments:files.map(f=>({...fileFields(f),url:'/api/archive/media/'+f.id}))};
 }
 if(path==='/api/intake'&&method==='POST') {
  const b=await body(request),iid=id(b.id),rhash=await receipt(),v=input(b);
  if(b.website)fail(400,'没有接受此提交。');
  const old=await first(db,'SELECT * FROM intake WHERE id=?',iid);
  if(old){await access(iid);return json({id:iid,status:old.status,version:old.version,duplicate:true})}
  // Raw IP addresses are not retained. The host may still keep access logs.
  const remote=request.headers.get('CF-Connecting-IP')||'unknown';
  await rate(db,await digest('intake:'+remote+':'+Math.floor(now()/86400)),'intake-create',3600,8);
  await rate(db,'site','intake-create',3600,100);
  await run(db,'INSERT INTO intake (id,owner,receipt_hash,kind,title,institution,region,body,source_note,scope,rights,allow_export,created,updated) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)',iid,user?.id||'',rhash,v.kind,v.title,v.institution,v.region,v.body,v.sourceNote,v.scope,v.rights,v.allowExport,now(),now());
  return json({id:iid,status:'draft',version:1},201);
 }
 if(path==='/api/intake/mine'&&method==='GET') {
  if(!user)fail(401,'登录后可以查看账号关联记录，也可以用私人回执查看单份记录。');
  const cursor=clean(url.searchParams.get('after')||'',64),rows=await all(db,'SELECT * FROM intake WHERE owner=? AND id>? ORDER BY id LIMIT 51',user.id,cursor);
  return json({items:rows.slice(0,50).map(intakeFields),next:rows.length>50?rows[49].id:null});
 }
 let m=path.match(/^\/api\/intake\/([\w-]+)(?:\/(submit|files))?$/);
 if(m) {
  const r=await access(m[1],method==='GET'),action=m[2];
  if(method==='GET'&&!action)return json({...intakeFields(r),files:(await all(db,"SELECT * FROM intake_files WHERE intake=? AND status<>'withdrawn' ORDER BY created,id",r.id)).map(fileFields),events:await all(db,'SELECT action,message,created FROM intake_events WHERE intake=? ORDER BY created,id',r.id)});
  if(method==='PATCH'&&!action) {
   if(!['draft','needs_changes'].includes(r.status))fail(409,'提交后先查看处理进度；需要修改时可以补充，或撤回再整理。');
   const b=await body(request),v=input(b);if(b.version!==r.version)fail(409,'资料已在其他页面更新，请重新读取后补充。');
   const result=await run(db,'UPDATE intake SET title=?,institution=?,region=?,body=?,source_note=?,scope=?,rights=?,allow_export=?,version=version+1,updated=? WHERE id=? AND version=? AND status IN (\'draft\',\'needs_changes\')',v.title,v.institution,v.region,v.body,v.sourceNote,v.scope,v.rights,v.allowExport,now(),r.id,r.version);
   if(!result.meta.changes)fail(409,'资料状态已变化，请重新读取。');return json({id:r.id,status:r.status,version:r.version+1});
  }
  if(method==='DELETE'&&!action) {
   await db.batch([statement(db,"UPDATE intake SET status='withdrawn',version=version+1,updated=? WHERE id=?",now(),r.id),statement(db,"UPDATE archive_records SET status='hidden',version=version+1,updated=? WHERE intake=?",now(),r.id),event(r.id,'withdraw','已停止处理和关联公开展示；已下载副本可能仍存在。')]);return json({ok:true});
  }
  if(action==='submit'&&method==='POST') {
   if(r.status==='pending')return json({id:r.id,status:'pending',duplicate:true});
   if(!['draft','needs_changes'].includes(r.status))fail(409,'这份记录已经处理或撤回。');
   if(r.title.length<2||r.body.length<2||!r.rights)fail(400,'请补充标题、说明并确认有权提交这些材料。');
   const incomplete=await first(db,"SELECT count(*) n FROM intake_files WHERE intake=? AND status='uploading'",r.id);if(incomplete.n)fail(409,'仍有附件上传中，请完成后再提交。');
   await db.batch([statement(db,"UPDATE intake SET status='pending',decision='',version=version+1,updated=? WHERE id=? AND status IN ('draft','needs_changes')",now(),r.id),event(r.id,'submit','已收到，等待核对。提交不等于已公开或认定事实。')]);return json({id:r.id,status:'pending'});
  }
  if(action==='files'&&method==='POST') {
   if(!['draft','needs_changes'].includes(r.status))fail(409,'只能为草稿或待补充记录上传。');
   if(!env.BUCKET)fail(503,'附件服务暂时不可用，请另存原件。');
   if(request.headers.get('X-Media-Consent')!=='confirmed')fail(400,'请先确认有权提交附件。');
   const fid=id(url.searchParams.get('id')),mime=request.headers.get('Content-Type')||'',size=Number(request.headers.get('X-File-Size')),sha=clean(request.headers.get('X-File-SHA256')||'',64);
   if(!['image/jpeg','image/png','image/webp','video/mp4','video/webm'].includes(mime)||!Number.isSafeInteger(size)||size<8||size>(mime.startsWith('image/')?10*1024*1024:MAX)||!/^[a-f0-9]{64}$/.test(sha))fail(413,'支持10MB以内JPEG/PNG/WebP图片及50MB以内MP4/WebM视频，请使用分包工具另存大原件。');
   const prior=await first(db,'SELECT * FROM intake_files WHERE id=?',fid);
   if(prior){if(prior.intake!==r.id||prior.sha256!==sha||prior.size!==size)fail(409,'文件编号或内容不一致。');if(prior.status==='ready')return json({...fileFields(prior),duplicate:true});if(prior.status==='uploading')fail(409,'该附件上传中；失败后可以重试。');}
   const name=clean(url.searchParams.get('name')||'附件',180).replace(/[\r\n/\\]/g,'_'),pub=r.scope==='public'&&url.searchParams.get('public')==='1'?1:0,exp=pub&&url.searchParams.get('export')==='1'?1:0;
   const key='intake/'+fid;
   if(prior)await run(db,'DELETE FROM intake_files WHERE id=? AND status=\'failed\'',fid);
   const reservation=await run(db,"INSERT INTO intake_files (id,intake,name,mime,size,storage_key,sha256,public_allowed,export_allowed,status,created) SELECT ?,?,?,?,?,?,?,?,?,?,? WHERE (SELECT count(*) FROM intake_files WHERE intake=? AND status IN ('ready','uploading'))<6 AND (SELECT coalesce(sum(size),0) FROM intake_files WHERE intake=?)+?<=104857600 AND (SELECT coalesce(sum(size),0) FROM intake_files)+(SELECT coalesce(sum(size),0) FROM attachments)+?<=1073741824",fid,r.id,name,mime,size,key,sha,pub,exp,'uploading',now(),r.id,r.id,size,size);
   if(!reservation.meta.changes)fail(413,'试用空间已满：每份6个/100MB，全站附件合计1GB。请保存本机草稿和原件。');
   try {
    const reader=request.body?.getReader();if(!reader)fail(400,'没有收到文件。');
    let receivedHead=0;const pieces=[];while(receivedHead<32&&receivedHead<size){const part=await reader.read();if(part.done)break;pieces.push(part.value);receivedHead+=part.value.length;}const prefix=new Uint8Array(receivedHead);let offset=0;for(const piece of pieces){prefix.set(piece,offset);offset+=piece.length;}if(!receivedHead||receivedHead>size||!h.sniff(prefix,mime)){await reader.cancel();fail(415,'文件格式与内容不符。');}
    let pending=prefix,length=0;const hash=new SHA256();
    const stream=new ReadableStream({async pull(controller){try{const part=pending?{value:pending,done:false}:await reader.read();pending=null;if(part.done){if(length!==size||hash.hex()!==sha)throw Error('file integrity mismatch');controller.close();return;}length+=part.value.length;if(length>size)throw Error('file too large');hash.update(part.value);controller.enqueue(part.value)}catch(e){await reader.cancel();controller.error(e)}},cancel(){return reader.cancel()}});
    if(typeof FixedLengthStream!=='undefined'){const fixed=new FixedLengthStream(size);await Promise.all([stream.pipeTo(fixed.writable),env.BUCKET.put(key,fixed.readable,{httpMetadata:{contentType:mime}})]);}else await env.BUCKET.put(key,stream,{httpMetadata:{contentType:mime}});
    await run(db,"UPDATE intake_files SET status='ready' WHERE id=?",fid);
   } catch(e) {
    await run(db,"UPDATE intake_files SET status='failed',size=0 WHERE id=?",fid);await env.BUCKET.delete(key).catch(()=>{});
    if(e?.status)throw e;fail(503,'附件没有保存成功，草稿仍保留；可以重试。');
   }
   return json({id:fid,status:'ready',sha256:sha},201);
  }
 }
 m=path.match(/^\/api\/intake\/files\/([\w-]+)$/);
 if(m) {
  const f=await first(db,'SELECT * FROM intake_files WHERE id=?',id(m[1]));if(!f||f.status!=='ready')fail(404,'附件不存在。');const r=await access(f.intake,method==='GET');
  if(method==='GET'||method==='HEAD')return media(f,'private');
  if(method==='DELETE'){await db.batch([statement(db,"UPDATE intake_files SET status='withdrawn',public_allowed=0,export_allowed=0 WHERE id=?",f.id),statement(db,"UPDATE archive_records SET updated=?,version=version+1 WHERE id IN (SELECT record FROM archive_media WHERE file=?)",now(),f.id),event(r.id,'withdraw_file','已停止一个附件的展示和导出；原件仍按保留规则保存。')]);return json({ok:true});}
 }
 if(path==='/api/archive/records'&&method==='GET') {
  const after=clean(url.searchParams.get('after')||'',64),q=clean(url.searchParams.get('q')||'',100),region=clean(url.searchParams.get('region')||'',60),exportOnly=url.searchParams.get('export')==='1';
  const rows=await all(db,"SELECT * FROM archive_records WHERE status='published' AND id>? AND (?=0 OR allow_export=1) AND (?='' OR region=?) AND (?='' OR instr(name||' '||aliases||' '||region||' '||city,?)>0) ORDER BY id LIMIT 31",after,exportOnly?1:0,region,region,q,q);
  const out=[];for(const r of rows.slice(0,30))out.push(await publicRecord(r));return json({format:'kanjian-archive-public-v1',items:out,next:rows.length>30?rows[29].id:null,exportedAt:new Date().toISOString()});
 }
 m=path.match(/^\/api\/archive\/records\/([\w-]+)(?:\/(export))?$/);
 if(m&&method==='GET') {
  const r=await first(db,"SELECT * FROM archive_records WHERE id=? AND status='published'",id(m[1]));if(!r)fail(404,'这份档案尚未公开或已更新。');if(m[2]&&!r.allow_export)fail(403,'这份档案尚未允许打包传播。');
  const record=await publicRecord(r);if(m[2])record.attachments=record.attachments.filter(f=>f.exportAllowed);
  return json({...record,format:'kanjian-archive-record-v1',notice:'核对范围见来源说明；公开材料不代表已经作出违法认定。',sourcePath:'/#archive/'+r.id});
 }
 m=path.match(/^\/api\/archive\/media\/([\w-]+)$/);
 if(m&&['GET','HEAD'].includes(method)) {
  const f=await first(db,"SELECT f.* FROM intake_files f WHERE f.id=? AND f.status='ready' AND f.public_allowed=1 AND EXISTS(SELECT 1 FROM archive_media m JOIN archive_records r ON r.id=m.record WHERE m.file=f.id AND r.status='published')",id(m[1]));if(!f)fail(404,'附件未公开或已停止展示。');return media(f,'public');
 }
 async function media(f,visibility) {
  const object=await env.BUCKET?.get(f.storage_key,{range:request.headers});if(!object)fail(404,'文件暂时不可用。');
  const headers=new Headers({'Content-Type':f.mime,'Content-Disposition':`inline; filename*=UTF-8''${encodeURIComponent(f.name)}`,'X-Content-Type-Options':'nosniff','Cache-Control':'private, no-store','Accept-Ranges':'bytes','X-File-SHA256':f.sha256});
  const range=object.range,status=range?206:200;if(range){headers.set('Content-Range',`bytes ${range.offset}-${range.offset+range.length-1}/${object.size}`);headers.set('Content-Length',String(range.length));}else headers.set('Content-Length',String(object.size));
  return new Response(method==='HEAD'?null:object.body,{headers,status});
 }
 if(path==='/api/intake/mod/queue'&&method==='GET') {
  moderator();const after=clean(url.searchParams.get('after')||'',64),rows=await all(db,"SELECT * FROM intake WHERE status NOT IN ('draft','withdrawn') AND id>? ORDER BY id LIMIT 31",after);return json({items:rows.slice(0,30).map(intakeFields),next:rows.length>30?rows[29].id:null});
 }
 if(path==='/api/intake/mod/action'&&method==='POST') {
  moderator();const b=await body(request),r=await first(db,'SELECT * FROM intake WHERE id=?',id(b.id));if(!r||['draft','withdrawn'].includes(r.status))fail(404,'资料尚未提交或已撤回。');
  const message=clean(b.message||'',4000),states={needs_changes:'needs_changes',reviewed:'reviewed',reject:'rejected'};if(message.length<2)fail(400,'请填写需要补充的内容或处理理由。');
  if(b.action==='publish') {
   if(r.kind!=='material'||r.scope!=='public'||!r.rights)fail(403,'提供者只允许私人核对，不能生成公开档案。');
   const name=clean(b.name||'',150),text=clean(b.body||'',20000),summary=clean(b.summary||'',500),verification=clean(b.verification||'',2000);
   if(name.length<2||text.length<2||summary.length<2||verification.length<2||!Array.isArray(b.sources)||b.sources.length<1||b.sources.length>20)fail(400,'公开档案需要名称、说明、核对范围及来源。');
   const sources=b.sources.map(s=>({url:source(s.url),label:clean(s.label||'来源',150)}));if(sources.some(s=>!s.url))fail(400,'请提供有效来源链接。');
   if(!Array.isArray(b.fileIds)||b.fileIds.length>6)fail(400,'公开附件清单不正确。');const files=[];
   for(const fid of new Set(b.fileIds)){const f=await first(db,"SELECT * FROM intake_files WHERE id=? AND intake=? AND public_allowed=1 AND status='ready'",id(fid),r.id);if(!f)fail(403,'这个附件未获准公开。');files.push(f);}
   if(files.length&&b.mediaReviewed!==true)fail(400,'请检查每份公开附件的画面、个人信息和授权。');
   const old=await first(db,'SELECT * FROM archive_records WHERE intake=?',r.id),rid=old?.id||uid(),time=now();
   await db.batch([
    statement(db,"INSERT INTO archive_records (id,intake,name,aliases,region,city,summary,body,sources,verification,allow_export,created,updated) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET name=excluded.name,aliases=excluded.aliases,region=excluded.region,city=excluded.city,summary=excluded.summary,body=excluded.body,sources=excluded.sources,verification=excluded.verification,allow_export=excluded.allow_export,status='published',updated=excluded.updated,version=archive_records.version+1",rid,r.id,name,clean(b.aliases||'',500),clean(b.region||r.region,60),clean(b.city||'',60),summary,text,JSON.stringify(sources),verification,r.allow_export,time,time),
    statement(db,'DELETE FROM archive_media WHERE record=?',rid),...files.map(f=>statement(db,'INSERT INTO archive_media (id,record,file) VALUES (?,?,?)',uid(),rid,f.id)),
    statement(db,"UPDATE intake SET status='reviewed',decision=?,version=version+1,updated=? WHERE id=?",message,time,r.id),event(r.id,'publish',message+' · 已生成公开档案，可申请更正或撤回。')
   ]);return json({id:r.id,status:'reviewed',recordId:rid});
  }
  if(!states[b.action])fail(400,'处理动作不正确。');
  await db.batch([statement(db,'UPDATE intake SET status=?,decision=?,version=version+1,updated=? WHERE id=?',states[b.action],message,now(),r.id),statement(db,"UPDATE archive_records SET status='hidden',version=version+1,updated=? WHERE intake=?",now(),r.id),event(r.id,b.action,message)]);return json({ok:true});
 }
 // Paginated administrator-only exports include private data. They are not public archive exports.
 if(path==='/api/backup/catalog'&&method==='GET') {
  moderator();const tables=[];for(const table of BACKUP_TABLES){const count=await first(db,`SELECT count(*) n FROM ${table}`);tables.push({name:table,count:count.n})}
  return json({format:'kanjian-private-backup-v1',createdAt:new Date().toISOString(),tables,notice:'包含私人身份、原件目录和处理记录；必须保密保存。导出期间应暂停写入，并复核前后摘要。'});
 }
 if(path==='/api/backup/table'&&method==='GET') {
  moderator();const table=url.searchParams.get('name');if(!BACKUP_TABLES.includes(table))fail(400,'备份表不正确。');const after=clean(url.searchParams.get('after')||'',500),key=table==='limits'?'key':'id';
  const rows=await all(db,`SELECT * FROM ${table} WHERE ${key}>? ORDER BY ${key} LIMIT 26`,after);
  return json({name:table,rows:rows.slice(0,25),next:rows.length>25?rows[24][key]:null});
 }
 m=path.match(/^\/api\/backup\/media\/(community|intake)\/([\w-]+)$/);
 if(m&&['GET','HEAD'].includes(method)) {
  moderator();const table=m[1]==='community'?'attachments':'intake_files',f=await first(db,`SELECT * FROM ${table} WHERE id=?`,id(m[2]));if(!f||f.size===0||['uploading','failed'].includes(f.status))fail(404,'没有可备份的原件。');return media(f,'private');
 }
 return null;
}
