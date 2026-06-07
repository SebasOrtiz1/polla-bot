# ============================================================
#  POLLA MUNDIAL 2026 — Bot de WhatsApp
#  Conecta Twilio + Claude API + Railway
# ============================================================

import os
import json
from datetime import datetime, date
from flask import Flask, request, Response
from twilio.twiml.messaging_response import MessagingResponse
from anthropic import Anthropic

app = Flask(__name__)

# ── CLIENTES ────────────────────────────────────────────────
# Las keys se ponen como variables de entorno en Railway (no en el código)
anthropic_client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

# ── DATOS PERSISTENTES (en archivo JSON simple) ──────────────
DATA_FILE = "polla_data.json"

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "resultados_reales": {},   # {"A1": "3-0", "A2": "1-1", ...}
        "puntos": {"u1": 0, "u2": 0},
        "exactos": {"u1": 0, "u2": 0},
        "resultados_ok": {"u1": 0, "u2": 0},
        "historial": []            # últimas actualizaciones
    }

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ── PRONOSTICOS COMPLETOS ────────────────────────────────────
PRONOSTICOS = {
    # Grupo A
    "A1": {"t1":"México","t2":"Sudáfrica","u1":"3-0","u2":"2-1"},
    "A2": {"t1":"Corea del Sur","t2":"Chequia","u1":"2-1","u2":"1-1"},
    "A3": {"t1":"México","t2":"Corea del Sur","u1":"2-1","u2":"1-1"},
    "A4": {"t1":"Chequia","t2":"Sudáfrica","u1":"2-0","u2":"1-1"},
    "A5": {"t1":"Chequia","t2":"México","u1":"0-2","u2":"1-2"},
    "A6": {"t1":"Sudáfrica","t2":"Corea","u1":"0-2","u2":"1-1"},
    # Grupo B
    "B1": {"t1":"Canadá","t2":"Bosnia-Herz.","u1":"2-0","u2":"2-1"},
    "B2": {"t1":"Qatar","t2":"Suiza","u1":"0-2","u2":"0-3"},
    "B3": {"t1":"Canadá","t2":"Qatar","u1":"3-0","u2":"2-0"},
    "B4": {"t1":"Suiza","t2":"Bosnia","u1":"2-1","u2":"1-1"},
    "B5": {"t1":"Suiza","t2":"Canadá","u1":"1-2","u2":"1-1"},
    "B6": {"t1":"Bosnia","t2":"Qatar","u1":"2-0","u2":"1-1"},
    # Grupo C
    "C1": {"t1":"Brasil","t2":"Marruecos","u1":"2-0","u2":"2-1"},
    "C2": {"t1":"Haití","t2":"Escocia","u1":"0-3","u2":"0-2"},
    "C3": {"t1":"Brasil","t2":"Haití","u1":"5-0","u2":"4-0"},
    "C4": {"t1":"Marruecos","t2":"Escocia","u1":"2-1","u2":"1-0"},
    "C5": {"t1":"Marruecos","t2":"Haití","u1":"3-0","u2":"2-0"},
    "C6": {"t1":"Escocia","t2":"Brasil","u1":"0-3","u2":"1-3"},
    # Grupo D
    "D1": {"t1":"EEUU","t2":"Paraguay","u1":"2-0","u2":"1-0"},
    "D2": {"t1":"Australia","t2":"Turquía","u1":"1-2","u2":"1-2"},
    "D3": {"t1":"EEUU","t2":"Australia","u1":"2-1","u2":"2-0"},
    "D4": {"t1":"Turquía","t2":"Paraguay","u1":"2-0","u2":"2-1"},
    "D5": {"t1":"Turquía","t2":"EEUU","u1":"1-2","u2":"1-1"},
    "D6": {"t1":"Paraguay","t2":"Australia","u1":"1-2","u2":"0-2"},
    # Grupo E
    "E1": {"t1":"Alemania","t2":"Curazao","u1":"5-0","u2":"4-0"},
    "E2": {"t1":"C. de Marfil","t2":"Ecuador","u1":"1-2","u2":"1-1"},
    "E3": {"t1":"Alemania","t2":"C. de Marfil","u1":"3-0","u2":"2-1"},
    "E4": {"t1":"Ecuador","t2":"Curazao","u1":"3-0","u2":"2-0"},
    "E5": {"t1":"Alemania","t2":"Ecuador","u1":"2-1","u2":"1-0"},
    "E6": {"t1":"Curazao","t2":"C. de Marfil","u1":"0-2","u2":"0-1"},
    # Grupo F
    "F1": {"t1":"P. Bajos","t2":"Japón","u1":"2-1","u2":"1-1"},
    "F2": {"t1":"Suecia","t2":"Túnez","u1":"2-0","u2":"1-0"},
    "F3": {"t1":"P. Bajos","t2":"Suecia","u1":"2-0","u2":"2-1"},
    "F4": {"t1":"Japón","t2":"Túnez","u1":"2-0","u2":"2-0"},
    "F5": {"t1":"P. Bajos","t2":"Túnez","u1":"3-0","u2":"3-0"},
    "F6": {"t1":"Japón","t2":"Suecia","u1":"2-1","u2":"1-1"},
    # Grupo G
    "G1": {"t1":"Bélgica","t2":"Egipto","u1":"3-0","u2":"2-0"},
    "G2": {"t1":"Irán","t2":"N. Zelanda","u1":"2-0","u2":"2-0"},
    "G3": {"t1":"Bélgica","t2":"Irán","u1":"2-0","u2":"3-1"},
    "G4": {"t1":"Egipto","t2":"N. Zelanda","u1":"2-0","u2":"2-1"},
    "G5": {"t1":"Bélgica","t2":"N. Zelanda","u1":"4-0","u2":"3-0"},
    "G6": {"t1":"Egipto","t2":"Irán","u1":"1-1","u2":"0-1"},
    # Grupo H
    "H1": {"t1":"España","t2":"Cabo Verde","u1":"4-0","u2":"3-0"},
    "H2": {"t1":"Arabia S.","t2":"Uruguay","u1":"0-2","u2":"0-2"},
    "H3": {"t1":"España","t2":"Arabia S.","u1":"3-0","u2":"2-0"},
    "H4": {"t1":"Uruguay","t2":"Cabo Verde","u1":"3-0","u2":"2-0"},
    "H5": {"t1":"España","t2":"Uruguay","u1":"2-1","u2":"1-1"},
    "H6": {"t1":"Cabo Verde","t2":"Arabia S.","u1":"1-1","u2":"0-1"},
    # Grupo I
    "I1": {"t1":"Francia","t2":"Senegal","u1":"2-0","u2":"2-1"},
    "I2": {"t1":"Irak","t2":"Noruega","u1":"0-3","u2":"0-2"},
    "I3": {"t1":"Francia","t2":"Irak","u1":"4-0","u2":"3-0"},
    "I4": {"t1":"Senegal","t2":"Noruega","u1":"1-2","u2":"1-1"},
    "I5": {"t1":"Francia","t2":"Noruega","u1":"2-1","u2":"2-1"},
    "I6": {"t1":"Irak","t2":"Senegal","u1":"0-2","u2":"0-2"},
    # Grupo J
    "J1": {"t1":"Argentina","t2":"Argelia","u1":"3-0","u2":"2-0"},
    "J2": {"t1":"Austria","t2":"Jordania","u1":"3-0","u2":"2-0"},
    "J3": {"t1":"Argentina","t2":"Austria","u1":"2-0","u2":"1-0"},
    "J4": {"t1":"Argelia","t2":"Jordania","u1":"2-0","u2":"1-0"},
    "J5": {"t1":"Argentina","t2":"Jordania","u1":"4-0","u2":"3-0"},
    "J6": {"t1":"Austria","t2":"Argelia","u1":"1-1","u2":"2-1"},
    # Grupo K
    "K1": {"t1":"Portugal","t2":"Congo RD","u1":"4-0","u2":"3-0"},
    "K2": {"t1":"Uzbekistán","t2":"Colombia","u1":"0-2","u2":"0-3"},
    "K3": {"t1":"Portugal","t2":"Uzbekistán","u1":"3-0","u2":"2-0"},
    "K4": {"t1":"Colombia","t2":"Congo RD","u1":"3-0","u2":"2-0"},
    "K5": {"t1":"Portugal","t2":"Colombia","u1":"2-1","u2":"1-1"},
    "K6": {"t1":"Congo","t2":"Uzbekistán","u1":"1-1","u2":"0-1"},
    # Grupo L
    "L1": {"t1":"Inglaterra","t2":"Croacia","u1":"2-1","u2":"1-0"},
    "L2": {"t1":"Ghana","t2":"Panamá","u1":"2-1","u2":"2-0"},
    "L3": {"t1":"Inglaterra","t2":"Ghana","u1":"3-0","u2":"2-0"},
    "L4": {"t1":"Croacia","t2":"Panamá","u1":"2-0","u2":"2-0"},
    "L5": {"t1":"Inglaterra","t2":"Panamá","u1":"4-0","u2":"3-0"},
    "L6": {"t1":"Croacia","t2":"Ghana","u1":"2-1","u2":"1-1"},
    # Octavos
    "O1":  {"t1":"España","t2":"3° grupo","u1":"3-0","u2":"2-0"},
    "O2":  {"t1":"Uruguay","t2":"Suiza","u1":"2-1","u2":"1-0"},
    "O3":  {"t1":"Francia","t2":"Senegal","u1":"2-0","u2":"3-1"},
    "O4":  {"t1":"Noruega","t2":"3° grupo","u1":"2-1","u2":"1-0"},
    "O5":  {"t1":"Argentina","t2":"3° grupo","u1":"3-0","u2":"2-0"},
    "O6":  {"t1":"Colombia","t2":"Austria","u1":"2-1","u2":"1-0"},
    "O7":  {"t1":"Inglaterra","t2":"3° grupo","u1":"3-0","u2":"2-0"},
    "O8":  {"t1":"Alemania","t2":"Ecuador","u1":"2-1","u2":"1-0"},
    "O9":  {"t1":"Brasil","t2":"Irán","u1":"3-0","u2":"2-1"},
    "O10": {"t1":"Marruecos","t2":"Canadá","u1":"2-1","u2":"1-1 (4-3p)"},
    "O11": {"t1":"Bélgica","t2":"Japón","u1":"2-1","u2":"1-1 (5-4p)"},
    "O12": {"t1":"Portugal","t2":"Corea","u1":"3-1","u2":"2-0"},
    "O13": {"t1":"México","t2":"EEUU","u1":"2-1","u2":"1-2"},
    "O14": {"t1":"P. Bajos","t2":"Turquía","u1":"2-1","u2":"1-1 (4-2p)"},
    "O15": {"t1":"Croacia","t2":"Australia","u1":"2-0","u2":"1-0"},
    "O16": {"t1":"Argelia","t2":"Ghana","u1":"2-1","u2":"1-1 (3-2p)"},
    # Cuartos
    "Q1": {"t1":"España","t2":"Marruecos","u1":"2-1","u2":"2-0"},
    "Q2": {"t1":"Francia","t2":"Bélgica","u1":"2-1","u2":"2-1"},
    "Q3": {"t1":"Argentina","t2":"Brasil","u1":"1-0","u2":"1-1 (4-2p)"},
    "Q4": {"t1":"Inglaterra","t2":"P. Bajos","u1":"2-1","u2":"1-1 (5-4p)"},
    "Q5": {"t1":"Alemania","t2":"Portugal","u1":"1-2","u2":"1-2"},
    "Q6": {"t1":"Uruguay","t2":"Colombia","u1":"2-1","u2":"1-2"},
    "Q7": {"t1":"Noruega","t2":"Croacia","u1":"2-1","u2":"1-0"},
    # Semis
    "S1": {"t1":"España","t2":"Argentina","u1":"2-1","u2":"1-1 (5-3p)"},
    "S2": {"t1":"Francia","t2":"Inglaterra","u1":"2-1","u2":"1-0"},
    "S3": {"t1":"Portugal","t2":"Uruguay","u1":"3-1","u2":"—"},
    "S4": {"t1":"Brasil","t2":"Noruega","u1":"—","u2":"2-1"},
    # Final
    "FN1": {"t1":"España","t2":"Portugal","u1":"2-1","u2":"Argentina vs Francia"},
}

