import {DatabaseSync} from 'node:sqlite';
import {readFileSync,readdirSync} from 'node:fs';
import {join} from 'node:path';
export function database(filename=':memory:'){
 const db=new DatabaseSync(filename);db.exec('PRAGMA foreign_keys=ON;');
 return {raw:db,prepare(sql){let args=[];const query={bind(...v){args=v;return query},async first(){const r=db.prepare(sql).get(...args);return r?{...r}:null},async all(){return {results:db.prepare(sql).all(...args).map(r=>({...r}))}},async run(){const r=db.prepare(sql).run(...args);return {meta:{changes:Number(r.changes)}}}};return query},async batch(list){db.exec('BEGIN');try{const out=[];for(const p of list)out.push(await p.run());db.exec('COMMIT');return out}catch(e){db.exec('ROLLBACK');throw e}}};
}
export function migrate(db,dir){db.raw.exec('CREATE TABLE IF NOT EXISTS local_migrations (name TEXT PRIMARY KEY)');for(const name of readdirSync(dir).filter(x=>x.endsWith('.sql')).sort()){if(db.raw.prepare('SELECT name FROM local_migrations WHERE name=?').get(name))continue;db.raw.exec('BEGIN');try{db.raw.exec(readFileSync(join(dir,name),'utf8'));db.raw.prepare('INSERT INTO local_migrations(name) VALUES (?)').run(name);db.raw.exec('COMMIT')}catch(e){db.raw.exec('ROLLBACK');throw e}}}
