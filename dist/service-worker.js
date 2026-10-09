// Only fixed public shell files are cached. NEVER cache APIs, identities, receipts, or private uploads.
const CACHE='jiewangyin-shell-2026-10-09-v1';
const FILES=['/','/index.html','/styles.css','/data.js','/map-data.js','/icons.js','/app.js','/views.js','/drafts.js','/community.js','/actions.js','/source-catalog.js','/sha256.js','/intake.js','/archive-ui.js','/backup-ui.js','/pwa.js','/manifest.webmanifest','/assets/brand.svg','/tools/intake-offline.html'];
self.addEventListener('install',event=>event.waitUntil(caches.open(CACHE).then(cache=>cache.addAll(FILES))));
self.addEventListener('activate',event=>event.waitUntil(caches.keys().then(keys=>Promise.all(keys.filter(k=>k.startsWith('jiewangyin-shell-')&&k!==CACHE).map(k=>caches.delete(k))))));
self.addEventListener('fetch',event=>{const u=new URL(event.request.url);if(event.request.method!=='GET'||u.origin!==self.location.origin||u.search||!FILES.includes(u.pathname))return;event.respondWith(fetch(event.request).then(response=>{if(response.ok){const clone=response.clone();event.waitUntil(caches.open(CACHE).then(cache=>cache.put(u.pathname,clone)))}return response}).catch(()=>caches.match(u.pathname)));});
