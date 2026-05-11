import streamlit as st
import requests
import pandas as pd
import os
from datetime import datetime

API_URL = os.environ.get("API_URL", "http://localhost:8000")

st.set_page_config(page_title="Chlorine Dosing Agent", page_icon="💧", layout="wide")

# --- Session State ---
if "history" not in st.session_state:
    st.session_state.history = []
if "last_prediction" not in st.session_state:
    st.session_state.last_prediction = None
if "api_connected" not in st.session_state:
    st.session_state.api_connected = False

# Persist dosing form values
dosing_defaults = {
    "turbidity": 15.0, "ph": 7.2, "conductivity": 500.0, "temperature": 22.0,
    "pipe_diameter": 50.0, "residual_chlorine": 0.5, "target_residual": 2.0,
    "pipeline_length": 500.0, "flow_rate": 10.0,
    "water_volume": 100.0, "purity": 65.0, "weight": 500.0,
}
for k, v in dosing_defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# --- Sidebar ---
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/water.png", width=64)
    st.title("💧 Dosing Agent")
    st.caption("Deep well water treatment")

    st.divider()

    # API Status
    try:
        resp = requests.get(f"{API_URL}/health", timeout=3)
        if resp.status_code == 200:
            health = resp.json()
            st.session_state.api_connected = True
            st.success(f"🟢 API Connected — v{health['model_version']}")
        else:
            st.session_state.api_connected = False
            st.error("🔴 API Offline")
    except:
        st.session_state.api_connected = False
        st.error("🔴 API Offline")

    st.divider()

    # Navigation
    page = st.radio("Navigation", ["🏠 Dashboard", "🧪 Dosing", "📦 Batch", "📈 Monitoring", "🔧 Maintenance", "🎮 Simulator", "📖 Manual"])

    st.divider()
    st.caption(f"v1.0 — {datetime.now().year}")

# ===================================================================
# DASHBOARD
# ===================================================================
if page == "🏠 Dashboard":
    st.title("🏠 Dashboard")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Predictions", len(st.session_state.history))
    with c2:
        if st.session_state.history:
            avg = sum(h["confidence"] for h in st.session_state.history) / len(st.session_state.history)
            st.metric("Avg Confidence", f"{avg:.1%}")
        else:
            st.metric("Avg Confidence", "—")
    with c3:
        try:
            r = requests.get(f"{API_URL}/maintenance/", timeout=3)
            if r.status_code == 200:
                m = r.json()
                st.metric("Maint. in", f"{m['days_until_maintenance']}d",
                          delta="⚠️" if m['maintenance_needed'] else None)
        except:
            st.metric("Maint. in", "—")
    with c4:
        try:
            r = requests.get(f"{API_URL}/feedback/stats", timeout=3)
            if r.status_code == 200:
                fb = r.json()
                st.metric("Feedback Acc.", f"{fb['accuracy']:.1%}" if fb['total'] > 0 else "—")
        except:
            st.metric("Feedback Acc.", "—")

    st.divider()
    st.subheader("📋 Recent Predictions")
    if st.session_state.history:
        hist = pd.DataFrame(st.session_state.history[-10:][::-1])
        hist["Time"] = hist["timestamp"].apply(lambda x: str(x)[:19])
        st.dataframe(hist[["Time", "dosing_rate_lh", "confidence", "should_dose", "alarms_count"]],
                     use_container_width=True, hide_index=True)
        csv = pd.DataFrame(st.session_state.history).to_csv(index=False)
        st.download_button("📥 Download History CSV", csv, "history.csv", "text/csv")
    else:
        st.info("No predictions yet. Go to 🧪 Dosing.")

    # Simulator status in dashboard
    st.divider()
    st.subheader("🎮 Simulator")
    try:
        sr = requests.get(f"{API_URL}/simulator/status", timeout=3)
        if sr.status_code == 200:
            sim = sr.json()
            sc1, sc2, sc3, sc4, sc5, sc6 = st.columns(6)
            with sc1:
                st.metric("Status", "🟢 Running" if sim["running"] else "⏸️ Stopped")
            with sc2:
                st.metric("Doses Applied", sim["doses_applied"])
            with sc3:
                st.metric("Doses Skipped", sim["doses_skipped"])
            with sc4:
                st.metric("Ticks", sim["iteration"])
            with sc5:
                if sim["last_prediction"]:
                    st.metric("Dosing Rate", f"{sim['last_prediction']['dosing_rate_lh']:.4f} L/h")
                else:
                    st.metric("Dosing Rate", "—")
            with sc6:
                if sim["last_water_data"]:
                    st.metric("Residual Cl", f"{sim['last_water_data']['residual_chlorine']:.3f} mg/L",
                              delta=f"Target: {sim['last_water_data']['target_residual_chlorine']:.1f}")
                else:
                    st.metric("Residual Cl", "—")

            if sim["last_prediction"] and sim["last_water_data"]:
                last = sim["history"][-1] if sim["history"] else None
                if last:
                    action = "💉 DOSED" if last["agent_dosed"] else "⏭️ SKIPPED"
                    st.info(f"**Last decision ({action}):** {last['reasoning']}")
    except:
        pass

