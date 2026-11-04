import streamlit as st
import plotly.graph_objects as go

st.set_page_config(page_title="저항의 연결과 소비 전력", layout="wide")
st.title("저항의 연결과 소비 전력")
st.caption("2022 개정 교육과정 물리학 · 전기 회로")


def fmt(x):
    return f"{x:,.2f}"


tab1, tab2 = st.tabs(["① 저항 하나의 소비 전력", "② 저항의 연결 (직렬 · 병렬)"])

# ------------------------------------------------------------------
# ① 저항 하나: 전압, 전류, 저항과 소비 전력
# ------------------------------------------------------------------
with tab1:
    st.subheader("전압 · 전류 · 저항에 따른 소비 전력")
    st.markdown("옴의 법칙 **V = IR** 에 의해 세 값 중 두 값을 정하면 나머지 하나가 정해집니다. "
                "직접 설정할 두 값을 고르세요.")

    mode = st.radio("직접 설정할 값", ["전압과 저항", "전류와 저항", "전압과 전류"], horizontal=True)

    c1, c2 = st.columns(2)
    if mode == "전압과 저항":
        V = c1.slider("전압 V (V)", 0.0, 24.0, 12.0, 0.5)
        R = c2.slider("저항 R (Ω)", 1.0, 100.0, 10.0, 1.0)
        I = V / R
    elif mode == "전류와 저항":
        I = c1.slider("전류 I (A)", 0.0, 5.0, 1.0, 0.1)
        R = c2.slider("저항 R (Ω)", 1.0, 100.0, 10.0, 1.0)
        V = I * R
    else:
        V = c1.slider("전압 V (V)", 0.0, 24.0, 12.0, 0.5)
        I = c2.slider("전류 I (A)", 0.1, 5.0, 1.0, 0.1)
        R = V / I if I > 0 else 0.0

    P = V * I

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("전압 V", f"{fmt(V)} V")
    m2.metric("전류 I", f"{fmt(I)} A")
    m3.metric("저항 R", f"{fmt(R)} Ω")
    m4.metric("소비 전력 P", f"{fmt(P)} W")

    st.markdown(
        f"P = VI = {fmt(V)} × {fmt(I)} = **{fmt(P)} W**  \n"
        f"P = I²R = {fmt(I)}² × {fmt(R)} = {fmt(I * I * R)} W  \n"
        f"P = V²/R = {fmt(V)}² ÷ {fmt(R)} = {fmt(V * V / R if R else 0)} W"
    )

    g1, g2 = st.columns(2)

    # 그래프 1: 저항이 일정할 때 전압에 따른 전력
    if R > 0:
        vs = [i * 0.25 for i in range(0, 121)]  # 0 ~ 30 V
        fig_v = go.Figure()
        fig_v.add_trace(go.Scatter(x=vs, y=[v * v / R for v in vs], mode="lines",
                                   name=f"R = {fmt(R)} Ω"))
        fig_v.add_trace(go.Scatter(x=[V], y=[P], mode="markers", marker=dict(size=12),
                                   name="현재 설정"))
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
    if I > 0:
        fig_r.add_trace(go.Scatter(x=rs, y=[I * I * r for r in rs], mode="lines",
                                   name=f"전류 일정 (I = {fmt(I)} A) : P = I²R"))
    fig_r.add_trace(go.Scatter(x=[R], y=[P], mode="markers", marker=dict(size=12),
                               name="현재 설정"))
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


