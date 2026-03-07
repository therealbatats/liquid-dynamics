const pptxgen = require("/sessions/eager-elegant-babbage/.npm-global/lib/node_modules/pptxgenjs");
const path = require("path");

const pres = new pptxgen();
pres.layout = "LAYOUT_16x9";
pres.author = "Ali Ahmed";
pres.title = "Liquid Dynamics";

const C = {
  bg:      "0D1117",
  mid:     "161B22",
  blue:    "58A6FF",
  orange:  "F0883E",
  green:   "7EE787",
  purple:  "D2A8FF",
  red:     "FF7B72",
  white:   "FFFFFF",
  light:   "C9D1D9",
  muted:   "8B949E",
  border:  "30363D",
};
const FH = "Trebuchet MS";
const FB = "Calibri";
const FC = "Consolas";
const TOTAL = 14;

function ds() { let s = pres.addSlide(); s.background = { color: C.bg }; return s; }
function bar(s, x, y, w, color) {
  s.addShape(pres.shapes.RECTANGLE, { x, y, w, h: 0.04, fill: { color } });
}
function footer(s, n) {
  s.addText("Ali Ahmed  ·  Liquid Dynamics", { x:0.5, y:5.2, w:6, h:0.25, fontSize:8, fontFace:FB, color:C.muted });
  s.addText(`${n} / ${TOTAL}`, { x:8.8, y:5.2, w:1, h:0.25, fontSize:8, fontFace:FB, color:C.muted, align:"right" });
}
function title(s, text, color) {
  s.addText(text, { x:0.7, y:0.25, w:8.6, h:0.7, fontSize:28, fontFace:FH, color:color||C.white, bold:true, valign:"middle" });
}
function card(s, x, y, w, h, topColor) {
  s.addShape(pres.shapes.RECTANGLE, { x, y, w, h, fill:{ color:C.mid }, shadow:{ type:"outer", blur:5, offset:2, angle:135, color:"000000", opacity:0.25 } });
  if (topColor) s.addShape(pres.shapes.RECTANGLE, { x, y, w, h:0.05, fill:{ color:topColor } });
}

// ── SLIDE 1: TITLE ────────────────────────────────────────────
{ let s = ds();
  s.addText("LIQUID DYNAMICS", { x:0.7, y:1.0, w:8.6, h:1.2, fontSize:52, fontFace:FH, bold:true, color:C.white, charSpacing:5, align:"center" });
  bar(s, 3.5, 2.2, 3, C.blue);
  s.addText("Computing with Ions at the Liquid-Electrode Interface", { x:0.7, y:2.4, w:8.6, h:0.5, fontSize:19, fontFace:FB, color:C.blue, align:"center" });
  s.addText("A unified framework where liquids compute, store energy, and self-heal.", { x:1.5, y:3.1, w:7, h:0.45, fontSize:14, fontFace:FB, color:C.light, align:"center", italic:true });
  s.addText("Ali Ahmed", { x:3.5, y:4.0, w:3, h:0.4, fontSize:18, fontFace:FB, color:C.white, bold:true, align:"center" });
  s.addText("Independent Researcher", { x:3, y:4.4, w:4, h:0.3, fontSize:12, fontFace:FB, color:C.muted, align:"center" });
  footer(s,1);
}

// ── SLIDE 2: THE QUESTION ─────────────────────────────────────
{ let s = ds(); title(s,"The Question That Started Everything", C.white); bar(s,0.7,1.05,2,C.orange);
  s.addText('"How do neurons actually compute?"', { x:0.7, y:1.3, w:8.6, h:0.7, fontSize:26, fontFace:FH, color:C.blue, italic:true, align:"center" });
  s.addText("Neurons don't use transistors. They compute with ions flowing through liquid membranes.", { x:0.7, y:2.2, w:8.6, h:0.5, fontSize:16, fontFace:FB, color:C.light, align:"center" });
  s.addText("The membrane interface is where computation happens — via concentration gradients, not circuits.", { x:0.7, y:2.8, w:8.6, h:0.5, fontSize:16, fontFace:FB, color:C.light, align:"center" });
  s.addText("What if we reverse-engineered this physics and built a computer that works like a neuron?", { x:1, y:3.6, w:8, h:0.55, fontSize:18, fontFace:FH, color:C.orange, bold:true, align:"center" });
  s.addText("That is Liquid Dynamics.", { x:1, y:4.3, w:8, h:0.4, fontSize:22, fontFace:FH, color:C.white, bold:true, align:"center" });
  footer(s,2);
}

