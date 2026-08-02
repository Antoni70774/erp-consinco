const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('erpDesktop', {
  salvarServidor: (url) => ipcRenderer.invoke('salvar-servidor', url),
  obterConfig: () => ipcRenderer.invoke('obter-config'),
  reconfigurar: () => ipcRenderer.invoke('reconfigurar-servidor'),
});
