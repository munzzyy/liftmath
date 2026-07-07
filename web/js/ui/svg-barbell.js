// Thin SVG renderer over the pure computePlateStack() result.
//
// No logic lives here beyond geometry/layout - the plate math (which plates,
// how many, what's left over) all comes from web/js/math/plate-loading.js so
// this module stays a "dumb" view, matching the design plan's "the SVG layer
// is a thin renderer, not where the logic lives" decision. Reused by both
// the plate-loading tool and the warm-up-ramp tool.

// IPF/IWF-standard plate color scheme, keyed by nominal per-side plate weight.
// CSS custom properties do the actual color values (theme-aware); this map
// only decides which token a given denomination uses.
const PLATE_COLOR_VAR = {
  25: "--plate-25",
  20: "--plate-20",
  15: "--plate-15",
  10: "--plate-10",
  5: "--plate-5",
  2.5: "--plate-2_5",
  1.25: "--plate-1_25",
  45: "--plate-25", // lb: treat the largest common plate the same as kg's biggest for color
  35: "--plate-20",
  10.0: "--plate-10",
};

function colorVarFor(weight) {
  return PLATE_COLOR_VAR[weight] || "--plate-other";
}

// Rough visual diameter scaling (px, before viewBox scaling) so heavier
// plates render visibly larger without needing a real physical-diameter
// lookup table (a "good enough for a schematic" approximation, not a
// technical drawing).
function diameterFor(weight, unit) {
  const ref = unit === "kg" ? 25 : 45;
  const minD = 40;
  const maxD = 130;
  const frac = Math.min(1, Math.max(0.18, weight / ref));
  return minD + frac * (maxD - minD);
}

/**
 * Render an inline SVG barbell for one side of the bar, given a
 * computePlateStack()-shaped result ({ bar, unit, plates: [[weight,count],...],
 * shortfall }).
 *
 * @param {{bar:number, unit:string, plates:Array<[number,number]>, shortfall:number}} stack
 * @returns {string} SVG markup (no surrounding <svg> sizing beyond viewBox - caller controls display size via CSS).
 */
export function renderBarbellSvg(stack) {
  const { unit, plates } = stack;
  const collarW = 14;
  const sleeveW = 46;
  const barH = 14;

  // Flatten plates into individual plate draw-instructions, largest-first
  // (innermost, i.e. closest to the collar) since that's how it's actually
  // loaded and it also reads best visually (biggest plates anchor the view).
  const perSideList = [];
  for (const [weight, count] of plates) {
    for (let i = 0; i < count; i++) perSideList.push(weight);
  }

  const plateGap = 3;
  const plateWidths = perSideList.map(() => 16);
  const totalPlatesW = plateWidths.reduce((a, w) => a + w + plateGap, 0);

  const barCoreW = 220;
  const width = sleeveW * 2 + totalPlatesW * 2 + barCoreW + collarW * 2 + 20;
  const height = 180;
  const midY = height / 2;

  let x = width / 2 - barCoreW / 2 - collarW;

  const parts = [];
  parts.push(
    `<svg class="barbell-svg" viewBox="0 0 ${width} ${height}" role="img" aria-label="Barbell plate loading diagram">`
  );

  // Bar core (the visible bar between the two collars)
  parts.push(
    `<rect class="bar" x="${width / 2 - barCoreW / 2}" y="${midY - barH / 2}" width="${barCoreW}" height="${barH}" rx="3" />`
  );

  // Draw one side, then mirror for the other.
  function drawSide(sign) {
    let cursorX = width / 2 + sign * (barCoreW / 2);
    // collar
    const collarX = sign > 0 ? cursorX : cursorX - collarW;
    parts.push(
      `<rect class="bar" x="${collarX}" y="${midY - barH / 2 - 2}" width="${collarW}" height="${barH + 4}" rx="2" />`
    );
    cursorX += sign * collarW;

    for (const weight of perSideList) {
      const d = diameterFor(weight, unit);
      const w = 16;
      const plateX = sign > 0 ? cursorX : cursorX - w;
      const colorVar = colorVarFor(weight);
      const label = weight % 1 === 0 ? String(weight) : weight.toFixed(2).replace(/0$/, "");
      // No inline style="..." attribute (CSP is style-src 'self', no
      // 'unsafe-inline') - the per-plate settle-in stagger comes from
      // styles.css's :nth-child selectors on .plate (see the
      // .barbell-svg .plate rule and its :nth-child(n) delay steps), keyed
      // off DOM order alone, so this stays a plain class + data attribute.
      parts.push(
        `<g class="plate">` +
          `<rect x="${plateX}" y="${midY - d / 2}" width="${w}" height="${d}" rx="4" ` +
          `fill="var(${colorVar})" stroke="var(--color-border-strong)" stroke-width="1" />` +
          // Thin top-edge highlight stripe (cast-steel rim catch-light) -
          // purely decorative, drawn with the same fill so it stays
          // theme-correct without a new custom property.
          `<rect x="${plateX + 2}" y="${midY - d / 2 + 2}" width="${w - 4}" height="2" rx="1" ` +
          `fill="var(${colorVar})" opacity="0.55" />` +
          `<text data-plate-color="${colorVar}" x="${plateX + w / 2}" y="${midY}" dominant-baseline="middle" ` +
          `transform="rotate(90 ${plateX + w / 2} ${midY})">${label}</text>` +
          `</g>`
      );
      cursorX += sign * (w + plateGap);
    }

    // sleeve end cap
    const sleeveX = sign > 0 ? cursorX : cursorX - sleeveW;
    parts.push(
      `<rect class="bar" x="${sleeveX}" y="${midY - barH / 2 + 2}" width="${sleeveW}" height="${barH - 4}" rx="2" />`
    );
  }

  drawSide(-1);
  drawSide(1);

  parts.push(`</svg>`);
  return parts.join("");
}

/**
 * Build a small text legend (color swatch + label) for the plates present in
 * a stack, so the color coding is never the only channel conveying the
 * value (each plate also has its own inline text label - see
 * renderBarbellSvg - this legend is a secondary aid, not the sole source).
 *
 * @param {{plates:Array<[number,number]>}} stack
 * @returns {string} HTML markup for a <div class="plate-legend">.
 */
export function renderPlateLegend(stack) {
  const seen = new Map();
  for (const [weight, count] of stack.plates) {
    seen.set(weight, count);
  }
  // No inline `style="..."` attribute (CSP is style-src 'self', no
  // 'unsafe-inline') - the swatch color comes from a CSS attribute selector
  // in styles.css keyed off data-plate-color, so this stays a plain class +
  // data-attribute markup string.
  const items = [...seen.entries()]
    .sort((a, b) => b[0] - a[0])
    .map(([weight, count]) => {
      const colorVar = colorVarFor(weight);
      return (
        `<span><span class="swatch" data-plate-color="${colorVar}"></span>` +
        `${weight} &times; ${count}</span>`
      );
    });
  return `<div class="plate-legend">${items.join("")}</div>`;
}