// ── SLIDE 3: FRAMEWORK ────────────────────────────────────────
{ let s = ds(); title(s,"The Framework"); bar(s,0.7,1.05,2,C.blue);
  const pillars = [
    { t:"ENCODE", d:"Information stored in\nionic concentration\ngradients c(x,t)", c:C.blue, x:0.5 },
    { t:"PROCESS", d:"Nonlinear computation\nat the liquid-electrode\ninterface via J = -D∇c - (zFD/RT)c∇φ", c:C.orange, x:3.55 },
    { t:"READ OUT", d:"Solid-state electrodes\nextract computed\nresults at boundary", c:C.green, x:6.6 },
  ];
  pillars.forEach(p => {
    card(s, p.x, 1.2, 2.9, 2.6, p.c);
    s.addText(p.t, { x:p.x+0.15, y:1.45, w:2.6, h:0.5, fontSize:18, fontFace:FH, color:p.c, bold:true, charSpacing:2 });
    s.addText(p.d, { x:p.x+0.15, y:2.05, w:2.6, h:1.5, fontSize:12, fontFace:FB, color:C.light });
  });
  s.addText("Core equation: J = -D ∇c  −  (zFD / RT) · c · ∇φ", { x:0.7, y:4.1, w:8.6, h:0.45, fontSize:16, fontFace:FC, color:C.purple, align:"center" });
  s.addText("Nernst-Planck · Poisson · Continuity  |  T = 310.15 K  ·  c₀ = 150 mol/m³  ·  λ_D = 0.78 nm", { x:0.7, y:4.6, w:8.6, h:0.35, fontSize:10, fontFace:FB, color:C.muted, align:"center" });
  footer(s,3);
}

// ── SLIDE 4: CENTRAL THEOREM ──────────────────────────────────
{ let s = ds(); title(s,"Central Theorem: Energy ≠ Computation"); bar(s,0.7,1.05,2,C.green);
  card(s, 0.5, 1.2, 4.2, 2.2, C.blue);
  s.addText("E  ∝  V", { x:0.5, y:1.45, w:4.2, h:0.8, fontSize:42, fontFace:FC, color:C.blue, bold:true, align:"center" });
  s.addText("Energy scales with VOLUME", { x:0.5, y:2.2, w:4.2, h:0.35, fontSize:13, fontFace:FB, color:C.light, align:"center" });
  s.addText("∂E / ∂A = 0", { x:0.5, y:2.6, w:4.2, h:0.55, fontSize:18, fontFace:FC, color:C.green, align:"center" });
  card(s, 5.3, 1.2, 4.2, 2.2, C.orange);
  s.addText("P  ∝  A", { x:5.3, y:1.45, w:4.2, h:0.8, fontSize:42, fontFace:FC, color:C.orange, bold:true, align:"center" });
  s.addText("Power scales with AREA", { x:5.3, y:2.2, w:4.2, h:0.35, fontSize:13, fontFace:FB, color:C.light, align:"center" });
  s.addText("∂P / ∂V = 0", { x:5.3, y:2.6, w:4.2, h:0.55, fontSize:18, fontFace:FC, color:C.green, align:"center" });
  s.addText("Pearson correlation r = −0.030  (effectively zero)", { x:0.7, y:3.7, w:8.6, h:0.4, fontSize:18, fontFace:FB, color:C.green, bold:true, align:"center" });
  s.addText("You can scale computation and energy independently. Impossible in any solid-state architecture.", { x:0.7, y:4.2, w:8.6, h:0.5, fontSize:13, fontFace:FB, color:C.light, align:"center" });
  footer(s,4);
}