# Fixture con fechas (hora Colombia UTC-5)
FIXTURE = [
    # Jornada 1
    {"id":"A1","fecha":"2026-06-11","hora":"17:00","grupo":"A"},
    {"id":"B1","fecha":"2026-06-12","hora":"14:00","grupo":"B"},
    {"id":"B2","fecha":"2026-06-12","hora":"17:00","grupo":"B"},
    {"id":"C1","fecha":"2026-06-12","hora":"20:00","grupo":"C"},
    {"id":"A2","fecha":"2026-06-13","hora":"14:00","grupo":"A"},
    {"id":"C2","fecha":"2026-06-13","hora":"17:00","grupo":"C"},
    {"id":"D1","fecha":"2026-06-13","hora":"20:00","grupo":"D"},
    {"id":"D2","fecha":"2026-06-14","hora":"14:00","grupo":"D"},
    {"id":"E1","fecha":"2026-06-14","hora":"17:00","grupo":"E"},
    {"id":"E2","fecha":"2026-06-14","hora":"20:00","grupo":"E"},
    {"id":"F1","fecha":"2026-06-15","hora":"14:00","grupo":"F"},
    {"id":"F2","fecha":"2026-06-15","hora":"17:00","grupo":"F"},
    {"id":"G1","fecha":"2026-06-15","hora":"20:00","grupo":"G"},
    {"id":"G2","fecha":"2026-06-16","hora":"14:00","grupo":"G"},
    {"id":"H1","fecha":"2026-06-16","hora":"17:00","grupo":"H"},
    {"id":"H2","fecha":"2026-06-16","hora":"20:00","grupo":"H"},
    {"id":"I1","fecha":"2026-06-17","hora":"14:00","grupo":"I"},
    {"id":"I2","fecha":"2026-06-17","hora":"17:00","grupo":"I"},
    {"id":"J1","fecha":"2026-06-17","hora":"20:00","grupo":"J"},
    {"id":"J2","fecha":"2026-06-18","hora":"14:00","grupo":"J"},
    {"id":"K1","fecha":"2026-06-18","hora":"17:00","grupo":"K"},
    {"id":"K2","fecha":"2026-06-18","hora":"20:00","grupo":"K"},
    {"id":"L1","fecha":"2026-06-19","hora":"14:00","grupo":"L"},
    {"id":"L2","fecha":"2026-06-19","hora":"17:00","grupo":"L"},
    # Jornada 2
    {"id":"A3","fecha":"2026-06-20","hora":"14:00","grupo":"A"},
    {"id":"A4","fecha":"2026-06-20","hora":"17:00","grupo":"A"},
    {"id":"B3","fecha":"2026-06-20","hora":"20:00","grupo":"B"},
    {"id":"B4","fecha":"2026-06-21","hora":"14:00","grupo":"B"},
    {"id":"C3","fecha":"2026-06-21","hora":"17:00","grupo":"C"},
    {"id":"C4","fecha":"2026-06-21","hora":"20:00","grupo":"C"},
    {"id":"D3","fecha":"2026-06-22","hora":"14:00","grupo":"D"},
    {"id":"D4","fecha":"2026-06-22","hora":"17:00","grupo":"D"},
    {"id":"E3","fecha":"2026-06-22","hora":"20:00","grupo":"E"},
    {"id":"E4","fecha":"2026-06-23","hora":"14:00","grupo":"E"},
    {"id":"F3","fecha":"2026-06-23","hora":"17:00","grupo":"F"},
    {"id":"F4","fecha":"2026-06-23","hora":"20:00","grupo":"F"},
    {"id":"G3","fecha":"2026-06-24","hora":"14:00","grupo":"G"},
    {"id":"G4","fecha":"2026-06-24","hora":"17:00","grupo":"G"},
    {"id":"H3","fecha":"2026-06-24","hora":"20:00","grupo":"H"},
    {"id":"H4","fecha":"2026-06-25","hora":"14:00","grupo":"H"},
    {"id":"I3","fecha":"2026-06-25","hora":"17:00","grupo":"I"},
    {"id":"I4","fecha":"2026-06-25","hora":"20:00","grupo":"I"},
    {"id":"J3","fecha":"2026-06-26","hora":"14:00","grupo":"J"},
    {"id":"J4","fecha":"2026-06-26","hora":"17:00","grupo":"J"},
    {"id":"K3","fecha":"2026-06-26","hora":"20:00","grupo":"K"},
    {"id":"K4","fecha":"2026-06-27","hora":"14:00","grupo":"K"},
    {"id":"L3","fecha":"2026-06-27","hora":"17:00","grupo":"L"},
    {"id":"L4","fecha":"2026-06-27","hora":"20:00","grupo":"L"},
    # Jornada 3 (simultáneos)
    {"id":"A5","fecha":"2026-07-01","hora":"16:00","grupo":"A"},
    {"id":"A6","fecha":"2026-07-01","hora":"16:00","grupo":"A"},
    {"id":"B5","fecha":"2026-07-01","hora":"20:00","grupo":"B"},
    {"id":"B6","fecha":"2026-07-01","hora":"20:00","grupo":"B"},
    {"id":"C5","fecha":"2026-07-02","hora":"16:00","grupo":"C"},
    {"id":"C6","fecha":"2026-07-02","hora":"16:00","grupo":"C"},
    {"id":"D5","fecha":"2026-07-02","hora":"20:00","grupo":"D"},
    {"id":"D6","fecha":"2026-07-02","hora":"20:00","grupo":"D"},
    {"id":"E5","fecha":"2026-07-03","hora":"16:00","grupo":"E"},
    {"id":"E6","fecha":"2026-07-03","hora":"16:00","grupo":"E"},
    {"id":"F5","fecha":"2026-07-03","hora":"20:00","grupo":"F"},
    {"id":"F6","fecha":"2026-07-03","hora":"20:00","grupo":"F"},
    {"id":"G5","fecha":"2026-07-04","hora":"16:00","grupo":"G"},
    {"id":"G6","fecha":"2026-07-04","hora":"16:00","grupo":"G"},
    {"id":"H5","fecha":"2026-07-04","hora":"20:00","grupo":"H"},
    {"id":"H6","fecha":"2026-07-04","hora":"20:00","grupo":"H"},
    {"id":"I5","fecha":"2026-07-05","hora":"16:00","grupo":"I"},
    {"id":"I6","fecha":"2026-07-05","hora":"16:00","grupo":"I"},
    {"id":"J5","fecha":"2026-07-05","hora":"20:00","grupo":"J"},
    {"id":"J6","fecha":"2026-07-05","hora":"20:00","grupo":"J"},
    {"id":"K5","fecha":"2026-07-06","hora":"16:00","grupo":"K"},
    {"id":"K6","fecha":"2026-07-06","hora":"16:00","grupo":"K"},
    {"id":"L5","fecha":"2026-07-06","hora":"20:00","grupo":"L"},
    {"id":"L6","fecha":"2026-07-06","hora":"20:00","grupo":"L"},
]