# ===================================================================
# DOSING
# ===================================================================
elif page == "🧪 Dosing":
    st.title("🧪 Dosing Prediction")

    # Load last form state from saved JSON
    if "form_loaded" not in st.session_state:
        st.session_state.form_loaded = False
    if not st.session_state.form_loaded:
        try:
            fr = requests.get(f"{API_URL}/simulator/form", timeout=3)
            if fr.status_code == 200:
                data = fr.json()
                if data:
                    for k, v in data.items():
                        if k in st.session_state:
                            st.session_state[k] = v
            st.session_state.form_loaded = True
        except:
            st.session_state.form_loaded = True

    with st.expander("💧 Water Quality", expanded=True):
        c1, c2 = st.columns(2)
        with c1:
            turbidity = st.number_input("Turbidity (NTU)", 0.0, 500.0, value=st.session_state.turbidity, key="turbidity")
            ph = st.slider("pH", 0.0, 14.0, value=st.session_state.ph, key="ph")
            conductivity = st.number_input("Conductivity (µS/cm)", 0.0, 5000.0, value=st.session_state.conductivity, key="conductivity")
            temperature = st.number_input("Temperature (°C)", 0.0, 50.0, value=st.session_state.temperature, key="temperature")
            pipe_diameter = st.number_input("Pipe Diameter (mm)", 10.0, 500.0, value=st.session_state.pipe_diameter, key="pipe_diameter")
        with c2:
            residual_chlorine = st.number_input("Current Residual Chlorine (mg/L)", 0.0, 5.0, value=st.session_state.residual_chlorine, key="residual_chlorine")
            target_residual = st.number_input("Target Residual at End (mg/L)", 0.1, 5.0, value=st.session_state.target_residual, key="target_residual")
            pipeline_length = st.number_input("Pipeline Length (m)", 0.0, 10000.0, value=st.session_state.pipeline_length, key="pipeline_length")
            flow_rate = st.number_input("Flow Rate (L/s)", 0.0, 200.0, value=st.session_state.flow_rate, key="flow_rate")

    with st.expander("🧴 Buffer Solution", expanded=True):
        c3, c4, c5 = st.columns(3)
        with c3:
            water_volume = st.number_input("Water Volume (L)", 1.0, 10000.0, value=st.session_state.water_volume, key="water_volume")
        with c4:
            purity = st.slider("Purity (%)", 0.0, 100.0, value=st.session_state.purity, key="purity")
        with c5:
            weight = st.number_input("Weight (g)", 0.1, 50000.0, value=st.session_state.weight, key="weight")

    col_save1, col_save2 = st.columns([3, 1])
    with col_save2:
        if st.button("💾 Save Station", use_container_width=True, help="Save as station setup for simulator"):
            form_data = {
                "turbidity": st.session_state.turbidity, "ph": st.session_state.ph,
                "conductivity": st.session_state.conductivity, "temperature": st.session_state.temperature,
                "pipe_diameter": pipe_diameter, "residual_chlorine": st.session_state.residual_chlorine,
                "target_residual": target_residual, "pipeline_length": pipeline_length,
                "flow_rate": flow_rate, "water_volume": water_volume,
                "purity": purity, "weight": weight,
            }
            requests.post(f"{API_URL}/simulator/form", json=form_data)
            requests.post(f"{API_URL}/simulator/config", json={
                "pipe_diameter_mm": pipe_diameter,
                "pipeline_length_m": pipeline_length,
                "target_residual_mgl": target_residual,
                "tank_volume_l": water_volume,
                "hypochlorite_purity_pct": purity,
                "hypochlorite_weight_g": weight
            })
            st.success("Station config saved ✓")

    if st.button("🚀 Calculate Dosing", type="primary", use_container_width=True,
                  disabled=not st.session_state.api_connected):
        # Save form state
        form_data = {
            "turbidity": st.session_state.turbidity, "ph": st.session_state.ph,
            "conductivity": st.session_state.conductivity, "temperature": st.session_state.temperature,
            "pipe_diameter": pipe_diameter, "residual_chlorine": st.session_state.residual_chlorine,
            "target_residual": target_residual, "pipeline_length": pipeline_length,
            "flow_rate": flow_rate, "water_volume": water_volume,
            "purity": purity, "weight": weight,
        }
        try:
            requests.post(f"{API_URL}/simulator/form", json=form_data, timeout=3)
        except:
            pass

        with st.spinner("Running ML prediction..."):
            try:
                resp = requests.post(f"{API_URL}/dosing/predict", json={
                    "water": {"turbidity": turbidity, "ph": ph, "conductivity": conductivity,
                              "temperature": temperature, "residual_chlorine": residual_chlorine,
                              "pipeline_length": pipeline_length, "flow_rate": flow_rate,
                              "target_residual_chlorine": target_residual, "pipe_diameter": pipe_diameter},
                    "buffer": {"water_volume": water_volume, "hypochlorite_purity": purity,
                               "hypochlorite_weight": weight}
                }, timeout=10)
                if resp.status_code == 200:
                    d = resp.json()
                    st.session_state.history.append({
                        "timestamp": d["timestamp"], "dosing_rate_lh": d["dosing_rate_lh"],
                        "confidence": d["confidence"], "should_dose": d["should_dose"],
                        "alarms_count": len(d["alarms"]), "prediction_id": d["prediction_id"]
                    })
                    st.success("✅ Prediction complete")
                    ca, cb, cc, cd = st.columns(4)
                    ca.metric("Buffer Conc.", f"{d['buffer_concentration_gpl']:.2f} g/L")
                    cb.metric("Dosing Rate", f"{d['dosing_rate_lh']:.4f} L/h")
                    cc.metric("Duration", f"{d['solution_duration_hours']:.1f} h")
                    cd.metric("Confidence", f"{d['confidence']:.1%}",
                              delta="✅ DOSE" if d['should_dose'] else "⏸️ SKIP")

                    ce, cf, cg, ch = st.columns(4)
                    ce.metric("Contact Time", f"{d['contact_time_min']:.1f} min")
                    cf.metric("Initial Cl Dose", f"{d['initial_chlorine_dose_mgl']:.2f} mg/L")
                    cg.metric("Target Residual", f"{d['target_residual_mgl']:.1f} mg/L")
                    ch.metric("Current Cl", f"{residual_chlorine:.1f} mg/L")
                    st.info(f"🧠 {d['reasoning']}")
                    if d['alarms']:
                        st.subheader("🚨 Alarms")
                        for a in d['alarms']:
                            if "CRITICAL" in a:
                                st.error(a)
                            elif any(w in a for w in ["HIGH", "LOW", "OVERDUE", "DUE"]):
                                st.warning(a)
                            else:
                                st.info(a)
                    st.subheader("📋 Rates")
                    st.dataframe(pd.DataFrame({
                        "Unit": ["L/s", "L/h", "GPM", "GPH"],
                        "Value": [d['dosing_rate_ls'], d['dosing_rate_lh'],
                                  d['dosing_rate_gpm'], d['dosing_rate_gph']]
                    }), use_container_width=True, hide_index=True)
                    st.subheader("📝 Feedback")
                    fb1, fb2 = st.columns(2)
                    with fb1:
                        if st.button("👍 Correct", use_container_width=True):
                            requests.post(f"{API_URL}/feedback/", json={
                                "prediction_id": d['prediction_id'],
                                "actual_dosing_rate": d['dosing_rate_lh'],
                                "was_correct": True, "operator_notes": "Confirmed"
                            })
                            st.success("Recorded ✓")
                    with fb2:
                        if st.button("👎 Incorrect", use_container_width=True):
                            requests.post(f"{API_URL}/feedback/", json={
                                "prediction_id": d['prediction_id'],
                                "actual_dosing_rate": d['dosing_rate_lh'],
                                "was_correct": False, "operator_notes": "Flagged"
                            })
                            st.error("Recorded — will retrain")
                else:
                    st.error(resp.text)
            except requests.ConnectionError:
                st.error("API not reachable on port 8000")

