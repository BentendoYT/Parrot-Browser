#!/usr/bin/env python3
"""Parrot UI polish. Run from the Firefox source directory (after parrot-nova-colors.py).

  1. Non-Nova design: neutral black/white accent instead of blue/cyan
     (tokens-shared.css + tokens-platform.css, same values as the Nova patch).
  2. New Tab (Nova): the newtab extension ships its OWN copy of the Nova tokens
     (browser/extensions/newtab/content-src/styles/nova/_tokens.scss), so the
     design-system patch never reached it. Patch the same tokens there.
  3. about:privatebrowsing (Nova): search field no longer uses violet #3e315f.
  4. Private-browsing "Who might ... see my activity?" links (about:privatebrowsing
     and the private-window info panel) -> exact Mozilla Support article URL.

  5. Private page search focus ring: same thickness as the normal New Tab (Nova and legacy).
  6. Info icons (moz-message-bar, About "updates" box): neutral instead of violet/blue.
  7. Chrome focus outline (URL bar etc.): the LWT override forced blue/cyan -> accent.
  8. Support links: moz-support-link builds app.support.baseURL + slug, which gave
     ".../issuespreferences". Three slugs now map to exact Parrot URLs; all others unchanged.

Every edit is exact-match and idempotent. If Firefox changed and a target no longer
matches, the script exits with an error and writes nothing for that file.
"""
import sys
from pathlib import Path

MYTHS_URL = "https://support.mozilla.org/en-US/kb/common-myths-about-private-browsing"
DIST = Path("toolkit/themes/shared/design-system/dist")

NEUTRAL_HOVER = "light-dark(rgba(0, 0, 0, 0.08), rgba(255, 255, 255, 0.1))"
NEUTRAL_ACTIVE = "light-dark(rgba(0, 0, 0, 0.14), rgba(255, 255, 255, 0.16))"


ICON_NEUTRAL = "light-dark(#171519, #efedf2)"
ISSUES_URL = "https://github.com/BentendoYT/Parrot-Browser/issues"
WIKI_BUILTIN_URL = "https://github.com/BentendoYT/Parrot-Browser/wiki/Built%E2%80%90in-Extensions-&-Themes"
# slug (support-page attribute) -> exact URL. Add "addons-help" here once decided.
SUPPORT_LINKS = {
    "preferences": ISSUES_URL,
    "cant-remove-addon": WIKI_BUILTIN_URL,
}


def die(msg):
    raise SystemExit(f"parrot-ui-polish: {msg}")


def patch_file(path, edits):
    """edits: list of (old, new). Each must match exactly once (or already be applied)."""
    path = Path(path)
    if not path.is_file():
        die(f"{path} not found; run from the Firefox source directory")
    raw = path.read_bytes()
    text = raw.decode("utf-8")
    for edit in edits:
        old, new = edit[0], edit[1]
        marker = edit[2] if len(edit) > 2 else None   # for edits whose new text still contains old
        if marker is not None and marker in text:
            continue
        n_old, n_new = text.count(old), text.count(new)
        if marker is None and n_old == 0 and n_new >= 1:
            continue  # already applied
        if n_old != 1:
            die(f"{path}: expected exactly one match, found {n_old} for:\n  {old[:140]}")
        text = text.replace(old, new, 1)
    data = text.encode("utf-8")
    if data != raw:
        path.write_bytes(data)
        print(f"Patched {path}")
    else:
        print(f"Already patched {path}")


# --- 1. non-Nova accent (foundation + browser-theme layers) -------------------------
NONNOVA_ACCENT = [
    ("--color-accent-primary: light-dark(var(--color-blue-60), var(--color-cyan-30));",
     "--color-accent-primary: light-dark(#171519, #ffffff);"),
    ("--color-accent-primary-hover: light-dark(var(--color-blue-70), var(--color-cyan-20));",
     "--color-accent-primary-hover: light-dark(#252428, #efedf2);"),
    ("--color-accent-primary-active: light-dark(var(--color-blue-80), var(--color-cyan-10));",
     "--color-accent-primary-active: light-dark(#3f3e42, #d6d5da);"),
    # Same choice as Nova: selected state follows the (neutral) active primary button.
    ("--color-accent-primary-selected: light-dark(var(--color-blue-60), var(--color-cyan-30));",
     "--color-accent-primary-selected: var(--button-background-color-primary-active);"),
]