// ── SLIDE 5: XOR GATE ─────────────────────────────────────────
{ let s = ds(); title(s,"XOR Gate: Proof of Nonlinear Computation"); bar(s,0.7,1.05,2,C.orange);
  const rows = [
    [{ text:"A", options:{ bold:true, color:C.white, fill:{color:C.border} } }, { text:"B", options:{ bold:true, color:C.white, fill:{color:C.border} } }, { text:"XOR", options:{ bold:true, color:C.white, fill:{color:C.border} } }, { text:"Status", options:{ bold:true, color:C.white, fill:{color:C.border} } }],
    ["0","0","0",{ text:"✓ PASS", options:{ color:C.green, bold:true } }],
    ["1","0","1",{ text:"✓ PASS", options:{ color:C.green, bold:true } }],
    ["0","1","1",{ text:"✓ PASS", options:{ color:C.green, bold:true } }],
    ["1","1","0",{ text:"✓ PASS", options:{ color:C.green, bold:true } }],
  ];
  s.addTable(rows, { x:0.7, y:1.2, w:4.2, colW:[0.8,0.8,0.9,1.4], fontSize:14, fontFace:FB, color:C.light, border:{pt:1,color:C.border}, rowH:0.42 });
  s.addText("100%", { x:5.3, y:1.2, w:4.2, h:1.1, fontSize:72, fontFace:FH, color:C.green, bold:true, align:"center" });
  s.addText("Classification Accuracy", { x:5.3, y:2.2, w:4.2, h:0.35, fontSize:14, fontFace:FB, color:C.light, align:"center" });
  s.addText("100%", { x:5.3, y:2.7, w:4.2, h:0.9, fontSize:56, fontFace:FH, color:C.orange, bold:true, align:"center" });
  s.addText("Superposition Violation", { x:5.3, y:3.5, w:4.2, h:0.35, fontSize:14, fontFace:FB, color:C.light, align:"center" });
  s.addText("XOR is not linearly separable (Minsky & Papert, 1969) — proving XOR proves genuine nonlinear computational power.", { x:0.7, y:4.3, w:8.6, h:0.5, fontSize:12, fontFace:FB, color:C.muted, align:"center", italic:true });
  footer(s,5);
}

// ── SLIDE 6: RESERVOIR COMPUTING ─────────────────────────────
{ let s = ds(); title(s,"Reservoir Computing"); bar(s,0.7,1.05,2,C.green);
  s.addText("87%", { x:0.7, y:1.2, w:3.5, h:1.2, fontSize:80, fontFace:FH, color:C.blue, bold:true, align:"center" });
  s.addText("temporal pattern\nclassification accuracy", { x:0.7, y:2.3, w:3.5, h:0.65, fontSize:14, fontFace:FB, color:C.light, align:"center" });
  card(s, 4.6, 1.2, 5, 2.6, null);
  s.addText("Two requirements for reservoir computing:", { x:4.8, y:1.35, w:4.6, h:0.4, fontSize:13, fontFace:FB, color:C.muted });
  s.addText("✓  Nonlinear dynamics", { x:4.8, y:1.85, w:4.6, h:0.4, fontSize:15, fontFace:FB, color:C.green, bold:true });
  s.addText("     from c·∇φ coupling in Nernst-Planck", { x:4.8, y:2.2, w:4.6, h:0.35, fontSize:12, fontFace:FB, color:C.muted });
  s.addText("✓  Fading memory", { x:4.8, y:2.65, w:4.6, h:0.4, fontSize:15, fontFace:FB, color:C.green, bold:true });
  s.addText("     τ_mem = L²/D  (all eigenvalues < 0)", { x:4.8, y:3.0, w:4.6, h:0.35, fontSize:12, fontFace:FB, color:C.muted });
  s.addText("Connects to: Nishioka et al. (ion-gating RC, 2024) · Chiolerio et al. (colloidal RC, Nature 2024)", { x:0.7, y:4.15, w:8.6, h:0.4, fontSize:11, fontFace:FB, color:C.muted, align:"center", italic:true });
  footer(s,6);
}