# ===================================================================
# BATCH
# ===================================================================
elif page == "📦 Batch":
    st.title("📦 Batch Prediction")
    with st.expander("🧴 Buffer Config", expanded=True):
        c3, c4, c5 = st.columns(3)
        with c3:
            b_vol = st.number_input("Water Volume (L)", 1.0, 10000.0, 100.0, key="bv")
        with c4:
            b_pur = st.slider("Purity (%)", 0.0, 100.0, 65.0, key="bp")
        with c5:
            b_wt = st.number_input("Weight (g)", 0.1, 50000.0, 500.0, key="bw")
    f = st.file_uploader("Upload CSV", type=["csv"],
                         help="Columns: turbidity, ph, conductivity, temperature, residual_chlorine, pipeline_length, flow_rate")
    if f:
        df = pd.read_csv(f)
        st.dataframe(df.head(10), use_container_width=True)
        if st.button("🔮 Run Batch", type="primary", disabled=not st.session_state.api_connected):
            with st.spinner(f"Processing {len(df)}..."):
                try:
                    resp = requests.post(f"{API_URL}/dosing/predict_batch", json={
                        "samples": df.to_dict(orient="records"),
                        "buffer_config": {"water_volume": b_vol, "hypochlorite_purity": b_pur, "hypochlorite_weight": b_wt}
                    }, timeout=30)
                    if resp.status_code == 200:
                        results = resp.json()["predictions"]
                        out = pd.DataFrame([{
                            "Dose (L/h)": r['dosing_rate_lh'], "Confidence": f"{r['confidence']:.1%}",
                            "Dose?": "✅" if r['should_dose'] else "❌",
                            "Alarms": len(r['alarms']), "Duration (h)": r['solution_duration_hours']
                        } for r in results])
                        st.dataframe(out, use_container_width=True)
                        st.success(f"✅ {len(results)} predictions")
                        st.download_button("📥 Download CSV", out.to_csv(index=False), "batch_results.csv", "text/csv")
                except Exception as e:
                    st.error(str(e))