def draw_circuit(conn, rows, V_tot):
    fig = go.Figure()
    shapes, notes = [], []

    def line(x0, y0, x1, y1, w=3):
        shapes.append(dict(type="line", x0=x0, y0=y0, x1=x1, y1=y1,
                           line=dict(color="#444", width=w)))

    def note(x, y, text, size=13):
        notes.append(dict(x=x, y=y, text=text, showarrow=False, font=dict(size=size)))

    # 전원 (왼쪽 세로선)
    line(0, 0, 0, 1.7)
    line(0, 2.3, 0, 4)
    line(-0.6, 2.3, 0.6, 2.3)          # 긴 극판 (+)
    line(-0.3, 1.7, 0.3, 1.7, w=6)     # 짧은 극판 (−)
    note(-1.4, 2.0, f"전원<br>{fmt(V_tot)} V")

    n = len(rows)
    if conn == "직렬":
        right = 10
        line(0, 4, right, 4)
        line(right, 4, right, 0)
        line(right, 0, 0, 0)
        xs = [right * (k + 1) / (n + 1) for k in range(n)]
        for k, (x, (r, v, i, p)) in enumerate(zip(xs, rows), start=1):
            shapes.append(dict(type="rect", x0=x - 0.8, y0=3.7, x1=x + 0.8, y1=4.3,
                               fillcolor="#f4b183", line=dict(color="#444", width=2)))
            note(x, 4.75, f"R{k} = {fmt(r)} Ω")
            note(x, 3.0, f"{fmt(v)} V<br>{fmt(i)} A<br><b>{fmt(p)} W</b>", 12)
        note(right / 2, -0.5, "전류가 하나의 길로 흐름 → 모든 저항에 흐르는 전류가 같음", 12)
    else:
        xs = [3 * (k + 1) for k in range(n)]
        right = xs[-1]
        line(0, 4, right, 4)
        line(0, 0, right, 0)
        for k, (x, (r, v, i, p)) in enumerate(zip(xs, rows), start=1):
            line(x, 0, x, 4)
            shapes.append(dict(type="rect", x0=x - 0.3, y0=1.3, x1=x + 0.3, y1=2.7,
                               fillcolor="#9dc3e6", line=dict(color="#444", width=2)))
            note(x + 1.3, 2.4, f"R{k} = {fmt(r)} Ω", 12)
            note(x + 1.3, 1.5, f"{fmt(v)} V · {fmt(i)} A<br><b>{fmt(p)} W</b>", 12)
        note(right / 2, -0.5, "전류가 여러 갈래로 나뉨 → 모든 저항에 걸리는 전압이 같음", 12)

    fig.update_layout(shapes=shapes, annotations=notes, height=340,
                      margin=dict(l=10, r=10, t=10, b=10),
                      xaxis=dict(visible=False, range=[-2.5, right + 2.5]),
                      yaxis=dict(visible=False, range=[-1, 5.3]),
                      plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
    return fig


with tab2:
    st.subheader("저항의 연결에 따른 전압 · 전류 · 소비 전력")

    s1, s2, s3 = st.columns(3)
    conn = s1.radio("연결 방식", ["직렬", "병렬"], horizontal=True)
    n = s2.radio("저항 개수", [2, 3], horizontal=True)
    source = s3.radio("전원에서 설정할 값", ["전원 전압", "전체 전류"], horizontal=True)

    if source == "전원 전압":
        value = st.slider("전원 전압 V (V)", 1.0, 24.0, 12.0, 0.5)
    else:
        value = st.slider("전체 전류 I (A)", 0.1, 5.0, 1.0, 0.1)

    rc = st.columns(n)
    defaults = [10.0, 20.0, 30.0]
    Rs = [rc[k].slider(f"R{k + 1} (Ω)", 1.0, 100.0, defaults[k], 1.0) for k in range(n)]

    R_tot, V_tot, I_tot, rows = solve(conn, Rs, source, value)
    P_tot = V_tot * I_tot

    st.plotly_chart(draw_circuit(conn, rows, V_tot))

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
    fig_c.update_layout(barmode="group", height=420, yaxis_title="소비 전력 P (W)",
                        title=f"직렬 vs 병렬 비교 ({source} {fmt(value)}{' V' if source == '전원 전압' else ' A'} 일정)",
                        legend=dict(orientation="h", y=-0.2))
    g2.plotly_chart(fig_c)

    if source == "전원 전압":
        g2.caption(f"전원 전압이 같을 때 합성 저항은 직렬 {fmt(Rt_s)} Ω, 병렬 {fmt(Rt_p)} Ω입니다. "
                   "합성 저항이 작은 병렬연결의 전체 소비 전력이 더 큽니다 (P = V²/R).")
    else:
        g2.caption(f"전체 전류가 같을 때 합성 저항은 직렬 {fmt(Rt_s)} Ω, 병렬 {fmt(Rt_p)} Ω입니다. "
                   "합성 저항이 큰 직렬연결의 전체 소비 전력이 더 큽니다 (P = I²R).")
