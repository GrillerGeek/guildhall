// Synthetic document/comment UI coverage. Live host and native artifact acceptance
// are separate gates. Supply fixture locations; never store runtime tokens here.
const { test, expect } = require('@playwright/test');
const fs = require('node:fs');
const crypto = require('node:crypto');

function fixture() {
  for (const name of ['REVIEW_STARTUP_RECEIPT', 'REVIEW_OFFLINE_URL', 'REVIEW_PLAN_PATH']) {
    if (!process.env[name]) throw new Error(`Required isolated fixture input: ${name}`);
  }
  const startup = JSON.parse(fs.readFileSync(process.env.REVIEW_STARTUP_RECEIPT, 'utf8'));
  if (!startup.ok || startup.result.capabilities.chat || startup.result.session_id !== null) {
    throw new Error('These tests require an unbound synthetic document/comment companion');
  }
  return startup.result;
}
const review = page => page.getByLabel('Review Markdown', { exact: true });
const status = page => page.getByRole('status');
const button = (page, name) => page.getByRole('button', { name, exact: true });
const comparison = page => page.getByRole('region', { name: 'Unsaved draft and conflict comparison', exact: true });
async function connect(page) {
  const input = fixture();
  await page.goto(input.origin);
  await page.getByLabel('One-time write token').fill(input.write_token);
  await button(page, 'Connect').click();
  await expect(button(page, 'Save review')).toBeEnabled();
  await expect(status(page)).toContainText('Connected.');
}
async function save(page, text) {
  await review(page).fill(text);
  await button(page, 'Save review').click();
  await expect(status(page)).toHaveText('Review saved. This does not accept the proposal.');
}
async function downloadText(page, name) {
  const pending = page.waitForEvent('download');
  await button(page, name).click();
  const download = await pending;
  const stream = await download.createReadStream();
  const chunks = [];
  for await (const chunk of stream) chunks.push(chunk);
  return { name: download.suggestedFilename(), text: Buffer.concat(chunks).toString('utf8') };
}
function hashFile(path) {
  return crypto.createHash('sha256').update(fs.readFileSync(path)).digest('hex');
}

test.beforeEach(async ({ page }) => {
  fixture();
  page.on('dialog', dialog => dialog.accept());
});

test('E11: connect displays local identity and the actual unavailable chat reason', async ({ page }) => {
  await connect(page);
  await expect(page.getByText('Session: local document/comments', { exact: true })).toBeVisible();
  await expect(page.getByText('Agent chat is unavailable in document/comment mode.', { exact: true })).toBeVisible();
  await expect(button(page, 'Save comment')).toBeEnabled();
  await expect(button(page, 'Cancel pending request')).toBeDisabled();
  const response = await page.request.get(`${fixture().origin}/state`);
  const state = (await response.json()).result;
  expect(state.binding).toBeNull();
  expect(state.capabilities.chat).toBe(false);
  expect(state).not.toHaveProperty('write_token');
});

test('E07/E11: a selected passage comment persists as a proposal after reconnect', async ({ page }) => {
  await connect(page);
  const original = await review(page).inputValue();
  const marker = `Unique UI passage ${crypto.randomUUID()}`;
  const comment = `Please compare this proposal ${crypto.randomUUID()}`;
  try {
    await save(page, marker + '\n' + original);
    await review(page).focus();
    await page.keyboard.press('ControlOrMeta+A');
    await page.keyboard.press('ArrowLeft');
    await page.keyboard.down('Shift');
    for (let i = 0; i < marker.length; i++) await page.keyboard.press('ArrowRight');
    await page.keyboard.up('Shift');
    await button(page, 'Use selection').click();
    await expect(page.getByLabel('Selected passage (optional)')).toHaveValue(marker);
    await expect(page.getByLabel('Comment or question')).toBeFocused();
    await page.getByLabel('Comment or question').fill(comment);
    await button(page, 'Save comment').click();
    await expect(status(page)).toContainText('Feedback recorded: prepared.');
    await page.reload();
    await page.getByLabel('One-time write token').fill(fixture().write_token);
    await button(page, 'Connect').click();
    await expect(page.locator('#responses')).toContainText(comment + '\nDisposition: proposed');
    const state = (await (await page.request.get(`${fixture().origin}/state`)).json()).result;
    const entry = state.feedback.find(item => item.text === comment);
    expect(entry.disposition).toBe('proposed');
    expect(entry.selection).toEqual({ status: 'attached', text: marker });
    expect(entry.source_ref).toBeTruthy();
  } finally {
    await save(page, original);
  }
});

test('E11: saved direct edits survive reload while dirty prose blocks passage feedback', async ({ page }) => {
  await connect(page);
  const original = await review(page).inputValue();
  const revised = original + '\nUI direct edit ' + crypto.randomUUID();
  try {
    await review(page).fill(revised);
    await expect(status(page)).toHaveText('Unsaved draft in this tab.');
    await page.getByLabel('Comment or question').fill('Discuss after saving');
    await button(page, 'Save comment').click();
    await expect(status(page)).toContainText('Save or download your edited draft');
    await expect(page.getByLabel('Comment or question')).toHaveValue('Discuss after saving');
    await save(page, revised);
    await page.reload();
    await page.getByLabel('One-time write token').fill(fixture().write_token);
    await button(page, 'Connect').click();
    await expect(review(page)).toHaveValue(revised);
  } finally {
    await save(page, original);
  }
});

