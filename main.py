import streamlit as st
import plotly.graph_objects as go

st.set_page_config(page_title="저항의 연결과 소비 전력", layout="wide")
st.title("저항의 연결과 소비 전력")
st.caption("2022 개정 교육과정 물리학 · 전기 회로")


def fmt(x):
    return f"{x:,.2f}"


# ------------------------------------------------------------------
# 회로도 컴포넌트: 회로 그림 안에서 전압 · 전류 · 저항을 조절
# ------------------------------------------------------------------
CIRCUIT_CSS = r"""
.cc-root { overflow-x: auto; }
.stage { position: relative; min-width: 720px; max-width: 960px; margin: 0 auto; }
.stage svg { display: block; width: 100%; height: auto; }
.w  { stroke: var(--st-text-color, #31333f); stroke-width: 3; fill: none; stroke-linecap: round; }
.r  { stroke: #e8590c; stroke-width: 3.5; fill: none; stroke-linejoin: round; stroke-linecap: round; }
.bp { stroke: var(--st-text-color, #31333f); stroke-width: 3; }
.bn { stroke: var(--st-text-color, #31333f); stroke-width: 7; }
.a  { fill: var(--st-text-color, #31333f); }
.t  { fill: var(--st-text-color, #31333f); font-size: 15px; font-family: var(--st-font, sans-serif); }
.c  { text-anchor: middle; }
.s  { font-size: 13px; }
.p  { fill: #d6336c; font-weight: 700; }
.big { font-size: 26px; font-weight: 700; }
.ctl {
  position: absolute; box-sizing: border-box; padding: 6px 8px; border-radius: 8px;
  background: var(--st-secondary-background-color, #f0f2f6);
  color: var(--st-text-color, #31333f);
  font: 12px/1.3 var(--st-font, sans-serif);
}
.ctl .top { display: flex; justify-content: space-between; gap: 6px; white-space: nowrap; }
.ctl em { font-style: normal; font-size: 10px; opacity: .7; }
.ctl input { width: 100%; margin: 4px 0 0; accent-color: var(--st-primary-color, #ff4b4b); }
.ctl.auto input { opacity: .45; }
"""

