const http = require('http');
const fs = require('fs');
const path = require('path');

const PORT = process.env.PORT || 3000;

// Log startup info
console.log('Starting server...');
console.log('Current directory:', __dirname);
console.log('Looking for dist at:', path.join(__dirname, 'dist'));

const mimeTypes = {
  '.html': 'text/html',
  '.js': 'text/javascript',
  '.css': 'text/css',
  '.json': 'application/json',
  '.png': 'image/png',
  '.jpg': 'image/jpg',
  '.gif': 'image/gif',
  '.svg': 'image/svg+xml',
  '.ico': 'image/x-icon'
};

const server = http.createServer((req, res) => {
  // Get the file path
  let filePath = path.join(__dirname, 'dist', req.url === '/' ? 'index.html' : req.url);
  
  // Try to read the requested file first
  fs.readFile(filePath, (error, content) => {
    if (error) {
      if (error.code === 'ENOENT') {
        // File doesn't exist, try serving index.html for SPA routing
        const indexPath = path.join(__dirname, 'dist', 'index.html');
        fs.readFile(indexPath, (indexError, indexContent) => {
          if (indexError) {
            res.writeHead(404);
            res.end('404 Not Found - Build may not exist. ' + indexError.message);
          } else {
            res.writeHead(200, { 'Content-Type': 'text/html' });
            res.end(indexContent, 'utf-8');
          }
        });
      } else {
        res.writeHead(500);
        res.end('Server Error: ' + error.code + ' - ' + error.message);
      }
    } else {
      // Get file extension for content type
      const extname = String(path.extname(filePath)).toLowerCase();
      const contentType = mimeTypes[extname] || 'application/octet-stream';
      res.writeHead(200, { 'Content-Type': contentType });
      res.end(content, 'utf-8');
    }
  });
});

server.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
});