// ── SLIDE 7: MULTI-ION ────────────────────────────────────────
{ let s = ds(); title(s,"Multi-Ion Systems: Richer Computation"); bar(s,0.7,1.05,2,C.purple);
  card(s, 0.5, 1.2, 4.3, 3.0, C.purple);
  s.addText("Accuracy vs Ion Species", { x:0.7, y:1.35, w:4, h:0.38, fontSize:15, fontFace:FH, color:C.purple, bold:true });
  const ions = [["1 ion (Na⁺)", "50%", C.muted], ["2 ions (Na⁺, K⁺)", "60%", C.blue], ["3 ions (Na⁺, K⁺, Cl⁻)", "70%", C.green]];
  ions.forEach((ion, i) => {
    s.addText(ion[0], { x:0.7, y:1.82+i*0.5, w:3, h:0.35, fontSize:13, fontFace:FB, color:C.light });
    s.addText(ion[1], { x:3.5, y:1.82+i*0.5, w:1, h:0.35, fontSize:13, fontFace:FH, color:ion[2], bold:true });
  });
  s.addShape(pres.shapes.LINE, { x:0.7, y:3.08, w:3.9, h:0, line:{ color:C.border, width:1 } });
  s.addText("Timescale per species  (τ = L²/D):", { x:0.7, y:3.15, w:4, h:0.35, fontSize:11, fontFace:FB, color:C.muted });
  s.addText("τ_Na = 1.88 µs    τ_K = 1.28 µs    τ_Cl = 1.23 µs", { x:0.7, y:3.5, w:4, h:0.35, fontSize:11, fontFace:FC, color:C.light });
  card(s, 5.2, 1.2, 4.3, 3.2, C.orange);
  s.addText("Information Capacity", { x:5.4, y:1.4, w:4, h:0.4, fontSize:15, fontFace:FH, color:C.orange, bold:true });
  s.addText("13.3 Mb/s", { x:5.2, y:1.85, w:4.3, h:0.9, fontSize:40, fontFace:FH, color:C.orange, bold:true, align:"center" });
  s.addText("peak bit rate at L = 10 nm", { x:5.2, y:2.65, w:4.3, h:0.35, fontSize:12, fontFace:FB, color:C.light, align:"center" });
  s.addText("Energy/bit → Landauer\nlimit  (kT ln 2)", { x:5.2, y:3.1, w:4.3, h:0.65, fontSize:14, fontFace:FB, color:C.green, bold:true, align:"center" });
  s.addText("Potentially the most energy-efficient computing substrate physically possible.", { x:0.7, y:4.55, w:8.6, h:0.35, fontSize:12, fontFace:FB, color:C.light, align:"center", italic:true });
  footer(s,7);
}

