'use strict';
if('serviceWorker' in navigator&&['http:','https:'].includes(location.protocol))window.addEventListener('load',()=>navigator.serviceWorker.register('/service-worker.js').catch(()=>{}));
