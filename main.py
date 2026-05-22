import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from supabase import create_client, Client
import os
import plotly.express as px
import io
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

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
        
        [data-testid="stSidebar"] div.stDownloadButton > button {
            background-color: #0b4d32 !important;
            color: #ffffff !important;
            border: 1px solid #1e7e54 !important;
            border-radius: 6px !important;
            width: 100% !important;
            font-weight: 600 !important;
        }
        
        h1 { font-size: 24px !important; font-weight: 700 !important; }
        h2 { font-size: 20px !important; font-weight: 600 !important; }
        
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
saldo_projetado_caixa = df_medicoes_global['valor'].astype(float).sum() if not df_medicoes_global.empty and 'valor' in df_medicoes_global.columns else 0.00

# ===================== SIDEBAR CONTROLE DE ACESSO =====================
with st.sidebar:
    st.sidebar.markdown("# 💹 Greenfield")
    st.markdown("### ERP FINANCEIRO CORPORATIVO")
    st.markdown("---")
    
    senha = st.text_input("Chave de Acesso", type="password")
    
    if senha == "compras123":
        paginas_disponiveis = ["🛒 Pedidos de Compra"]
        st.sidebar.success("Acesso: Módulo Compras")
    elif senha == "admin789":
        paginas_disponiveis = ["📊 Dashboard", "💳 Contas a Pagar & Caixa", "🛒 Pedidos de Compra", "⚖️ Acordos Judiciais", "👥 Salários"]
        st.sidebar.success("Acesso: Administrador")
    else:
        paginas_disponiveis = []
        if senha != "": st.sidebar.error("Senha incorreta!")

    if paginas_disponiveis:
        page = st.radio("Navegação", paginas_disponiveis)
    else:
        st.info("🔒 Insira uma chave de acesso válida.")
        page = None

