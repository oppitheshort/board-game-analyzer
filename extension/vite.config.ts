import { defineConfig } from 'vite';
import { resolve } from 'path';
import { copyFileSync, mkdirSync, existsSync, readdirSync } from 'fs';

function copyStaticFiles() {
  return {
    name: 'copy-extension-files',
    writeBundle() {
      const dist = resolve(__dirname, 'dist');
      copyFileSync(resolve(__dirname, 'manifest.json'), resolve(dist, 'manifest.json'));

      const sidebarDir = resolve(dist, 'sidebar');
      if (!existsSync(sidebarDir)) mkdirSync(sidebarDir, { recursive: true });
      copyFileSync(resolve(__dirname, 'sidebar/index.html'), resolve(sidebarDir, 'index.html'));

      const popupDir = resolve(dist, 'popup');
      if (!existsSync(popupDir)) mkdirSync(popupDir, { recursive: true });
      copyFileSync(resolve(__dirname, 'popup/index.html'), resolve(popupDir, 'index.html'));

      const iconsDir = resolve(dist, 'icons');
      if (!existsSync(iconsDir)) mkdirSync(iconsDir, { recursive: true });
      const iconsSrc = resolve(__dirname, 'icons');
      if (existsSync(iconsSrc)) {
        for (const f of readdirSync(iconsSrc)) {
          copyFileSync(resolve(iconsSrc, f), resolve(iconsDir, f));
        }
      }
    },
  };
}

export default defineConfig({
  plugins: [copyStaticFiles()],
  build: {
    outDir: 'dist',
    emptyOutDir: true,
    rollupOptions: {
      input: {
        'background/service-worker': resolve(__dirname, 'background/service-worker.ts'),
        'content/content': resolve(__dirname, 'content/content-entry.ts'),
        'sidebar/sidebar': resolve(__dirname, 'sidebar/sidebar-app.ts'),
        'popup/popup': resolve(__dirname, 'popup/popup-app.ts'),
      },
      output: {
        entryFileNames: '[name].js',
        chunkFileNames: 'chunks/[name]-[hash].js',
        assetFileNames: 'assets/[name][extname]',
      },
    },
    target: 'chrome120',
    minify: false,
  },
});