CIRCUIT_JS = r"""
export default function (component) {
  const { data, setStateValue, parentElement } = component;
  if (!data) return;

  let root = parentElement.querySelector(".cc-root");
  if (!root) {
    root = document.createElement("div");
    root.className = "cc-root";
    parentElement.appendChild(root);
  }

  const vals = Object.assign({}, data.values);
  const C = data.controls;
  const svg = [];
  const html = [];
  const add = (s) => svg.push(s);
  const f2 = (x) => Number(x).toFixed(2);
  let W = 800, H = 450;

  const wire = (x1, y1, x2, y2) =>
    add(`<line class="w" x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}"/>`);
  const text = (x, y, s, cls = "t") =>
    add(`<text class="${cls}" x="${x}" y="${y}">${s}</text>`);

  // 저항 (지그재그) - 가로
  const zigH = (xc, y, len) => {
    const x0 = xc - len / 2, lead = len * 0.12, body = len - 2 * lead;
    let d = `M${x0},${y} L${x0 + lead},${y}`;
    for (let k = 0; k < 6; k++) d += ` L${x0 + lead + body * (k + 0.5) / 6},${y + (k % 2 ? 11 : -11)}`;
    d += ` L${x0 + len - lead},${y} L${x0 + len},${y}`;
    add(`<path class="r" d="${d}"/>`);
  };
  // 저항 (지그재그) - 세로
  const zigV = (x, yc, len) => {
    const y0 = yc - len / 2, lead = len * 0.12, body = len - 2 * lead;
    let d = `M${x},${y0} L${x},${y0 + lead}`;
    for (let k = 0; k < 6; k++) d += ` L${x + (k % 2 ? 11 : -11)},${y0 + lead + body * (k + 0.5) / 6}`;
    d += ` L${x},${y0 + len - lead} L${x},${y0 + len}`;
    add(`<path class="r" d="${d}"/>`);
  };
  // 전원 (긴 극판 +, 짧은 극판 -)
  const battery = (x, yc) => {
    add(`<line class="bp" x1="${x - 26}" y1="${yc - 12}" x2="${x + 26}" y2="${yc - 12}"/>`);
    add(`<line class="bn" x1="${x - 13}" y1="${yc + 12}" x2="${x + 13}" y2="${yc + 12}"/>`);
    text(x + 30, yc - 18, "+", "t s");
    text(x + 30, yc + 26, "−", "t s");
  };
  // 전류 방향 화살표
  const arrowH = (x, y, dir) =>
    add(`<polygon class="a" points="${x + dir * 9},${y} ${x - dir * 7},${y - 7} ${x - dir * 7},${y + 7}"/>`);
  const arrowV = (x, y, dir) =>
    add(`<polygon class="a" points="${x},${y + dir * 9} ${x - 7},${y - dir * 7} ${x + 7},${y - dir * 7}"/>`);

  // 조절 슬라이더
  const ctrl = (id, x, y, w) => {
    const c = C[id];
    if (!c) return;
    const v = vals[id];
    html.push(
      `<div class="ctl${c.auto ? " auto" : ""}" style="left:${x / W * 100}%;top:${y / H * 100}%;width:${w / W * 100}%">` +
      `<div class="top"><span>${c.label}${c.auto ? " <em>자동 계산</em>" : ""}</span>` +
      `<b data-val="${id}">${f2(v)} ${c.unit}</b></div>` +
      `<input type="range" data-id="${id}" min="${c.min}" max="${c.max}" step="${c.step}" value="${v}"${c.auto ? " disabled" : ""}/>` +
      `</div>`
    );
  };

  if (data.layout === "single") {
    W = 800; H = 450;
    const l = 90, r = 710, t = 150, b = 340, yc = 245, rx = 400, rl = 120;
    wire(l, t, rx - rl / 2, t); zigH(rx, t, rl); wire(rx + rl / 2, t, r, t);
    wire(r, t, r, b); wire(r, b, l, b);
    wire(l, b, l, yc + 12); wire(l, yc - 12, l, t); battery(l, yc);
    arrowH(560, b, -1); text(560, b - 14, "I", "t c");
    text(530, 228, "소비 전력", "t c");
    text(530, 266, `P = ${data.results.P} W`, "t c p big");
    ctrl("R", rx - 100, 52, 200);
    ctrl("V", l + 50, yc - 31, 200);
    ctrl("I", 460, b + 16, 200);
  } else if (data.layout === "series") {
    W = 900; H = 470;
    const l = 250, r = 830, t = 150, b = 340, yc = 245, rl = 80;
    const n = data.results.rows.length;
    const xs = Array.from({ length: n }, (_, k) => l + (r - l) * (k + 1) / (n + 1));
    let x = l;
    xs.forEach((xc, k) => {
      wire(x, t, xc - rl / 2, t); zigH(xc, t, rl); x = xc + rl / 2;
      const row = data.results.rows[k];
      ctrl(`R${k + 1}`, xc - 70, 56, 140);
      text(xc, t + 40, `V = ${row.V} V`, "t c s");
      text(xc, t + 60, `I = ${row.I} A`, "t c s");
      text(xc, t + 82, `P = ${row.P} W`, "t c p");
    });
    wire(x, t, r, t); wire(r, t, r, b); wire(r, b, l, b);
    wire(l, b, l, yc + 12); wire(l, yc - 12, l, t); battery(l, yc);
    arrowH(740, b, -1); text(740, b - 14, "I", "t c");
    ctrl("V", 10, yc - 31, 185);
    ctrl("I", 440, b + 16, 200);
  } else {
    W = 940; H = 540;
    const l = 250, t = 110, b = 420, yc = 265, rl = 90;
    const n = data.results.rows.length;
    const xs = n === 2 ? [460, 720] : [420, 590, 760];
    const last = xs[xs.length - 1];
    wire(l, t, last, t); wire(l, b, last, b);
    wire(l, b, l, yc + 12); wire(l, yc - 12, l, t); battery(l, yc);
    xs.forEach((x, k) => {
      wire(x, t, x, yc - rl / 2); zigV(x, yc, rl); wire(x, yc + rl / 2, x, b);
      arrowV(x, yc + 90, 1);
      const row = data.results.rows[k];
      ctrl(`R${k + 1}`, x + 14, t + 18, 140);
      text(x + 20, yc + 2, `V = ${row.V} V`, "t s");
      text(x + 20, yc + 22, `I = ${row.I} A`, "t s");
      text(x + 20, yc + 44, `P = ${row.P} W`, "t p");
    });
    const ax = (l + xs[0]) / 2;
    arrowH(ax, b, -1); text(ax, b - 14, "I", "t c");
    ctrl("V", 10, yc - 31, 185);
    ctrl("I", 250, b + 16, 200);
  }

  root.innerHTML =
    `<div class="stage"><svg viewBox="0 0 ${W} ${H}" xmlns="http://www.w3.org/2000/svg">${svg.join("")}</svg>` +
    html.join("") + `</div>`;

  root.querySelectorAll("input[type=range]").forEach((inp) => {
    const id = inp.dataset.id;
    const out = root.querySelector(`[data-val="${id}"]`);
    inp.addEventListener("input", () => {
      vals[id] = parseFloat(inp.value);
      out.textContent = `${f2(vals[id])} ${C[id].unit}`;
    });
    inp.addEventListener("change", () => {
      vals[id] = parseFloat(inp.value);
      setStateValue("setting", Object.assign({}, vals));
    });
  });
}
"""