# ===================================================================
# MONITORING
# ===================================================================
elif page == "📈 Monitoring":
    st.title("📈 Drift Monitoring")
    if st.button("🔍 Check Drift", type="primary", disabled=not st.session_state.api_connected):
        with st.spinner("Analyzing..."):
            try:
                resp = requests.get(f"{API_URL}/monitoring/drift", timeout=10)
                if resp.status_code == 200:
                    d = resp.json()
                    c1, c2, c3 = st.columns(3)
                    c1.metric("Drift", "⚠️ YES" if d['drift_detected'] else "✅ NO")
                    c2.metric("Score", f"{d['drift_score']:.1%}")
                    c3.metric("Action", d['recommended_action'].replace("_", " ").title())
                    if d['feature_drifts']:
                        st.dataframe(pd.DataFrame([
                            {"Feature": k, "Drift": "⚠️" if v['drift_detected'] else "✅", "Score": v['drift_score']}
                            for k, v in d['feature_drifts'].items()
                        ]), use_container_width=True, hide_index=True)
                    if d['drift_detected']:
                        st.warning("⚠️ Retraining recommended")
                        if st.button("🔄 Retrain Now"):
                            rr = requests.post(f"{API_URL}/model/retrain")
                            if rr.status_code == 200:
                                st.success(f"Retrained: {rr.json()['model_version']}")
                                st.rerun()
            except Exception as e:
                st.error(str(e))

