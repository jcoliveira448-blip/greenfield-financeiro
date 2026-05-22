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

# Estilização CSS customizada corrigida para botões da sidebar
st.markdown("""
    <style>
        [data-testid="stSidebar"] { background-color: #062618 !important; }
        [data-testid="stSidebar"] * { color: #ffffff !important; }
        
        /* Correção para o botão de download na sidebar não ficar invisível */
        [data-testid="stSidebar"] div.stDownloadButton > button {
            background-color: #0b4d32 !important;
            color: #ffffff !important;
            border: 1px solid #1e7e54 !important;
            border-radius: 6px !important;
            width: 100% !important;
            font-weight: 600 !important;
        }
        [data-testid="stSidebar"] div.stDownloadButton > button:hover {
            background-color: #116943 !important;
            border: 1px solid #ffffff !important;
        }
        
        h1 { font-size: 24px !important; font-weight: 700 !important; }
        h2 { font-size: 20px !important; font-weight: 600 !important; }
        
        [data-testid="stMetricLabel"] { font-size: 14px !important; }
        [data-testid="stMetricValue"] { font-size: 22px !important; }
        
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

# ===================== GERADOR DO PDF DO MANUAL DE CONSULTA =====================
def gerar_pdf_manual():
    pdf_buffer = io.BytesIO()
    doc = SimpleDocTemplate(pdf_buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    
    style_titulo = ParagraphStyle('TituloManual', parent=styles['Heading1'], textColor='#062618', spaceAfter=15, fontSize=18)
    style_sub = ParagraphStyle('SubManual', parent=styles['Heading2'], textColor='#0b4d32', spaceAfter=10, fontSize=14)
    style_corpo = ParagraphStyle('CorpoManual', parent=styles['Normal'], fontSize=11, leading=16, spaceAfter=8)
    
    story = [
        Paragraph("<b>Manual do Usuário: Módulo de Pedidos de Compra (OC)</b>", style_titulo),
        Paragraph("<i>Greenfield - ERP Corporativo</i>", style_corpo),
        Spacer(1, 15),
        
        Paragraph("<b>1. Como preencher o Passo 1:</b>", style_sub),
        Paragraph("• <b>Número da OC:</b> Código sequencial identificador do pedido (Ex: OC-2026-001).", style_corpo),
        Paragraph("• <b>Solicitante / Engenheiro:</b> Nome de quem requisitou o suprimento na obra.", style_corpo),
        Paragraph("• <b>Fornecedor:</b> Empresa ou parceiro onde a compra está sendo executada.", style_corpo),
        Paragraph("• <b>Valor Total (R$):</b> Valor final negociado. Use ponto para os centavos.", style_corpo),
        Paragraph("• <b>Data de Vencimento:</b> Defina o vencimento acordado para o pagamento deste pedido.", style_corpo),
        Paragraph("• <b>Observações:</b> Campo opcional para detalhar termos de entrega, restrições ou recados.", style_corpo),
        Spacer(1, 10),
        
        Paragraph("<b>2. Salvando e Gerando o Documento (Passo 2):</b>", style_sub),
        Paragraph("• Clique em 'Gerar PDF do Pedido' para revisar a folha de Ordem de Compra.", style_corpo),
        Paragraph("• Use o botão 'Baixar PDF' para guardar uma cópia do documento emitido.", style_corpo),
        Paragraph("• <b>OBRIGATÓRIO:</b> Clique em 'Salvar Pedido no Histórico'. Esse botão integra a compra à fila de Contas a Pagar do Financeiro Central.", style_corpo),
        Spacer(1, 10),
        
        Paragraph("<b>3. Edições e Correções:</b>", style_sub),
        Paragraph("• Se errar, utilize a aba 'Gerenciar' para alterar valores ou fornecedores.", style_corpo),
        Paragraph("• Lembre-se de clicar em 'Sincronizar Compras' para consolidar as alterações.", style_corpo),
    ]
    doc.build(story)
    pdf_buffer.seek(0)
    return pdf_buffer.getvalue()

# ===================== CÁLCULO DINÂMICO DE SALDO =====================
df_medicoes_global = load_data("medicoes_caixa")
if not df_medicoes_global.empty and 'valor' in df_medicoes_global.columns:
    saldo_projetado_caixa = df_medicoes_global['valor'].astype(float).sum()
else:
    saldo_projetado_caixa = 0.00

# ===================== SIDEBAR CONTROLE DE ACESSO =====================
with st.sidebar:
    if os.path.exists("logo.png"):
        st.image("logo.png", use_container_width=True)
        
    st.sidebar.markdown("# 💹 Greenfield")
    st.markdown("### ERP FINANCEIRO CORPORATIVO")
    st.markdown("---")
    
    senha = st.text_input("Chave de Acesso", type="password", help="Insira sua senha para liberar os módulos.")
    
    if senha == "compras123":
        paginas_disponiveis = ["🛒 Pedidos de Compra"]
        st.sidebar.success("Acesso: Módulo Compras")
        
        st.markdown("---")
        st.markdown("### 📚 Central de Ajuda")
        manual_pdf = gerar_pdf_manual()
        st.download_button(
            label="📥 Baixar Manual de Consulta",
            data=manual_pdf,
            file_name="Manual_Modulo_Compras_Greenfield.pdf",
            mime="application/pdf"
        )
        
    elif senha == "admin789":
        paginas_disponiveis = [
            "📊 Dashboard", 
            "💳 Contas a Pagar & Caixa", 
            "🛒 Pedidos de Compra", 
            "⚖️ Acordos Judiciais", 
            "👥 Salários"
        ]
        st.sidebar.success("Acesso: Administrador")
    else:
        paginas_disponiveis = []
        if senha != "":
            st.sidebar.error("Senha incorreta!")

    # Se o usuário digitou a senha correta e liberou páginas, mostra o menu
    if paginas_disponiveis:
        page = st.radio("Navegação", paginas_disponiveis)
    else:
        # AQUI COMPLETA O QUE ESTAVA INCOMPLETO:
        st.info("Por favor, insira uma senha válida no menu lateral para acessar o sistema.")