# ── SISTEMA DE PUNTOS ────────────────────────────────────────
def parse_score(s):
    if not s or s in ["—", ""] or "(" in s:
        return None
    import re
    m = re.match(r'^(\d+)-(\d+)$', s.strip())
    return (int(m.group(1)), int(m.group(2))) if m else None

def get_result(s):
    p = parse_score(s)
    if not p: return None
    return "win" if p[0] > p[1] else "loss" if p[0] < p[1] else "draw"

def calc_points(pred, real):
    pp, rp = parse_score(pred), parse_score(real)
    if not pp or not rp: return 0
    if pp == rp: return 3
    if get_result(pred) == get_result(real): return 1
    return 0

def registrar_resultado(match_id, marcador_real):
    """Registra un resultado real y recalcula puntos."""
    data = load_data()
    match_id = match_id.upper()

    if match_id not in PRONOSTICOS:
        return f"❌ No encontré el partido con ID *{match_id}*. Ejemplo: A1, B3, O2"

    data["resultados_reales"][match_id] = marcador_real
    pron = PRONOSTICOS[match_id]

    p1 = calc_points(pron["u1"], marcador_real)
    p2 = calc_points(pron["u2"], marcador_real)

    # Recalcular totales desde cero para evitar duplicados
    data["puntos"] = {"u1": 0, "u2": 0}
    data["exactos"] = {"u1": 0, "u2": 0}
    data["resultados_ok"] = {"u1": 0, "u2": 0}

    for mid, real in data["resultados_reales"].items():
        if mid in PRONOSTICOS:
            p = PRONOSTICOS[mid]
            for u, pred in [("u1", p["u1"]), ("u2", p["u2"])]:
                pts = calc_points(pred, real)
                data["puntos"][u] += pts
                if pts == 3: data["exactos"][u] += 1
                elif pts == 1: data["resultados_ok"][u] += 1

    save_data(data)

    def badge(pts):
        if pts == 3: return "🎯 +3 exacto"
        if pts == 1: return "✅ +1 resultado"
        return "❌ 0 pts"

    resp = f"""⚽ *Resultado guardado*
{pron['t1']} {marcador_real} {pron['t2']}

📊 *Puntos de este partido:*
👤 U1 (pronóstico: {pron['u1']}) → {badge(p1)}
👤 U2 (pronóstico: {pron['u2']}) → {badge(p2)}

🏆 *Tabla actual:*
👤 U1: *{data['puntos']['u1']} pts* ({data['exactos']['u1']} exactos · {data['resultados_ok']['u1']} resultados)
👤 U2: *{data['puntos']['u2']} pts* ({data['exactos']['u2']} exactos · {data['resultados_ok']['u2']} resultados)"""

    lider = "U1 🥇" if data["puntos"]["u1"] > data["puntos"]["u2"] else \
            "U2 🥇" if data["puntos"]["u2"] > data["puntos"]["u1"] else "Empate 🤝"
    resp += f"\n\n👑 Líder: *{lider}*"
    return resp

