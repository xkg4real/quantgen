const { chromium } = require('playwright');
(async () => {
  const files = process.argv.slice(2);
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 }, deviceScaleFactor: 2 });
  for (const f of files) {
    await page.goto('file://' + require('path').resolve(f));
    await page.waitForTimeout(300);
    const out = f.replace(/\.html$/, '.png');
    await page.screenshot({ path: out });
    console.log('rendered', out);
  }
  await browser.close();
})();
