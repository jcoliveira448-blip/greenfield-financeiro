import streamlit as st
import pandas as pd
from datetime import datetime
from supabase import create_client, Client
import os
import plotly.express as px  # Corrigido: Import do Plotly

# ===================== CONFIGURAÇÕES =====================
# Dica: No ambiente de produção, use st.secrets para proteger estes dados
SUPABASE_URL = "https://ztqymabxqbjmaktrcavj.supabase.co"
SUPABASE_KEY = "sb_publishable_SXqZhVhu0oyCRz5AMnTFoA_l8bYiPeq"

@st.cache_resource
def init_connection():
    if not SUPABASE_KEY or SUPABASE_KEY.startswith("SUA_"):
        st.error("Supabase key não configurada!")
        return None
    try:
        client = create_client(SUPABASE_URL, SUPABASE_KEY)
        # Teste rápido de conexão
        client.table("contas_pagar").select("count", count="exact").execute()
        return client
    except Exception as e:
        st.error(f"Erro ao conectar com Supabase: {e}")
        return None

supabase: Client = init_connection()

# ===================== CONFIGURAÇÃO DA PÁGINA =====================
st.set_page_config(
    page_title="Greenfield Financeiro | ERP",
    page_icon="💹",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ===================== FUNÇÕES DE BANCO =====================
def load_data(table: str) -> pd.DataFrame:
    if not supabase:
        return pd.DataFrame()
    try:
        res = supabase.table(table).select("*").execute()
        if res.data:
            return pd.DataFrame(res.data)
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Erro ao carregar {table}: {e}")
        return pd.DataFrame()

def save_to_db(table: str, data: dict):
    if not supabase:
        st.error("Supabase não conectado.")
        return False
    try:
        res = supabase.table(table).insert(data).execute()
        st.success("✅ Salvo com sucesso!")
        return True
    except Exception as e:
        st.error(f"Erro ao salvar: {e}")
        return False

# ===================== SIDEBAR =====================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
logo_path = os.path.join(BASE_DIR, "assets", "logo.png")

with st.sidebar:
    page = st.radio("Navegação", [
        "📊 Dashboard", 
        "💳 Contas a Pagar", 
        "🛒 Pedidos de Compra", 
        "⚖️ Acordos Judiciais", 
        "👥 Salários", 
        "🏭 Fornecedores"
    ])
    
    if st.button("🔄 Sincronizar Nuvem"):
        st.cache_resource.clear()
        st.rerun()

# ===================== PÁGINAS =====================
if page == "📊 Dashboard":
    st.title("📊 Dashboard Executivo")
    df_contas = load_data("contas_pagar")
    
    if not df_contas.empty:
        col1, col2, col3 = st.columns(3)
        col1.metric("Saldo Estimado", "R$ 1.250.000,00")
        
        # Proteção contra colunas ausentes ou vazias
        if 'status' in df_contas.columns and 'valor' in df_contas.columns:
            total_pendente = df_contas[df_contas['status'] == 'Pendente']['valor'].sum()
            col2.metric("Contas Pendentes", f"R$ {total_pendente:,.2f}")
            
            fig = px.pie(df_contas, values='valor', names='status', title="Status Financeiro", hole=0.4)
            st.plotly_chart(fig, use_container_width=True)
        else:
            col2.metric("Contas Pendentes", "R$ 0,00")
            st.warning("Colunas 'status' ou 'valor' não encontradas na tabela do banco.")
    else:
        st.info("Nenhum dado encontrado ou aguardando conexão com Supabase.")

elif page == "💳 Contas a Pagar":
    st.title("💳 Contas a Pagar")
    
    with st.expander("➕ Novo Lançamento", expanded=False):
        with st.form("f_conta"):
            c1, c2, c3 = st.columns(3)
            forn = c1.text_input("Fornecedor")
            venc = c2.date_input("Vencimento", value=datetime.today())
            valor = c3.number_input("Valor (R$)", min_value=0.01, format="%.2f")
            
            if st.form_submit_button("💾 Salvar"):
                if forn and valor > 0:
                    sucesso = save_to_db("contas_pagar", {
                        "fornecedor": forn,
                        "vencimento": str(venc),
                        "valor": float(valor),
                        "status": "Pendente"
                    })
                    if sucesso:
                        st.rerun()
                else:
                    st.warning("Preencha todos os campos obrigatórios.")

    df = load_data("contas_pagar")
    if not df.empty:
        st.subheader("Registros")
        edited_df = st.data_editor(
            df,
            use_container_width=True,
            num_rows="dynamic",
            hide_index=True
        )
    else:
        st.info("Nenhuma conta cadastrada ainda.")

else:
    st.title(page)
    # Ajuste simples para bater com os nomes prováveis das tabelas (removendo emojis)
    table_name = page.lower().replace("🛒 ", "").replace("⚖️ ", "").replace("👥 ", "").replace("🏭 ", "")
    table_name = table_name.replace(" ", "_").replace("ç", "c").replace("ã", "a")
    
    df = load_data(table_name)
    if not df.empty:
        st.data_editor(df, use_container_width=True, num_rows="dynamic")
    else:
        st.info(f"Módulo {page} (Tabela: {table_name}) - Nenhum dado encontrado.")