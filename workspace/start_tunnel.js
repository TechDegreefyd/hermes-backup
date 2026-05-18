const localtunnel = require('localtunnel');
(async () => {
  const tunnel = await localtunnel({ port: 5000 });
  console.log('TUNNEL_URL=' + tunnel.url, flush=true);
  tunnel.on('close', () => console.log('TUNNEL_CLOSED'));
  setInterval(() => {}, 1000);
})().catch(err => { console.error(err); process.exit(1); });