circuit = st.components.v2.component("circuit_board", css=CIRCUIT_CSS, js=CIRCUIT_JS)


def read_setting(key, default):
    """회로 그림에서 마지막으로 조절한 값 읽기"""
    saved = None
    state = st.session_state.get(key)
    if state is not None:
        try:
            saved = state["setting"]
        except Exception:
            saved = getattr(state, "setting", None)
    result = dict(default)
    if isinstance(saved, dict):
        for k in default:
            if isinstance(saved.get(k), (int, float)):
                result[k] = float(saved[k])
    return result


def show_circuit(key, data, used, inputs):
    """회로 그림을 표시하고, 새로 조절된 값이 있으면 다시 계산"""
    res = circuit(data=data, key=key, on_setting_change=lambda: None)
    new = getattr(res, "setting", None)
    if isinstance(new, dict) and any(
        isinstance(new.get(k), (int, float)) and abs(float(new[k]) - used[k]) > 1e-9 for k in inputs
    ):
        st.rerun()


def control(label, unit, lo, hi, step, auto=False):
    return {"label": label, "unit": unit, "min": lo, "max": hi, "step": step, "auto": auto}


tab1, tab2 = st.tabs(["① 저항 하나의 소비 전력", "② 저항의 연결 (직렬 · 병렬)"])

