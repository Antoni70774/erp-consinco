const { app, BrowserWindow, ipcMain, Menu } = require('electron');
const path = require('path');
const fs = require('fs');

const CONFIG_PATH = path.join(app.getPath('userData'), 'config.json');

function lerConfig() {
  try {
    return JSON.parse(fs.readFileSync(CONFIG_PATH, 'utf-8'));
  } catch (e) {
    return null;
  }
}

function salvarConfig(config) {
  fs.writeFileSync(CONFIG_PATH, JSON.stringify(config, null, 2), 'utf-8');
}

let mainWindow;

function criarJanela() {
  mainWindow = new BrowserWindow({
    width: 1360,
    height: 860,
    minWidth: 1024,
    minHeight: 640,
    title: 'ERP · Sistema de Gestão',
    backgroundColor: '#12182b',
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
    },
  });

  Menu.setApplicationMenu(null); // remove menu padrão do Electron (mais limpo p/ ERP)

  const config = lerConfig();
  if (config && config.serverUrl) {
    mainWindow.loadURL(config.serverUrl).catch(() => {
      mainWindow.loadFile(path.join(__dirname, 'setup.html'));
    });
  } else {
    mainWindow.loadFile(path.join(__dirname, 'setup.html'));
  }
}

// Chamado pela tela de configuração (setup.html) quando o técnico informa a URL do servidor
ipcMain.handle('salvar-servidor', async (_event, serverUrl) => {
  let url = serverUrl.trim();
  if (!/^https?:\/\//i.test(url)) url = `https://${url}`;
  url = url.replace(/\/$/, '');
  salvarConfig({ serverUrl: url });
  mainWindow.loadURL(url);
  return { ok: true };
});

ipcMain.handle('obter-config', async () => lerConfig());

// Permite voltar à tela de configuração (ex: botão "Trocar servidor" dentro do app)
ipcMain.handle('reconfigurar-servidor', async () => {
  mainWindow.loadFile(path.join(__dirname, 'setup.html'));
});

app.whenReady().then(criarJanela);

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit();
});

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) criarJanela();
});