# ===================================================================
# MAINTENANCE
# ===================================================================
elif page == "🔧 Maintenance":
    st.title("🔧 Tank Maintenance")
    try:
        resp = requests.get(f"{API_URL}/maintenance/", timeout=5)
        if resp.status_code == 200:
            m = resp.json()
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Tank", m['tank_id'])
            days = m['days_until_maintenance']
            c2.metric("Days Left", f"{days}d",
                      delta="⚠️ OVERDUE" if days <= 0 else ("⚠️ Soon" if days <= 3 else None),
                      delta_color="inverse")
            c3.metric("Frequency", f"{m['frequency_days']}d")
            c4.metric("Status", "⚠️ NEEDED" if m['maintenance_needed'] else "✅ OK")
            if m['maintenance_needed']:
                st.error("🚨 Maintenance overdue!")
            else:
                st.success("✅ Up to date")
            st.info(f"Last: {m['last_maintenance'][:10]}  →  Next: {m['next_maintenance'][:10]}")
            if st.button("🔄 Reset Timer", type="primary"):
                rr = requests.post(f"{API_URL}/maintenance/reset")
                if rr.status_code == 200:
                    st.success("Reset ✓")
                    st.rerun()
    except:
        st.error("API not reachable")

# ===================================================================
# SIMULATOR
# ===================================================================
elif page == "🎮 Simulator":
    st.title("🎮 Dosing Simulator")
    st.caption("Real-time water quality simulation with trending data")

    # Station config
    try:
        cr = requests.get(f"{API_URL}/simulator/config", timeout=3)
        if cr.status_code == 200:
            cfg = cr.json()
            with st.expander("⚙️ Station Setup", expanded=False):
                sc1, sc2, sc3, sc4, sc5, sc6 = st.columns(6)
                sc1.metric("Pipe Ø", f"{cfg['pipe_diameter_mm']:.0f} mm")
                sc2.metric("Pipeline", f"{cfg['pipeline_length_m']:.0f} m")
                sc3.metric("Target Cl", f"{cfg['target_residual_mgl']:.1f} mg/L")
                sc4.metric("Tank", f"{cfg['tank_volume_l']:.0f} L")
                sc5.metric("Purity", f"{cfg['hypochlorite_purity_pct']:.0f}%")
                sc6.metric("Hypochlorite", f"{cfg['hypochlorite_weight_g']:.0f} g")
    except:
        pass

    col_ctrl1, col_ctrl2, col_ctrl3 = st.columns([1, 1, 2])
    with col_ctrl1:
        if st.button("▶️ Start", type="primary", use_container_width=True, disabled=not st.session_state.api_connected):
            requests.post(f"{API_URL}/simulator/start")
            st.rerun()
    with col_ctrl2:
        if st.button("⏹️ Stop", use_container_width=True):
            requests.post(f"{API_URL}/simulator/stop")
            st.rerun()

    # Poll status
    try:
        resp = requests.get(f"{API_URL}/simulator/status", timeout=5)
        if resp.status_code == 200:
            s = resp.json()

            with col_ctrl3:
                if s["running"]:
                    st.success(f"🟢 Running — {s['iteration']} ticks | Started: {s['started_at'][:19] if s['started_at'] else '?'}")
                else:
                    st.info("⏸️ Stopped")

            if s["running"] or s["history"]:
                st.divider()

                # Metrics row
                m1, m2, m3, m4, m5, m6 = st.columns(6)
                with m1:
                    st.metric("💉 Dosed", s["doses_applied"])
                with m2:
                    st.metric("⏭️ Skipped", s["doses_skipped"])
                with m3:
                    st.metric("🔄 API Calls", s["prediction_count"])
                with m4:
                    eff = s["skip_count"] / max(1, s["iteration"]) * 100
                    st.metric("📊 Efficiency", f"{eff:.0f}%")
                with m5:
                    if s["last_prediction"]:
                        st.metric("Last Dose", f"{s['last_prediction']['dosing_rate_lh']:.4f} L/h")
                    else:
                        st.metric("Last Dose", "—")
                with m6:
                    if s["last_prediction"]:
                        st.metric("Confidence", f"{s['last_prediction']['confidence']:.1%}")
                    else:
                        st.metric("Confidence", "—")

                # Current water data
                if s["last_water_data"]:
                    st.subheader("💧 Latest Water Quality")
                    w = s["last_water_data"]
                    w1, w2, w3, w4, w5 = st.columns(5)
                    w1.metric("Turbidity", f"{w['turbidity']:.1f} NTU")
                    w2.metric("pH", f"{w['ph']:.2f}")
                    w3.metric("Conductivity", f"{w['conductivity']:.0f} µS/cm")
                    w4.metric("Temperature", f"{w['temperature']:.1f} °C")
                    w5.metric("Residual Cl", f"{w['residual_chlorine']:.3f} mg/L")

                # Dosing rate chart
                if s["history"]:
                    st.subheader("📈 Dosing Rate Trend")
                    hist_df = pd.DataFrame(s["history"])
                    hist_df["time"] = pd.to_datetime(hist_df["timestamp"])
                    hist_df = hist_df.set_index("time")

                    chart_data = hist_df[["dosing_rate_lh", "turbidity"]].copy()
                    chart_data["turbidity_scaled"] = chart_data["turbidity"] * chart_data["dosing_rate_lh"].max() / max(1, chart_data["turbidity"].max())
                    st.line_chart(chart_data[["dosing_rate_lh"]], use_container_width=True)

                    # History table
                    st.subheader("📋 History")
                    display = hist_df.tail(20)[::-1][["iteration", "turbidity", "ph", "residual_chlorine", "dosing_rate_lh", "should_dose", "agent_dosed", "confidence", "reasoning"]]
                    display["confidence"] = display["confidence"].apply(lambda x: f"{x:.1%}")
                    display["should_dose"] = display["should_dose"].apply(lambda x: "✅" if x else "❌")
                    display["agent_dosed"] = display["agent_dosed"].apply(lambda x: "💉" if x else "⏭️")
                    display["reasoning"] = display["reasoning"].apply(lambda x: x[:80] + "..." if len(x) > 80 else x)
                    st.dataframe(display.rename(columns={
                        "iteration": "#", "turbidity": "Turb", "ph": "pH",
                        "residual_chlorine": "Cl_res", "dosing_rate_lh": "Dose L/h",
                        "should_dose": "Need?", "agent_dosed": "Action",
                        "confidence": "Conf", "reasoning": "Why?"
                    }), use_container_width=True)

            # Auto-refresh if running
            if s["running"]:
                time.sleep(2)
                st.rerun()
    except:
        st.error("API not reachable")