// ── SLIDE 8: BIOLOGICAL EQUIVALENCE ──────────────────────────
{ let s = ds(); title(s,"Same Physics as Biology"); bar(s,0.7,1.05,2,C.green);
  card(s, 0.5, 1.2, 4.3, 2.9, C.green);
  s.addText("Biological Neuron", { x:0.7, y:1.4, w:4, h:0.4, fontSize:16, fontFace:FH, color:C.green, bold:true });
  s.addText("Hodgkin-Huxley model\nNa⁺ and K⁺ ions\nMembrane interface\nIon channels as gates\n\nGoverned by: Nernst-Planck", { x:0.7, y:1.9, w:4, h:1.9, fontSize:13, fontFace:FB, color:C.light });
  card(s, 5.2, 1.2, 4.3, 2.9, C.orange);
  s.addText("Liquid Computer", { x:5.4, y:1.4, w:4, h:0.4, fontSize:16, fontFace:FH, color:C.orange, bold:true });
  s.addText("Liquid Dynamics framework\nNa⁺, K⁺, Cl⁻ ions\nElectrode interface\nConcentration gradients\n\nGoverned by: Nernst-Planck", { x:5.4, y:1.9, w:4, h:1.9, fontSize:13, fontFace:FB, color:C.light });
  s.addText("Same equation. Different parameters. Same computational power.", { x:0.7, y:4.35, w:8.6, h:0.45, fontSize:17, fontFace:FH, color:C.white, bold:true, align:"center" });
  footer(s,8);
}

// ── SLIDE 9: RADIATION SELF-HEALING ───────────────────────────
{ let s = ds(); title(s,"Self-Healing: Space Computing"); bar(s,0.7,1.05,2,C.orange);
  card(s, 0.5, 1.2, 4.2, 2.0, C.red);
  s.addText("Solid-State", { x:0.7, y:1.4, w:4, h:0.4, fontSize:16, fontFace:FH, color:C.red, bold:true });
  s.addText("Radiation → bit flip → PERMANENT\nRequires ECC hardware\nAdds power, mass, cost", { x:0.7, y:1.9, w:4, h:1.1, fontSize:13, fontFace:FB, color:C.light });
  card(s, 5.3, 1.2, 4.2, 2.0, C.green);
  s.addText("Liquid Computer", { x:5.5, y:1.4, w:4, h:0.4, fontSize:16, fontFace:FH, color:C.green, bold:true });
  s.addText("Radiation → spike → SELF-HEALS\nDiffusion restores equilibrium\nNo correction hardware needed", { x:5.5, y:1.9, w:4, h:1.1, fontSize:13, fontFace:FB, color:C.light });
  s.addText("τ_recovery  ~  l² / D", { x:0.7, y:3.5, w:8.6, h:0.5, fontSize:24, fontFace:FC, color:C.purple, align:"center" });
  s.addText([
    { text:"Measured exponent: ", options:{ color:C.light, fontSize:16 } },
    { text:"α = 1.977 ± 0.009 ", options:{ color:C.green, bold:true, fontSize:16 } },
    { text:" (theory: 2.0)   |   Recovery: ", options:{ color:C.light, fontSize:16 } },
    { text:">85%", options:{ color:C.green, bold:true, fontSize:16 } },
    { text:" at 2τ", options:{ color:C.light, fontSize:16 } },
  ], { x:0.5, y:4.1, w:9, h:0.45, align:"center" });
  footer(s,9);
}

// ── SLIDE 10: 2D EXTENSION ────────────────────────────────────
{ let s = ds(); title(s,"2D Domains: Geometry as Computation"); bar(s,0.7,1.05,2,C.purple);
  card(s, 0.5, 1.2, 4.2, 2.8, null);
  s.addText("1D domain (current):", { x:0.7, y:1.35, w:4, h:0.4, fontSize:14, fontFace:FH, color:C.muted });
  s.addText("C ~ L / λ_D  ×  log₂(n_levels)", { x:0.7, y:1.8, w:4, h:0.4, fontSize:14, fontFace:FC, color:C.blue });
  s.addText("Capacity scales as LENGTH", { x:0.7, y:2.25, w:4, h:0.35, fontSize:12, fontFace:FB, color:C.light });
  s.addText("2D domain (extended):", { x:0.7, y:2.75, w:4, h:0.4, fontSize:14, fontFace:FH, color:C.purple });
  s.addText("C ~ (L × L) / λ_D²  ×  log₂(n)", { x:0.7, y:3.2, w:4, h:0.4, fontSize:14, fontFace:FC, color:C.purple });
  s.addText("Capacity scales as AREA", { x:0.7, y:3.65, w:4, h:0.35, fontSize:12, fontFace:FB, color:C.light });
  card(s, 5.2, 1.2, 4.3, 2.8, C.purple);
  s.addText("1.74×", { x:5.2, y:1.4, w:4.3, h:1.0, fontSize:64, fontFace:FH, color:C.purple, bold:true, align:"center" });
  s.addText("more information entropy\nin 2D boundary vs 1D slice", { x:5.2, y:2.3, w:4.3, h:0.55, fontSize:14, fontFace:FB, color:C.light, align:"center" });
  s.addText("Domain geometry is a\ncomputational resource,\nnot just a constraint.", { x:5.2, y:3.0, w:4.3, h:0.9, fontSize:14, fontFace:FB, color:C.orange, bold:true, align:"center" });
  s.addText("Prediction: 3D droplet computers would be dramatically more powerful than any 1D or 2D system.", { x:0.7, y:4.5, w:8.6, h:0.4, fontSize:12, fontFace:FB, color:C.muted, align:"center", italic:true });
  footer(s,10);
}