# ------------------------------------------------------------------
# ① 저항 하나: 전압, 전류, 저항과 소비 전력
# ------------------------------------------------------------------
with tab1:
    st.subheader("전압 · 전류 · 저항에 따른 소비 전력")
    st.markdown("옴의 법칙 **V = IR** 에 의해 세 값 중 두 값을 정하면 나머지 하나가 정해집니다. "
                "직접 조절할 두 값을 고른 뒤, **회로 그림 안의 슬라이더**로 값을 바꿔 보세요.")

    mode = st.radio("직접 조절할 값", ["전압과 저항", "전류와 저항", "전압과 전류"], horizontal=True)
    auto = {"전압과 저항": "I", "전류와 저항": "V", "전압과 전류": "R"}[mode]

    s = read_setting("single_circuit", {"V": 12.0, "I": 1.0, "R": 10.0})
    if auto == "I":
        V, R = s["V"], s["R"]
        I = V / R
    elif auto == "V":
        I, R = s["I"], s["R"]
        V = I * R
    else:
        V, I = s["V"], s["I"]
        R = V / I
    P = V * I

    show_circuit(
        "single_circuit",
        {
            "layout": "single",
            "values": {"V": V, "I": I, "R": R},
            "controls": {
                "V": control("전압 V", "V", 0, 24, 0.5, auto == "V"),
                "I": control("전류 I", "A", 0.1, 5, 0.1, auto == "I"),
                "R": control("저항 R", "Ω", 1, 100, 1, auto == "R"),
            },
            "results": {"P": fmt(P)},
        },
        s,
        [k for k in ("V", "I", "R") if k != auto],
    )

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("전압 V", f"{fmt(V)} V")
    m2.metric("전류 I", f"{fmt(I)} A")
    m3.metric("저항 R", f"{fmt(R)} Ω")
    m4.metric("소비 전력 P", f"{fmt(P)} W")

    st.markdown(
        f"P = VI = {fmt(V)} × {fmt(I)} = **{fmt(P)} W**  \n"
        f"P = I²R = {fmt(I)}² × {fmt(R)} = {fmt(I * I * R)} W  \n"
        f"P = V²/R = {fmt(V)}² ÷ {fmt(R)} = {fmt(V * V / R)} W"
    )

    g1, g2 = st.columns(2)

    # 그래프 1: 저항이 일정할 때 전압에 따른 전력
    vs = [i * 0.25 for i in range(0, 121)]  # 0 ~ 30 V
    fig_v = go.Figure()
    fig_v.add_trace(go.Scatter(x=vs, y=[v * v / R for v in vs], mode="lines", name=f"R = {fmt(R)} Ω"))
    fig_v.add_trace(go.Scatter(x=[V], y=[P], mode="markers", marker=dict(size=12), name="현재 설정"))
    fig_v.update_layout(title="저항이 일정할 때: 전압과 소비 전력 (P = V²/R)",
                        xaxis_title="전압 V (V)", yaxis_title="소비 전력 P (W)", height=420)
    g1.plotly_chart(fig_v)
    g1.caption("저항이 같으면 소비 전력은 전압의 제곱에 비례합니다. 전압이 2배가 되면 전력은 4배가 됩니다.")

    # 그래프 2: 전압 일정 vs 전류 일정일 때 저항에 따른 전력
    rs = [i * 0.5 for i in range(2, 241)]  # 1 ~ 120 Ω
    fig_r = go.Figure()
    if V > 0:
        fig_r.add_trace(go.Scatter(x=rs, y=[V * V / r for r in rs], mode="lines",
                                   name=f"전압 일정 (V = {fmt(V)} V) : P = V²/R"))
    fig_r.add_trace(go.Scatter(x=rs, y=[I * I * r for r in rs], mode="lines",
                               name=f"전류 일정 (I = {fmt(I)} A) : P = I²R"))
    fig_r.add_trace(go.Scatter(x=[R], y=[P], mode="markers", marker=dict(size=12), name="현재 설정"))
    fig_r.update_layout(title="저항에 따른 소비 전력: 전압 일정 vs 전류 일정",
                        xaxis_title="저항 R (Ω)", yaxis_title="소비 전력 P (W)", height=420,
                        legend=dict(orientation="h", y=-0.25))
    g2.plotly_chart(fig_r)
    g2.caption("전압이 일정하면 저항이 클수록 전력이 작아지고(반비례), "
               "전류가 일정하면 저항이 클수록 전력이 커집니다(비례).")


# ------------------------------------------------------------------
# ② 저항의 연결
# ------------------------------------------------------------------
def solve(conn, Rs, source, value):
    """연결 방식과 전원 설정에 따라 각 저항의 V, I, P 계산"""
    if conn == "직렬":
        R_tot = sum(Rs)
    else:
        R_tot = 1 / sum(1 / r for r in Rs)

    if source == "전원 전압":
        V_tot = value
        I_tot = V_tot / R_tot
    else:
        I_tot = value
        V_tot = I_tot * R_tot

    rows = []
    for r in Rs:
        if conn == "직렬":
            i = I_tot
            v = i * r
        else:
            v = V_tot
            i = v / r
        rows.append((r, v, i, v * i))
    return R_tot, V_tot, I_tot, rows


