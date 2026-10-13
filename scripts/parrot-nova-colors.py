#!/usr/bin/env python3
"""Give Firefox Nova a neutral (black / white) accent instead of violet.

Run from the Firefox source directory.

  --patch-dist      patch the generated CSS that the browser actually ships
  --patch-importer  patch the Figma importer, AND the shipped CSS (see below)

Why two targets
---------------
The browser does not run the importer (figma-import.mjs) or style-dictionary
during a normal build. It ships the *already generated* CSS that is checked in
under toolkit/themes/shared/design-system/dist/. Patching only the importer
therefore has no effect on the compiled browser. The importer is still patched
so that regenerating the tokens (npm run build-figma-nova && npm run build)
produces the same colors.

`--patch-importer` is the flag scripts/librewolf-patches.py already uses, so it
now does both. Every expectation is checked; if Firefox changes and a target no
longer matches, this script exits with an error instead of silently leaving
purple in the build.
"""
import sys
from pathlib import Path

DESIGN_SYSTEM = Path("toolkit/themes/shared/design-system")
IMPORTER = DESIGN_SYSTEM / "src" / "figma-import.mjs"
DIST = DESIGN_SYSTEM / "dist"

# token: (light, dark). Same values the importer patch writes.
ACCENT = {
    "--color-accent-primary": ("#171519", "#ffffff"),
    "--color-accent-primary-hover": ("#252428", "#efedf2"),
    "--color-accent-primary-active": ("#3f3e42", "#d6d5da"),
}
# What Firefox 157 generates for the Nova layers (violet).
OLD = {
    "--color-accent-primary": "light-dark(var(--color-violet-50), var(--color-violet-30))",
    "--color-accent-primary-hover": "light-dark(var(--color-violet-60), var(--color-violet-20))",
    "--color-accent-primary-active": "light-dark(var(--color-violet-70), var(--color-violet-10))",
}
# Both Nova layers define the accent: tokens-foundation-nova (tokens-shared.css)
# and tokens-browser-theme-nova (tokens-platform.css). Each must match once.
DIST_FILES = ("tokens-shared.css", "tokens-platform.css")


def die(message):
    raise SystemExit(f"parrot-nova-colors: {message}")


def patch_dist():
    for name in DIST_FILES:
        path = DIST / name
        if not path.is_file():
            die(f"{path} not found; run from the Firefox source directory")
        text = path.read_bytes().decode("utf-8")
        for token, (light, dark) in ACCENT.items():
            old = f"{token}: {OLD[token]};"
            new = f"{token}: light-dark({light}, {dark});"
            n_old, n_new = text.count(old), text.count(new)
            if n_old == 0 and n_new == 1:
                continue  # already patched
            if n_old != 1 or n_new != 0:
                die(f"{path}: expected exactly one '{token}' Nova definition "
                    f"(found {n_old} original, {n_new} patched); no changes made")
            text = text.replace(old, new, 1)
        data = text.encode("utf-8")
        if data != path.read_bytes():
            path.write_bytes(data)
            print(f"Patched Nova accent colors in {path}")
        else:
            print(f"Nova accent colors already patched in {path}")


def patch_importer():
    if not IMPORTER.is_file():
        die(f"{IMPORTER} not found; run from the Firefox source directory")
    source = IMPORTER.read_bytes().decode("utf-8")
    marker = "Applied Parrot neutral Nova accent colors."
    old = '      writeFileSync(novaPath, JSON.stringify(stripped, null, 2) + "\\n");'
    new = old + '''
      if (novaPath.endsWith("color.nova.tokens.json")) {
        const data = JSON.parse(readFileSync(novaPath, "utf8"));
        function setColors(path, light, dark, nativeTheme) {
          let node = data;
          for (const key of path.split(".")) {
            if (!node || typeof node !== "object" || !(key in node)) {
              throw new Error(`Nova token not found: ${path}`);
            }
            node = node[key];
          }
          if (!node.value || typeof node.value !== "object") {
            throw new Error(`Unexpected Nova token structure: ${path}`);
          }
          node.value.light = light;
          node.value.dark = dark;
          if (nativeTheme !== undefined) node.value.nativeTheme = nativeTheme;
        }
        setColors("accent.primary.@base", "#171519", "#ffffff", "#171519");
        setColors("accent.primary.hover", "#252428", "#efedf2");
        setColors("accent.primary.active", "#3f3e42", "#d6d5da");
        writeFileSync(novaPath, JSON.stringify(data, null, 2) + "\\n");
        console.log("Applied Parrot neutral Nova accent colors.");
      }'''
    if marker in source:
        print("Importer patch already present.")
        return
    if source.count(old) != 1:
        die(f"{IMPORTER}: expected one write location, found {source.count(old)}; "
            "no changes made")
    IMPORTER.write_bytes(source.replace(old, new, 1).encode("utf-8"))
    print(f"Patched Nova token importer {IMPORTER}")


def main(argv):
    if len(argv) < 2 or argv[1] not in ("--patch-importer", "--patch-dist"):
        die("use --patch-importer (importer + shipped CSS) or --patch-dist "
            "from the Firefox source directory")
    if argv[1] == "--patch-importer":
        patch_importer()
    patch_dist()


if __name__ == "__main__":
    main(sys.argv)
