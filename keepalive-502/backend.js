// The API behind the proxy: a plain Node.js HTTP server, one per port.
// usage: node backend.js <keepAliveTimeout in ms, or "default"> <first port> <number of ports>
'use strict';
const http = require('http');

const [arg, firstPort, count] = process.argv.slice(2);

for (let n = 0; n < Number(count); n++) {
  const server = http.createServer((req, res) => {
    req.resume();
    req.on('end', () => {
      res.writeHead(200, { 'Content-Type': 'text/plain' });
      res.end('ok\n');
    });
  });
  if (arg !== 'default') server.keepAliveTimeout = Number(arg);
  server.listen(Number(firstPort) + n, '127.0.0.1');
  if (n === 0) console.log(`node ${process.version}, server.keepAliveTimeout = ${server.keepAliveTimeout} ms`);
}