def partidos_hoy():
    """Devuelve los partidos de hoy con pronósticos."""
    hoy = date.today().isoformat()
    partidos = [f for f in FIXTURE if f["fecha"] == hoy]
    data = load_data()

    if not partidos:
        return "📅 No hay partidos programados para hoy."

    lines = [f"📅 *Partidos del {hoy}*\n"]
    for p in partidos:
        mid = p["id"]
        pron = PRONOSTICOS.get(mid, {})
        t1 = pron.get("t1", "?")
        t2 = pron.get("t2", "?")
        real = data["resultados_reales"].get(mid)
        estado = f"✅ {real}" if real else "⏳ Pendiente"
        lines.append(
            f"🕐 {p['hora']} (COL) | Grupo {p['grupo']}\n"
            f"  {t1} vs {t2}\n"
            f"  🔵 U1: {pron.get('u1','?')} · 🟢 U2: {pron.get('u2','?')}\n"
            f"  {estado}\n"
        )
    return "\n".join(lines)

def tabla_puntos():
    data = load_data()
    jugados = len(data["resultados_reales"])
    lider = "U1 🥇" if data["puntos"]["u1"] > data["puntos"]["u2"] else \
            "U2 🥇" if data["puntos"]["u2"] > data["puntos"]["u1"] else "Empate 🤝"
    return f"""🏆 *Tabla de la Polla*

👤 *Usuario 1*
  Puntos: {data['puntos']['u1']} pts
  Exactos: {data['exactos']['u1']} 🎯
  Resultados: {data['resultados_ok']['u1']} ✅

👤 *Usuario 2*
  Puntos: {data['puntos']['u2']} pts
  Exactos: {data['exactos']['u2']} 🎯
  Resultados: {data['resultados_ok']['u2']} ✅

📊 Partidos ingresados: {jugados}
👑 Líder: *{lider}*"""

