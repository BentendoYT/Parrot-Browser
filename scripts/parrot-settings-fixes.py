#!/usr/bin/env python3
"""Parrot settings, support-link and UI fixes. Run from the Firefox source directory,
AFTER scripts/parrot-ui-polish.py (it extends the PARROT_SUPPORT_LINKS table that
script creates in moz-support-link.mjs).

Root cause of the malformed links: parrot.cfg sets app.support.baseURL to
".../Parrot-Browser/issues" (no trailing slash), and moz-support-link builds
baseURL + slug, e.g. ".../issuesfirefox-suggest". Instead of touching the pref (which would
redirect every Mozilla link) each requested slug is mapped to its exact destination.
Slugs shared with controls that need a different destination get a dedicated slug.

  1. Support-link table: exact URLs for every requested Learn more link.
  2. Dedicated slugs: About > Get help (FAQ) and Tabs > Container Tabs (FPI FAQ).
  3. Sidebar Parrot Support button -> FAQ.
  4. Help menu: "How to migrate your data" -> exact SUMO URL (no utm params),
     Get help -> LibreWolf FAQ, neutral switch-device bubble (Nova).
  5. Disabled primary buttons: neutral instead of violet (Nova tokens + New Tab copy).
  6. Main address bar (#urlbar): pure #ffffff focus outline.

Every edit is exact-match and idempotent; a missing or ambiguous anchor aborts the run.
"""
import re
from pathlib import Path

SUMO = "https://support.mozilla.org/en-US/kb/"
WIKI = "https://github.com/BentendoYT/Parrot-Browser/wiki/FAQ"
FAQ_PW = WIKI + "#why-is-the-built-in-password-manager-disabled"

# slug (support-page attribute) -> exact URL
LINKS = {
    # Settings > Search
    "quick-actions-firefox-search-bar": SUMO + "quick-actions-firefox-search-bar",
    "firefox-suggest": SUMO + "firefox-suggest",
    # Settings > Account and Sync
    "managed-browser-firefox": SUMO + "managed-browser-firefox",
    "profile-management": SUMO + "profile-management",
    "firefox-backup": SUMO + "firefox-backup",
    # Settings > Privacy & Security
    "enhanced-tracking-protection": SUMO + "enhanced-tracking-protection-firefox-desktop",
    "manage-enhanced-tracking-protection-exceptions": SUMO + "manage-enhanced-tracking-protection-exceptions",
    "global-privacy-control": SUMO + "global-privacy-control",
    "firefox-relay-integration": SUMO + "relay-integration?redirectslug=firefox-relay-integration&redirectlocale=en-US",
    "jit-toggle": WIKI + "#how-do-i-toggle-javascript-jit-per-site",
    "dns-over-https": SUMO + "dns-over-https",
    # Settings > Passwords and Autofill
    "how-generate-secure-password-firefox": SUMO + "how-generate-secure-password-firefox",
    "windows-sso": SUMO + "windows-sso",
    "primary-password-stored-logins": FAQ_PW,
    "lockwise-alerts": FAQ_PW,
    "credit-card-autofill": SUMO + "credit-card-autofill",
    "credit-card-autofill#w_require-authentication-for-autofill": SUMO + "credit-card-autofill#w_require-authentication-for-autofill",
    "automatically-fill-your-address-web-forms": SUMO + "automatically-fill-your-address-web-forms",
    # Settings > Tabs and Browsing
    "picture-in-picture": SUMO + "picture-in-picture",
    "drm-content": WIKI + "#how-do-i-allow-playback-of-drm-controlled-content-when-should-i-allow-it",
    "open-h264-plugin-firefox": SUMO + "open-h264-plugin-firefox",
    "performance": SUMO + "performance",
    # dedicated slugs (the original slug is shared with controls that keep their own link)
    "parrot-support-faq": WIKI,
    "parrot-containers-faq": WIKI + "#why-isnt-first-party-isolation-fpi-enabled-by-default",
}

SWITCHING_URL = SUMO + "switching-devices"
HELP_URL = "https://librewolf.net/docs/faq/"

MARK = "Parrot settings fixes"


def die(msg):
    raise SystemExit(f"parrot-settings-fixes: {msg}")


def read(path):
    path = Path(path)
    if not path.is_file():
        die(f"{path} not found; run from the Firefox source directory")
    return path, path.read_bytes().decode("utf-8")


def write_if_changed(path, old_text, new_text):
    if new_text != old_text:
        path.write_bytes(new_text.encode("utf-8"))
        print(f"Patched {path}")
    else:
        print(f"Already patched {path}")


def patch_file(path, edits):
    """edits: (old, new) pairs. Each must match exactly once, or already be applied."""
    path, text = read(path)
    orig = text
    for old, new in edits:
        n_old, n_new = text.count(old), text.count(new)
        if n_old == 0 and n_new >= 1:
            continue
        if n_old != 1:
            die(f"{path}: expected exactly one match, found {n_old} for:\n  {old[:160]}")
        text = text.replace(old, new, 1)
    write_if_changed(path, orig, text)


def append_block(path, marker, block):
    path, text = read(path)
    if marker in text:
        print(f"Already patched {path}")
        return
    if not text.endswith("\n"):
        text += "\n"
    path.write_bytes((text + "\n" + block).encode("utf-8"))
    print(f"Patched {path}")


