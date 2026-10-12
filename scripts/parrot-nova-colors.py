import sys
from pathlib import Path

if len(sys.argv) < 2 or sys.argv[1] != "--patch-importer":
    raise SystemExit("Use --patch-importer from the Firefox source directory.")

path = Path("toolkit/themes/shared/design-system/src/figma-import.mjs")
raw = path.read_bytes()
source = raw.decode("utf-8")

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

if "Applied Parrot neutral Nova accent colors." in source:
    print("Patch already present.")
elif source.count(old) != 1:
    raise SystemExit(f"Expected one write location, found {source.count(old)}; no changes made.")
else:
    path.write_bytes(source.replace(old, new, 1).encode("utf-8"))
    print("Patched Nova token generation.")