// ── SLIDE 11: ALL 12 RESULTS ──────────────────────────────────
{ let s = ds(); title(s,"12 Simulations. 12 Confirmations."); bar(s,0.7,1.05,2,C.blue);
  const results = [
    ["01","Energy Decoupling","r = −0.030",C.green],
    ["02","Signal Processing","sep = 1246",C.green],
    ["03","Memory Timescale","α = 2.000",C.green],
    ["04","Energy Scaling","∂E/∂A = 0",C.green],
    ["05","XOR Gate","100% accuracy",C.green],
    ["06","Reservoir Computing","87% accuracy",C.green],
    ["07","Biological Equivalence","same equations",C.blue],
    ["08","Radiation Healing","α = 1.977",C.green],
    ["09","Multi-Ion","50% → 70%",C.orange],
    ["10","Info Capacity","13.3 Mb/s",C.orange],
    ["11","Optimal Readout","3-regime ✓",C.orange],
    ["12","2D Domain","1.74× entropy",C.purple],
  ];
  results.forEach((r, i) => {
    const col = i % 3; const row = Math.floor(i/3);
    const x = 0.5 + col * 3.15; const y = 1.15 + row * 0.97;
    card(s, x, y, 3.0, 0.88, null);
    s.addText(r[0], { x:x+0.1, y:y+0.06, w:0.45, h:0.35, fontSize:10, fontFace:FB, color:C.muted });
    s.addText(r[1], { x:x+0.5, y:y+0.06, w:2.4, h:0.35, fontSize:11, fontFace:FB, color:C.light });
    s.addText(r[2], { x:x+0.5, y:y+0.45, w:2.4, h:0.35, fontSize:13, fontFace:FH, color:r[3], bold:true });
  });
  footer(s,11);
}

// ── SLIDE 12: PHYSICAL DEVICE ─────────────────────────────────
{ let s = ds(); title(s,"Building the Physical Device"); bar(s,0.7,1.05,2,C.orange);
  s.addText("Precision Ionic Doping System — the first step toward a real Liquid Computer", { x:0.7, y:1.15, w:8.6, h:0.4, fontSize:14, fontFace:FB, color:C.muted });
  const specs = [
    ["Concentration range","10 – 500 mol/m³",C.blue],
    ["Precision","± 5%",C.green],
    ["Control","PID via conductivity sensor",C.light],
    ["Platform","Arduino + peristaltic pump",C.light],
    ["Electrolyte","NaCl solution",C.light],
    ["Cost","< $200 total",C.green],
  ];
  specs.forEach((sp, i) => {
    const y = 1.55 + i * 0.47;
    s.addShape(pres.shapes.RECTANGLE, { x:0.7, y, w:8.6, h:0.44, fill:{ color: i%2===0 ? C.mid : C.bg } });
    s.addText(sp[0], { x:0.9, y:y+0.05, w:3.5, h:0.35, fontSize:13, fontFace:FB, color:C.muted });
    s.addText(sp[1], { x:4.5, y:y+0.05, w:4.5, h:0.35, fontSize:13, fontFace:FB, color:sp[2], bold:true });
  });
  s.addText("No lab. No supervisor. No institution. Built from scratch.", { x:0.7, y:4.55, w:8.6, h:0.4, fontSize:16, fontFace:FH, color:C.orange, bold:true, align:"center" });
  footer(s,12);
}

