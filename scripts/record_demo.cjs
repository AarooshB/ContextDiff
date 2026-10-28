// Optional delivery tool: npm install playwright in a separate temporary folder.
// Requires Chrome and FFmpeg on PATH; no application dependency is added.
const { chromium } = require('playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs/promises');
const path = require('node:path');
const os = require('node:os');
const { execFileSync } = require('node:child_process');

async function main() {
  const url = process.env.DEMO_URL || 'http://127.0.0.1:8501';
  const output = path.resolve('docs/assets/contextdiff-demo.gif');
  const work = await fs.mkdtemp(path.join(os.tmpdir(), 'contextdiff-demo-'));
  const browser = await chromium.launch({ channel: 'chrome', headless: true });
  try {
    const page = await browser.newPage({
      viewport: { width: 1280, height: 960 }, deviceScaleFactor: 1,
      acceptDownloads: true, colorScheme: 'light',
    });
    const errors = [];
    page.on('pageerror', error => errors.push(error.message));
    const frames = [];
    async function capture(seconds) {
      const filename = path.join(work, `${String(frames.length).padStart(3, '0')}.png`);
      await page.screenshot({ path: filename });
      frames.push({ filename, seconds });
    }
    const mainPanel = page.locator('[data-testid="stMain"]');
    async function scrollTo(y) {
      const start = await mainPanel.evaluate(el => el.scrollTop);
      for (let i = 1; i <= 10; i++) {
        const t = i / 10;
        const eased = t * t * (3 - 2 * t);
        await mainPanel.evaluate((el, value) => { el.scrollTop = value; }, start + (y - start) * eased);
        await capture(0.06);
      }
    }
    async function show(locator) {
      const y = await locator.evaluate(el => {
        const panel = document.querySelector('[data-testid="stMain"]');
        return panel.scrollTop + el.getBoundingClientRect().top - 70;
      });
      await scrollTo(y);
    }
    async function choose(name) {
      await page.getByRole('combobox', { name: 'Bundled example', exact: true }).click();
      await capture(0.6);
      await page.getByRole('option', { name, exact: true }).click();
      await page.getByRole('button', { name: 'Download JSON report', exact: true }).waitFor({ state: 'hidden' });
      await capture(0.6);
    }
    async function compare(variant, total, status) {
      await page.getByRole('button', { name: 'Load sample', exact: true }).click();
      await page.waitForFunction(expected => {
        const after = document.querySelector('textarea[aria-label="After content"]');
        return after && after.value.includes(`${expected} handoff`);
      }, variant);
      await capture(0.9);
      await page.getByRole('button', { name: 'Compare', exact: true }).click();
      const download = page.getByRole('button', { name: 'Download JSON report', exact: true });
      await download.waitFor();
      await page.getByRole('heading', { name: 'Blocks and line edits', exact: true }).waitFor();
      await page.getByText('After source IDs: ' + (variant === 'lossy' ? 'None' : 'handoff-summary'), { exact: true }).first().waitFor();
      assert.deepEqual(await page.locator('[data-testid="stMetricValue"]').allTextContents(),
        ['271', String(total), String(total - 271), '1', '3', '1', '1']);
      assert.equal(await page.locator('[data-testid="stException"]').count(), 0);
      await page.evaluate(() => document.fonts.ready);
      await page.waitForTimeout(300);
      await capture(0.5);
      await show(page.getByRole('heading', { name: 'Comparison', exact: true }));
      await capture(2.2);
      await show(page.getByRole('heading', { name: 'Watched phrases', exact: true }));
      const phrase = page.locator('code').filter({ hasText: /^24-hour idempotency window$/ }).first();
      await phrase.evaluate(el => {
        const range = document.createRange();
        range.selectNodeContents(el);
        window.getSelection().removeAllRanges();
        window.getSelection().addRange(range);
      });
      await capture(variant === 'lossy' ? 4.2 : 5.2);
      const downloadEvent = page.waitForEvent('download');
      await download.click();
      const file = await downloadEvent;
      const reportPath = path.join(work, `${variant}-report.json`);
      await file.saveAs(reportPath);
      const report = JSON.parse(await fs.readFile(reportPath, 'utf8'));
      assert.equal(report.tokens.before_total, 271);
      assert.equal(report.tokens.after_total, total);
      assert.equal(report.watches[0].status, status);
      assert.deepEqual(report.watches[0].after_block_ids, variant === 'lossy' ? [] : ['handoff-summary']);
      await page.evaluate(() => window.getSelection().removeAllRanges());
    }
    await page.goto(url);
    await page.getByRole('heading', { name: 'ContextDiff', exact: true }).waitFor();
    await page.getByRole('combobox', { name: 'Bundled example', exact: true }).waitFor();
    await page.evaluate(() => document.fonts.ready);
    await capture(1.8);
    await choose('Coding handoff · lossy');
    await compare('lossy', 52, 'missing_after');
    await scrollTo(0);
    await choose('Coding handoff · preserved');
    await compare('preserved', 64, 'present_after');
    assert.deepEqual(errors, []);
    const duration = frames.reduce((sum, frame) => sum + frame.seconds, 0);
    const manifest = frames.map(f => `file '${f.filename}'\nduration ${f.seconds}`).join('\n')
      + `\nfile '${frames.at(-1).filename}'\n`;
    await fs.writeFile(path.join(work, 'frames.txt'), manifest);
    // Palette quantization only; no overlays, synthetic UI, or altered metrics.
    execFileSync('ffmpeg', ['-hide_banner', '-loglevel', 'error', '-y',
      '-f', 'concat', '-safe', '0', '-i', path.join(work, 'frames.txt'),
      '-filter_complex', '[0:v]fps=16,split[a][b];[a]palettegen=stats_mode=diff[p];[b][p]paletteuse=dither=bayer:bayer_scale=4',
      '-t', duration.toFixed(2), '-loop', '0', output]);
    console.log(JSON.stringify({ output, work, duration, frames: frames.length,
      bytes: (await fs.stat(output)).size, browserErrors: errors }, null, 2));
  } finally {
    await browser.close();
  }
}
main().catch(error => { console.error(error); process.exitCode = 1; });
