import {fileURLToPath} from 'node:url';
import {mkdir,cp,readFile,writeFile,readdir,rm} from 'node:fs/promises';
import {build} from 'esbuild';
const root=new URL('../',import.meta.url),dist=new URL('dist/',root);
await rm(new URL('client/',dist),{recursive:true,force:true});
await mkdir(new URL('client/',dist),{recursive:true});
for(const entry of await readdir(dist,{withFileTypes:true})){
 if(['client','server','.openai'].includes(entry.name)||entry.name.startsWith('.'))continue;
 await cp(new URL(entry.name,dist),new URL('client/'+entry.name,dist),{recursive:true});
}
await mkdir(new URL('server/',dist),{recursive:true});
await build({entryPoints:[fileURLToPath(new URL('worker/community.js',root))],outfile:fileURLToPath(new URL('server/index.js',dist)),bundle:true,format:'esm',platform:'browser',target:'es2022',minify:false});
await mkdir(new URL('.openai/',dist),{recursive:true});
try{await cp(new URL('.openai/hosting.json',root),new URL('.openai/hosting.json',dist));}catch(e){if(e.code!=='ENOENT')throw e;console.log('No Sites binding: built portable assets and Worker; configure your own hosting before deployment.');}
await cp(new URL('drizzle/',root),new URL('.openai/drizzle/',dist),{recursive:true});
const config={name:'kanjian-community',main:'index.js',compatibility_date:'2026-10-01',assets:{directory:'../client',binding:'ASSETS',run_worker_first:true},d1_databases:[{binding:'DB',database_name:'local-community',database_id:'local-community',migrations_dir:'../../drizzle'}],r2_buckets:[{binding:'BUCKET',bucket_name:'local-community-media'}]};
await writeFile(new URL('server/wrangler.json',dist),JSON.stringify(config,null,2));
console.log('Built community Worker and preserved public archive assets.');
