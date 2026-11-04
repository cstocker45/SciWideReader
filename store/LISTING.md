# Chrome Web Store listing (copy into the developer dashboard)

**Name:** WideReader – full-width journal articles
**Category:** Productivity (or Education)
**Language:** English

**Summary (≤132 chars):**
Hides sidebars on journal websites (Nature, Cell, Science, PMC, bioRxiv…) so the paper uses the full width. Adjustable typography.

**Description:**
Reading papers on publisher websites means squinting at a narrow column squeezed between a table of contents, "related articles", metrics and download boxes. WideReader hides everything that sits beside the article, so the text and figures use the full width of your browser.

• Works on ~30 journal sites out of the box: Nature, Cell Press, Science, PNAS, PubMed Central, bioRxiv/medRxiv, eLife, PLOS, BMC, Springer, Wiley, Oxford Academic, EMBO, Frontiers, MDPI, JCI, arXiv and more
• Any other site: click the toolbar menu or press Alt+W
• No per-site rules: it finds the article automatically and hides only what's beside it. Headers, figures, tables and references stay
• Typography menu: font (Serif, Book, Sans, Wide), text size, line spacing, paragraph spacing, maximum text width. Changes apply live
• Remembers on/off per site
• No data collection, no network requests, no account

Open source: https://github.com/cstocker45/WideReader

**Single purpose (dashboard field):**
Make scientific articles on journal websites easier to read by hiding sidebars and letting the article use the full browser width, with adjustable typography.

**Permission justifications:**
- storage: saves the user's on/off choice per site and typography settings locally.
- activeTab: lets the user apply the layout to the current page (toolbar menu / Alt+W) on sites that are not in the built-in list.
- scripting: injects the layout script into the current tab when the user turns it on for a site not in the built-in list.
- Host permissions (journal domains, via content_scripts): applies the layout automatically on supported journal websites.
- Remote code: No, all code is in the package.

**Data usage:** Does not collect or use any user data (tick none of the categories). Certify all three disclosures.

**Privacy policy URL:** https://cstocker45.github.io/WideReader/privacy.html
**Homepage URL:** https://cstocker45.github.io/WideReader/
**Support URL:** https://github.com/cstocker45/WideReader/issues

**Assets (in this folder):**
- icon128.png (store icon)
- screenshot-1-before.png, screenshot-2-after.png, screenshot-3-menu.png (1280×800)
