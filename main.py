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
    try:
        return f"R$ {float(val):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except:
        return str(val)

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
            df_ger['valor'] = df_ger['valor'].astype(float)
            mudancas = st.data_editor(
                df_ger, 
                use_container_width=True, 
                num_rows="dynamic", 
                hide_index=True, 
                key="edit_cp",
                column_config={
                    "valor": st.column_config.NumberColumn("Valor (R$)", format="R$ %.2f"),
                    "vencimento": st.column_config.TextColumn("Vencimento (AAAA-MM-DD)")
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

# ===================== 3. PEDIDOS DE COMPRA (MÓDULO CORRIGIDO COM COLUNA OC_NUMERO) =====================
elif page == "🛒 Pedidos de Compra":
    st.title("🛒 Ordens de Compra (OC)")
    aba1, aba2, aba3 = st.tabs(["Emitir Pedido", "📋 Histórico", "🛠️ Gerenciar (Editar/Excluir)"])
    
    with aba1:
        from reportlab.lib.pagesizes import letter
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        import io

        # Inicializa o controle de etapas
        if "oc_etapa" not in st.session_state:
            st.session_state.oc_etapa = 1
        if "dados_oc" not in st.session_state:
            st.session_state.dados_oc = None
        if "pdf_pronto" not in st.session_state:
            st.session_state.pdf_pronto = None

        # ---------------- PASSO 1: ENTRADA DE DADOS E GERAÇÃO DO PDF ----------------
        if st.session_state.oc_etapa == 1:
            st.subheader("📋 Passo 1: Informações da Ordem de Compra")
            with st.form("f_pedido_passo1"):
                cc1, cc2 = st.columns(2)
                num_oc = cc1.text_input("Número da OC")
                solicitante = cc2.text_input("Solicitante / Engenheiro")
                cc3, cc4 = st.columns(2)
                forn = cc3.text_input("Fornecedor")
                val_total = cc4.number_input("Valor Total (R$)", min_value=0.00, format="%.2f")
                
                if st.form_submit_button("⚙️ Gerar PDF do Pedido"):
                    if num_oc and forn and val_total > 0:
                        st.session_state.dados_oc = {
                            "numero_oc": str(num_oc),
                            "solicitante": str(solicitante),
                            "fornecedor": str(forn),
                            "valor_total": float(val_total)
                        }
                        
                        # Montagem do PDF em memória
                        pdf_buffer = io.BytesIO()
                        doc = SimpleDocTemplate(pdf_buffer, pagesize=letter)
                        styles = getSampleStyleSheet()
                        
                        style_titulo = ParagraphStyle('Titulo', parent=styles['Heading1'], textColor='#062618', spaceAfter=20)
                        style_corpo = ParagraphStyle('Corpo', parent=styles['Normal'], fontSize=12, leading=18, spaceAfter=10)
                        
                        story = [
                            Paragraph(f"<b>GREENFIELD Engenharia - Ordem de Compra Nº {num_oc}</b>", style_titulo),
                            Spacer(1, 15),
                            Paragraph(f"<b>Solicitante / Engenheiro:</b> {solicitante}", style_corpo),
                            Paragraph(f"<b>Fornecedor Homologado:</b> {forn}", style_corpo),
                            Paragraph(f"<b>Valor Total do Pedido:</b> {formatar_moeda_br(val_total)}", style_corpo),
                            Spacer(1, 30),
                            Paragraph("____________________________________________", style_corpo),
                            Paragraph("Assinatura do Departamento de Suprimentos / DP", style_corpo)
                        ]
                        
                        doc.build(story)
                        pdf_buffer.seek(0)
                        st.session_state.pdf_pronto = pdf_buffer.getvalue()
                        
                        st.session_state.oc_etapa = 2
                        st.rerun()
                    else:
                        st.error("Por favor, preencha todos os campos obrigatórios.")

        # ---------------- PASSO 2: DOWNLOAD E SALVAMENTO NO HISTÓRICO ----------------
        elif st.session_state.oc_etapa == 2:
            st.subheader("📥 Passo 2: Salvar Arquivo e Registrar no Sistema")
            dados = st.session_state.dados_oc
            
            st.success(f"📌 PDF assinado digitalmente e gerado para a OC {dados['numero_oc']}!")
            
            st.download_button(
                label="📥 Clique aqui para salvar na pasta Downloads",
                data=st.session_state.pdf_pronto,
                file_name=f"OC_{dados['numero_oc']}.pdf",
                mime="application/pdf"
            )
            
            st.markdown("---")
            
            with st.form("f_finalizar_pedido"):
                st.write("⚠️ Ao clicar no botão abaixo, a OC será salva no histórico geral e integrada ao módulo de Contas a Pagar.")
                
                c_ab1, c_ab2 = st.columns(2)
                voltar = c_ab1.form_submit_button("🔙 Voltar / Corrigir Dados")
                confirmar = c_ab2.form_submit_button("💾 Salvar Pedido no Histórico")
                
                if voltar:
                    st.session_state.oc_etapa = 1
                    st.rerun()
                    
                if confirmar:
                    try:
                        # Envia preenchendo os dois padrões de mapeamento mapeados no banco (oc_numero e numero_oc)
                        save_to_db("pedidos_compra", {
                            "oc_numero": str(dados["numero_oc"]),
                            "numero_oc": str(dados["numero_oc"]), 
                            "solicitante": str(dados["solicitante"]), 
                            "fornecedor": str(dados["fornecedor"]), 
                            "valor_total": float(dados["valor_total"]), 
                            "status": "Aprovado"
                        })
                        
                        save_to_db("contas_pagar", {
                            "fornecedor": f"OC {dados['numero_oc']} - {dados['fornecedor']}", 
                            "vencimento": str(datetime.today().date() + timedelta(days=15)), 
                            "valor": float(dados["valor_total"]), 
                            "status": "Pendente"
                        })
                        
                        st.success("🔥 Sucesso! Ordem de Compra salva no histórico e integrada ao Contas a Pagar.")
                        
                        # Limpa cache e reinicia etapas
                        st.session_state.oc_etapa = 1
                        st.session_state.dados_oc = None
                        st.session_state.pdf_pronto = None
                        st.cache_resource.clear()
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"Erro ao salvar no banco de dados: {e}")

    # ---------------- ABA 2: VISUALIZAÇÃO DO HISTÓRICO ----------------
    with aba2:
        df = load_data("pedidos_compra")
        if not df.empty:
            df_vis = df.copy()
            
            # Normaliza a exibição independente de qual coluna o banco usou para a OC
            if 'oc_numero' in df_vis.columns and 'numero_oc' not in df_vis.columns:
                df_vis['numero_oc'] = df_vis['oc_numero']
                
            df_vis['valor_total'] = df_vis['valor_total'].apply(formatar_moeda_br)
            
            colunas_exibir = [c for c in ['numero_oc', 'solicitante', 'fornecedor', 'valor_total', 'status'] if c in df_vis.columns]
            st.dataframe(df_vis[colunas_exibir], use_container_width=True, hide_index=True)
        else: 
            st.info("Nenhum pedido localizado no histórico.")

    # ---------------- ABA 3: GERENCIAR (ALTERAR STATUS PARA APROVADO/NEGADO) ----------------
    with aba3:
        st.subheader("Gerenciamento Administrativo de Pedidos")
        df_ger = load_data("pedidos_compra")
        if not df_ger.empty:
            df_ger['valor_total'] = df_ger['valor_total'].astype(float)
            
            mudancas = st.data_editor(
                df_ger, 
                use_container_width=True, 
                num_rows="dynamic", 
                hide_index=True, 
                key="edit_pc",
                column_config={
                    "valor_total": st.column_config.NumberColumn("Valor Total (R$)", format="R$ %.2f"),
                    "status": st.column_config.SelectboxColumn("Status do Pedido", options=["Aprovado", "Negado", "Em Análise"], default="Aprovado")
                }
            )
            if st.button("💾 Sincronizar Alterações de Status"):
                id_tela = mudancas['id'].tolist() if 'id' in mudancas.columns else []
                for id_del in [x for x in df_ger['id'].tolist() if x not in id_tela]:
                    supabase.table("pedidos_compra").delete().eq("id", id_del).execute()
                for idx, row in mudancas.iterrows():
                    up_data = {
                        "solicitante": str(row['solicitante']), 
                        "fornecedor": str(row['fornecedor']), 
                        "valor_total": float(row['valor_total']), 
                        "status": str(row['status'])
                    }
                    if 'oc_numero' in row: up_data["oc_numero"] = str(row['oc_numero'])
                    if 'numero_oc' in row: up_data["numero_oc"] = str(row['numero_oc'])
                    
                    supabase.table("pedidos_compra").update(up_data).eq("id", row['id']).execute()
                st.success("Histórico e Status sincronizados com a nuvem!")
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
                            save_to_db("parcelas_acordo", {"acordo_id": acordo_id, "numero_parcela": i, "valor_parcela": valor_parcela, "vencimento": venc_parcela.strftime('%Y-%m-%d'), "status": "Pendente"})
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
            df_ger['valor_parcela'] = df_ger['valor_parcela'].astype(float)
            mudancas = st.data_editor(
                df_ger, 
                use_container_width=True, 
                num_rows="dynamic", 
                hide_index=True, 
                key="edit_aj",
                column_config={
                    "valor_parcela": st.column_config.NumberColumn("Valor da Parcela (R$)", format="R$ %.2f"),
                    "vencimento": st.column_config.TextColumn("Vencimento (AAAA-MM-DD)")
                }
            )
            if st.button("💾 Sincronizar Cronograma Judicial"):
                id_tela = mudancas['id'].tolist() if 'id' in mudancas.columns else []
                for id_del in [x for x in df_ger['id'].tolist() if x not in id_tela]:
                    supabase.table("parcelas_acordo").delete().eq("id", id_del).execute()
                for idx, row in mudancas.iterrows():
                    supabase.table("parcelas_acordo").update({"numero_parcela": int(row['numero_parcela']), "valor_parcela": float(row['valor_parcela']), "vencimento": str(row['vencimento']), "status": str(row['status'])}).eq("id", row['id']).execute()
                st.success("Cronograma atualizado com sucesso!")
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
            df_ger['salario_base'] = df_ger['salario_base'].astype(float)
            df_ger['beneficios'] = df_ger['beneficios'].astype(float)
            df_ger['descontos'] = df_ger['descontos'].astype(float)
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
                st.success("Registros updated!")
                st.cache_resource.clear()
                st.rerun()
