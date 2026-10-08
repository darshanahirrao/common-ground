import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import postcss from "postcss";

const sheet = postcss.parse(
  readFileSync(new URL("./style.css", import.meta.url), "utf8"),
);
const rules = [];
sheet.walkRules((rule) => {
  if (
    rule.selector === ":root" ||
    rule.selector.startsWith(":root[data-theme=")
  ) {
    const tokens = {};
    rule.walkDecls((decl) => {
      if (decl.prop.startsWith("--")) tokens[decl.prop] = decl.value;
    });
    rules.push({
      name: rule.parent.type === "atrule" ? rule.parent.params : rule.selector,
      tokens,
    });
  }
});

function luminance(hex) {
  const channels = hex
    .slice(1)
    .match(/.{2}/g)
    .map((channel) => parseInt(channel, 16) / 255)
    .map((value) =>
      value <= 0.04045 ? value / 12.92 : ((value + 0.055) / 1.055) ** 2.4,
    );
  return channels[0] * 0.2126 + channels[1] * 0.7152 + channels[2] * 0.0722;
}
function contrast(a, b) {
  const x = luminance(a),
    y = luminance(b);
  return (Math.max(x, y) + 0.05) / (Math.min(x, y) + 0.05);
}

for (const { name, tokens } of rules) {
  assert.deepEqual(
    Object.keys(tokens).sort(),
    Object.keys(rules[0].tokens).sort(),
    `${name}: missing token`,
  );
  for (const ground of ["--ground", "--panel"]) {
    for (const text of ["--ink", "--muted", "--accent", "--warning"]) {
      assert.ok(
        contrast(tokens[text], tokens[ground]) >= 4.5,
        `${name}: ${text} on ${ground}`,
      );
    }
    assert.ok(
      contrast(tokens["--line"], tokens[ground]) >= 3,
      `${name}: control boundary`,
    );
  }
  assert.ok(
    contrast(tokens["--accent-ink"], tokens["--accent"]) >= 4.5,
    `${name}: primary button`,
  );
}
console.log(
  `Contrast and complete token sets verified for ${rules.length} theme rules.`,
);