# ===================================================================
# MANUAL
# ===================================================================
elif page == "📖 Manual":
    st.title("📖 User Manual — Chlorine Dosing Agent")
    st.caption("ML-powered calcium hypochlorite dosing for deep well water treatment")

    st.markdown("""
    ---
    ## 🎯 What This System Does

    This agent **automatically calculates and decides** how much calcium hypochlorite solution
    to inject into a deep well water pipeline to maintain a target residual chlorine level
    at the end of the line (typically **2.0 mg/L**).

    It combines **machine learning** with **chlorine decay kinetics** to make intelligent
    dosing decisions in real time.

    ---
    ## 🧠 How It Works

    ### 1. Water Quality Analysis
    The agent reads 7 water quality parameters from the well:
    - **Turbidity** (NTU) — higher values demand more chlorine
    - **pH** — chlorine is less effective at high pH
    - **Conductivity** (µS/cm) — indicates dissolved solids
    - **Temperature** (°C) — affects chlorine decay rate
    - **Current residual chlorine** (mg/L) — what's already in the water
    - **Pipeline length** (m) — distance to the storage tank
    - **Flow rate** (L/s) — how fast water moves

    ### 2. ML Prediction
    A **Ridge Regression model** trained on historical data predicts the required
    chlorine dose (mg/L) based on these parameters. The model learns from operator
    feedback and retrains automatically.

    ### 3. Chlorine Decay Model
    Chlorine decays over time as water travels through the pipeline. The agent
    calculates:
    - **Contact time** = pipeline length ÷ flow velocity
    - **Decay factor** = e^(k × contact_time) where k depends on temperature
    - **Initial dose needed** = target_residual × decay_factor

    The final dose = **max(ML prediction, decay requirement)**.

    ### 4. Autonomous Decision
    The agent decides **whether to dose or not**:
    - ✅ **DOSE** if residual chlorine is below target and dose > 0.1 mg/L
    - ⏭️ **SKIP** if residual chlorine is already sufficient

    ### 5. Dosing Rate Calculation
    Converts the required dose (mg/L) into a pump flow rate (L/h) based on:
    - Buffer tank concentration (g/L)
    - Raw water flow rate (L/s)

    ---
    ## 📋 Pages Guide

    ### 🏠 Dashboard
    System overview with key metrics, recent predictions, and simulator status.
    Download prediction history as CSV.

    ### 🧪 Dosing
    **Main prediction page.** Enter water quality parameters and buffer configuration.
    - Click **Calculate Dosing** to get a prediction
    - Click **Save Station** to persist configuration for the simulator
    - Provide **feedback** (👍/👎) to help the model learn

    ### 📦 Batch
    Upload a CSV file with multiple water samples for bulk predictions.
    Download results as CSV.

    ### 📈 Monitoring
    Run **data drift detection** using Evidently AI. If significant drift is
    detected, retrain the model with one click.

    ### 🔧 Maintenance
    Track calcium hypochlorite tank maintenance schedule. Reset the timer
    after each service (default: 30 days).

    ### 🎮 Simulator
    Real-time simulation that generates trending water quality data every 60 seconds.
    The agent makes autonomous dosing decisions and explains why.
    - **Start/Stop** the simulation
    - View **dosing rate trends** and **decision history**
    - Uses the station configuration saved from the Dosing page

    ---
    ## ⚙️ Station Configuration

    The following parameters define your treatment station and are saved to
    `data/station_setup.json`:

    | Parameter | Description | Default |
    |---|---|---|
    | Pipe diameter | Internal pipe diameter (mm) | 50 |
    | Pipeline length | Distance to tank (m) | 800 |
    | Target residual Cl | Desired Cl at endpoint (mg/L) | 2.0 |
    | Tank volume | Buffer solution tank (L) | 100 |
    | Hypochlorite purity | Product purity (%) | 65 |
    | Hypochlorite weight | Grams per batch (g) | 500 |

    ---
    ## 🚨 Alarms

    The agent generates alarms for abnormal conditions:

    | Alarm | Trigger |
    |---|---|
    | 🔴 CRITICAL_TURBIDITY | > 100 NTU |
    | 🟡 HIGH_TURBIDITY | > 50 NTU |
    | 🟡 LOW_PH / HIGH_PH | < 6.5 / > 8.5 |
    | 🟡 HIGH_CONDUCTIVITY | > 1500 µS/cm |
    | 🟡 HIGH_TEMPERATURE | > 30°C |
    | 🟡 LOW_RESIDUAL_CHLORINE | < 0.2 mg/L |
    | 🟡 LOW_SOLUTION | Buffer lasts < 24h |
    | 🔴 MAINTENANCE_OVERDUE | Tank service past due |

    ---
    ## 🔄 Model Retraining

    The model retrains automatically when:
    - Operator feedback indicates incorrect predictions
    - Data drift is detected (> 30% drift score)
    - Manual retrain is triggered from the Monitoring page

    ---
    ## 🏗️ Architecture

    ```
    Streamlit Frontend (:8501)
           │
    FastAPI Backend (:8000)
           │
    ├── Dosing Service (ML + decay kinetics)
    ├── Buffer Calculator
    ├── Drift Monitor (Evidently AI)
    ├── Feedback Loop
    ├── Maintenance Scheduler
    └── Simulator (data generator + autonomous agent)
    ```

    ---
    ## 🚀 Quick Start

    ```bash
    # Terminal 1: Backend
    uvicorn src.app:app --host 0.0.0.0 --port 8000 --reload

    # Terminal 2: Frontend
    streamlit run frontend/app.py
    ```

    Open **http://localhost:8501** in your browser.
    API docs at **http://localhost:8000/docs**.
    """)