def ayuda():
    return """🤖 *Comandos del Bot Polla Mundial 2026*

📅 *hoy* → Partidos de hoy con pronósticos
🏆 *tabla* → Ver puntos actuales
📋 *pronostico [ID]* → Ver pronóstico de un partido
  Ej: _pronostico A1_

⚽ *resultado [ID] [marcador]* → Ingresar resultado real
  Ej: _resultado A1 3-0_
  Ej: _resultado B2 1-1_

🔍 *pendientes* → Partidos sin resultado todavía
📊 *resumen* → Análisis completo del torneo
❓ *ayuda* → Ver este menú

💡 *IDs de partidos:*
Grupos: A1-A6, B1-B6 ... L1-L6
Octavos: O1-O16
Cuartos: Q1-Q7
Semis: S1-S4
Final: FN1"""

def pronostico_partido(match_id):
    mid = match_id.upper()
    if mid not in PRONOSTICOS:
        return f"❌ ID *{mid}* no encontrado. Usa IDs como A1, B3, O2, Q1, S1, FN1"
    p = PRONOSTICOS[mid]
    data = load_data()
    real = data["resultados_reales"].get(mid, "⏳ Sin resultado aún")
    return f"""📋 *Partido {mid}*
{p['t1']} vs {p['t2']}

🔵 U1 pronostica: *{p['u1']}*
🟢 U2 pronostica: *{p['u2']}*
⚽ Resultado real: *{real}*"""

