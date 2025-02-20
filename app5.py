import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import gdown
import os
import hashlib
from datetime import datetime

# Configuração de cache com controle de versão
@st.cache_data(ttl=3600, show_spinner="Atualizando dados...")
def carregar_dados():
    """Carrega dados com versionamento automático"""
    try:
        # URLs dos arquivos (atualize com seus links)
        url_clientes = 'https://drive.google.com/uc?id=12doumGMLErxW6j1KM5idWHAzXAH1Woqd'
        url_vendas = 'https://drive.google.com/uc?id=1dYHZlfvZlwOhJP1cJlQRbMowoVRBY78N'
        
        # Gera nomes únicos baseados no conteúdo das URLs
        hash_cli = hashlib.md5(url_clientes.encode()).hexdigest()[:8]
        hash_vnd = hashlib.md5(url_vendas.encode()).hexdigest()[:8]
        
        caminho_clientes = f'clientes_{hash_cli}.xlsx'
        caminho_vendas = f'vendas_{hash_vnd}.xlsx'

        # Download condicional
        if not os.path.exists(caminho_clientes):
            gdown.download(url_clientes, caminho_clientes, quiet=False)
        if not os.path.exists(caminho_vendas):
            gdown.download(url_vendas, caminho_vendas, quiet=False)

        # Carregar dados
        clientes_df = pd.read_excel(caminho_clientes, engine='openpyxl')
        vendas_df = pd.read_excel(caminho_vendas, engine='openpyxl')

        # Padronização de colunas
        clientes_df.columns = [
            "Inativo", "Nro.", "Empresa", "Cliente", "Fantasia", "Referência", "Vencimento",
            "Vl.liquido", "TD", "Nr.docto", "Dt.pagto", "Vl.pagamento", "TP", "Nr.pagamento",
            "Conta", "Dt.Emissão", "Cobrança", "Modelo", "Negociação", "Duplicata", 
            "Razão Social", "CNPJ/CPF", "PDD"
        ]

        vendas_df.columns = [
            "Inativo", "Nro.", "Empresa", "Cliente", "Fantasia", "Referência", "Vencimento", 
            "Vl.liquido", "TD", "Nr.docto", "Dt.pagto", "Vl.pagto", "TP", "Nr.pagto", 
            "Conta", "Dt.Emissão", "Cobrança", "Modelo", "Negociação", "Duplicata", 
            "Razão Social", "CNPJ/CPF", "PDD"
        ]

        # Processamento de datas e valores
        for df in [clientes_df, vendas_df]:
            df["Vencimento"] = pd.to_datetime(df["Vencimento"], errors='coerce')
            df["Dt.Emissão"] = pd.to_datetime(df["Dt.Emissão"], errors='coerce')
            df["Vl.liquido"] = pd.to_numeric(df["Vl.liquido"], errors='coerce')
            df["Vl.pagto"] = pd.to_numeric(df["Vl.pagto"], errors='coerce')

        clientes_df["Cliente_Fantasia"] = clientes_df["Cliente"] + " - " + clientes_df["Fantasia"]
        
        return clientes_df, vendas_df

    except Exception as e:
        st.error(f"Erro crítico: {str(e)}")
        st.stop()

def categorizar_cliente_por_faturamento(faturamento):
    categorias = [
        (10000, 'Até 10 mil'),
        (50000, '11-50 mil'),
        (100000, '51-100 mil'),
        (150000, '101-150 mil'),
        (350000, '151-350 mil'),
        (1000000, '351 mil-1 Mi'),
        (float('inf'), 'Acima de 1 Mi')
    ]
    for limite, categoria in categorias:
        if faturamento <= limite:
            return categoria

def grafico_regua_faturamento(total_geral):
    fig, ax = plt.subplots(figsize=(10, 2))
    posicoes = [10000, 50000, 100000, 150000, 350000, 1000000, 1500000]
    categorias = ['10k', '50k', '100k', '150k', '350k', '1M', '+1M']
    
    ax.hlines(1, 0, 1500000, color='lightgray', linewidth=20, alpha=0.3)
    ax.plot(total_geral, 1, 'o', markersize=15, color='#FF6F61')
    
    ax.set_xlim(0, 1500000)
    ax.set_xticks(posicoes)
    ax.set_xticklabels(categorias, rotation=45)
    ax.yaxis.set_visible(False)
    plt.title('Posicionamento de Faturamento', pad=20)
    st.pyplot(fig)