if page is not None:

    # ===================== 1. DASHBOARD PRINCIPAL DINÂMICO =====================
    if page == "📊 Dashboard":
        st.title("📊 Dashboard Executivo Real-Time")
        
        df_contas = load_data("contas_pagar")
        df_pedidos = load_data("pedidos_compra")
        df_parcelas = load_data("parcelas_acordo")
        
        val_contas = df_contas['valor'].astype(float).sum() if not df_contas.empty and 'valor' in df_contas.columns else 0.0
        
        if not df_pedidos.empty:
            col_valor_pc = 'valor' if 'valor' in df_pedidos.columns else ('valor_total' if 'valor_total' in df_pedidos.columns else None)
            val_pedidos = df_pedidos[col_valor_pc].astype(float).sum() if col_valor_pc else 0.0
        else:
            val_pedidos = 0.0
            
        val_judiciais = df_parcelas['valor_parcela'].astype(float).sum() if not df_parcelas.empty and 'valor_parcela' in df_parcelas.columns else 0.0
        
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Saldo Projetado em Caixa", formatar_moeda_br(saldo_projetado_caixa))
        c2.metric("Total Contas a Pagar", formatar_moeda_br(val_contas))
        c3.metric("Total Pedidos / OS", formatar_moeda_br(val_pedidos))
        c4.metric("Total Acordos (Parcelas)", formatar_moeda_br(val_judiciais))
        
        st.markdown("---")
        g1, g2 = st.columns(2)
        
        with g1:
            if not df_contas.empty and 'status' in df_contas.columns:
                df_contas['valor'] = df_contas['valor'].astype(float)
                fig1 = px.pie(df_contas, values='valor', names='status', title="Situação do Contas a Pagar", hole=0.4, color_discrete_sequence=['#0b4d32', '#c94c4c', '#e6b800'])
                st.plotly_chart(fig1, use_container_width=True)
                
        with g2:
            if not df_pedidos.empty:
                col_val_grafico = 'valor' if 'valor' in df_pedidos.columns else 'valor_total'
                df_pedidos[col_val_grafico] = df_pedidos[col_val_grafico].astype(float)
                eixo_x = 'solicitante' if 'solicitante' in df_pedidos.columns else 'fornecedor'
                fig2 = px.bar(df_pedidos, x=eixo_x, y=col_val_grafico, title="Compras/Serviços por Responsável (R$)", color_discrete_sequence=['#0b4d32'])
                st.plotly_chart(fig2, use_container_width=True)

    # ===================== 2. CONTAS A PAGAR & GESTÃO DE CAIXA =====================
    elif page == "💳 Contas a Pagar & Caixa":
        st.title("💳 Contas a Pagar & Controle de Caixa")
        
        # Correção 2: Abas alinhadas com o pedido original
        aba_caixa, aba_lancar, aba_gerenciar = st.tabs(["📊 Saldo & Medições", "📋 Lançar Nova Conta", "🛠️ Gerenciar Contas"])
        
        with aba_caixa:
            st.subheader("Saldo Projetado de Caixa")
            st.metric(label="Saldo Atual Acumulado", value=formatar_moeda_br(saldo_projetado_caixa))
            
            st.markdown("---")
            st.subheader("📈 Registrar Nova Medição")
            with st.form("f_nova_medicao"):
                cc1, cc2, cc3 = st.columns(3)
                nova_ordem = cc1.text_input("Identificador da Medição")
                novo_valor = cc2.number_input("Valor Recebido (R$)", min_value=0.00, format="%.2f")
                nova_data = cc3.date_input("Data da Medição", value=datetime.today().date())
                
                if st.form_submit_button("🚀 Inserir Medição"):
                    if nova_ordem and novo_valor > 0:
                        save_to_db("medicoes_caixa", {"ordem": str(nova_ordem), "valor": float(novo_valor), "data_medicao": str(nova_data)})
                        st.success("Saldo atualizado!")
                        st.cache_resource.clear()
                        st.rerun()

        with aba_lancar:
            st.subheader("Cadastrar Despesa / Contas a Pagar")
            with st.form("f_contas"):
                c1, c2 = st.columns(2)
                forn = c1.text_input("Fornecedor / Despesa")
                valor = c2.number_input("Valor da Conta (R$)", min_value=0.00, format="%.2f")
                c3, c4 = st.columns(2)
                venc = c3.date_input("Data de Vencimento", value=datetime.today().date())
                status_c = c4.selectbox("Status de Pagamento", ["Pendente", "Pago", "Atrasado"])
                
                if st.form_submit_button("💾 Salvar Conta"):
                    if forn and valor > 0:
                        save_to_db("contas_pagar", {"fornecedor": forn, "valor": float(valor), "vencimento": str(venc), "status": status_c})
                        st.success("Conta provisionada!")
                        st.cache_resource.clear()
                        st.rerun()

        with aba_gerenciar:
            st.subheader("Gerenciamento Geral de Títulos (Gerenciar Contas)")
            df_contas_ger = load_data("contas_pagar")
            if not df_contas_ger.empty:
                df_contas_ger['valor'] = df_contas_ger['valor'].astype(float)
                df_contas_exibir = df_contas_ger.copy()
                if 'vencimento' in df_contas_exibir.columns:
                    df_contas_exibir['vencimento'] = pd.to_datetime(df_contas_exibir['vencimento']).dt.date

                mudancas_cp = st.data_editor(
                    df_contas_exibir, use_container_width=True, num_rows="dynamic", hide_index=True, key="edit_cp_geral",
                    column_config={
                        "valor": st.column_config.NumberColumn("Valor (R$)", format="R$ %.2f"),
                        "vencimento": st.column_config.DateColumn("Vencimento", format="DD/MM/YYYY"),
                        "status": st.column_config.SelectboxColumn("Status", options=["Pendente", "Pago", "Atrasado"])
                    }
                )
                if st.button("💾 Sincronizar Títulos Financeiros"):
                    id_tela = mudancas_cp['id'].tolist() if 'id' in mudancas_cp.columns else []
                    for id_del in [x for x in df_contas_ger['id'].tolist() if x not in id_tela]:
                        supabase.table("contas_pagar").delete().eq("id", id_del).execute()
                    for idx, row in mudancas_cp.iterrows():
                        supabase.table("contas_pagar").update({"fornecedor": str(row['fornecedor']), "valor": float(row['valor']), "vencimento": str(row['vencimento']), "status": str(row['status'])}).eq("id", row['id']).execute()
                    st.success("Tabela financeira sincronizada!")
                    st.cache_resource.clear()
                    st.rerun()

    # ===================== 3. PEDIDOS DE COMPRA & ORDEM DE SERVIÇO =====================
    elif page == "🛒 Pedidos de Compra":
        st.title("🛒 Ordens de Compra / Serviço (OC/OS)")
        
        aba1, aba2, aba3 = st.tabs(["Emitir Pedido/Ordem", "📋 Histórico Integrado", "🛠️ Gerenciar (Editar/Excluir)"])
        
        with aba1:
            if "oc_etapa" not in st.session_state: st.session_state.oc_etapa = 1
            if "dados_oc" not in st.session_state: st.session_state.dados_oc = None
            if "pdf_pronto" not in st.session_state: st.session_state.pdf_pronto = None

            if st.session_state.oc_etapa == 1:
                st.subheader("📋 Passo 1: Informações da Ordem de Compra / Serviço")
                with st.form("f_pedido_passo1"):
                    cc1, cc2 = st.columns(2)
                    num_oc = cc1.text_input("Número da OC / OS")
                    solicitante = cc2.text_input("Solicitante / Engenheiro / Setor")
                    
                    cc3, cc4 = st.columns(2)
                    forn = cc3.text_input("Fornecedor / Prestador de Serviço")
                    val_total = cc4.number_input("Valor Total (R$)", min_value=0.00, format="%.2f")
                    
                    obs = st.text_area("Observações / Escopo do Serviço")
                    
                    if st.form_submit_button("⚙️ Gerar PDF da Ordem"):
                        if num_oc and forn and val_total > 0:
                            st.session_state.dados_oc = {
                                "oc_numero": str(num_oc), 
                                "solicitante": str(solicitante), 
                                "fornecedor": str(forn), 
                                "valor": float(val_total),
                                "observacoes": str(obs)
                            }
                            
                            pdf_buffer = io.BytesIO()
                            doc = SimpleDocTemplate(pdf_buffer, pagesize=letter)
                            styles = getSampleStyleSheet()
                            style_titulo = ParagraphStyle('Titulo', parent=styles['Heading1'], textColor='#062618', spaceAfter=20)
                            style_corpo = ParagraphStyle('Corpo', parent=styles['Normal'], fontSize=12, leading=18, spaceAfter=10)
                            
                            story = [
                                Paragraph("<b>GREENFIELD Engenharia - Ordem de Compra e Serviço (OC/OS)</b>", style_titulo),
                                Spacer(1, 15),
                                Paragraph(f"<b>Identificador N°:</b> {num_oc}", style_corpo),
                                Paragraph(f"<b>Solicitante / Engenheiro Responsável:</b> {solicitante}", style_corpo),
                                Paragraph(f"<b>Fornecedor / Prestador:</b> {forn}", style_corpo),
                                Paragraph(f"<b>Valor Total:</b> {formatar_moeda_br(val_total)}", style_corpo),
                            ]
                            if obs:
                                story.append(Paragraph(f"<b>Escopo / Observações:</b> {obs}", style_corpo))
                            
                            doc.build(story)
                            pdf_buffer.seek(0)
                            st.session_state.pdf_pronto = pdf_buffer.getvalue()
                            st.session_state.oc_etapa = 2
                            st.rerun()

            elif st.session_state.oc_etapa == 2:
                st.subheader("📥 Passo 2: Salvar Arquivo e Registrar no Sistema")
                dados = st.session_state.dados_oc
                st.success(f"📌 Documento PDF da Ordem {dados['oc_numero']} gerado!")
                st.download_button(label="📥 Baixar Documento PDF", data=st.session_state.pdf_pronto, file_name=f"Ordem_{dados['oc_numero']}.pdf", mime="application/pdf")
                
                c_ab1, c_ab2 = st.columns(2)
                if c_ab1.button("🔙 Voltar / Corrigir Dados"):
                    st.session_state.oc_etapa = 1
                    st.rerun()
                    
                if c_ab2.button("💾 Salvar Ordem no Histórico"):
                    # Correção Crítica de Alimentação no Banco: Mapeamento de 'valor' explícito
                    save_to_db("pedidos_compra", {
                        "oc_numero": str(dados["oc_numero"]), 
                        "solicitante": str(dados["solicitante"]), 
                        "fornecedor": str(dados["fornecedor"]), 
                        "valor": float(dados["valor"]), 
                        "status": "Aprovado",
                        "observacoes": str(dados.get("observacoes", ""))
                    })
                    save_to_db("contas_pagar", {
                        "fornecedor": f"OC {dados['oc_numero']} - {dados['fornecedor']}", 
                        "vencimento": str(datetime.today().date() + timedelta(days=15)), 
                        "valor": float(dados["valor"]), 
                        "status": "Pendente"
                    })
                    st.success("🎉 Processo concluído com sucesso!")
                    st.session_state.oc_etapa = 1
                    st.session_state.dados_oc = None
                    st.session_state.pdf_pronto = None
                    st.cache_resource.clear()
                    st.rerun()

        with aba2:
            st.subheader("📋 Histórico Geral de Pedidos & Ordens")
            df = load_data("pedidos_compra")
            if df is not None and not df.empty:
                df_vis = df.copy()
                col_valor = 'valor' if 'valor' in df_vis.columns else 'valor_total'
                df_vis['valor_total_formatado'] = df_vis[col_valor].apply(formatar_moeda_br)
                
                df_vis = df_vis.rename(columns={'oc_numero': 'Nº da OC/OS', 'solicitante': 'Solicitante', 'fornecedor': 'Fornecedor', 'valor_total_formatado': 'Valor Alocado', 'status': 'Status', 'observacoes': 'Observações'})
                st.dataframe(df_vis[[c for c in ['Nº da OC/OS', 'Solicitante', 'Fornecedor', 'Valor Alocado', 'Status', 'Observações'] if c in df_vis.columns]], use_container_width=True, hide_index=True)
            else:
                st.info("Nenhuma ordem cadastrada no histórico do Supabase.")

        with aba3:
            st.subheader("🛠️ Gerenciar Ordens de Compra e Serviço")
            df_ger = load_data("pedidos_compra")
            
            if not df_ger.empty:
                if 'valor_total' in df_ger.columns and 'valor' not in df_ger.columns:
                    df_ger = df_ger.rename(columns={'valor_total': 'valor'})
                
                df_ger['valor'] = df_ger['valor'].astype(float) if 'valor' in df_ger.columns else 0.0
                colunas_finais_editor = ["id", "oc_numero", "solicitante", "fornecedor", "valor", "status", "observacoes"]
                df_ger_filtrado = df_ger[[c for c in colunas_finais_editor if c in df_ger.columns]]

                mudancas = st.data_editor(
                    df_ger_filtrado, 
                    use_container_width=True, 
                    num_rows="dynamic", 
                    hide_index=True, 
                    key="edit_pc_v4", 
                    column_config={
                        "id": st.column_config.NumberColumn("ID Interno", disabled=True),
                        "valor": st.column_config.NumberColumn("Valor Total (R$)", format="R$ %.2f"), 
                        "status": st.column_config.SelectboxColumn("Status", options=["Aprovado", "Negado", "Em Análise"])
                    }
                )
                
                if st.button("💾 Sincronizar e Salvar Alterações"):
                    try:
                        ids_originais = set(df_ger['id'].dropna().tolist()) if 'id' in df_ger.columns else set()
                        ids_finais = set(mudancas['id'].dropna().tolist()) if 'id' in mudancas.columns else set()
                        ids_deletados = ids_originais - ids_finais
                        
                        if ids_deletados:
                            for id_del in ids_deletados: 
                                supabase.table("pedidos_compra").delete().eq("id", id_del).execute()
                        
                        for idx, row in mudancas.iterrows():
                            dados_linha = {
                                "oc_numero": str(row['oc_numero']) if pd.notna(row.get('oc_numero')) else "",
                                "solicitante": str(row['solicitante']) if pd.notna(row.get('solicitante')) else "", 
                                "fornecedor": str(row['fornecedor']) if pd.notna(row.get('fornecedor')) else "", 
                                "valor": float(row['valor']) if pd.notna(row.get('valor')) else 0.0, 
                                "status": str(row['status']) if pd.notna(row.get('status')) else "Em Análise", 
                                "observacoes": str(row['observacoes']) if pd.notna(row.get('observacoes')) else ""
                            }
                            if 'id' in row and pd.notna(row['id']) and row['id'] in ids_originais:
                                supabase.table("pedidos_compra").update(dados_linha).eq("id", row['id']).execute()
                            else:
                                supabase.table("pedidos_compra").insert(dados_linha).execute()
                 
                        st.success("Banco de dados sincronizado com sucesso!")
                        st.cache_resource.clear()
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro: {e}")

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
                data_ini = j5.date_input("Vencimento da 1ª Parcela", value=datetime.today())
                
                if st.form_submit_button("🤝 Gerar Acordo e Cronograma"):
                    if proc and rec and val_total > 0:
                        acordo = save_to_db("acordos_judiciais", {"processo": proc, "reclamante": rec, "valor_total": float(val_total), "qtd_parcelas": int(qtd_parc), "status": "Em andamento"})
                        if acordo:
                            acordo_id = acordo[0]['id']
                            valor_parcela = float(val_total) / int(qtd_parc)
                            for i in range(1, int(qtd_parc) + 1):
                                venc_parcela = data_ini + timedelta(days=(i-1)*30)
                                save_to_db("parcelas_acordo", {"acordo_id": acuerdo_id if 'acuerdo_id' in locals() else acordo_id, "numero_parcela": i, "valor_parcela": valor_parcela, "vencimento": venc_parcela.strftime('%Y-%m-%d'), "status_parc": "Pendente"})
                            st.success("✅ Acordo firmado!")
                            st.cache_resource.clear()
                            st.rerun()

        with aba2:
            df_parc = load_data("parcelas_acordo")
            df_acod = load_data("acordos_judiciais")
            if not df_parc.empty and not df_acod.empty:
                df_mestre = pd.merge(df_parc, df_acod, left_on="acordo_id", right_on="id")
                df_mestre['valor_parcela'] = df_mestre['valor_parcela'].apply(formatar_moeda_br)
                df_mestre['vencimento'] = df_mestre['vencimento'].apply(formatar_data_br)
                st.dataframe(df_mestre[['processo', 'reclamante', 'numero_parcela', 'valor_parcela', 'vencimento', 'status_parc']], use_container_width=True, hide_index=True)

        with aba3:
            df_ger = load_data("parcelas_acordo")
            if not df_ger.empty:
                df_ger['valor_parcela'] = df_ger['valor_parcela'].astype(float)
                df_ger_exibir = df_ger.copy()
                if 'vencimento' in df_ger_exibir.columns: df_ger_exibir['vencimento'] = pd.to_datetime(df_ger_exibir['vencimento']).dt.date
                mudancas = st.data_editor(df_ger_exibir, use_container_width=True, num_rows="dynamic", hide_index=True, key="edit_aj")
                if st.button("💾 Sincronizar Cronograma"):
                    id_tela = mudancas['id'].tolist() if 'id' in mudancas.columns else []
                    for id_del in [x for x in df_ger['id'].tolist() if x not in id_tela]: supabase.table("parcelas_acordo").delete().eq("id", id_del).execute()
                    for idx, row in mudancas.iterrows(): supabase.table("parcelas_acordo").update({"numero_parcela": int(row['numero_parcela']), "valor_parcela": float(row['valor_parcela']), "vencimento": str(row['vencimento']), "status_parc": str(row['status_parc'])}).eq("id", row['id']).execute()
                    st.success("Atualizado!")
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
                cargo = s2.text_input("Função")
                s3, s4, s5 = st.columns(3)
                sal_base = s3.number_input("Salário Base (R$)", min_value=0.00, format="%.2f")
                beneficios = s4.number_input("Benefícios", min_value=0.00, format="%.2f")
                descontos = s5.number_input("Descontos", min_value=0.00, format="%.2f")
                mes_ref = st.selectbox("Mês de Referência", ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"])
                
                if st.form_submit_button("📊 Lançar"):
                    if func and sal_base > 0:
                        custo_liquido_folha = float(sal_base) + float(beneficios) - float(descontos)
                        save_to_db("folha_pagamento", {"funcionario": func, "funcao": cargo, "salario_base": float(sal_base), "beneficios": float(beneficios), "descontos": float(descontos), "mes_referencia": mes_ref})
                        save_to_db("contas_pagar", {"fornecedor": f"Folha - {mes_ref} ({func})", "valor": custo_liquido_folha, "vencimento": str(calcular_quinto_dia_util_mes_seguinte()), "status": "Pendente"})
                        st.success("Folha provisionada!")
                        st.cache_resource.clear()
                        st.rerun()

        with aba2:
            df = load_data("folha_pagamento")
            if not df.empty:
                df_vis = df.copy()
                df_vis['Custo Total'] = df_vis['salario_base'] + df_vis['beneficios'] - df_vis['descontos']
                for col in ['salario_base', 'beneficios', 'descontos', 'Custo Total']: df_vis[col] = df_vis[col].apply(formatar_moeda_br)
                st.dataframe(df_vis[['funcionario', 'funcao', 'mes_referencia', 'salario_base', 'beneficios', 'descontos', 'Custo Total']], use_container_width=True, hide_index=True)

        with aba3:
            df_ger = load_data("folha_pagamento")
            if not df_ger.empty:
                df_ger['salario_base'] = df_ger['salario_base'].astype(float)
                df_ger['beneficios'] = df_ger['beneficios'].astype(float)
                df_ger['descontos'] = df_ger['descontos'].astype(float)
                mudancas = st.data_editor(df_ger, use_container_width=True, num_rows="dynamic", hide_index=True, key="edit_sl")
                if st.button("💾 Sincronizar Folha"):
                    id_tela = mudancas['id'].tolist() if 'id' in mudancas.columns else []
                    for id_del in [x for x in df_ger['id'].tolist() if x not in id_tela]: supabase.table("folha_pagamento").delete().eq("id", id_del).execute()
                    for idx, row in mudancas.iterrows():
                        supabase.table("folha_pagamento").update({"funcionario": str(row['funcionario']), "funcao": str(row['funcao']), "salario_base": float(row['salario_base']), "beneficios": float(row['beneficios']), "descontos": float(row['descontos']), "mes_referencia": str(row['mes_referencia'])}).eq("id", row['id']).execute()
                    st.success("Folha atualizada!")
                    st.cache_resource.clear()
                    st.rerun()
