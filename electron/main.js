const { app, BrowserWindow, Menu, protocol, net } = require('electron');
const path = require('path');
const { pathToFileURL } = require('url');
const { spawn, exec } = require('child_process');

let mainWindow = null;
let pyProc = null;
const isDev = !app.isPackaged || process.argv.includes('--dev');

// Register custom protocol scheme before app ready
protocol.registerSchemesAsPrivileged([
  { scheme: 'app', privileges: { standard: true, secure: true, supportFetchAPI: true } }
]);

function getBackendPath() {
  if (isDev) {
    return null;
  }
  // Path when packaged: dist/dpos_backend/dpos_backend.exe
  return path.join(app.getAppPath(), 'dist', 'dpos_backend', 'dpos_backend.exe');
}

function startBackend() {
  const backendPath = getBackendPath();
  if (!backendPath) {
    console.log('Development mode detected. Python sidecar is managed concurrently.');
    return;
  }

  console.log(`Spawning production Python sidecar: ${backendPath}`);
  
  pyProc = spawn(backendPath, [], {
    cwd: path.dirname(backendPath),
    detached: false
  });

  pyProc.stdout.on('data', (data) => {
    console.log(`[Sidecar] ${data.toString().trim()}`);
  });

  pyProc.stderr.on('data', (data) => {
    console.error(`[Sidecar Error] ${data.toString().trim()}`);
  });

  pyProc.on('close', (code) => {
    console.log(`Sidecar process exited with code ${code}`);
  });
}

function killBackend() {
  if (pyProc) {
    console.log('Terminating background Python sidecar process...');
    if (process.platform === 'win32') {
      exec(`taskkill /pid ${pyProc.pid} /T /F`, (err) => {
        if (err) {
          console.error('Error executing taskkill on sidecar:', err);
        } else {
          console.log('Background sidecar killed cleanly.');
        }
      });
    } else {
      pyProc.kill('SIGKILL');
    }
    pyProc = null;
  }
}

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1280,
    height: 800,
    minWidth: 1024,
    minHeight: 720,
    backgroundColor: '#050508',
    show: false,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true
    }
  });

  // Disable default File/Edit menu for a clean client experience
  Menu.setApplicationMenu(null);

  // Load the statically built Next.js bundle using the custom app:// protocol
  mainWindow.loadURL('app://-');

  mainWindow.once('ready-to-show', () => {
    mainWindow.show();
  });

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

// Lifecycle Hooks
app.whenReady().then(() => {
  // Register custom protocol handler to intercept files and resolve Next.js asset paths
  protocol.handle('app', (request) => {
    const urlObj = new URL(request.url);
    let pathname = urlObj.pathname;
    
    // Default to index.html for root page
    if (pathname === '/' || pathname === '') {
      pathname = '/index.html';
    }
    
    const filePath = path.join(app.getAppPath(), 'frontend', 'out', pathname);
    return net.fetch(pathToFileURL(filePath).toString());
  });

  startBackend();
  createWindow();

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });
});

app.on('window-all-closed', () => {
  killBackend();
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('will-quit', () => {
  killBackend();
});

process.on('exit', () => {
  killBackend();
});