# --- 2. New Tab: private copy of the Nova tokens --------------------------------------
NEWTAB_TOKENS = Path("browser/extensions/newtab/content-src/styles/nova/_tokens.scss")
NEWTAB_EDITS = [
    ("--color-accent-primary: light-dark(var(--color-violet-50), var(--color-violet-30));",
     "--color-accent-primary: light-dark(#171519, #ffffff);"),
    ("--color-accent-primary-hover: light-dark(var(--color-violet-60), var(--color-violet-20));",
     "--color-accent-primary-hover: light-dark(#252428, #efedf2);"),
    ("--color-accent-primary-active: light-dark(var(--color-violet-70), var(--color-violet-10));",
     "--color-accent-primary-active: light-dark(#3f3e42, #d6d5da);"),
    ("--button-background-color-hover: light-dark(var(--color-violet-desaturated-20), var(--color-violet-desaturated-50));",
     f"--button-background-color-hover: {NEUTRAL_HOVER};"),
    ("--button-background-color-active: light-dark(var(--color-violet-desaturated-30), var(--color-violet-desaturated-40));",
     f"--button-background-color-active: {NEUTRAL_ACTIVE};"),
    ("--toolbarbutton-background-color-hover: light-dark(rgba(117, 102, 159, 25%), rgba(182, 170, 217, 25%));",
     f"--toolbarbutton-background-color-hover: {NEUTRAL_HOVER};"),
    ("--toolbarbutton-background-color-active: light-dark(rgba(117, 102, 159, 40%), rgba(182, 170, 217, 40%));",
     f"--toolbarbutton-background-color-active: {NEUTRAL_ACTIVE};"),
]

# --- 3. about:privatebrowsing (Nova) search field ----------------------------------------
PB_CSS = Path("browser/themes/shared/privatebrowsing/aboutPrivateBrowsing.css")
PB_CSS_EDITS = [
    # violet-desaturated-70 == #3e315f. The page is dark, so keep a dark neutral
    # field (white text) and let the focus ring use the white accent (already tokenised).
    ("--content-search-handoff-ui-background-color: var(--color-violet-desaturated-70);",
     "--content-search-handoff-ui-background-color: var(--color-gray-80);"),
    ("--content-search-handoff-ui-unfocused-border-color: var(--color-violet-desaturated-50);",
     "--content-search-handoff-ui-unfocused-border-color: var(--color-gray-60);"),
    # Focus ring like the normal New Tab: accent border + 25% inner ring, no outer glow.
    ("--content-search-handoff-ui-fakefocus-box-shadow-inner: var(--color-accent-primary);",
     "--content-search-handoff-ui-fakefocus-box-shadow-inner: color-mix(in srgb, var(--color-accent-primary) 25%, transparent);"),
    ("--content-search-handoff-ui-fakefocus-box-shadow-outer: color-mix(in srgb, var(--color-accent-primary) 30%, transparent);",
     "--content-search-handoff-ui-fakefocus-box-shadow-outer: transparent;"),
    # Legacy (non-Nova) private page: blue focus ring -> same accent ring. The leading
    # newline + 2 spaces keeps these anchors distinct from the Nova block (6 spaces).
    ("\n  --content-search-handoff-ui-fakefocus-border-color: #0060df;",
     "\n  --content-search-handoff-ui-fakefocus-border-color: var(--color-accent-primary);"),
    ("\n  --content-search-handoff-ui-fakefocus-box-shadow-inner: #0060df;",
     "\n  --content-search-handoff-ui-fakefocus-box-shadow-inner: color-mix(in srgb, var(--color-accent-primary) 25%, transparent);"),
    ("\n  --content-search-handoff-ui-fakefocus-box-shadow-outer: rgba(0, 96, 223, 0.3);",
     "\n  --content-search-handoff-ui-fakefocus-box-shadow-outer: transparent;"),
]

