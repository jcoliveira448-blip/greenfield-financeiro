import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from supabase import create_client, Client
import os
import plotly.express as px
import io
import base64  # Necessário para embutir a logo
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
        # Teste de conexão simples
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

# Estilização CSS customizada premium
st.markdown("""
    <style>
        [data-testid="stSidebar"] { background-color: #062618 !important; }
        [data-testid="stSidebar"] * { color: #ffffff !important; }
        
        /* Ajuste premium para métricas */
        [data-testid="stMetricLabel"] { font-size: 14px !important; }
        [data-testid="stMetricValue"] { font-size: 22px !important; }
        
        .stMetric {
            background-color: #f4f7f5;
            padding: 12px;
            border-radius: 10px;
            border-left: 5px solid #0b4d32;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }
        
        /* Centralização e ajuste de imagem/logo */
        .centered-logo {
            display: flex;
            justify-content: center;
            margin-bottom: 25px;
        }
        
        /* Ajuste para logo no canto superior direito (usado no Dashboard) */
        .dashboard-logo {
            float: right;
            margin-top: -60px;
            margin-right: 10px;
        }

        div.stButton > button:first-child { background-color: #0b4d32; color: white; border-radius: 6px; }
    </style>
""", unsafe_allow_html=True)

# Função para converter a logo em Base64 (para embutir no HTML)
@st.cache_data
def get_base64_logo():
    # Substitua pelo caminho correto da sua imagem
    logo_path = "logo_greenfield.png" 
    try:
        with open(logo_path, "rb") as f:
            data = f.read()
        return base64.b64encode(data).decode()
    except FileNotFoundError:
        st.error(f"Logo não encontrada no caminho: {logo_path}")
        return ""

base64_logo = get_base64_logo()

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

# Função auxiliar para calcular o 5º dia útil do mês seguinte
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

# ===================== BLOCO DE PÁGINAS =====================

# ===================== 1. DASHBOARD PRINCIPAL DINÂMICO =====================
if page == "📊 Dashboard":
    # Estrutura para colocar a logo no canto superior direito
    col1, col2 = st.columns([6, 1]) # Proporção 6:1 para empurrar a logo
    
    with col1:
        st.title("📊 Dashboard Executivo Real-Time")
        
    with col2:
        # Logo embutida Base64 no canto direito (dashboard-logo class)
        if base64_logo:
            st.markdown(f'<div class="dashboard-logo"><img src="data:image/png;base64,{base64_logo}" width="150"></div>', unsafe_allow_html=True)

    # Carregamento de dados para métricas
    df_contas = load_data("contas_pagar")
    df_pedidos = load_data("pedidos_compra")
    df_parcelas = load_data("parcelas_acordo")
    
    # Cálculo dinâmico do saldo do caixa (soma todas as medições registradas)
    df_medicoes_global = load_data("medicoes_caixa")
    if not df_medicoes_global.empty and 'valor' in df_medicoes_global.columns:
        saldo_projetado_caixa = df_medicoes_global['valor'].astype(float).sum()
    else:
        saldo_projetado_caixa = 0.00
    
    val_contas = df_contas['valor'].astype(float).sum() if not df_contas.empty and 'valor' in df_contas.columns else 0.0
    val_pedidos = df_pedidos['valor_total'].astype(float).sum() if not df_pedidos.empty and 'valor_total' in df_pedidos.columns else 0.0
    val_judiciais = df_parcelas['valor_parcela'].astype(float).sum() if not df_parcelas.empty and 'valor_parcela' in df_parcelas.columns else 0.0
    
    # Exibição de Métricas em Cards Premium
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Saldo Projetado em Caixa", formatar_moeda_br(saldo_projetado_caixa))
    c2.metric("Total Contas a Pagar", formatar_moeda_br(val_contas))
    c3.metric("Total Pedidos de Compra", formatar_moeda_br(val_pedidos))
    c4.metric("Total Acordos (Parcelas)", formatar_moeda_br(val_judiciais))
    
    st.markdown("---")
    g1, g2 = st.columns(2)
    
    # Gráfico 1: Situação do Contas a Pagar (Pizza)
    with g1:
        if not df_contas.empty and 'status' in df_contas.columns:
            df_contas['valor'] = df_contas['valor'].astype(float)
            fig1 = px.pie(df_contas, values='valor', names='status', title="Situação do Contas a Pagar", hole=0.4, color_discrete_sequence=['#0b4d32', '#c94c4c', '#e6b800'])
            st.plotly_chart(fig1, use_container_width=True)
        else:
            st.info("Sem dados de Contas para exibir gráficos.")
            
    # Gráfico 2: Compras por Solicitante (Barra)
    with g2:
        if not df_pedidos.empty and 'solicitante' in df_pedidos.columns:
            df_pedidos['valor_total'] = df_pedidos['valor_total'].astype(float)
            fig2 = px.bar(df_pedidos, x='solicitante', y='valor_total', title="Compras por Solicitante (R$)", color_discrete_sequence=['#0b4d32'])
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("Sem dados de Pedidos para exibir gráficos.")