with tab2:
    st.subheader("저항의 연결에 따른 전압 · 전류 · 소비 전력")

    s1, s2, s3 = st.columns(3)
    conn = s1.radio("연결 방식", ["직렬", "병렬"], horizontal=True)
    n = s2.radio("저항 개수", [2, 3], horizontal=True)
    source = s3.radio("전원에서 조절할 값", ["전원 전압", "전체 전류"], horizontal=True)
    st.markdown("**회로 그림 안의 슬라이더**로 전원과 각 저항의 값을 바꿔 보세요.")

    s = read_setting("conn_circuit", {"V": 12.0, "I": 1.0, "R1": 10.0, "R2": 20.0, "R3": 30.0})
    Rs = [s[f"R{k + 1}"] for k in range(n)]
    value = s["V"] if source == "전원 전압" else s["I"]

    R_tot, V_tot, I_tot, rows = solve(conn, Rs, source, value)
    P_tot = V_tot * I_tot

    controls = {
        "V": control("전원 전압 V", "V", 1, 24, 0.5, source != "전원 전압"),
        "I": control("전체 전류 I", "A", 0.1, 5, 0.1, source != "전체 전류"),
    }
    values = {"V": V_tot, "I": I_tot}
    for k, r in enumerate(Rs, start=1):
        controls[f"R{k}"] = control(f"R{k}", "Ω", 1, 100, 1)
        values[f"R{k}"] = r

    show_circuit(
        "conn_circuit",
        {
            "layout": "series" if conn == "직렬" else "parallel",
            "values": values,
            "controls": controls,
            "results": {"rows": [{"V": fmt(v), "I": fmt(i), "P": fmt(p)} for _, v, i, p in rows]},
        },
        s,
        ["V" if source == "전원 전압" else "I"] + [f"R{k + 1}" for k in range(n)],
    )

    t1, t2, t3, t4 = st.columns(4)
    t1.metric("합성 저항", f"{fmt(R_tot)} Ω")
    t2.metric("전체 전압", f"{fmt(V_tot)} V")
    t3.metric("전체 전류", f"{fmt(I_tot)} A")
    t4.metric("전체 소비 전력", f"{fmt(P_tot)} W")

    st.table({
        "저항": [f"R{k + 1}" for k in range(n)] + ["합계"],
        "저항값 (Ω)": [fmt(r) for r, _, _, _ in rows] + [fmt(R_tot)],
        "전압 (V)": [fmt(v) for _, v, _, _ in rows] + [fmt(V_tot)],
        "전류 (A)": [fmt(i) for _, _, i, _ in rows] + [fmt(I_tot)],
        "소비 전력 (W)": [fmt(p) for _, _, _, p in rows] + [fmt(P_tot)],
    })

    if conn == "직렬":
        st.info("직렬연결: R = R₁ + R₂ + … 이고 전류가 같으므로 P = I²R → "
                "**저항이 큰 저항일수록 소비 전력이 큽니다.** 전력의 비 = 저항의 비")
    else:
        st.info("병렬연결: 1/R = 1/R₁ + 1/R₂ + … 이고 전압이 같으므로 P = V²/R → "
                "**저항이 작은 저항일수록 소비 전력이 큽니다.** 전력의 비 = 저항의 역수의 비")

    g1, g2 = st.columns(2)

    # 그래프 1: 현재 회로의 저항별 소비 전력
    labels = [f"R{k + 1} ({fmt(r)} Ω)" for k, r in enumerate(Rs)]
    fig_p = go.Figure(go.Bar(x=labels, y=[p for _, _, _, p in rows],
                             text=[f"{fmt(p)} W" for _, _, _, p in rows], textposition="outside"))
    fig_p.update_layout(title=f"{conn}연결에서 저항별 소비 전력",
                        yaxis_title="소비 전력 P (W)", height=420)
    g1.plotly_chart(fig_p)

    # 그래프 2: 같은 저항, 같은 전원 조건에서 직렬 vs 병렬 비교
    _, _, _, rows_s = solve("직렬", Rs, source, value)
    Rt_p, _, _, rows_p = solve("병렬", Rs, source, value)
    Rt_s = sum(Rs)
    fig_c = go.Figure()
    fig_c.add_trace(go.Bar(name="직렬", x=labels + ["전체"],
                           y=[p for *_, p in rows_s] + [sum(p for *_, p in rows_s)]))
    fig_c.add_trace(go.Bar(name="병렬", x=labels + ["전체"],
                           y=[p for *_, p in rows_p] + [sum(p for *_, p in rows_p)]))
    unit = " V" if source == "전원 전압" else " A"
    fig_c.update_layout(barmode="group", height=420, yaxis_title="소비 전력 P (W)",
                        title=f"직렬 vs 병렬 비교 ({source} {fmt(value)}{unit} 일정)",
                        legend=dict(orientation="h", y=-0.2))
    g2.plotly_chart(fig_c)

    if source == "전원 전압":
        g2.caption(f"전원 전압이 같을 때 합성 저항은 직렬 {fmt(Rt_s)} Ω, 병렬 {fmt(Rt_p)} Ω입니다. "
                   "합성 저항이 작은 병렬연결의 전체 소비 전력이 더 큽니다 (P = V²/R).")
    else:
        g2.caption(f"전체 전류가 같을 때 합성 저항은 직렬 {fmt(Rt_s)} Ω, 병렬 {fmt(Rt_p)} Ω입니다. "
                   "합성 저항이 큰 직렬연결의 전체 소비 전력이 더 큽니다 (P = I²R).")
