import streamlit as st
import plotly.graph_objects as go

st.set_page_config(page_title="저항의 연결과 소비 전력", layout="wide")

V_MAX = 24.0          # 전압 최대 (V)
R_MIN, R_MAX = 1.0, 100.0  # 저항 범위 (Ω)


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
.ctl input { width: 100%; margin: 4px 0 0; accent-color: var(--st-primary-color, #ff4b4b); }
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
      `<div class="ctl" style="left:${x / W * 100}%;top:${y / H * 100}%;width:${w / W * 100}%">` +
      `<div class="top"><span>${c.label}</span><b data-val="${id}">${f2(v)} ${c.unit}</b></div>` +
      `<input type="range" data-id="${id}" min="${c.min}" max="${c.max}" step="${c.step}" value="${v}"/>` +
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
  } else {
    W = 940; H = 540;
    const l = 250, t = 110, b = 420, yc = 265, rl = 90;
    const xs = data.results.rows.length === 2 ? [460, 720] : [420, 590, 760];
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
      out.textContent = `${f2(inp.value)} ${C[id].unit}`;
    });
    inp.addEventListener("change", () => {
      setStateValue("setting", { id: id, value: parseFloat(inp.value), seq: Date.now() });
    });
  });
}
"""

circuit = st.components.v2.component("circuit_board", css=CIRCUIT_CSS, js=CIRCUIT_JS)


def take_change(key):
    """회로 그림에서 새로 조절한 값이 있으면 (조절한 요소, 값)을 돌려줌"""
    state = st.session_state.get(key)
    if state is None:
        return None
    try:
        ev = state["setting"]
    except Exception:
        ev = getattr(state, "setting", None)
    return new_event(key, ev)


def new_event(key, ev):
    if isinstance(ev, dict) and "id" in ev and ev.get("seq") != st.session_state.get(f"{key}_seq"):
        st.session_state[f"{key}_seq"] = ev.get("seq")
        return ev["id"], float(ev["value"])
    return None


def show_circuit(key, data):
    """회로 그림을 표시하고, 아직 계산에 반영되지 않은 조절이 있으면 다시 계산"""
    res = circuit(data=data, key=key, on_setting_change=lambda: None)
    ev = getattr(res, "setting", None)
    if isinstance(ev, dict) and ev.get("seq") != st.session_state.get(f"{key}_seq"):
        st.rerun()


def control(label, unit, lo, hi, step):
    return {"label": label, "unit": unit, "min": lo, "max": hi, "step": step}


# ------------------------------------------------------------------
# 페이지 1: 저항 하나의 소비 전력
# ------------------------------------------------------------------
def page_single():
    I_MAX = 5.0
    st.title("직렬연결")
    st.caption("2022 개정 교육과정 물리학 · 전기 회로")
    st.markdown("**회로 그림 안의 슬라이더**로 전압 · 전류 · 저항을 직접 조절해 보세요.  \n"
                "옴의 법칙 **V = IR** 을 지키도록, 전압이나 전류를 바꾸면 저항은 그대로 두고, "
                "저항을 바꾸면 전압은 그대로 두고 나머지 값을 계산합니다.")

    m = st.session_state.setdefault("single_model", {"V": 12.0, "I": 1.2, "R": 10.0})
    change = take_change("single_circuit")
    if change:
        cid, v = change
        if cid == "V":
            m["V"] = v
            m["I"] = v / m["R"]
            if m["I"] > I_MAX:
                m["I"] = I_MAX
                m["R"] = m["V"] / I_MAX
        elif cid == "I":
            m["I"] = v
            m["V"] = v * m["R"]
            if m["V"] > V_MAX:
                m["V"] = V_MAX
                m["R"] = V_MAX / v
        elif cid == "R":
            m["R"] = v
            m["I"] = m["V"] / v
            if m["I"] > I_MAX:
                m["I"] = I_MAX
                m["V"] = I_MAX * v

    V, I, R = m["V"], m["I"], m["R"]
    P = V * I

    show_circuit("single_circuit", {
        "layout": "single",
        "values": {"V": V, "I": I, "R": R},
        "controls": {
            "V": control("전압 V", "V", 0, V_MAX, 0.5),
            "I": control("전류 I", "A", 0, I_MAX, 0.1),
            "R": control("저항 R", "Ω", R_MIN, R_MAX, 1),
        },
        "results": {"P": fmt(P)},
    })

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

    # 그래프: 저항이 일정할 때 전압에 따른 전력
    vs = [i * 0.25 for i in range(0, 121)]  # 0 ~ 30 V
    fig_v = go.Figure()
    fig_v.add_trace(go.Scatter(x=vs, y=[v * v / R for v in vs], mode="lines", name=f"R = {fmt(R)} Ω"))
    fig_v.add_trace(go.Scatter(x=[V], y=[P], mode="markers", marker=dict(size=12), name="현재 설정"))
    fig_v.update_layout(title="저항이 일정할 때: 전압과 소비 전력 (P = V²/R)",
                        xaxis_title="전압 V (V)", yaxis_title="소비 전력 P (W)", height=420)
    st.plotly_chart(fig_v)
    st.caption("저항이 같으면 소비 전력은 전압의 제곱에 비례합니다. 전압이 2배가 되면 전력은 4배가 됩니다.")


# ------------------------------------------------------------------
# 페이지 2: 저항의 병렬연결
# ------------------------------------------------------------------
def page_parallel():
    I_MAX = 10.0
    st.title("병렬연결")
    st.caption("2022 개정 교육과정 물리학 · 전기 회로")
    st.markdown("**회로 그림 안의 슬라이더**로 전원 전압 · 전체 전류 · 각 저항을 직접 조절해 보세요.  \n"
                "옴의 법칙 **V = IR** 을 지키도록, 전압이나 전체 전류를 바꾸면 저항은 그대로 두고, "
                "저항을 바꾸면 전압은 그대로 두고 나머지 값을 계산합니다.")

    m = st.session_state.setdefault("par_model", {"V": 12.0, "R1": 10.0, "R2": 20.0})
    names = ["R1", "R2"]

    def r_total():
        return 1 / sum(1 / m[k] for k in names)

    m.setdefault("I", m["V"] / r_total())
    change = take_change("par_circuit")
    if change:
        cid, v = change
        if cid == "I":
            m["I"] = v
            m["V"] = v * r_total()
            if m["V"] > V_MAX:
                m["V"] = V_MAX
                m["I"] = V_MAX / r_total()
        else:
            m[cid] = v
            m["I"] = m["V"] / r_total()
            if m["I"] > I_MAX:
                m["I"] = I_MAX
                m["V"] = I_MAX * r_total()

    R_tot = r_total()
    V_tot, I_tot = m["V"], m["I"]
    P_tot = V_tot * I_tot
    rows = [(m[k], V_tot, V_tot / m[k], V_tot * V_tot / m[k]) for k in names]

    controls = {
        "V": control("전원 전압 V", "V", 0, V_MAX, 0.5),
        "I": control("전체 전류 I", "A", 0, I_MAX, 0.1),
    }
    for k in names:
        controls[k] = control(k, "Ω", R_MIN, R_MAX, 1)

    show_circuit("par_circuit", {
        "layout": "parallel",
        "values": {"V": V_tot, "I": I_tot, **{k: m[k] for k in names}},
        "controls": controls,
        "results": {"rows": [{"V": fmt(v), "I": fmt(i), "P": fmt(p)} for _, v, i, p in rows]},
    })

    t1, t2, t3, t4 = st.columns(4)
    t1.metric("합성 저항", f"{fmt(R_tot)} Ω")
    t2.metric("전체 전압", f"{fmt(V_tot)} V")
    t3.metric("전체 전류", f"{fmt(I_tot)} A")
    t4.metric("전체 소비 전력", f"{fmt(P_tot)} W")

    st.table({
        "저항": names + ["합계"],
        "저항값 (Ω)": [fmt(r) for r, _, _, _ in rows] + [fmt(R_tot)],
        "전압 (V)": [fmt(v) for _, v, _, _ in rows] + [fmt(V_tot)],
        "전류 (A)": [fmt(i) for _, _, i, _ in rows] + [fmt(I_tot)],
        "소비 전력 (W)": [fmt(p) for _, _, _, p in rows] + [fmt(P_tot)],
    })

    st.info("병렬연결: 1/R = 1/R₁ + 1/R₂ 이고 모든 저항에 걸리는 전압이 같으므로 P = V²/R → "
            "**저항이 작은 저항일수록 소비 전력이 큽니다.** 전력의 비 = 저항의 역수의 비")

    # 그래프: 저항이 일정할 때 전압에 따른 전력 (각 저항과 전체)
    vs = [i * 0.25 for i in range(0, 121)]  # 0 ~ 30 V
    fig_v = go.Figure()
    for k in names:
        fig_v.add_trace(go.Scatter(x=vs, y=[v * v / m[k] for v in vs], mode="lines",
                                   name=f"{k} = {fmt(m[k])} Ω"))
    fig_v.add_trace(go.Scatter(x=vs, y=[v * v / R_tot for v in vs], mode="lines",
                               line=dict(dash="dash"), name=f"전체 (합성 저항 {fmt(R_tot)} Ω)"))
    fig_v.add_trace(go.Scatter(x=[V_tot] * (len(names) + 1),
                               y=[p for *_, p in rows] + [P_tot],
                               mode="markers", marker=dict(size=12), name="현재 설정"))
    fig_v.update_layout(title="저항이 일정할 때: 전압과 소비 전력 (P = V²/R)",
                        xaxis_title="전압 V (V)", yaxis_title="소비 전력 P (W)", height=420)
    st.plotly_chart(fig_v)
    st.caption("저항이 같으면 소비 전력은 전압의 제곱에 비례합니다. 전압이 2배가 되면 전력은 4배가 됩니다. "
               "병렬연결에서는 두 저항에 같은 전압이 걸리므로, 저항이 작은 쪽의 곡선이 더 가파릅니다.")


pg = st.navigation([
    st.Page(page_single, title="직렬연결", url_path="series", default=True),
    st.Page(page_parallel, title="병렬연결", url_path="parallel"),
])
pg.run()
