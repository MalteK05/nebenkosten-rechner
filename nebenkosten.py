import streamlit as st
from datetime import date, timedelta, datetime

# --- WICHTIG: Dies muss der ERSTE Streamlit-Befehl sein ---
st.set_page_config(page_title="Nebenkostenrechner 2024", layout="centered")

# --- Konfiguration ---
YEAR = 2024
DAYS_IN_YEAR = 366

# HGZ Tabelle
HGZ_MAP = {
    1: 170, 2: 150, 3: 130, 4: 80, 5: 40,
    6: 40/3, 7: 40/3, 8: 40/3,
    9: 30, 10: 80, 11: 120, 12: 160
}

# --- Hilfsfunktionen ---
def days_in_month(month, year):
    if month == 2:
        return 29 if year % 4 == 0 else 28
    elif month in [4, 6, 9, 11]:
        return 30
    else:
        return 31

def calculate_stats(start, end):
    if not start or not end or start > end:
        return 0, 0.0
    total_days = (end - start).days + 1
    total_hgz = 0.0
    current = start
    while current <= end:
        if current.year == YEAR:
            m_days = days_in_month(current.month, current.year)
            daily_hgz = HGZ_MAP[current.month] / m_days
            total_hgz += daily_hgz
        current += timedelta(days=1)
    return total_days, total_hgz

