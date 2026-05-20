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

st.markdown("""
    <style>
        [data-testid="stSidebar"] { background-color: #062618 !important; }
        [data-testid="stSidebar"] * { color: #ffffff !important; }
        .stMetric {
            background-color: #f4f7f5;
            padding: 15px;
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
    return f"R$ {val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def formatar_data_br(dt_str):
    try:
        return pd.to_datetime(dt_str).dt.strftime('%d/%m/%Y')
    except Exception:
        return dt_str

# ===================== SIDEBAR NAVEGAÇÃO =====================
with st.sidebar:
    st.sidebar.markdown("# 💹 Greenfield")
    st.markdown("### ERP FINANCEIRO CORPORATIVO")
    
    page = st.radio("Navegação", [
        "📊 Dashboard", 
        "💳 Contas a Pagar", 
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
    c1.metric("Saldo Projetado em Caixa", "R$ 1.250.000,00")
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
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("Sem dados de Pedidos para exibir gráficos.")

# ===================== 2. CONTAS A PAGAR =====================
elif page == "💳 Contas a Pagar":
    st.title("💳 Gestão de Contas a Pagar")
    aba1, aba2, aba3 = st.tabs(["Lançamento", "📋 Histórico", "🛠️ Gerenciar (Editar/Excluir)"])
    
    with aba1:
        with st.form("f_conta"):
            cx1, cx2, cx3 = st.columns(3)
            forn = cx1.text_input("Fornecedor / Favorecido")
            venc = cx2.date_input("Data de Vencimento", value=datetime.today(), format="DD/MM/YYYY")
            valor = cx3.number_input("Valor (R$)", min_value=0.01, format="%.2f")
            if st.form_submit_button("💾 Agendar Pagamento"):
                if forn and valor > 0:
                    save_to_db("contas_pagar", {"fornecedor": forn, "vencimento": str(venc), "valor": float(valor), "status": "Pendente"})
                    st.success("Conta provisionada!")
                    st.rerun()

    with aba2:
        df = load_data("contas_pagar")
        if not df.empty:
            df_vis = df.copy()
            df_vis['vencimento'] = formatar_data_br(df_vis['vencimento'])
            df_vis['valor'] = df_vis['valor'].apply(formatar_moeda_br)
            st.dataframe(df_vis[['fornecedor', 'vencimento', 'valor', 'status']], use_container_width=True, hide_index=True)
        else: st.info("Nenhuma conta localizada.")

    with aba3:
        df_ger = load_data("contas_pagar")
        if not df_ger.empty:
            # Configuração no padrão Excel Brasil para a coluna de valor
            mudancas = st.data_editor(
                df_ger, 
                use_container_width=True, 
                num_rows="dynamic", 
                hide_index=True, 
                key="edit_cp",
                column_config={
                    "valor": st.column_config.NumberColumn("Valor (R$)", format="R$ %.2f", help="Formato Excel Brasil"),
                    "vencimento": st.column_config.DateColumn("Vencimento", format="DD/MM/YYYY")
                }
            )
            if st.button("💾 Sincronizar Contas a Pagar"):
                id_tela = mudancas['id'].tolist() if 'id' in mudancas.columns else []
                for id_del in [x for x in df_ger['id'].tolist() if x not in id_tela]:
                    supabase.table("contas_pagar").delete().eq("id", id_del).execute()
                for idx, row in mudancas.iterrows():
                    supabase.table("contas_pagar").update({"fornecedor": str(row['fornecedor']), "vencimento": str(row['vencimento']), "valor": float(row['valor']), "status": str(row['status'])}).eq("id", row['id']).execute()
                st.success("Banco de Dados Atualizado!")
                st.cache_resource.clear()
                st.rerun()

# ===================== 3. PEDIDOS DE COMPRA =====================
elif page == "🛒 Pedidos de Compra":
    st.title("🛒 Ordens de Compra (OC)")
    aba1, aba2, aba3 = st.tabs(["Emitir Pedido", "📋 Histórico", "🛠️ Gerenciar (Editar/Excluir)"])
    
    with aba1:
        with st.form("f_pedido"):
            cc1, cc2 = st.columns(2)
            num_oc = cc1.text_input("Número da OC")
            solicitante = cc2.text_input("Solicitante / Engenheiro")
            cc3, cc4 = st.columns(2)
            forn = cc3.text_input("Fornecedor")
            val_total = cc4.number_input("Valor Total (R$)", min_value=0.00, format="%.2f")
            if st.form_submit_button("🚀 Enviar Pedido"):
                if num_oc and val_total > 0:
                    save_to_db("pedidos_compra", {"numero_oc": num_oc, "solicitante": solicitante, "fornecedor": forn, "valor_total": float(val_total), "status": "Aberto"})
                    save_to_db("contas_pagar", {"fornecedor": f"OC {num_oc} - {forn}", "vencimento": str(datetime.today().date() + timedelta(days=15)), "valor": float(val_total), "status": "Pendente"})
                    st.success("Pedido registrado e integrado ao Contas a Pagar!")
                    st.rerun()

    with aba2:
        df = load_data("pedidos_compra")
        if not df.empty:
            df_vis = df.copy()
            df_vis['valor_total'] = df_vis['valor_total'].apply(formatar_moeda_br)
            st.dataframe(df_vis[['numero_oc', 'solicitante', 'fornecedor', 'valor_total', 'status']], use_container_width=True, hide_index=True)
        else: st.info("Nenhum pedido localizado.")

    with aba3:
        df_ger = load_data("pedidos_compra")
        if not df_ger.empty:
            # Configuração no padrão Excel Brasil para a coluna de valor_total
            mudancas = st.data_editor(
                df_ger, 
                use_container_width=True, 
                num_rows="dynamic", 
                hide_index=True, 
                key="edit_pc",
                column_config={
                    "valor_total": st.column_config.NumberColumn("Valor Total (R$)", format="R$ %.2f")
                }
            )
            if st.button("💾 Sincronizar Pedidos"):
                id_tela = mudancas['id'].tolist() if 'id' in mudancas.columns else []
                for id_del in [x for x in df_ger['id'].tolist() if x not in id_tela]:
                    supabase.table("pedidos_compra").delete().eq("id", id_del).execute()
                for idx, row in mudancas.iterrows():
                    supabase.table("pedidos_compra").update({"numero_oc": str(row['numero_oc']), "solicitante": str(row['solicitante']), "fornecedor": str(row['fornecedor']), "valor_total": float(row['valor_total']), "status": str(row['status'])}).eq("id", row['id']).execute()
                st.success("Alterações salvas!")
                st.cache_resource.clear()
                st.rerun()

# ===================== 4. ACORDOS JUDICIAIS =====================
elif page == "⚖️ Acordos Judiciais":
    st.title("⚖️ Controle de Acordos Judiciais")
    aba1, aba2, aba3 = st.tabs(["Firmar Acordo", "📋 Histórico de Parcelas Completo", "🛠️ Gerenciar (Editar/Excluir)"])
    
    with aba1:
        with st.form("f_judicial"):
            j1, j2 = st.columns(2)
            proc = j1.text_input("Número do Processo / Vara")
            rec = j2.text_input("Nome do Reclamante")
            j3, j4, j5 = st.columns(3)
            val_total = j3.number_input("Valor Total do Acordo (R$)", min_value=1.00, format="%.2f")
            qtd_parc = j4.number_input("Quantidade de Parcelas", min_value=1, max_value=48, value=1)
            data_ini = j5.date_input("Vencimento da 1ª Parcela", value=datetime.today(), format="DD/MM/YYYY")
            
            if st.form_submit_button("🤝 Gerar Acordo e Cronograma"):
                if proc and rec and val_total > 0:
                    acordo = save_to_db("acordos_judiciais", {"processo": proc, "reclamante": rec, "valor_total": float(val_total), "qtd_parcelas": int(qtd_parc), "status": "Em andamento"})
                    if acordo:
                        acordo_id = acordo[0]['id']
                        valor_parcela = float(val_total) / int(qtd_parc)
                        for i in range(1, int(qtd_parc) + 1):
                            venc_parcela = data_ini + timedelta(days=(i-1)*30)
                            save_to_db("parcelas_acordo", {"acordo_id": acuerdo_id, "numero_parcela": i, "valor_parcela": valor_parcela, "vencimento": venc_parcela.strftime('%Y-%m-%d'), "status": "Pendente"})
                        st.success("✅ Acordo firmado e parcelas geradas!")
                        st.rerun()

    with aba2:
        df_parc = load_data("parcelas_acordo")
        df_acod = load_data("acordos_judiciais")
        
        if not df_parc.empty and not df_acod.empty:
            df_mestre = pd.merge(df_parc, df_acod, left_on="acordo_id", right_on="id", suffixes=('_parc', '_acord'))
            df_mestre['vencimento'] = formatar_data_br(df_mestre['vencimento'])
            df_mestre['valor_parcela'] = df_mestre['valor_parcela'].apply(formatar_moeda_br)
            
            df_exibir = df_mestre[['processo', 'reclamante', 'numero_parcela', 'valor_parcela', 'vencimento', 'status_parc']]
            df_exibir.columns = ['Processo / Vara', 'Nome do Reclamante', 'Nº Parcela', 'Valor da Parcela', 'Data Vencimento', 'Status']
            
            st.dataframe(df_exibir, use_container_width=True, hide_index=True)
        else:
            st.info("Nenhuma parcela disponível para exibição.")

    with aba3:
        st.subheader("Gerenciamento de Parcelas")
        df_ger = load_data("parcelas_acordo")
        if not df_ger.empty:
            # Configuração no padrão Excel Brasil para valor_parcela e data dentro do editor
            mudancas = st.data_editor(
                df_ger, 
                use_container_width=True, 
                num_rows="dynamic", 
                hide_index=True, 
                key="edit_aj",
                column_config={
                    "valor_parcela": st.column_config.NumberColumn("Valor da Parcela (R$)", format="R$ %.2f"),
                    "vencimento": st.column_config.DateColumn("Vencimento", format="DD/MM/YYYY")
                }
            )
            if st.button("💾 Sincronizar Cronograma Judicial"):
                id_tela = mudancas['id'].tolist() if 'id' in mudancas.columns else []
                for id_del in [x for x in df_ger['id'].tolist() if x not in id_tela]:
                    supabase.table("parcelas_acordo").delete().eq("id", id_del).execute()
                for idx, row in mudancas.iterrows():
                    supabase.table("parcelas_acordo").update({"numero_parcela": int(row['numero_parcela']), "valor_parcela": float(row['valor_parcela']), "vencimento": str(row['vencimento']), "status": str(row['status'])}).eq("id", row['id']).execute()
                st.success("Cronograma updated!")
                st.cache_resource.clear()
                st.rerun()

# ===================== 5. SALÁRIOS =====================
elif page == "👥 Salários":
    st.title("👥 Gestão de Custos com Pessoal")
    aba1, aba2, aba3 = st.tabs(["Lançar Folha", "📋 Histórico", "🛠️ Gerenciar (Editar/Excluir)"])
    
    with aba1:
        with st.form("f_folha"):
            s1, s2 = st.columns(2)
            func = s1.text_input("Nome do Colaborador")
            cargo = s2.text_input("Função / Cargo")
            s3, s4, s5 = st.columns(3)
            sal_base = s3.number_input("Salário Base (R$)", min_value=0.00, format="%.2f")
            beneficios = s4.number_input("Benefícios (R$)", min_value=0.00, format="%.2f")
            descontos = s5.number_input("Descontos (R$)", min_value=0.00, format="%.2f")
            mes_ref = st.selectbox("Mês de Referência", ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"])
            
            if st.form_submit_button("📊 Lançar"):
                if func and sal_base > 0:
                    save_to_db("folha_pagamento", {"funcionario": func, "funcao": cargo, "salario_base": float(sal_base), "beneficios": float(beneficios), "descontos": float(descontos), "mes_referencia": mes_ref})
                    st.success("Folha consolidada!")
                    st.rerun()

    with aba2:
        df = load_data("folha_pagamento")
        if not df.empty:
            df_vis = df.copy()
            df_vis['Custo Total'] = df_vis['salario_base'] + df_vis['beneficios'] - df_vis['descontos']
            for col in ['salario_base', 'beneficios', 'descontos', 'Custo Total']:
                df_vis[col] = df_vis[col].apply(formatar_moeda_br)
            st.dataframe(df_vis[['funcionario', 'funcao', 'mes_referencia', 'salario_base', 'beneficios', 'descontos', 'Custo Total']], use_container_width=True, hide_index=True)
        else: st.info("Nenhum registro lançado.")

    with aba3:
        df_ger = load_data("folha_pagamento")
        if not df_ger.empty:
            # Configuração no padrão Excel Brasil para todas as colunas de valor da Folha
            mudancas = st.data_editor(
                df_ger, 
                use_container_width=True, 
                num_rows="dynamic", 
                hide_index=True, 
                key="edit_sl",
                column_config={
                    "salario_base": st.column_config.NumberColumn("Salário Base (R$)", format="R$ %.2f"),
                    "beneficios": st.column_config.NumberColumn("Benefícios (R$)", format="R$ %.2f"),
                    "descontos": st.column_config.NumberColumn("Descontos (R$)", format="R$ %.2f")
                }
            )
            if st.button("💾 Sincronizar Folha"):
                id_tela = mudancas['id'].tolist() if 'id' in mudancas.columns else []
                for id_del in [x for x in df_ger['id'].tolist() if x not in id_tela]:
                    supabase.table("folha_pagamento").delete().eq("id", id_del).execute()
                for idx, row in mudancas.iterrows():
                    supabase.table("folha_pagamento").update({"funcionario": str(row['funcionario']), "funcao": str(row['funcao']), "salario_base": float(row['salario_base']), "beneficios": float(row['beneficios']), "descontos": float(row['descontos']), "mes_referencia": str(row['mes_referencia'])}).eq("id", row['id']).execute()
                st.success("Registros atualizados!")
                st.cache_resource.clear()
                st.rerun()
