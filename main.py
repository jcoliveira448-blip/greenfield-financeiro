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
        # Teste de conexão básico
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

# Estilização Dark Green Corporativa (CSS Injetado)
st.markdown("""
    <style>
        [data-testid="stSidebar"] {
            background-color: #062618 !important;
        }
        [data-testid="stSidebar"] * {
            color: #ffffff !important;
        }
        .stMetric {
            background-color: #f4f7f5;
            padding: 15px;
            border-radius: 10px;
            border-left: 5px solid #0b4d32;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }
        div.stButton > button:first-child {
            background-color: #0b4d32;
            color: white;
            border-radius: 6px;
        }
    </style>
""", unsafe_allow_html=True)

# ===================== FUNÇÕES DE INTERAÇÃO COM BANCO =====================
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

# ===================== SIDEBAR NAVEGAÇÃO =====================
with st.sidebar:
    st.image("https://via.placeholder.com/150x50/062618/ffffff?text=GREENFIELD", use_container_width=True)
    st.markdown("### ERP CORPORATIVO")
    
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

# ===================== MÓDULOS DO SISTEMA =====================

# 1. DASHBOARD PRINCIPAL
if page == "📊 Dashboard":
    st.title("📊 Dashboard Executivo Premium")
    
    df_contas = load_data("contas_pagar")
    df_acordos = load_data("acordos_judiciais")
    df_pedidos = load_data("pedidos_compra")
    
    # KPIs Superiores
    c1, c2, c3, c4 = st.columns(4)
    
    val_contas = df_contas['valor'].sum() if not df_contas.empty and 'valor' in df_contas.columns else 0.0
    val_acordos = df_acordos['valor_total'].sum() if not df_acordos.empty and 'valor_total' in df_acordos.columns else 0.0
    val_pedidos = df_pedidos['valor_total'].sum() if not df_pedidos.empty and 'valor_total' in df_pedidos.columns else 0.0
    
    c1.metric("Saldo Estimado em Caixa", "R$ 1.250.000,00")
    c2.metric("Total em Contas a Pagar", f"R$ {val_contas:,.2f}")
    c3.metric("Total Acordos Judiciais", f"R$ {val_acordos:,.2f}")
    c4.metric("Total Pedidos de Compra", f"R$ {val_pedidos:,.2f}")
    
    st.markdown("---")
    
    # Gráficos Dinâmicos
    g1, g2 = st.columns(2)
    
    with g1:
        if not df_contas.empty and 'status' in df_contas.columns:
            fig1 = px.pie(df_contas, values='valor', names='status', title="Distribuição de Contas a Pagar", hole=0.4, color_discrete_sequence=['#0b4d32', '#c94c4c', '#e6b800'])
            st.plotly_chart(fig1, use_container_width=True)
        else:
            st.info("Aguardando dados de contas para gráfico.")
            
    with g2:
        if not df_pedidos.empty and 'solicitante' in df_pedidos.columns:
            fig2 = px.bar(df_pedidos, x='solicitante', y='valor_total', title="Volume de Compras por Solicitante", color_discrete_sequence=['#0b4d32'])
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("Aguardando dados de pedidos para gráfico.")

# 2. CONTAS A PAGAR
elif page == "💳 Contas a Pagar":
    st.title("💳 Gestão de Contas a Pagar")
    
    with st.expander("➕ Novo Lançamento Manual", expanded=False):
        with st.form("f_conta"):
            cx1, cx2, cx3 = st.columns(3)
            forn = cx1.text_input("Fornecedor / Favorecido")
            venc = cx2.date_input("Data de Vencimento", value=datetime.today())
            valor = cx3.number_input("Valor do Título (R$)", min_value=0.01, format="%.2f")
            
            if st.form_submit_button("💾 Agendar Pagamento"):
                if forn and valor > 0:
                    save_to_db("contas_pagar", {
                        "fornecedor": forn, "vencimento": str(venc),
                        "valor": float(valor), "status": "Pendente"
                    })
                    st.success("Conta provisionada com sucesso!")
                    st.rerun()

    df = load_data("contas_pagar")
    if not df.empty:
        st.data_editor(df, use_container_width=True, hide_index=True)
    else:
        st.info("Nenhum registro de conta a pagar localizado.")