def exibir_analise_completa(clientes_filtro, vendas_cliente):
    hoje = pd.Timestamp.today()
    
    # Cálculos básicos
    vencidos = clientes_filtro[clientes_filtro["Vencimento"] < hoje]
    a_vencer = clientes_filtro[clientes_filtro["Vencimento"] >= hoje]
    
    total_vencidos = vencidos["Vl.liquido"].sum()
    total_a_vencer = a_vencer["Vl.liquido"].sum()
    total_geral = total_vencidos + total_a_vencer

    # ======================= MÉTRICAS PRINCIPAIS =======================
    st.subheader("📊 Métricas Financeiras")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Valores Vencidos", f"R$ {total_vencidos:,.2f}", 
                 f"{len(vencidos)} títulos", delta_color="inverse")
    with col2:
        st.metric("A Vencer", f"R$ {total_a_vencer:,.2f}", 
                 f"{len(a_vencer)} títulos")
    with col3:
        st.metric("Total em Aberto", f"R$ {total_geral:,.2f}", 
                 categorizar_cliente_por_faturamento(total_geral))
    
    grafico_regua_faturamento(total_geral)

    # ======================= ANÁLISE DE PRAZOS =======================
    with st.expander("⏳ Análise de Prazos", expanded=True):
        col4, col5, col6 = st.columns(3)
        
        # PMF - Prazo Médio de Faturamento
        clientes_filtro["Prazo"] = (clientes_filtro["Vencimento"] - clientes_filtro["Dt.Emissão"]).dt.days
        pmf = (clientes_filtro["Prazo"] * clientes_filtro["Vl.liquido"]).sum() / clientes_filtro["Vl.liquido"].sum()
        with col4:
            st.metric("PMF (Dias)", f"{pmf:.1f}", help="Prazo Médio de Faturamento")
        
        # PMR - Prazo Médio de Recebimento
        vendas_cliente["Dias Recebimento"] = (vendas_cliente["Dt.pagto"] - vendas_cliente["Vencimento"]).dt.days
        pmr = (vendas_cliente["Dias Recebimento"] * vendas_cliente["Vl.liquido"]).sum() / vendas_cliente["Vl.liquido"].sum()
        with col5:
            st.metric("PMR (Dias)", f"{pmr:.1f}", help="Prazo Médio de Recebimento")
        
        # DSO
        dias_periodo = (vendas_cliente["Dt.Emissão"].max() - vendas_cliente["Dt.Emissão"].min()).days
        fat_diario_medio = vendas_cliente["Vl.liquido"].sum() / dias_periodo if dias_periodo > 0 else 0
        dso = total_geral / fat_diario_medio if fat_diario_medio > 0 else 0
        with col6:
            st.metric("DSO (Dias)", f"{dso:.1f}", help="Days Sales Outstanding")

    # ======================= EFICIÊNCIA COBRANÇA =======================
    with st.expander("📈 Eficiência de Cobrança"):
        col7, col8 = st.columns(2)
        
        # CEI
        total_recebido = vendas_cliente["Vl.pagto"].sum()
        cei = (total_recebido / total_geral * 100) if total_geral > 0 else 0
        with col7:
            st.metric("CEI (%)", f"{cei:.1f}", help="Collection Effectiveness Index")
        
        # Turnover
        turnover = (vendas_cliente["Vl.liquido"].sum() / total_geral) if total_geral > 0 else 0
        with col8:
            st.metric("Giro Contas Receber", f"{turnover:.2f}x")

    # ======================= ANÁLISE TEMPORAL =======================
    with st.expander("📅 Tendência de Valores"):
        fig, ax = plt.subplots(figsize=(12, 6))
        clientes_filtro.set_index("Vencimento", inplace=True)
        ax.bar(clientes_filtro.index, clientes_filtro["Vl.liquido"], 
              color=['#FF6F61' if d < hoje else '#6FA2FF' for d in clientes_filtro.index])
        ax.set_title("Distribuição por Data de Vencimento")
        ax.set_xlabel("")
        ax.set_ylabel("Valor (R$)")
        st.pyplot(fig)

    # ======================= SAZONALIDADE =======================
    with st.expander("🌦️ Sazonalidade de Vendas"):
        vendas_cliente['Mês'] = vendas_cliente['Dt.Emissão'].dt.month_name()
        meses_ordem = ['January', 'February', 'March', 'April', 'May', 'June',
                      'July', 'August', 'September', 'October', 'November', 'December']
        sazonalidade = vendas_cliente.groupby('Mês')['Vl.liquido'].sum().reindex(meses_ordem)
        
        fig, ax = plt.subplots(figsize=(12, 6))
        sazonalidade.plot(kind='bar', color='#4CAF50', ax=ax)
        ax.set_title("Vendas Mensais")
        ax.set_xlabel("Mês")
        ax.set_ylabel("Valor Total (R$)")
        st.pyplot(fig)

    # ======================= INADIMPLÊNCIA =======================
    with st.expander("⚠️ Risco de Inadimplência"):
        col9, col10 = st.columns(2)
        
        # Taxa de Inadimplência
        inadimplencia = (total_vencidos / total_geral * 100) if total_geral > 0 else 0
        with col9:
            st.metric("Taxa Inadimplência", f"{inadimplencia:.1f}%")
        
        # Análise Comparativa
        desempenho_atual = vendas_cliente["Vl.liquido"].sum()
        desempenho_anterior = clientes_filtro["Vl.liquido"].sum()
        variacao = ((desempenho_atual - desempenho_anterior)/desempenho_anterior * 100) if desempenho_anterior > 0 else 0
        with col10:
            st.metric("Variação Histórica", f"{variacao:.1f}%", 
                     help="Comparativo com período anterior")

def main():
    st.set_page_config(page_title="Analytics Financeiro", layout="wide")
    
    # Controle de atualização
    if st.sidebar.button("🔄 Atualizar Dados"):
        st.cache_data.clear()
    
    # Carregar dados
    clientes_df, vendas_df = carregar_dados()
    
    # Seletor de cliente
    cliente_selecionado = st.sidebar.selectbox(
        "👤 Selecione o Cliente:",
        options=[""] + clientes_df["Cliente_Fantasia"].unique().tolist(),
        format_func=lambda x: "Selecione..." if x == "" else x
    )
    
    if not cliente_selecionado:
        st.info("ℹ️ Selecione um cliente na barra lateral")
        return
    
    # Filtragem de dados
    try:
        cliente_filtro = clientes_df[clientes_df["Cliente_Fantasia"] == cliente_selecionado].copy()
        vendas_cliente = vendas_df[vendas_df["Cliente"] == cliente_filtro["Cliente"].iloc[0]].copy()
    except Exception as e:
        st.error(f"Erro ao filtrar dados: {str(e)}")
        st.stop()
    
    # Exibição principal
    st.title(f"📊 Análise: {cliente_selecionado}")
    exibir_analise_completa(cliente_filtro, vendas_cliente)

if __name__ == "__main__":
    main()