// ── SLIDE 13: NARRATIVE ───────────────────────────────────────
{ let s = ds(); title(s,"The Narrative"); bar(s,0.7,1.05,2,C.blue);
  const steps = [
    { n:"1", t:"The Question", d:'"How do neurons compute?"  — a Grade 11 student asks.',c:C.blue },
    { n:"2", t:"The Theory", d:"25-page framework derived from first principles. Nernst-Planck physics.",c:C.purple },
    { n:"3", t:"The Simulations", d:"12 Python simulations validate every prediction. XOR. Reservoir. Healing.",c:C.orange },
    { n:"4", t:"The Paper", d:"Full research paper ready for arXiv submission.",c:C.green },
    { n:"5", t:"The Device", d:"Building the physical doping device. No lab. $200 budget. From scratch.",c:C.orange },
  ];
  steps.forEach((st, i) => {
    const y = 1.2 + i * 0.74;
    s.addShape(pres.shapes.RECTANGLE, { x:0.7, y, w:0.55, h:0.55, fill:{ color:st.c }, shadow:{ type:"outer", blur:4, offset:1, angle:135, color:"000000", opacity:0.2 } });
    s.addText(st.n, { x:0.7, y:y+0.05, w:0.55, h:0.45, fontSize:18, fontFace:FH, color:C.bg, bold:true, align:"center" });
    s.addText(st.t, { x:1.4, y:y+0.03, w:2.2, h:0.3, fontSize:13, fontFace:FH, color:st.c, bold:true });
    s.addText(st.d, { x:1.4, y:y+0.3, w:7.8, h:0.32, fontSize:12, fontFace:FB, color:C.light });
  });
  footer(s,13);
}

// ── SLIDE 14: CLOSING ─────────────────────────────────────────
{ let s = ds();
  s.addText("LIQUID DYNAMICS", { x:0.7, y:1.0, w:8.6, h:1.0, fontSize:50, fontFace:FH, bold:true, color:C.white, charSpacing:5, align:"center" });
  bar(s, 3.5, 2.05, 3, C.blue);
  s.addText("Silicon orchestrates.  Liquids execute.", { x:0.7, y:2.25, w:8.6, h:0.55, fontSize:22, fontFace:FB, color:C.blue, italic:true, align:"center" });
  s.addText("12 simulations  ·  1 research paper  ·  1 physical device design", { x:0.7, y:3.0, w:8.6, h:0.4, fontSize:15, fontFace:FB, color:C.light, align:"center" });
  s.addText("github.com/therealbatats/liquid-dynamics", { x:0.7, y:3.55, w:8.6, h:0.4, fontSize:14, fontFace:FB, color:C.blue, align:"center" });
  s.addText("Ali Ahmed", { x:3, y:4.1, w:4, h:0.45, fontSize:20, fontFace:FB, color:C.white, bold:true, align:"center" });
  s.addText("Independent Researcher", { x:3, y:4.55, w:4, h:0.3, fontSize:12, fontFace:FB, color:C.muted, align:"center" });
  footer(s,14);
}

const out = "/sessions/eager-elegant-babbage/mnt/extracurrculars/liquid-dynamics/presentation/liquid_dynamics_pitch.pptx";
pres.writeFile({ fileName: out }).then(() => console.log("Saved:", out)).catch(e => console.error(e));
