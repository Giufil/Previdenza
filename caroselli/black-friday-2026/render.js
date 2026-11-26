// Esporta ogni <section class="slide"> di carosello.html in png/slide-NN.png (1080x1350)
const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

(async () => {
  const scale = Number(process.env.SCALE || 1);
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1080, height: 1350 }, deviceScaleFactor: scale });
  await page.goto('file://' + path.resolve(__dirname, 'carosello.html'), { waitUntil: 'networkidle' });
  await page.evaluate(() => document.fonts.ready);
  const out = path.resolve(__dirname, process.env.OUT || 'png');
  fs.mkdirSync(out, { recursive: true });
  const slides = await page.$$('section.slide');
  for (let i = 0; i < slides.length; i++) {
    const f = path.join(out, `slide-${String(i + 1).padStart(2, '0')}.png`);
    await slides[i].screenshot({ path: f });
    console.log(f);
  }
  await browser.close();
})();
