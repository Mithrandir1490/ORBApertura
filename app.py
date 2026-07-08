import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import datetime
import pytz
import warnings

warnings.filterwarnings('ignore')

st.set_page_config(page_title="The One Ring: Bot 5 Francotirador ORB", layout="wide", page_icon="🏹")

st.title("🏹 Bot 5 — Francotirador de Apertura (ORB)")
st.caption("Ecosistema Cuantitativo 'The One Ring' | Rupturas de Rango Inicial en Barras de 5 Minutos")
st.markdown("---")

# BARRA LATERAL TÁCTICA
st.sidebar.header("⚙️ Parámetros del Rango de Apertura")
minutos_rango = st.sidebar.selectbox("Ventana de Rango Inicial", [15, 30], index=0)
filtro_volumen = st.sidebar.slider("Filtro de Volumen Anómalo (x)", 1.0, 2.5, 1.2, step=0.1)

UNIVERSO_ORB = [
    "IBIT", "MSTR", "COIN", "IONQ", "ASTS", "OKLO", "NVDA", "AMD", "AVGO", "TSM", 
    "TSLA", "CELH", "NFLX", "AAPL", "MSFT", "GOOGL", "JPM", "V", "FANG", "MCO"
]
TICKERS = list(set(UNIVERSO_ORB))

def analizar_breakout_apertura(ticker, ventana_min):
    try:
        # Descargamos barras de 5 minutos del día de hoy
        df = yf.download(ticker, period="1d", interval="5m", progress=False, auto_adjust=True)
        if df.empty or len(df) < (ventana_min // 5): return None
        
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
            
        # Asegurar orden cronológico
        df = df.sort_index()
        
        # Identificar las barras del rango inicial (ej. las primeras 3 barras de 5 min = 15 min)
        barras_rango = ventana_min // 5
        df_rango_inicial = df.iloc[:barras_rango]
        
        # Calcular los límites del búnker de apertura
        techo_apertura = float(df_rango_inicial['High'].max())
        suelo_apertura = float(df_rango_inicial['Low'].min())
        volumen_promedio_rango = float(df_rango_inicial['Volume'].mean())
        
        # Datos de la barra más reciente (barra viva)
        precio_actual = float(df['Close'].iloc[-1])
        volumen_actual = float(df['Volume'].iloc[-1])
        
        # --- LÓGICA DE DETECCIÓN DE BREAKOUT ---
        estatus = "⌛ DENTRO DEL RANGO"
        
        # Validamos barras posteriores al rango inicial
        if len(df) > barras_rango:
            df_post_rango = df.iloc[barras_rango:]
            
            # Criterio: El precio actual superó el techo y hay volumen institucional superior al promedio inicial
            if precio_actual > techo_apertura and volumen_actual >= (volumen_promedio_rango * filtro_volumen):
                estatus = "🚀 BREAKOUT ALCISTA (Gatillo de Compra)"
            elif precio_actual < suelo_apertura:
                estatus = "📉 BREAKOUT BAJISTA (Fuga de Fuerza)"
                
        return {
            "Ticker": ticker,
            "Precio Spot": precio_actual,
            "Techo Rango": techo_apertura,
            "Suelo Rango": suelo_apertura,
            "Volumen Actual": volumen_actual,
            "Vol Ratio": volumen_actual / np.where(volumen_promedio_rango == 0, 1e-6, volumen_promedio_rango),
            "Estatus ORB": estatus
        }
    except:
        return None

if st.button("🏹 Lanzar Escaneo de Apertura Volátil"):
    with st.spinner("Midiendo perímetros y volúmenes de la primera media hora..."):
        resultados = []
        for t in TICKERS:
            res = analizar_breakout_apertura(t, minutos_rango)
            if res: resultados.append(res)
            
        if resultados:
            df_res = pd.DataFrame(resultados)
            rupturas = df_res[df_res["Estatus ORB"] == "🚀 BREAKOUT ALCISTA (Gatillo de Compra)"]
            otros = df_res[df_res["Estatus ORB"] != "🚀 BREAKOUT ALCISTA (Gatillo de Compra)"]
            df_visual = pd.concat([rupturas, otros], ignore_index=True)
            
            def style_orb(val):
                if "🚀" in val: return "background-color: #e6fffa; color: #234e52; font-weight: bold;"
                if "📉" in val: return "background-color: #fff5f5; color: #742a2a;"
                return "color: #a0aec0;"

            st.dataframe(df_visual.style.map(style_orb, subset=["Estatus ORB"]).format({
                "Precio Spot": "${:.2f}", "Techo Rango": "${:.2f}", "Suelo Rango": "${:.2f}",
                "Volumen Actual": "{:,.0f}", "Vol Ratio": "{:.2f}x"
            }), use_container_width=True, hide_index=True)
        else:
            st.info("Esperando los datos oficiales de la campana de apertura del mercado.")