# 3. PEDIDOS DE COMPRA (ORDENS DE COMPRA)
elif page == "🛒 Pedidos de Compra":
    st.title("🛒 Ordens de Compra (OC)")
    
    with st.expander("📝 Emitir Nova Ordem de Compra", expanded=False):
        with st.form("f_pedido"):
            cc1, cc2 = st.columns(2)
            num_oc = cc1.text_input("Número da OC (Ex: OC-2026-001)")
            solicitante = cc2.text_input("Engenheiro / Solicitante")
            
            cc3, cc4 = st.columns(2)
            forn = cc3.text_input("Fornecedor Vinculado")
            val_total = cc4.number_input("Valor Total da Compra (R$)", min_value=0.00, format="%.2f")
            
            if st.form_submit_button("🚀 Enviar para Aprovação"):
                if num_oc and val_total > 0:
                    # Salva o Pedido
                    save_to_db("pedidos_compra", {
                        "numero_oc": num_oc, "solicitante": solicitante,
                        "fornecedor": forn, "valor_total": float(val_total), "status": "Aberto"
                    })
                    # Integração Automática: Gera provisionamento em contas a pagar
                    save_to_db("contas_pagar", {
                        "fornecedor": f"OC {num_oc} - {forn}",
                        "vencimento": str(datetime.today().date() + timedelta(days=15)), # Prazo padrão 15 dias
                        "valor": float(val_total),
                        "status": "Pendente"
                    })
                    st.success("Pedido emitido e integrado ao Contas a Pagar!")
                    st.rerun()

    df_pedidos = load_data("pedidos_compra")
    if not df_pedidos.empty:
        st.dataframe(df_pedidos, use_container_width=True, hide_index=True)
    else:
        st.info("Nenhum pedido de compra cadastrado.")

