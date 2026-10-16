// Shared helpers for the five IKEA charts.
const SOURCE_HTML = `Source: Jeffrey Zhou, <a href="https://huggingface.co/datasets/jeffreyszhou/ikea-us-products-2025" target="_blank" rel="noopener">IKEA US Product Dataset (July 2025)</a>, Hugging Face — scraped from ikea.com/us product pages, July 2025. Product text and images © IKEA; used for non-commercial research. Chart: Hebin Rachel Shin.`;

document.querySelectorAll(".source").forEach(el => { if (!el.innerHTML.trim()) el.innerHTML = SOURCE_HTML; });

// Read a CSS custom property (so colors follow light/dark tokens).
const cssVar = name => getComputedStyle(document.documentElement).getPropertyValue(name).trim();

// Grayscale fills. Sequential steps get denser diagonal hatch so the ramp reads as a gradient.
let _hatchSeq = 0;
function addHatches(svg) {
  const uid = "h" + (++_hatchSeq);
  const defs = svg.insert("defs", ":first-child");
  const seq = [
    { bg: "#f6f6f6", ink: "#cfcfcf", gap: 10, sw: 0.75 },
    { bg: "#eaeaea", ink: "#b0b0b0", gap: 8.5, sw: 0.9 },
    { bg: "#d8d8d8", ink: "#8c8c8c", gap: 7, sw: 1 },
    { bg: "#c0c0c0", ink: "#666666", gap: 5.8, sw: 1.1 },
    { bg: "#9e9e9e", ink: "#404040", gap: 4.8, sw: 1.2 },
    { bg: "#757575", ink: "#1c1c1c", gap: 3.8, sw: 1.3 },
    { bg: "#454545", ink: "#0e0e0e", gap: 3, sw: 1.45, cross: true },
  ];
  seq.forEach((s, i) => {
    const p = defs.append("pattern").attr("id", `${uid}-seq-${i + 1}`)
      .attr("patternUnits", "userSpaceOnUse").attr("width", s.gap).attr("height", s.gap);
    p.append("rect").attr("width", s.gap).attr("height", s.gap).attr("fill", s.bg);
    diagonal(p, s.gap, s.ink, s.sw, 1);
    if (s.cross) diagonal(p, s.gap, s.ink, s.sw, -1);
  });
  [
    { n: 1, bg: "#efefef", ink: "#3a3a3a", gap: 5.5, sw: 1.15, dir: 1 },
    { n: 2, bg: "#e4e4e4", ink: "#3a3a3a", gap: 5.5, sw: 1.15, dir: -1 },
    { n: 3, bg: "#d6d6d6", ink: "#2a2a2a", gap: 5.5, sw: 1.05, dir: 1, cross: true },
  ].forEach(s => {
    const p = defs.append("pattern").attr("id", `${uid}-series-${s.n}`)
      .attr("patternUnits", "userSpaceOnUse").attr("width", s.gap).attr("height", s.gap);
    p.append("rect").attr("width", s.gap).attr("height", s.gap).attr("fill", s.bg);
    diagonal(p, s.gap, s.ink, s.sw, s.dir);
    if (s.cross) diagonal(p, s.gap, s.ink, s.sw, -1);
  });
  const neutral = defs.append("pattern").attr("id", `${uid}-neutral`)
    .attr("patternUnits", "userSpaceOnUse").attr("width", 6).attr("height", 6);
  neutral.append("rect").attr("width", 6).attr("height", 6).attr("fill", "#e8e8e8");
  neutral.append("circle").attr("cx", 3).attr("cy", 3).attr("r", 0.7).attr("fill", "#9a9a9a");
  return {
    seq: i => `url(#${uid}-seq-${i})`,
    seqAll() { return [1, 2, 3, 4, 5, 6, 7].map(i => this.seq(i)); },
    series: i => `url(#${uid}-series-${i})`,
    neutral: () => `url(#${uid}-neutral)`,
  };
}

// Seamless diagonal so neighboring tiles don't leave a gap. dir > 0 is /, dir < 0 is \.
function diagonal(pattern, g, ink, sw, dir) {
  const o = sw;
  const d = dir < 0
    ? `M${-o},${o} L${o},${-o} M0,${g} L${g},0 M${g - o},${g + o} L${g + o},${g - o}`
    : `M${-o},${g - o} L${o},${g + o} M0,0 L${g},${g} M${g - o},${-o} L${g + o},${o}`;
  pattern.append("path").attr("d", d).attr("fill", "none")
    .attr("stroke", ink).attr("stroke-width", sw).attr("stroke-linecap", "square");
}

function appendRamp(legend) {
  const n = 7, w = 16, h = 12;
  const svg = legend.append("span").attr("class", "ramp").append("svg")
    .attr("viewBox", [0, 0, n * w, h]).attr("width", n * w).attr("height", h);
  const hatch = addHatches(svg);
  svg.append("g").selectAll("rect").data(d3.range(1, n + 1)).join("rect")
    .attr("x", i => (i - 1) * w).attr("width", w).attr("height", h)
    .attr("fill", i => hatch.seq(i));
}

document.querySelectorAll(".sw[data-hatch]").forEach(el => {
  const svg = d3.select(el).append("svg").attr("viewBox", [0, 0, 12, 12]).attr("width", 12).attr("height", 12);
  const hatch = addHatches(svg);
  const n = +String(el.dataset.hatch).replace("series-", "");
  svg.append("rect").attr("width", 12).attr("height", 12).attr("fill", hatch.series(n));
});

// Pick readable text for a sequential hatch step (steps 6–7 are the dark end).
function textOn(fill) {
  const step = /seq-(\d)/.exec(String(fill));
  return step && +step[1] >= 6 ? "#ffffff" : "#0b0b0b";
}

// One tooltip element per page.
const tip = d3.select("body").append("div").attr("class", "tooltip");
function showTip(event, html) {
  tip.html(html).style("opacity", 1);
  const pad = 14, w = tip.node().offsetWidth, h = tip.node().offsetHeight;
  let x = event.clientX + pad, y = event.clientY + pad;
  if (x + w > window.innerWidth - 8) x = event.clientX - w - pad;
  if (y + h > window.innerHeight - 8) y = event.clientY - h - pad;
  tip.style("left", x + "px").style("top", y + "px");
}
function hideTip() { tip.style("opacity", 0); }

const fmtPrice = v => v == null ? "—" : "$" + d3.format(v >= 100 ? ",.0f" : ",.2f")(v);
const fmtInt = d3.format(",");

// Re-draw when the OS theme changes, so token colors baked into SVG update.
function onThemeChange(fn) {
  window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", fn);
}

// Render a simple table inside <details class="table-view">.
function tableView(el, columns, rows) {
  const t = d3.select(el).append("table");
  t.append("thead").append("tr").selectAll("th").data(columns).join("th")
    .attr("class", c => c.num ? "num" : null).text(c => c.label);
  t.append("tbody").selectAll("tr").data(rows).join("tr")
    .selectAll("td").data(r => columns.map(c => ({ c, v: c.value(r) }))).join("td")
    .attr("class", d => d.c.num ? "num" : null).text(d => d.v);
}