# --- State & History Management ---
def init_state():
    defaults = {
        "m1_start": date(2024, 1, 1), "m1_end": date(2024, 6, 30),
        "has_m2": False,
        "m2_start": date(2024, 7, 1), "m2_end": date(2024, 12, 31),
        "grundsteuer": None, "umlage": None,
        "heiz_in_umlage": "Nein",
        "heiz_periods": "1 Zeitraum (Nicht aufgeteilt)",
        "h1": None, "h2": None, "h3": None,
        "match_periods": "Nein",
        "calc_triggered": False,
        "history_list": [] 
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val

def save_to_history(data_dict):
    timestamp = datetime.now().strftime("%d.%m.%Y | %H:%M Uhr")
    entry = {
        "meta_timestamp": timestamp,
        "data": data_dict
    }
    # Nur im Speicher behalten (RAM)
    st.session_state.history_list.insert(0, entry)
    st.session_state.history_list = st.session_state.history_list[:20]

def restore_from_history(entry_data):
    try:
        st.session_state.m1_start = entry_data["m1_start"]
        st.session_state.m1_end = entry_data["m1_end"]
        st.session_state.has_m2 = entry_data["has_m2"]
        st.session_state.m2_start = entry_data["m2_start"] if entry_data["m2_start"] else date(2024, 7, 1)
        st.session_state.m2_end = entry_data["m2_end"] if entry_data["m2_end"] else date(2024, 12, 31)
        
        st.session_state.grundsteuer = entry_data["grundsteuer"]
        st.session_state.umlage = entry_data["umlage"]
        st.session_state.heiz_in_umlage = entry_data["heiz_in_umlage"]
        st.session_state.heiz_periods = entry_data["heiz_periods"]
        st.session_state.h1 = entry_data["h1"]
        st.session_state.h2 = entry_data["h2"]
        st.session_state.h3 = entry_data["h3"]
        st.session_state.match_periods = entry_data["match_periods"]
        
        st.session_state.calc_triggered = True
    except Exception as e:
        st.error(f"Fehler beim Laden: {e}")

# Initialisierung aufrufen (NACH set_page_config)
init_state()

# --- UI Aufbau ---
st.title("💰 Nebenkostenrechner (2024)")

# --- 1. MIETERDATEN ---
m2_active = st.session_state.has_m2
lbl_m1_s = "Startdatum erster Mieter" if m2_active else "Startdatum Mieter"
lbl_m1_e = "Enddatum erster Mieter" if m2_active else "Enddatum Mieter"

col1, col2 = st.columns(2)
with col1:
    st.date_input(lbl_m1_s, key="m1_start", min_value=date(2024, 1, 1), max_value=date(2024, 12, 31))
with col2:
    st.date_input(lbl_m1_e, key="m1_end", min_value=date(2024, 1, 1), max_value=date(2024, 12, 31))

st.checkbox("Zweiter Mieter vorhanden?", key="has_m2")

if st.session_state.has_m2:
    col3, col4 = st.columns(2)
    with col3:
        st.date_input("Startdatum zweiter Mieter", key="m2_start", min_value=date(2024, 1, 1), max_value=date(2024, 12, 31))
    with col4:
        st.date_input("Enddatum zweiter Mieter", key="m2_end", min_value=date(2024, 1, 1), max_value=date(2024, 12, 31))

st.markdown("---")

# --- 2. KOSTENBASIS ---
c_grund, c_umlage = st.columns(2)
with c_grund:
    st.number_input("Grundsteuer (€)", key="grundsteuer", min_value=0.0, step=0.01, format="%.2f", value=None, placeholder="0,00")
with c_umlage:
    st.number_input("Umlagefähige Kosten (€)", key="umlage", min_value=0.0, step=0.01, format="%.2f", value=None, placeholder="0,00")

st.markdown("#### Heizkosten")

st.radio(
    "Sind die Heizkosten in den oben eingegebenen 'Umlagefähigen Kosten' enthalten?",
    options=["Nein", "Ja"],
    horizontal=True,
    key="heiz_in_umlage",
    help="Falls Ja, werden die gesamten Heizkosten von den umlagefähigen Kosten abgezogen."
)

st.write("")

st.radio(
    "In wie viele Zeiträume ist die Heizkostenabrechnung aufgeteilt?",
    options=["1 Zeitraum (Nicht aufgeteilt)", "2 Zeiträume", "3 Zeiträume"],
    horizontal=True,
    key="heiz_periods"
)

# Dynamische Eingabefelder Heizung
if st.session_state.heiz_periods == "1 Zeitraum (Nicht aufgeteilt)":
    st.number_input("Heizkosten (€)", key="h1", min_value=0.0, step=0.01, format="%.2f", value=None, placeholder="0,00")
elif st.session_state.heiz_periods == "2 Zeiträume":
    hc1, hc2 = st.columns(2)
    with hc1: st.number_input("Heizkosten erster Zeitraum (€)", key="h1", min_value=0.0, step=0.01, format="%.2f", value=None, placeholder="0,00")
    with hc2: st.number_input("Heizkosten zweiter Zeitraum (€)", key="h2", min_value=0.0, step=0.01, format="%.2f", value=None, placeholder="0,00")
else:
    hc1, hc2, hc3 = st.columns(3)
    with hc1: st.number_input("Heizkosten erster Zeitraum (€)", key="h1", min_value=0.0, step=0.01, format="%.2f", value=None, placeholder="0,00")
    with hc2: st.number_input("Heizkosten zweiter Zeitraum (€)", key="h2", min_value=0.0, step=0.01, format="%.2f", value=None, placeholder="0,00")
    with hc3: st.number_input("Heizkosten dritter Zeitraum (€)", key="h3", min_value=0.0, step=0.01, format="%.2f", value=None, placeholder="0,00")

# Summenberechnung
val_h1 = st.session_state.h1 if st.session_state.h1 is not None else 0.0
val_h2 = st.session_state.h2 if st.session_state.h2 is not None else 0.0
val_h3 = st.session_state.h3 if st.session_state.h3 is not None else 0.0

heiz_total_sum = val_h1
if st.session_state.heiz_periods == "2 Zeiträume":
    heiz_total_sum += val_h2
if st.session_state.heiz_periods == "3 Zeiträume":
    heiz_total_sum += val_h2 + val_h3

st.write("")

st.radio(
    "Decken sich die Zeiträume der Heizkostenabrechnung mit den Zeiträumen der Mieter?",
    options=["Nein", "Ja"],
    horizontal=True,
    key="match_periods"
)

# --- BERECHNUNGS-LOGIK ---

def perform_calculation():
    save_data = {
        "m1_start": st.session_state.m1_start,
        "m1_end": st.session_state.m1_end,
        "has_m2": st.session_state.has_m2,
        "m2_start": st.session_state.m2_start,
        "m2_end": st.session_state.m2_end,
        "grundsteuer": st.session_state.grundsteuer,
        "umlage": st.session_state.umlage,
        "heiz_in_umlage": st.session_state.heiz_in_umlage,
        "heiz_periods": st.session_state.heiz_periods,
        "h1": st.session_state.h1,
        "h2": st.session_state.h2,
        "h3": st.session_state.h3,
        "match_periods": st.session_state.match_periods
    }
    save_to_history(save_data)
    st.session_state.calc_triggered = True

st.markdown("---")
st.button("Berechnung starten", type="primary", on_click=perform_calculation)

# --- ERGEBNIS ANZEIGE ---
if st.session_state.calc_triggered:
    st.markdown("### 3. Ergebnisse")
    
    gs_val = st.session_state.grundsteuer if st.session_state.grundsteuer is not None else 0.0
    um_val = st.session_state.umlage if st.session_state.umlage is not None else 0.0

    basis_umlage = um_val
    if st.session_state.heiz_in_umlage == "Ja":
        basis_umlage = um_val - heiz_total_sum
        if basis_umlage < 0:
            st.error(f"⚠️ Heizkosten ({heiz_total_sum:.2f} €) > Umlagekosten ({um_val:.2f} €)!")
            basis_umlage = 0

    d1, hgz1 = calculate_stats(st.session_state.m1_start, st.session_state.m1_end)
    gs1 = (gs_val / DAYS_IN_YEAR) * d1
    uk1 = (basis_umlage / DAYS_IN_YEAR) * d1
    
    hk1 = 0.0
    note1 = ""
    if st.session_state.match_periods == "Ja":
        hk1 = val_h1
        note1 = "(Direkt Zeitraum 1)"
    else:
        hk1 = heiz_total_sum * (hgz1 / 1000)
        note1 = f"(Anteilig HGZ: {hgz1:.2f})"

    st.info(f"👤 **{lbl_m1_s.replace('Startdatum ', '')}** ({d1} Tage)")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Grundsteuer", f"{gs1:.2f} €")
    c2.metric("Umlage", f"{uk1:.2f} €")
    c3.metric("Heizkosten", f"{hk1:.2f} €")
    c4.markdown(f"<small style='color:gray'>{note1}</small>", unsafe_allow_html=True)

    if st.session_state.has_m2:
        d2, hgz2 = calculate_stats(st.session_state.m2_start, st.session_state.m2_end)
        gs2 = (gs_val / DAYS_IN_YEAR) * d2
        uk2 = (basis_umlage / DAYS_IN_YEAR) * d2
        
        hk2 = 0.0
        note2 = ""
        if st.session_state.match_periods == "Ja":
            hk2 = val_h2
            note2 = "(Direkt Zeitraum 2)"
        else:
            hk2 = heiz_total_sum * (hgz2 / 1000)
            note2 = f"(Anteilig HGZ: {hgz2:.2f})"

        st.success(f"👤 **Zweiter Mieter** ({d2} Tage)")
        x1, x2, x3, x4 = st.columns(4)
        x1.metric("Grundsteuer", f"{gs2:.2f} €")
        x2.metric("Umlage", f"{uk2:.2f} €")
        x3.metric("Heizkosten", f"{hk2:.2f} €")
        x4.markdown(f"<small style='color:gray'>{note2}</small>", unsafe_allow_html=True)

# --- VERWALTUNG ---
st.markdown("---")
st.markdown("### Verwaltung")

col_reset, col_space = st.columns([1, 2])
with col_reset:
    if st.button("🔄 Neue Berechnung (Reset)"):
        save_hist = st.session_state.history_list
        st.session_state.clear()
        st.session_state.history_list = save_hist 
        st.rerun()

with st.expander("📂 Letzte Berechnungen anzeigen (Aktuelle Sitzung)"):
    if not st.session_state.history_list:
        st.write("Noch keine Berechnungen in dieser Sitzung.")
    else:
        st.write("Klicken Sie auf eine Berechnung, um sie wiederherzustellen:")
        for idx, entry in enumerate(st.session_state.history_list):
            ts = entry["meta_timestamp"]
            if st.button(f"Laden: {ts}", key=f"hist_{idx}"):
                restore_from_history(entry["data"])
                st.rerun()