# 4. ACORDOS JUDICIAIS (COM CORREÇÃO DE DATA, EDIÇÃO E EXCLUSÃO)
elif page == "⚖️ Acordos Judiciais":
    st.title("⚖️ Controle de Acordos Judiciais")
    
    aba1, aba2, aba3 = st.tabs(["Firmar Novo Acordo", "📊 Histórico de Parcelas", "⚙️ Gerenciar / Excluir"])
    
    with aba1:
        with st.form("f_judicial"):
            j1, j2 = st.columns(2)
            proc = j1.text_input("Número do Processo / Vara")
            rec = j2.text_input("Nome do Reclamante")
            
            j3, j4, j5 = st.columns(3)
            val_total = j3.number_input("Valor Total do Acordo (R$)", min_value=1.00, format="%.2f")
            qtd_parc = j4.number_input("Quantidade de Parcelas", min_value=1, max_value=48, value=1)
            
            # Aqui garantimos que o componente use o padrão local de exibição
            data_ini = j5.date_input("Vencimento da 1ª Parcela", value=datetime.today(), format="DD/MM/YYYY")
            
            if st.form_submit_button("🤝 Gerar Acordo e Cronograma"):
                if proc and rec and val_total > 0:
                    # 1. Salva o acordo principal
                    acordo = save_to_db("acordos_judiciais", {
                        "processo": proc, 
                        "reclamante": rec,
                        "valor_total": float(val_total), 
                        "qtd_parcelas": int(qtd_parc), 
                        "status": "Em andamento"
                    })
                    
                    if acordo:
                        acordo_id = acordo[0]['id']
                        valor_parcela = float(val_total) / int(qtd_parc)
                        
                        erro_parcela = False
                        # 2. Loop de Parcelamento Automático (Salvando no formato que o banco exige YYYY-MM-DD)
                        for i in range(1, int(qtd_parc) + 1):
                            # Adiciona 30 dias para cada parcela subsequente
                            venc_parcela = data_ini + timedelta(days=(i-1)*30)
                            
                            res_parc = save_to_db("parcelas_acordo", {
                                "acordo_id": acordo_id,
                                "numero_parcela": i,
                                "valor_parcela": valor_parcela,
                                "vencimento": venc_parcela.strftime('%Y-%m-%d'), # Formato do Banco
                                "status": "Pendente"
                            })
                            if res_parc is None:
                                erro_parcela = True
                        
                        if not erro_parcela:
                            st.success(f"✅ Acordo firmado com sucesso! {qtd_parc} parcelas geradas.")
                            st.rerun()
                        else:
                            st.warning("O acordo principal foi criado, mas houve uma falha nas parcelas. Verifique o RLS no Supabase.")

    with aba2:
        df_visualizacao = load_data("parcelas_acordo")
        if not df_visualizacao.empty:
            st.subheader("Cronograma Geral de Pagamentos")
            
            # Formata a exibição da data para o usuário como DD/MM/YYYY
            if 'vencimento' in df_visualizacao.columns:
                try:
                    df_visualizacao['vencimento_pt'] = pd.to_datetime(df_visualizacao['vencimento']).dt.strftime('%d/%m/%Y')
                except Exception:
                    df_visualizacao['vencimento_pt'] = df_visualizacao['vencimento']
            
            # Organiza as colunas para exibição limpa
            colunas_exibicao = ['numero_parcela', 'valor_parcela', 'vencimento_pt', 'status']
            colunas_existentes = [c for c in colunas_exibicao if c in df_visualizacao.columns]
            
            st.dataframe(
                df_visualizacao[colunas_existentes].rename(columns={
                    'numero_parcela': 'Parcela',
                    'valor_parcela': 'Valor',
                    'vencimento_pt': 'Vencimento',
                    'status': 'Status'
                }),
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("Nenhuma parcela gerada no sistema ainda.")

    with aba3:
        st.subheader("🛠️ Editar ou Excluir Registros")
        st.markdown("Use esta tabela para alterar o Status, Valores ou **Excluir** linhas selecionando-as e apertando `Delete` no seu teclado.")
        
        df_gerenciar = load_data("parcelas_acordo")
        if not df_gerenciar.empty:
            # O data_editor permite que você clique e edite qualquer campo diretamente na tela!
            mudancas = st.data_editor(
                df_gerenciar,
                use_container_width=True,
                num_rows="dynamic", # Permite que você delete linhas selecionando e apertando Delete
                hide_index=True,
                key="editor_parcelas"
            )
            
            # Botão para salvar as alterações de edição ou exclusão de volta no Supabase
            if st.button("💾 Salvar Alterações / Exclusões"):
                if supabase:
                    try:
                        # Para fins de simplificação na nuvem, reiniciamos a sincronização limpa do que foi alterado
                        # Se você deletou linhas no componente, precisamos deletar no banco.
                        # O jeito mais seguro de sincronizar o estado atual editado na tela:
                        id_na_tela = mudancas['id'].tolist() if 'id' in mudancas.columns else []
                        
                        # Identifica o que foi deletado (o que tinha antes e não está mais na tela)
                        id_originais = df_gerenciar['id'].tolist()
                        deletados = [id_orig_item for id_orig_item in id_originais if id_orig_item not in id_na_tela]
                        
                        # 1. Processa Exclusões no banco
                        for id_del in deletados:
                            supabase.table("parcelas_acordo").delete().eq("id", id_del).execute()
                            
                        # 2. Processa Edições/Atualizações das linhas que ficaram
                        for index, row in mudancas.iterrows():
                            # Atualiza cada linha no Supabase baseando-se no ID dela
                            dados_linha = {
                                "numero_parcela": int(row['numero_parcela']),
                                "valor_parcela": float(row['valor_parcela']),
                                "vencimento": str(row['vencimento']),
                                "status": str(row['status'])
                            }
                            supabase.table("parcelas_acordo").update(dados_linha).eq("id", row['id']).execute()
                            
                        st.success("🔄 Banco de dados atualizado com sucesso!")
                        st.cache_resource.clear()
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao sincronizar edições: {e}")
        else:
            st.info("Nenhum dado disponível para gerenciamento.")
# 5. SALÁRIOS E FOLHA DE PAGAMENTO
elif page == "👥 Salários":
    st.title("👥 Gestão de Custos com Pessoal")
    
    with st.form("f_folha"):
        s1, s2 = st.columns(2)
        func = s1.text_input("Nome do Colaborador")
        func_cargo = s2.text_input("Função / Cargo")
        
        s3, s4, s5 = st.columns(3)
        sal_base = s3.number_input("Salário Base (R$)", min_value=0.00, format="%.2f")
        beneficios = s4.number_input("Benefícios (VT, VR, etc)", min_value=0.00, format="%.2f")
        descontos = s5.number_input("Descontos (INSS, Faltas)", min_value=0.00, format="%.2f")
        
        mes_ref = st.selectbox("Mês de Referência", ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"])
        
        if st.form_submit_button("📊 Lançar na Folha"):
            if func and sal_base > 0:
                save_to_db("folha_pagamento", {
                    "funcionario": func, "funcao": func_cargo,
                    "salario_base": float(sal_base), "beneficios": float(beneficios),
                    "descontos": float(descontos), "mes_referencia": mes_ref
                })
                st.success("Custos de folha consolidados!")
                st.rerun()

    df_folha = load_data("folha_pagamento")
    if not df_folha.empty:
        # Cálculo de Custo Total por Funcionário em tempo real (Pandas)
        df_folha['Custo Total da Empresa'] = df_folha['salario_base'] + df_folha['beneficios'] - df_folha['descontos']
        st.subheader("Análise da Folha de Pagamento")
        st.dataframe(df_folha, use_container_width=True, hide_index=True)
        
        custo_total_folha = df_folha['Custo Total da Empresa'].sum()
        st.info(f"💰 Custo Operacional Total da Folha no período: R$ {custo_total_folha:,.2f}")
    else:
        st.info("Nenhum registro lançado na folha de pagamento.")
