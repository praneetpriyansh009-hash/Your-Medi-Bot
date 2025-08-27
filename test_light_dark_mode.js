const puppeteer = require('puppeteer');

(async () => {
    const browser = await puppeteer.launch();
    const page = await browser.newPage();
    await page.goto('http://localhost:5000');

    // Test light/dark mode toggle
    const darkModeToggle = await page.$('#darkModeToggle');
    await darkModeToggle.click(); // Switch to light mode
    let bodyClass = await page.evaluate(() => document.body.className);
    console.assert(bodyClass.includes('light-mode'), 'Light mode not activated');

    await darkModeToggle.click(); // Switch back to dark mode
    bodyClass = await page.evaluate(() => document.body.className);
    console.assert(!bodyClass.includes('light-mode'), 'Dark mode not activated');

    // Test if theme preference is saved
    await page.reload();
    bodyClass = await page.evaluate(() => document.body.className);
    console.assert(!bodyClass.includes('light-mode'), 'Theme preference not saved correctly');

    // Test responsive design
    await page.setViewport({ width: 500, height: 800 });
    const sidebar = await page.$('.sidebar');
    const sidebarVisible = await sidebar.evaluate(el => el.offsetWidth > 0);
    console.assert(sidebarVisible, 'Sidebar not visible in responsive mode');

    await browser.close();
})();
