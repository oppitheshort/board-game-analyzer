export function injectPopupStyles(): void {
  const style = document.createElement('style');
  style.textContent = `
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body { width: 320px; background: #1a1a2e; color: #e0e0e0; font-family: system-ui, -apple-system, sans-serif; font-size: 13px; }
    .popup-header { padding: 16px; text-align: center; border-bottom: 1px solid #0f3460; }
    .popup-header h1 { font-size: 16px; font-weight: 600; }
    .popup-body { padding: 16px; }
    .form-group { margin-bottom: 12px; }
    .form-group label { display: block; font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px; color: #7f8c8d; margin-bottom: 4px; }
    .form-group input { width: 100%; padding: 8px 10px; background: #16213e; border: 1px solid #0f3460; border-radius: 6px; color: #e0e0e0; font-size: 13px; outline: none; }
    .form-group input:focus { border-color: #2ecc71; }
    .btn { width: 100%; padding: 10px; border: none; border-radius: 6px; font-size: 13px; font-weight: 600; cursor: pointer; transition: opacity 0.2s; }
    .btn:hover { opacity: 0.9; }
    .btn-primary { background: #2ecc71; color: #000; }
    .btn-secondary { background: #0f3460; color: #e0e0e0; margin-top: 8px; }
    .btn-danger { background: #e74c3c; color: #fff; margin-top: 8px; }
    .error { color: #e74c3c; font-size: 11px; margin-top: 4px; }
    .mode-selector { display: flex; gap: 8px; margin-bottom: 12px; }
    .mode-btn { flex: 1; padding: 8px; border: 1px solid #0f3460; border-radius: 6px; background: #16213e; color: #7f8c8d; font-size: 12px; cursor: pointer; text-align: center; }
    .mode-btn.active { border-color: #2ecc71; color: #2ecc71; }
    .status-row { display: flex; justify-content: space-between; align-items: center; padding: 8px 0; font-size: 12px; }
    .status-indicator { display: inline-block; width: 8px; height: 8px; border-radius: 50%; margin-right: 6px; }
    .status-indicator.on { background: #2ecc71; }
    .status-indicator.off { background: #e74c3c; }
    .toggle-label { display: flex; align-items: center; justify-content: space-between; cursor: pointer; }
    .toggle-switch { position: relative; width: 36px; height: 20px; background: #333; border-radius: 10px; transition: background 0.3s; }
    .toggle-switch.on { background: #2ecc71; }
    .toggle-switch::after { content: ''; position: absolute; top: 2px; left: 2px; width: 16px; height: 16px; background: #fff; border-radius: 50%; transition: transform 0.3s; }
    .toggle-switch.on::after { transform: translateX(16px); }
    .section-title { font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px; color: #7f8c8d; margin: 16px 0 8px; }
    .user-info { font-size: 12px; color: #7f8c8d; margin-bottom: 8px; }
    .tab-bar { display: flex; border-bottom: 1px solid #0f3460; }
    .tab { flex: 1; padding: 10px; text-align: center; font-size: 12px; cursor: pointer; color: #7f8c8d; border-bottom: 2px solid transparent; }
    .tab.active { color: #2ecc71; border-bottom-color: #2ecc71; }
  `;
  document.head.appendChild(style);
}