# --- 5/6/7/8. info icons, focus outline, support links -----------------------------------
MSGBAR_TOKENS = Path("toolkit/content/widgets/moz-message-bar/moz-message-bar.tokens.css")
MSGBAR_EDITS = [("--message-bar-icon-color: var(--icon-color-information);",
                 f"--message-bar-icon-color: {ICON_NEUTRAL};")]
UPDATE_STATE = Path("browser/components/preferences/widgets/update-state/update-state.css")
UPDATE_STATE_EDITS = [("--box-icon-start-fill: var(--icon-color-information);",
                       f"--box-icon-start-fill: {ICON_NEUTRAL};")]
BROWSER_COLORS = Path("browser/themes/shared/browser-colors.css")
BROWSER_COLORS_EDITS = [("--focus-outline-color: light-dark(#0061e0, #00ddff);",
                         "--focus-outline-color: var(--color-accent-primary);")]
SUPPORT_LINK = Path("toolkit/content/widgets/moz-support-link/moz-support-link.mjs")
_map = ",\n".join(f'    "{k}": "{v}"' for k, v in SUPPORT_LINKS.items())
SUPPORT_LINK_EDITS = [
    ('  static SUPPORT_URL = "https://www.mozilla.org/";',
     '  static SUPPORT_URL = "https://www.mozilla.org/";\n'
     '  // Parrot: slugs that must open an exact URL instead of app.support.baseURL + slug.\n'
     '  static PARROT_SUPPORT_LINKS = {\n' + _map + ',\n  };',
     'static PARROT_SUPPORT_LINKS = {'),
    ('    let base = MozSupportLink.SUPPORT_URL + supportPage;',
     '    let base = Object.hasOwn(MozSupportLink.PARROT_SUPPORT_LINKS, supportPage)\n'
     '      ? MozSupportLink.PARROT_SUPPORT_LINKS[supportPage]\n'
     '      : MozSupportLink.SUPPORT_URL + supportPage;'),
]

# --- 4. private-browsing links ------------------------------------------------------------
PB_JS = Path("browser/components/privatebrowsing/content/aboutPrivateBrowsing.js")
PB_JS_EDITS = [(
    '  linkEl.setAttribute(\n    "href",\n'
    '    RPMGetFormatURLPref("app.support.baseURL") + "private-browsing-myths"\n  );',
    f'  linkEl.setAttribute(\n    "href",\n    "{MYTHS_URL}"\n  );',
)]
POPUPSET = Path("browser/base/content/main-popupset.inc.xhtml")
POPUPSET_EDITS = [(
    '        <html:a is="moz-support-link"\n'
    '                data-l10n-name="learn-more"\n'
    '                support-page="private-browsing-myths"/>',
    '        <html:a data-l10n-name="learn-more"\n'
    f'                href="{MYTHS_URL}"\n'
    '                onclick="event.preventDefault(); openTrustedLinkIn(this.href, \'tab\');"/>',
)]


def main():
    for name in ("tokens-shared.css", "tokens-platform.css"):
        patch_file(DIST / name, NONNOVA_ACCENT)
    patch_file(NEWTAB_TOKENS, NEWTAB_EDITS)
    patch_file(PB_CSS, PB_CSS_EDITS)
    patch_file(PB_JS, PB_JS_EDITS)
    patch_file(POPUPSET, POPUPSET_EDITS)
    patch_file(MSGBAR_TOKENS, MSGBAR_EDITS)
    patch_file(UPDATE_STATE, UPDATE_STATE_EDITS)
    patch_file(BROWSER_COLORS, BROWSER_COLORS_EDITS)
    patch_file(SUPPORT_LINK, SUPPORT_LINK_EDITS)


if __name__ == "__main__":
    main()