def extend_support_table():
    path, text = read("toolkit/content/widgets/moz-support-link/moz-support-link.mjs")
    m = re.search(r"static PARROT_SUPPORT_LINKS = \{\n(.*?)\n  \};", text, re.S)
    if not m:
        die("PARROT_SUPPORT_LINKS not found; run parrot-ui-polish.py first")
    body = m.group(1)
    missing = [(k, v) for k, v in LINKS.items() if f'"{k}":' not in body]
    for k, v in LINKS.items():
        for line in body.splitlines():
            if line.strip().startswith(f'"{k}":') and f'"{v}"' not in line:
                die(f"{path}: slug {k!r} already mapped to a different URL: {line.strip()}")
    if not missing:
        print(f"Already patched {path}")
        return
    add = "".join(f'    "{k}": "{v}",\n' for k, v in missing)
    body = body if body.endswith(",") else body + ","
    new = text[:m.start(1)] + body + "\n" + add.rstrip("\n") + text[m.end(1):]
    path.write_bytes(new.encode("utf-8"))
    print(f"Patched {path} (+{len(missing)} links)")


# --- 2. dedicated slugs --------------------------------------------------------------
ABOUT_HELP = ("browser/components/preferences/config/about-firefox.mjs", [(
    '            l10nId: "support-get-help",\n            control: "moz-box-link",\n            supportPage: "preferences",',
    '            l10nId: "support-get-help",\n            control: "moz-box-link",\n            supportPage: "parrot-support-faq",',
)])
CONTAINERS = ("browser/components/preferences/config/tabs-browsing.mjs", [(
    '            l10nId: "browser-containers-enabled-2",\n            supportPage: "containers",',
    '            l10nId: "browser-containers-enabled-2",\n            supportPage: "parrot-containers-faq",',
)])

# --- 3. sidebar Parrot Support button ----------------------------------------------------
SIDEBAR = ("browser/components/preferences/preferences.xhtml", [(
    '        href="https://github.com/BentendoYT/Parrot-Browser/issues"\n        iconsrc="chrome://global/skin/icons/help.svg"',
    f'        href="{WIKI}"\n        iconsrc="chrome://global/skin/icons/help.svg"',
)])

# --- 4. Help menu ----------------------------------------------------------------------------
SWITCH_OLD = (
    '  let url = getHelpLinkURL("switching-devices");\n'
    '  let parsedUrl = new URL(url);\n'
    '  parsedUrl.searchParams.set("utm_content", "switch-to-new-device");\n'
    '  parsedUrl.searchParams.set("utm_source", "help-menu");\n'
    '  parsedUrl.searchParams.set("utm_medium", "firefox-desktop");\n'
    '  parsedUrl.searchParams.set("utm_campaign", "migration");\n'
    '  openTrustedLinkIn(parsedUrl.href, "tab");'
)
SWITCH_NEW = f'  // Parrot: exact URL, no support-base concatenation and no utm parameters.\n  openTrustedLinkIn("{SWITCHING_URL}", "tab");'
OPEN_HELP = f'openTrustedLinkIn("{HELP_URL}", "tab");'
HELP_EDITS = [
    ("browser/base/content/utilityOverlay.js", [(SWITCH_OLD, SWITCH_NEW)]),
    ("browser/components/customizableui/content/panelUI.js", [(
        '      case "appMenu_menu_openHelp":\n        openHelpLink("firefox-help");',
        f'      case "appMenu_menu_openHelp":\n        {OPEN_HELP}')]),
    ("browser/base/content/browser-menubar.js", [(
        '        case "menu_openHelp":\n          openHelpLink("firefox-help");',
        f'        case "menu_openHelp":\n          {OPEN_HELP}')]),
    ("browser/base/content/browser.js", [(
        '    case "Help":\n      openHelpLink("firefox-help");',
        f'    case "Help":\n      {OPEN_HELP}')]),
]

PROMO_MARK = "/* Parrot: neutral switch-device promo"
PROMO_CSS = f"""{PROMO_MARK} (instead of violet vibrant tokens) */
#appMenu-nova-switch-device-promo {{
  --promo-background-color-vibrant: light-dark(rgba(0, 0, 0, 0.06), rgba(255, 255, 255, 0.12));
  --promo-border-color-vibrant: light-dark(rgba(0, 0, 0, 0.16), rgba(255, 255, 255, 0.24));
  --promo-message-text-color-vibrant: light-dark(#171519, #efedf2);
  --promo-heading-text-color-vibrant: light-dark(#171519, #efedf2);
  --promo-image-fill: light-dark(#171519, #efedf2);
}}
"""

# --- 5. disabled primary buttons ----------------------------------------------------------------
DISABLED_OLD = "--button-background-color-primary-disabled: light-dark(var(--color-violet-desaturated-50), var(--color-violet-desaturated-40));"
DISABLED_NEW = "--button-background-color-primary-disabled: light-dark(#9d9ca2, #cfced4);"
DISABLED_FILES = [
    "toolkit/themes/shared/design-system/dist/tokens-shared.css",
    "browser/extensions/newtab/content-src/styles/nova/_tokens.scss",
]

# --- 6. address bar focus outline ----------------------------------------------------------------
URLBAR_MARK = "/* Parrot: pure white focus outline"
URLBAR_CSS = f"""{URLBAR_MARK} for the main address bar (Nova and classic).
   Every focus border/outline of #urlbar reads --toolbar-field-border-color-focus
   (urlbar.css), so overriding it on the element itself also beats LWT themes. */
#urlbar {{
  --toolbar-field-border-color-focus: #ffffff;
}}
"""


def main():
    extend_support_table()
    for path, edits in (ABOUT_HELP, CONTAINERS, SIDEBAR, *HELP_EDITS):
        patch_file(path, edits)
    append_block("browser/themes/shared/customizableui/panelUI-shared.css", PROMO_MARK, PROMO_CSS)
    for path in DISABLED_FILES:
        patch_file(path, [(DISABLED_OLD, DISABLED_NEW)])
    append_block("browser/themes/shared/urlbar.css", URLBAR_MARK, URLBAR_CSS)
    print(f"{MARK}: done")


if __name__ == "__main__":
    main()