def partidos_pendientes():
    data = load_data()
    jugados = set(data["resultados_reales"].keys())
    pendientes = [f for f in FIXTURE if f["id"] not in jugados]
    if not pendientes:
        return "✅ ¡Todos los partidos tienen resultado!"
    lines = [f"⏳ *Partidos pendientes ({len(pendientes)}):*\n"]
    for p in pendientes[:15]:  # Máx 15 para no saturar
        pron = PRONOSTICOS.get(p["id"], {})
        lines.append(f"• {p['id']} | {p['fecha']} {p['hora']} | {pron.get('t1','?')} vs {pron.get('t2','?')}")
    if len(pendientes) > 15:
        lines.append(f"\n... y {len(pendientes)-15} más.")
    return "\n".join(lines)

def resumen_claude(pregunta):
    """Usa Claude API para responder preguntas complejas."""
    data = load_data()
    context = f"""Eres el asistente de una polla mundialista del Mundial 2026 para 2 usuarios.

ESTADO ACTUAL:
- Puntos U1: {data['puntos']['u1']} (exactos: {data['exactos']['u1']}, resultados: {data['resultados_ok']['u1']})
- Puntos U2: {data['puntos']['u2']} (exactos: {data['exactos']['u2']}, resultados: {data['resultados_ok']['u2']})
- Partidos jugados: {len(data['resultados_reales'])}
- Resultados reales: {json.dumps(data['resultados_reales'], ensure_ascii=False)}

PRONOSTICOS CLAVE:
- U1: Campeón España, Subcampeón Francia, 3° Argentina. Bota de Oro Mbappé.
- U2: Campeón Argentina, Subcampeón España, 3° Brasil. Bota de Oro Vinicius Jr.

Responde en español, de forma concisa (máx 200 palabras), usando emojis moderadamente.
"""
    try:
        response = anthropic_client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=300,
            system=context,
            messages=[{"role": "user", "content": pregunta}]
        )
        return response.content[0].text
    except Exception as e:
        return f"❌ Error con Claude API: {str(e)}"