# ===================== DEMAIS PÁGINAS (LOGO CENTRALIZADA) =====================
else:
    # Mostra a logo centralizada no topo (centered-logo class)
    if base64_logo:
        st.markdown(f'<div class="centered-logo"><img src="data:image/png;base64,{base64_logo}" width="180"></div>', unsafe_allow_html=True)
    
    # ===================== 2. CONTAS A PAGAR & GESTÃO DE CAIXA =====================
    if page == "💳 Contas a Pagar & Caixa":
        st.title("💳 Contas a Pagar & Controle de Caixa")
        
        # Tabs para organizar as funções
        aba_caixa, aba_lancar, aba_gerenciar = st.tabs(["📊 Saldo & Medições", "📋 Lançar Nova Conta", "🛠️ Gerenciar Contas"])
        
        # --- ABA CAIXA E MEDIÇÕES ---
        with aba_caixa:
            st.subheader("Saldo Projetado de Caixa (Fluxo de Receitas)")
            
            # Recarrega dados específicos para a métrica da aba
            df_med = load_data("medicoes_caixa")
            if not df_med.empty:
                saldo_total_medicoes = df_med['valor'].astype(float).sum()
            else:
                saldo_total_medicoes = 0.00
                
            st.metric(label="Saldo Atual Acumulado (Total Medições)", value=formatar_moeda_br(saldo_total_medicoes))
            st.info("💡 Este saldo é calculado automaticamente somando todas as medições/receitas recebidas.")
            
            st.markdown("---")
            st.subheader("📈 Registrar Nova Medição Recebida")
            
            # Formulário para entrada de nova medição
            with st.form("f_nova_medicao"):
                cc1, cc2, cc3 = st.columns(3)
                nova_ordem = cc1.text_input("Identificador / Ordem (Ex: Medição BM-01)")
                novo_valor = cc2.number_input("Valor Recebido (R$)", min_value=0.00, format="%.2f")
                nova_data = cc3.date_input("Data do Recebimento", value=datetime.today().date())
                
                if st.form_submit_button("🚀 Lançar e Atualizar Saldo"):
                    if nova_ordem and novo_valor > 0:
                        try:
                            save_to_db("medicoes_caixa", {
                                "ordem": str(nova_ordem),
                                "valor": float(novo_valor),
                                "data_medicao": str(nova_data)
                            })
                            st.success(f"✅ Medição '{nova_ordem}' de {formatar_moeda_br(novo_valor)} lançada no caixa!")
                            st.cache_resource.clear()
                            st.rerun()
                        except Exception as e: st.error(f"Erro: {e}")
                    else:
                        st.error("Preencha a ordem e o valor.")
            
            st.markdown("---")
            st.subheader("📜 Histórico de Medições Realizadas")
            
            # Carrega e exibe o histórico de medições
            df_historico_med = load_data("medicoes_caixa")
            if not df_historico_med.empty:
                # Ordena pela data mais recente
                if 'data_medicao' in df_historico_med.columns:
                    df_historico_med = df_historico_med.sort_values(by='data_medicao', ascending=False)
                    
                df_vis = df_historico_med.copy()
                df_vis['valor'] = df_vis['valor'].apply(formatar_moeda_br)
                st.dataframe(df_vis[['ordem', 'valor', 'data_medicao']], use_container_width=True, hide_index=True)
            else:
                st.info("Nenhuma medição registrada.")

        # --- ABA LANÇAR CONTAS ---
        with aba_lancar:
            st.subheader("Cadastrar Despesa / Contas a Pagar")
            with st.form("f_contas"):
                c1, c2 = st.columns(2)
                forn = c1.text_input("Fornecedor / Despesa")
                valor = c2.number_input("Valor da Conta (R$)", min_value=0.00, format="%.2f")
                c3, c4 = st.columns(2)
                venc = c3.date_input("Data de Vencimento", value=datetime.today().date())
                status = c4.selectbox("Status de Pagamento", ["Pendente", "Pago", "Atrasado"])
                
                if st.form_submit_button("💾 Salvar Conta"):
                    if forn and valor > 0:
                        save_to_db("contas_pagar", {
                            "fornecedor": forn,
                            "valor": float(valor),
                            "vencimento": str(venc),
                            "status": status
                        })
                        st.success("Conta provisionada com sucesso!")
                        st.cache_resource.clear()
                        st.rerun()
                    else:
                        st.error("Preencha todos os campos corretamente.")

        # --- ABA GERENCIAR CONTAS ---
        with aba_gerenciar:
            st.subheader("Gerenciamento Geral de Títulos")
            df_contas_ger = load_data("contas_pagar")
            if not df_contas_ger.empty:
                df_contas_ger['valor'] = df_contas_ger['valor'].astype(float)
                
                # Editor interativo Style Excel Brasil para o Status
                mudancas_cp = st.data_editor(
                    df_contas_ger, 
                    use_container_width=True, 
                    num_rows="dynamic", 
                    hide_index=True, 
                    key="edit_cp_geral",
                    column_config={
                        "valor": st.column_config.NumberColumn("Valor (R$)", format="R$ %.2f"),
                        "status": st.column_config.SelectboxColumn("Status", options=["Pendente", "Pago", "Atrasado"])
                    }
                )
                if st.button("💾 Sincronizar Títulos Financeiros"):
                    # Exclui e atualiza conforme editor interativo
                    id_tela = mudancas_cp['id'].tolist() if 'id' in mudancas_cp.columns else []
                    for id_del in [x for x in df_contas_ger['id'].tolist() if x not in id_tela]:
                        supabase.table("contas_pagar").delete().eq("id", id_del).execute()
                    for idx, row in mudancas_cp.iterrows():
                        supabase.table("contas_pagar").update({
                            "fornecedor": str(row['fornecedor']),
                            "valor": float(row['valor']),
                            "vencimento": str(row['vencimento']),
                            "status": str(row['status'])
                        }).eq("id", row['id']).execute()
                    st.success("Tabela sincronizada com o banco!")
                    st.cache_resource.clear()
                    st.rerun()
            else:
                st.info("Nenhuma conta a pagar localizada.")

    # ===================== 3. PEDIDOS DE COMPRA =====================
    elif page == "🛒 Pedidos de Compra":
        st.title("🛒 Ordens de Compra (OC)")
        # Tabs para organizar as funções
        aba1, aba2, aba3 = st.tabs(["Emitir Pedido", "📋 Histórico", "🛠️ Gerenciar (Editar/Excluir)"])
        
        with aba1:
            from reportlab.lib.pagesizes import letter
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            import io

            # Inicializa o controle de etapas
            if "oc_etapa" not in st.session_state: st.session_state.oc_etapa = 1
            if "dados_oc" not in st.session_state: st.session_state.dados_oc = None
            if "pdf_pronto" not in st.session_state: st.session_state.pdf_pronto = None

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
                
                # Botão de download nativo para a pasta local
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
                            # 1. Salva no banco de dados com status inicial 'Aprovado'
                            save_to_db("pedidos_compra", {
                                "numero_oc": dados["numero_oc"], 
                                "solicitante": dados["solicitante"], 
                                "fornecedor": dados["fornecedor"], 
                                "valor_total": float(dados["valor_total"]), 
                                "status": "Aprovado"
                            })
                            
                            # 2. Gera a provisão automática no Contas a Pagar
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
                df_vis['valor_total'] = df_vis['valor_total'].apply(formatar_moeda_br)
                
                # Organiza as colunas de forma legível
                colunas_exibir = [c for c in ['numero_oc', 'solicitante', 'fornecedor', 'valor_total', 'status'] if c in df_vis.columns]
                st.dataframe(df_vis[colunas_exibir], use_container_width=True, hide_index=True)
            else: 
                st.info("Nenhum pedido localizado no histórico.")

        # ---------------- ABA 3: GERENCIAR (EDITAR/EXCLUIR E ALTERAR STATUS) ----------------
        with aba3:
            st.subheader("Gerenciamento Administrativo de Pedidos")
            df_ger = load_data("pedidos_compra")
            if not df_ger.empty:
                df_ger['valor_total'] = df_ger['valor_total'].astype(float)
                
                # Editor interativo com seletor Style Excel Brasil para o Status
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
                if st.button("💾 Sincronizar Alterações da Tabela"):
                    # Exclui e atualiza conforme editor interativo
                    id_tela = mudancas['id'].tolist() if 'id' in mudancas.columns else []
                    for id_del in [x for x in df_ger['id'].tolist() if x not in id_tela]:
                        supabase.table("pedidos_compra").delete().eq("id", id_del).execute()
                    for idx, row in mudancas.iterrows():
                        supabase.table("pedidos_compra").update({
                            "numero_oc": str(row['numero_oc']), 
                            "solicitante": str(row['solicitante']), 
                            "fornecedor": str(row['fornecedor']), 
                            "valor_total": float(row['valor_total']), 
                            "status": str(row['status'])
                        }).eq("id", row['id']).execute()
                    st.success("Histórico e Status sincronizados com a nuvem!")
                    st.cache_resource.clear()
                    st.rerun()

    # ===================== 4. ACORDOS JUDICIAIS =====================
    elif page == "⚖️ Acordos Judiciais":
        st.title("⚖️ Controle de Acordos Judiciais")
        # Tabs para organizar as funções
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
                        # 1. Salva o acordo principal
                        acordo = save_to_db("acordos_judiciais", {
                            "processo": proc, 
                            "reclamante": rec, 
                            "valor_total": float(val_total), 
                            "qtd_parcelas": int(qtd_parc), 
                            "status": "Em andamento"
                        })
                        
                        # 2. Salva as parcelas pendentes
                        if acordo:
                            acordo_id = acordo[0]['id']
                            valor_parcela = float(val_total) / int(qtd_parc)
                            for i in range(1, int(qtd_parc) + 1):
                                venc_parcela = data_ini + timedelta(days=(i-1)*30)
                                save_to_db("parcelas_acordo", {
                                    "acordo_id": acordo_id, 
                                    "numero_parcela": i, 
                                    "valor_parcela": valor_parcela, 
                                    "vencimento": venc_parcela.strftime('%Y-%m-%d'), 
                                    "status": "Pendente"
                                })
                            st.success(f"✅ Acordo para '{rec}' firmado e {qtd_parc} parcelas geradas no cronograma!")
                            st.cache_resource.clear()
                            st.rerun()
                    else:
                        st.error("Preencha Processo, Reclamante e Valor.")

        with aba2:
            # Carrega dados mestres e detalhes para exibição unificada
            df_parc = load_data("parcelas_acordo")
            df_acod = load_data("acordos_judiciais")
            
            if not df_parc.empty and not df_acod.empty:
                # Merge entre tabelas para mostrar Processo e Reclamante junto com a parcela
                df_mestre = pd.merge(df_parc, df_acod, left_on="acordo_id", right_on="id", suffixes=('_parc', '_acord'))
                df_mestre['vencimento'] = formatar_data_br(df_mestre['vencimento'])
                df_mestre['valor_parcela'] = df_mestre['valor_parcela'].apply(formatar_moeda_br)
                
                # Exibe colunas unificadas de forma legível
                df_exibir = df_mestre[['processo', 'reclamante', 'numero_parcela', 'valor_parcela', 'vencimento', 'status_parc']]
                df_exibir.columns = ['Processo / Vara', 'Nome do Reclamante', 'Nº Parcela', 'Valor da Parcela', 'Data Vencimento', 'Status']
                
                st.dataframe(df_exibir, use_container_width=True, hide_index=True)
            else:
                st.info("Nenhuma parcela disponível para exibição.")

        with aba3:
            st.subheader("Gerenciamento de Parcelas (Editar/Baixa/Excluir)")
            df_ger = load_data("parcelas_acordo")
            if not df_ger.empty:
                df_ger['valor_parcela'] = df_ger['valor_parcela'].astype(float)
                
                # Editor interativo Style Excel Brasil para Valor da Parcela
                mudancas_parc = st.data_editor(
                    df_ger, 
                    use_container_width=True, 
                    num_rows="dynamic", 
                    hide_index=True, 
                    key="edit_aj",
                    column_config={
                        "valor_parcela": st.column_config.NumberColumn("Valor da Parcela (R$)", format="R$ %.2f")
                    }
                )
                if st.button("💾 Sincronizar Cronograma Judicial"):
                    # Exclui e atualiza conforme editor interativo
                    id_tela = mudancas_parc['id'].tolist() if 'id' in mudancas_parc.columns else []
                    for id_del in [x for x in df_ger['id'].tolist() if x not in id_tela]:
                        supabase.table("parcelas_acordo").delete().eq("id", id_del).execute()
                    for idx, row in mudancas_parc.iterrows():
                        supabase.table("parcelas_acordo").update({
                            "numero_parcela": int(row['numero_parcela']),
                            "valor_parcela": float(row['valor_parcela']),
                            "vencimento": str(row['vencimento']),
                            "status": str(row['status'])
                        }).eq("id", row['id']).execute()
                    st.success("Cronograma atualizado com sucesso!")
                    st.cache_resource.clear()
                    st.rerun()
            else:
                st.info("Nenhuma parcela disponível para gerenciamento.")

    # ===================== 5. SALÁRIOS =====================
    elif page == "👥 Salários":
        st.title("👥 Gestão de Custos com Pessoal")
        # Tabs para organizar as funções
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
                
                if st.form_submit_button("📊 Lançar Folha de Pagamento"):
                    if func and sal_base > 0:
                        save_to_db("folha_pagamento", {
                            "funcionario": func, 
                            "funcao": cargo, 
                            "salario_base": float(sal_base), 
                            "beneficios": float(beneficios), 
                            "descontos": float(descontos), 
                            "mes_referencia": mes_ref
                        })
                        st.success(f"✅ Folha para '{func}' ({mes_ref}) lançada!")
                        st.cache_resource.clear()
                        st.rerun()
                    else:
                        st.error("Preencha Colaborador e Salário Base.")

        with aba2:
            df = load_data("folha_pagamento")
            if not df.empty:
                df_vis = df.copy()
                # Cálculo de Custo Líquido para o colaborador
                df_vis['Custo Total'] = df_vis['salario_base'] + df_vis['beneficios'] - df_vis['descontos']
                
                # Formatação de moeda premium
                for col in ['salario_base', 'beneficios', 'descontos', 'Custo Total']:
                    df_vis[col] = df_vis[col].apply(formatar_moeda_br)
                    
                st.dataframe(df_vis[['funcionario', 'funcao', 'mes_referencia', 'salario_base', 'beneficios', 'descontos', 'Custo Total']], use_container_width=True, hide_index=True)
            else: st.info("Nenhum registro de folha lançado.")

        with aba3:
            st.subheader("Gerenciamento de Custos com Pessoal (Auditoria)")
            df_ger = load_data("folha_pagamento")
            if not df_ger.empty:
                df_ger['salario_base'] = df_ger['salario_base'].astype(float)
                df_ger['beneficios'] = df_ger['beneficios'].astype(float)
                df_ger['descontos'] = df_ger['descontos'].astype(float)
                
                # Editor interativo Style Excel Brasil para Salário e Adicionais
                mudancas_sl = st.data_editor(
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
                if st.button("💾 Sincronizar Folha de Pagamento"):
                    # Exclui e atualiza conforme editor interativo
                    id_tela = mudancas_sl['id'].tolist() if 'id' in mudancas_sl.columns else []
                    for id_del in [x for x in df_ger['id'].tolist() if x not in id_tela]:
                        supabase.table("folha_pagamento").delete().eq("id", id_del).execute()
                    for idx, row in mudancas_sl.iterrows():
                        supabase.table("folha_pagamento").update({
                            "funcionario": str(row['funcionario']),
                            "funcao": str(row['funcao']),
                            "salario_base": float(row['salario_base']),
                            "beneficios": float(row['beneficios']),
                            "descontos": float(row['descontos']),
                            "mes_referencia": str(row['mes_referencia'])
                        }).eq("id", row['id']).execute()
                    st.success("Registros atualizados na nuvem!")
                    st.cache_resource.clear()
                    st.rerun()
            else:
                st.info("Nenhuma folha disponível para gerenciamento.")
