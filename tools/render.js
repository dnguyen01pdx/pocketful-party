// Render HTML with headless Chromium.
//   node tools/render.js pdf  <in.html> <out.pdf> <pngDir>   printable: PDF + one PNG per .page
//   node tools/render.js shot <in.html> <out.png> <w> <h>    pin or cover image
// Needs Playwright (NODE_PATH=/opt/node22/lib/node_modules in the cloud box).
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

(async () => {
  const [mode, input, out, a, b] = process.argv.slice(2);
  const launch = { args: ['--allow-file-access-from-files'] };
  const browser = await chromium.launch(launch);
  try {
    if (mode === 'pdf') {
      const page = await browser.newPage({ viewport: { width: 816, height: 1056 }, deviceScaleFactor: 2 });
      await page.goto('file://' + path.resolve(input), { waitUntil: 'networkidle' });
      await page.evaluate(() => document.fonts.ready);
      fs.mkdirSync(path.dirname(out), { recursive: true });
      // grain + blend modes force full-page rasters in PDFs; print the clean vector version
      const clean = await page.addStyleTag({ content: '.grain{display:none!important}.ov,.blob,.corner{mix-blend-mode:normal!important}' });
      await page.pdf({ path: out, format: 'Letter', printBackground: true, margin: { top: 0, right: 0, bottom: 0, left: 0 } });
      await clean.evaluate(el => el.remove());
      fs.mkdirSync(a, { recursive: true });
      const pages = await page.$$('.page');
      for (let i = 0; i < pages.length; i++) await pages[i].screenshot({ path: path.join(a, `p${i + 1}.png`) });
      console.log(`pdf ${out} + ${pages.length} pngs`);
    } else if (mode === 'shot') {
      const w = +a, h = +b;
      const page = await browser.newPage({ viewport: { width: w, height: h }, deviceScaleFactor: 1 });
      await page.goto('file://' + path.resolve(input), { waitUntil: 'networkidle' });
      await page.evaluate(() => document.fonts.ready);
      await page.waitForFunction(() => window.__fitDone !== false, null, { timeout: 15000 });
      await page.waitForTimeout(150);
      fs.mkdirSync(path.dirname(out), { recursive: true });
      await page.screenshot({ path: out, clip: { x: 0, y: 0, width: w, height: h } });
      console.log(`shot ${out}`);
    } else {
      throw new Error('mode must be pdf or shot');
    }
  } finally {
    await browser.close();
  }
})().catch(e => { console.error(e); process.exit(1); });
