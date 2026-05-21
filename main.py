import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from supabase import create_client, Client
import os
import plotly.express as px

# ===================== CONFIGURAÇÕES E CONEXÃO =====================
SUPABASE_URL = "https://ztqymabxqbjmaktrcavj.supabase.co"
SUPABASE_KEY = "sb_publishable_SXqZhVhu0oyCRz5AMnTFoA_l8bYiPeq"

@st.cache_resource
def init_connection():
    try:
        client = create_client(SUPABASE_URL, SUPABASE_KEY)
        client.table("contas_pagar").select("count", count="exact").execute()
        return client
    except Exception as e:
        st.error(f"Erro ao conectar com Supabase: {e}")
        return None

supabase: Client = init_connection()

# ===================== CONFIGURAÇÃO DA PÁGINA & DESIGN PREMIUM =====================
st.set_page_config(
    page_title="Greenfield Financeiro | ERP Premium",
    page_icon="💹",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Estilização CSS customizada para reduzir o tamanho dos títulos solicitados
st.markdown("""
    <style>
        [data-testid="stSidebar"] { background-color: #062618 !important; }
        [data-testid="stSidebar"] * { color: #ffffff !important; }
        
        /* Redução dos títulos principais solicitados */
        h1 {
            font-size: 24px !important;
            font-weight: 700 !important;
        }
        h2 {
            font-size: 20px !important;
            font-weight: 600 !important;
        }
        
        /* Ajuste específico para os rótulos e valores dos cards de métricas */
        [data-testid="stMetricLabel"] {
            font-size: 14px !important;
        }
        [data-testid="stMetricValue"] {
            font-size: 22px !important;
        }
        
        .stMetric {
            background-color: #f4f7f5;
            padding: 12px;
            border-radius: 10px;
            border-left: 5px solid #0b4d32;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }
        div.stButton > button:first-child { background-color: #0b4d32; color: white; border-radius: 6px; }
    </style>
""", unsafe_allow_html=True)

# ===================== FUNÇÕES AUXILIARES DE BANCO =====================
def load_data(table: str) -> pd.DataFrame:
    if not supabase: return pd.DataFrame()
    try:
        res = supabase.table(table).select("*").execute()
        return pd.DataFrame(res.data) if res.data else pd.DataFrame()
    except Exception as e:
        st.error(f"Erro ao carregar {table}: {e}")
        return pd.DataFrame()

def save_to_db(table: str, data: dict):
    if not supabase: return None
    try:
        res = supabase.table(table).insert(data).execute()
        return res.data
    except Exception as e:
        st.error(f"Erro ao salvar em {table}: {e}")
        return None

def formatar_moeda_br(val):
    try:
        return f"R$ {float(val):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except:
        return str(val)

def formatar_data_br(dt_str):
    try:
        return pd.to_datetime(dt_str).strftime('%d/%m/%Y')
    except Exception:
        return dt_str

# Função auxiliar para calcular o 5º dia útil do mês seguinte (para provisionamento da folha)
def calcular_quinto_dia_util_mes_seguinte():
    hoje = datetime.today()
    if hoje.month == 12:
        proximo_mes = datetime(hoje.year + 1, 1, 1)
    else:
        proximo_mes = datetime(hoje.year, hoje.month + 1, 1)
    
    dias_uteis = 0
    data_alvo = proximo_mes
    while dias_uteis < 5:
        if data_alvo.weekday() < 5:
            dias_uteis += 1
        if dias_uteis < 5:
            data_alvo += timedelta(days=1)
    return data_alvo.date()

# ===================== CÁLCULO DINÂMICO DE SALDO =====================
df_medicoes_global = load_data("medicoes_caixa")
if not df_medicoes_global.empty and 'valor' in df_medicoes_global.columns:
    saldo_projetado_caixa = df_medicoes_global['valor'].astype(float).sum()
else:
    saldo_projetado_caixa = 0.00  # Inicia estritamente zerado conforme preferência

# ===================== SIDEBAR NAVEGAÇÃO =====================
with st.sidebar:
    st.sidebar.markdown("# 💹 Greenfield")
    st.markdown("### ERP FINANCEIRO CORPORATIVO")
    
    page = st.radio("Navegação", [
        "📊 Dashboard", 
        "💳 Contas a Pagar & Caixa", 
        "🛒 Pedidos de Compra", 
        "⚖️ Acordos Judiciais", 
        "👥 Salários"
    ])
    
    if st.button("🔄 Sincronizar Nuvem"):
        st.cache_resource.clear()
        st.rerun()

# ===================== 1. DASHBOARD PRINCIPAL DINÂMICO =====================
if page == "📊 Dashboard":
    st.title("📊 Dashboard Executivo Real-Time")
    
    df_contas = load_data("contas_pagar")
    df_pedidos = load_data("pedidos_compra")
    df_parcelas = load_data("parcelas_acordo")
    
    val_contas = df_contas['valor'].astype(float).sum() if not df_contas.empty and 'valor' in df_contas.columns else 0.0
    val_pedidos = df_pedidos['valor_total'].astype(float).sum() if not df_pedidos.empty and 'valor_total' in df_pedidos.columns else 0.0
    val_judiciais = df_parcelas['valor_parcela'].astype(float).sum() if not df_parcelas.empty and 'valor_parcela' in df_parcelas.columns else 0.0
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Saldo Projetado em Caixa", formatar_moeda_br(saldo_projetado_caixa))
    c2.metric("Total Contas a Pagar", formatar_moeda_br(val_contas))
    c3.metric("Total Pedidos de Compra", formatar_moeda_br(val_pedidos))
    c4.metric("Total Acordos (Parcelas)", formatar_moeda_br(val_judiciais))
    
    st.markdown("---")
    g1, g2 = st.columns(2)
    
    with g1:
        if not df_contas.empty and 'status' in df_contas.columns:
            df_contas['valor'] = df_contas['valor'].astype(float)
            fig1 = px.pie(df_contas, values='valor', names='status', title="Situação do Contas a Pagar", hole=0.4, color_discrete_sequence=['#0b4d32', '#c94c4c', '#e6b800'])
            st.plotly_chart(fig1, use_container_width=True)
        else:
            st.info("Sem dados de Contas para exibir gráficos.")
            
    with g2:
        if not df_pedidos.empty and 'solicitante' in df_pedidos.columns:
            df_pedidos['valor_total'] = df_pedidos['valor_total'].astype(float)
            fig2 = px.bar(df_pedidos, x='solicitante', y='valor_total', title="Compras por Solicitante (R$)", color_discrete_sequence=['#0b4d32'])
            st.plotly_chart(fig2, use_container_