# ── WEBHOOK TWILIO ───────────────────────────────────────────
@app.route("/webhook", methods=["POST"])
def webhook():
    # Limpiar mensaje: quitar espacios, bajar a minúsculas, eliminar caracteres invisibles
    raw = request.form.get("Body", "")
    mensaje = " ".join(raw.strip().lower().split())  # normaliza espacios múltiples
    
    resp = MessagingResponse()
    msg = resp.message()

    # Partir en tokens para comandos con argumentos
    partes = mensaje.split()
    cmd = partes[0] if partes else ""

    # Comandos simples
    if cmd in ["hoy", "partidos"] or mensaje == "partidos hoy":
        msg.body(partidos_hoy())
    elif cmd in ["tabla", "puntos", "score"]:
        msg.body(tabla_puntos())
    elif cmd in ["ayuda", "help", "menu", "menú", "comandos"]:
        msg.body(ayuda())
    elif cmd in ["pendientes", "faltan"]:
        msg.body(partidos_pendientes())

    # resultado [ID] [marcador]  — ej: resultado a1 2-1
    elif cmd == "resultado":
        if len(partes) >= 3:
            mid = partes[1].upper()        # a1 → A1
            marcador = partes[2].strip()   # 2-1
            msg.body(registrar_resultado(mid, marcador))
        else:
            msg.body("❌ Formato: *resultado A1 2-1*\nEjemplo: resultado a1 3-0")

    # pronostico [ID]  — ej: pronostico b2
    elif cmd in ["pronostico", "pronóstico", "prono"]:
        if len(partes) >= 2:
            msg.body(pronostico_partido(partes[1].upper()))
        else:
            msg.body("❌ Formato: *pronostico A1*")

    # Cualquier otra cosa → Claude responde
    else:
        msg.body(resumen_claude(mensaje))

    return Response(str(resp), mimetype="text/xml")

@app.route("/", methods=["GET"])
def home():
    return "🏆 Bot Polla Mundial 2026 activo!", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
