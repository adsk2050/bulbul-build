// Build of Hitman Cricket for bulbul-build, served at /hitman/.
// Copied into the game's checkout by tools/hitman/build.sh; see README.md there.
import { defineConfig } from 'vite';

export default defineConfig({
  // Relative paths: the page lives at /hitman/ and resolves avatars/, lotties/ and
  // assets/ against its own URL.
  base: './',
  // Production: the Marathon (still in playtest upstream) stays hidden and no
  // made-up rows fill the boards.
  define: { 'import.meta.env.VITE_VERCEL_ENV': JSON.stringify('production') },
  build: {
    outDir: process.env.HITMAN_OUT ?? 'dist-bulbul',
    emptyOutDir: true,
    chunkSizeWarningLimit: 4096,
    rollupOptions: { input: 'index.html', output: { manualChunks: { three: ['three'] } } },
  },
});