test('E06/E11: two tabs retain a rejected draft and keyboard-scroll the saved comparison', async ({ page, context }) => {
  await connect(page);
  const other = await context.newPage();
  other.on('dialog', dialog => dialog.accept());
  await connect(other);
  const original = await review(page).inputValue();
  const draft = original + '\nSecond tab unsaved ' + crypto.randomUUID();
  const winner = original + '\n' + Array.from({ length: 80 }, (_, i) => `Saved comparison line ${i}`).join('\n');
  try {
    await review(other).fill(draft);
    await save(page, winner);
    await button(other, 'Check for updates').click();
    await expect(status(other)).toContainText('Your unsaved draft remains in the editor');
    await expect(review(other)).toHaveValue(draft);
    await button(other, 'Save review').click();
    await expect(status(other)).toContainText('Your draft remains in this tab');
    await expect(review(other)).toHaveValue(draft);
    await other.getByText('Unsaved draft and conflict comparison', { exact: true }).click();
    await expect(comparison(other)).toContainText(winner);
    await other.locator('summary').focus();
    await other.keyboard.press('Tab');
    await expect(comparison(other)).toBeFocused();
    await other.keyboard.press('PageDown');
    await expect.poll(() => comparison(other).evaluate(node => node.scrollTop)).toBeGreaterThan(0);
    expect((await downloadText(other, 'Download Markdown')).text).toBe(draft);
    await button(page, 'Check for updates').click();
    await expect(review(page)).toHaveValue(winner);
  } finally {
    await save(page, original);
    await other.close();
  }
});

test('E07/E09: local checkpoint records synchronization without changing the plan or accepting decisions', async ({ page }) => {
  await connect(page);
  const planHash = hashFile(process.env.REVIEW_PLAN_PATH);
  const before = (await (await page.request.get(`${fixture().origin}/state`)).json()).result;
  await button(page, 'Checkpoint local review').click();
  await expect(status(page)).toHaveText('Local review checkpoint complete. The proposal remains subject to owner acceptance.');
  const after = (await (await page.request.get(`${fixture().origin}/state`)).json()).result;
  expect(after.checkpoint.state).toBe('clean');
  expect(after.feedback).toEqual(before.feedback);
  expect(hashFile(process.env.REVIEW_PLAN_PATH)).toBe(planHash);
});

for (const width of [1280, 390]) {
  test(`E05: offline export at ${width}px supports local edits, selection and downloads without network`, async ({ page }) => {
    await page.setViewportSize({ width, height: 900 });
    const network = [];
    page.on('request', request => {
      if (/^https?:/.test(request.url())) network.push(request.url());
    });
    await page.context().setOffline(true);
    await page.goto(process.env.REVIEW_OFFLINE_URL);
    await expect(page.getByRole('heading', { name: 'Review the proposal', exact: true })).toBeVisible();
    await expect(review(page)).not.toHaveValue('');
    await expect(page.getByText(/Agent chat and hosted comments are unavailable in this offline export/)).toBeVisible();
    for (const name of ['Save review', 'Send feedback', 'Cancel pending request', 'Connect', 'Check for updates', 'Checkpoint local review']) {
      await expect(button(page, name)).toBeDisabled();
    }
    const draft = 'Offline draft with meaningful local controls';
    await review(page).fill(draft);
    await review(page).focus();
    await page.keyboard.press('ControlOrMeta+A');
    await button(page, 'Use selection').click();
    await expect(page.getByLabel('Selected passage (optional)')).toHaveValue(draft);
    await expect(status(page)).toHaveText('Unsaved draft in this tab.');
    await page.getByText('Unsaved draft and conflict comparison', { exact: true }).click();
    await expect(page.getByText('This tab contains unsaved edits. Download them before closing.', { exact: true })).toBeVisible();
    expect(await downloadText(page, 'Download Markdown')).toEqual({ name: 'review.md', text: draft });
    await page.getByLabel('Option to explore').selectOption({ label: 'Alternative' });
    await page.getByLabel('Benefits, costs and unresolved questions').fill('Benefits and unresolved costs');
    expect(await downloadText(page, 'Download comparison')).toEqual({ name: 'comparison.md', text: 'Alternative\n\nBenefits and unresolved costs' });
    await expect(page.getByText(/A choice here is a proposal, not acceptance/)).toBeVisible();
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
    expect(network).toEqual([]);
  });
}

test('E05/E06 accessibility: keyboard focus contrast meets 3:1 in both themes', async ({ page }) => {
  function luminance(rgb) {
    const channels = rgb.match(/[\d.]+/g).slice(0, 3).map(Number).map(n => {
      const s = n / 255;
      return s <= 0.04045 ? s / 12.92 : ((s + 0.055) / 1.055) ** 2.4;
    });
    return channels[0] * 0.2126 + channels[1] * 0.7152 + channels[2] * 0.0722;
  }
  for (const colorScheme of ['light', 'dark']) {
    await page.emulateMedia({ colorScheme });
    await page.goto(process.env.REVIEW_OFFLINE_URL);
    await review(page).focus();
    await page.keyboard.press('Tab');
    await expect(button(page, 'Download Markdown')).toBeFocused();
    const colors = await button(page, 'Download Markdown').evaluate(node => {
      const style = getComputedStyle(node);
      return { outline: style.outlineColor, width: style.outlineWidth, button: style.backgroundColor, body: getComputedStyle(document.body).backgroundColor };
    });
    expect(parseFloat(colors.width)).toBeGreaterThanOrEqual(3);
    for (const background of [colors.body, colors.button]) {
      const values = [luminance(colors.outline), luminance(background)].sort((a, b) => b - a);
      expect((values[0] + 0.05) / (values[1] + 0.05)).toBeGreaterThanOrEqual(3);
    }
  }
});
