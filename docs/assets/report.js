/* The Filing Desk: chart and table helpers for report pages.
   Charts are inline SVG drawn to the width of their container, with a
   per-year hover/tap tooltip. Colors come from CSS tokens. */
(function () {
  const FD = {};
  const tip = document.createElement("div");
  tip.className = "tip"; tip.hidden = true;
  document.addEventListener("DOMContentLoaded", () => document.body.appendChild(tip));

  FD.bn = v => (v / 1000).toLocaleString("en-US", {minimumFractionDigits: 1, maximumFractionDigits: 1});
  FD.sbn = v => (v < 0 ? "−" : "") + FD.bn(Math.abs(v));
  FD.pct = (a, b) => a / b * 100;
  FD.minus = s => String(s).replace(/^-/, "−");

  function topPath(x0, x1, yTop, yBase, r) {
    const h = yBase - yTop; r = Math.max(0, Math.min(r, h, (x1 - x0) / 2));
    return `M${x0},${yBase}V${yTop + r}Q${x0},${yTop} ${x0 + r},${yTop}H${x1 - r}Q${x1},${yTop} ${x1},${yTop + r}V${yBase}Z`;
  }
  const widthOf = host => Math.round(Math.max(340, Math.min(640, host.clientWidth || 640)));

  function frame(years, {W, H = 250, L = 44, R = 14, T = 16, B = 28, max, step, fmt}) {
    const N = years.length;
    const top = Math.ceil(max / step) * step;
    const y = v => T + (H - T - B) * (1 - v / top);
    const band = (W - L - R) / N;
    const cx = i => L + band * (i + 0.5);
    const short = band < 38;
    let s = "";
    for (let v = 0; v <= top + 1e-9; v += step) {
      s += `<line class="${v === 0 ? "base" : "grid"}" x1="${L}" x2="${W - R}" y1="${y(v)}" y2="${y(v)}"/>`;
      s += `<text x="${L - 8}" y="${y(v) + 4}" text-anchor="end">${fmt(v)}</text>`;
    }
    years.forEach((f, i) => {
      const lab = short ? "’" + String(f).slice(2) : "FY" + String(f).slice(2);
      s += `<text x="${cx(i)}" y="${H - B + 18}" text-anchor="middle">${lab}</text>`;
    });
    const bands = years.map((_, i) => `<rect class="band" data-i="${i}" x="${L + band * i + 2}" y="${T}" width="${band - 4}" height="${H - T - B}"/>`).join("");
    const hits = years.map((_, i) => `<rect class="hit" data-i="${i}" x="${L + band * i}" y="0" width="${band}" height="${H}"/>`).join("");
    return {W, H, L, R, T, B, N, y, band, cx, grid: s, bands, hits};
  }

  function wire(host, years, rowsFor) {
    const svg = host.querySelector("svg");
    const show = (e, i) => {
      svg.querySelectorAll(".band").forEach(b => b.classList.toggle("on", +b.dataset.i === i));
      svg.querySelectorAll(".xhair").forEach(x => { x.classList.add("on"); x.setAttribute("x1", x.dataset["x" + i]); x.setAttribute("x2", x.dataset["x" + i]); });
      tip.innerHTML = `<b>Fiscal ${years[i]}</b>` + rowsFor(i).map(([c, k, v]) =>
        `<div class="row"><span>${c ? `<i style="background:${c}"></i>` : ""}${k}</span><span>${v}</span></div>`).join("");
      tip.hidden = false;
      const w = tip.offsetWidth, h = tip.offsetHeight;
      let x = e.clientX + 14, yy = e.clientY - h - 10;
      if (x + w > window.innerWidth - 8) x = e.clientX - w - 14;
      if (yy < 8) yy = e.clientY + 16;
      tip.style.left = Math.max(8, x) + "px"; tip.style.top = yy + "px";
    };
    const hide = () => {
      tip.hidden = true;
      svg.querySelectorAll(".band").forEach(b => b.classList.remove("on"));
      svg.querySelectorAll(".xhair").forEach(x => x.classList.remove("on"));
    };
    svg.querySelectorAll(".hit").forEach(r => {
      r.addEventListener("pointermove", e => show(e, +r.dataset.i));
      r.addEventListener("pointerdown", e => show(e, +r.dataset.i));
      r.addEventListener("pointerleave", hide);
    });
  }

  /* single-series columns; values already in display units */
  FD.columns = (host, {years, values, step, fmt = v => v, color = "var(--s1)", labels = [], labelFmt = i => values[i], aria, rows}) => {
    const f = frame(years, {W: widthOf(host), max: Math.max(...values), step, fmt});
    let marks = "";
    values.forEach((v, i) => { const x0 = f.cx(i) - 12; marks += `<path d="${topPath(x0, x0 + 24, f.y(v), f.y(0), 4)}" fill="${color}"/>`; });
    labels.forEach(i => { marks += `<text class="lab" x="${f.cx(i)}" y="${f.y(values[i]) - 7}" text-anchor="middle">${labelFmt(i)}</text>`; });
    host.innerHTML = `<svg class="chart" viewBox="0 0 ${f.W} ${f.H}" role="img" aria-label="${aria}">${f.bands}${f.grid}${marks}${f.hits}</svg>`;
    wire(host, years, rows);
  };

  /* line series on one axis, end dot and end label per series */
  FD.lines = (host, {years, series, max, step, fmt, aria, rows}) => {
    const f = frame(years, {W: widthOf(host), max, step, fmt, R: 104});
    const li = years.length - 1;
    let marks = `<line class="xhair" y1="${f.T}" y2="${f.H - f.B}" ${years.map((_, i) => `data-x${i}="${f.cx(i)}"`).join(" ")}/>`;
    series.forEach(s => {
      const pts = s.values.map((v, i) => `${f.cx(i)},${f.y(v)}`).join(" ");
      marks += `<polyline points="${pts}" fill="none" stroke="${s.color}" stroke-width="2" stroke-linejoin="round" stroke-linecap="round"/>`;
      marks += `<circle cx="${f.cx(li)}" cy="${f.y(s.values[li])}" r="4" fill="${s.color}" stroke="var(--sheet)" stroke-width="2"/>`;
      marks += `<text class="lab" x="${f.cx(li) + 10}" y="${f.y(s.values[li]) + 4}">${s.end}</text>`;
    });
    host.innerHTML = `<svg class="chart" viewBox="0 0 ${f.W} ${f.H}" role="img" aria-label="${aria}">${f.grid}${marks}${f.hits}</svg>`;
    wire(host, years, rows);
  };

  /* two-part stacked columns: bottom + top = total */
  FD.stacked = (host, {years, bottom, top, step, fmt = v => v, endLabel, aria, rows}) => {
    const totals = bottom.values.map((b, i) => b + top.values[i]);
    const f = frame(years, {W: widthOf(host), max: Math.max(...totals), step, fmt});
    let marks = "";
    years.forEach((_, i) => {
      const x0 = f.cx(i) - 12, x1 = x0 + 24, yb = f.y(0), yM = f.y(bottom.values[i]), yT = f.y(totals[i]);
      marks += `<rect x="${x0}" y="${yM}" width="24" height="${yb - yM}" fill="${bottom.color}"/>`;
      marks += `<path d="${topPath(x0, x1, yT, yM - 2, 4)}" fill="${top.color}"/>`;
    });
    if (endLabel) { const li = years.length - 1; marks += `<text class="lab" x="${f.cx(li)}" y="${f.y(totals[li]) - 7}" text-anchor="middle">${endLabel}</text>`; }
    host.innerHTML = `<svg class="chart" viewBox="0 0 ${f.W} ${f.H}" role="img" aria-label="${aria}">${f.bands}${f.grid}${marks}${f.hits}</svg>`;
    wire(host, years, rows);
  };

  FD.table = (el, cols, rows) => {
    const n = cols.idx.length;
    const head = `<thead><tr><th scope="col">${cols.head}</th>${cols.idx.map((i, k) => `<th scope="col" class="${k === n - 1 ? "last" : ""}">${cols.label(i)}</th>`).join("")}</tr></thead>`;
    const body = rows.map(r => {
      if (r.section) return `<tr class="sec"><td colspan="${n + 1}">${r.section}</td></tr>`;
      return `<tr class="${r.strong ? "sub" : ""}"><td>${r.name}</td>${cols.idx.map((i, k) => {
        const v = r.get(i);
        const isNeg = typeof v === "number" && v < 0;
        const txt = typeof v === "number" ? r.fmt(v) : v;
        return `<td class="${isNeg ? "neg " : ""}${k === n - 1 ? "last" : ""}">${txt}</td>`;
      }).join("")}</tr>`;
    }).join("");
    el.innerHTML = head + `<tbody>${body}</tbody>`;
  };

  /* draw now and again when the width changes */
  FD.draw = fn => {
    const run = () => { tip.hidden = true; fn(); };
    run();
    let w = window.innerWidth, t;
    window.addEventListener("resize", () => {
      clearTimeout(t);
      t = setTimeout(() => { if (window.innerWidth !== w) { w = window.innerWidth; run(); } }, 150);
    });
  };

  window.FD = FD;
})();
