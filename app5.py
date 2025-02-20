import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import gdown
import hashlib
import os
from datetime import datetime

# ================= CONFIGURAÇÕES =================
URL_CLIENTES = "https://drive.google.com/uc?id=SEU_ID_CLIENTES"
URL_VENDAS = "https://drive.google.com/uc?id=SEU_ID_VENDAS"

# ================= FUNÇÕES PRINCIPAIS =================
@st.cache_data(ttl=3600, show_spinner="Sincronizando dados...")
def carregar_dados():
    """Carrega e processa dados com versionamento"""
    try:
        # Controle de versão por hash
        hash_cli = hashlib.md5(URL_CLIENTES.encode()).hexdigest()[:8]
        hash_vnd = hashlib.md5(URL_VENDAS.encode()).hexdigest()[:8]
        
        # Nomes de arquivo únicos
        arq_cli = f"clientes_{hash_cli}.xlsx"
        arq_vnd = f"vendas_{hash_vnd}.xlsx"

        # Download seguro
        if not os.path.exists(arq_cli):
            gdown.download(URL_CLIENTES, arq_cli, quiet=False)
        if not os.path.exists(arq_vnd):
            gdown.download(URL_VENDAS, arq_vnd, quiet=False)

        # Carregar dados
        clientes = pd.read_excel(arq_cli, engine="openpyxl")
        vendas = pd.read_excel(arq_vnd, engine="openpyxl")

        # Validação rigorosa
        colunas_necessarias = {
            'clientes': ['Cliente', 'Fantasia', 'Vencimento', 'Vl.liquido', 'Dt.Emissão'],
            'vendas': ['Cliente', 'Vl.liquido', 'Dt.pagto', 'Vencimento', 'Dt.Emissão']
        }
        
        for df, tipo in zip([clientes, vendas], ['clientes', 'vendas']):
            if df.empty:
                raise ValueError(f"Arquivo de {tipo} está vazio")
            cols_faltando = [col for col in colunas_necessarias[tipo] if col not in df.columns]
            if cols_faltando:
                raise ValueError(f"Colunas faltando em {tipo}: {', '.join(cols_faltando)}")

        # Processamento padrão
        clientes.columns = [
            "Inativo", "Nro.", "Empresa", "Cliente", "Fantasia", "Referência", "Vencimento",
            "Vl.liquido", "TD", "Nr.docto", "Dt.pagto", "Vl.pagamento", "TP", "Nr.pagamento",
            "Conta", "Dt.Emissão", "Cobrança", "Modelo", "Negociação", "Duplicata", "Razão Social",
            "CNPJ/CPF", "PDD"
        ]
        
        vendas.columns = [
            "Inativo", "Nro.", "Empresa", "Cliente", "Fantasia", "Referência", "Vencimento", "Vl.liquido",
            "TD", "Nr.docto", "Dt.pagto", "Vl.pagto", "TP", "Nr.pagto", "Conta", "Dt.Emissão",
            "Cobrança", "Modelo", "Negociação", "Duplicata", "Razão Social", "CNPJ/CPF", "PDD"
        ]

        # Transformação de dados
        for df in [clientes, vendas]:
            df["Vencimento"] = pd.to_datetime(df["Vencimento"], errors='coerce')
            df["Dt.Emissão"] = pd.to_datetime(df["Dt.Emissão"], errors='coerce')
            df["Vl.liquido"] = pd.to_numeric(df["Vl.liquido"], errors="coerce")
            df["Vl.pagto"] = pd.to_numeric(df["Vl.pagto"], errors="coerce")
            
        clientes["Cliente_Fantasia"] = clientes["Cliente"].astype(str) + " - " + clientes["Fantasia"].astype(str)

        return clientes, vendas

    except Exception as e:
        st.error(f"ERRO CRÍTICO: {str(e)}")
        st.stop()

# ================= ANÁLISES COMPLETAS =================
def exibir_analise_completa(clientes_filtro, vendas_cliente):
    hoje = pd.Timestamp.today()
    
    # Cálculos básicos
    vencidos = clientes_filtro[clientes_filtro["Vencimento"] < hoje]
    a_vencer = clientes_filtro[clientes_filtro["Vencimento"] >= hoje]
    
    total_vencidos = vencidos["Vl.liquido"].sum()
    total_a_vencer = a_vencer["Vl.liquido"].sum()
    total_geral = total_vencidos + total_a_vencer
    
    # ============ MÉTRICAS PRINCIPAIS ============
    st.subheader("📊 Métricas Financeiras")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Valores Vencidos", f"R$ {total_vencidos:,.2f}", 
                 help="Soma de todos os títulos em atraso")
    with col2:
        st.metric("Valores a Vencer", f"R$ {total_a_vencer:,.2f}", 
                 help="Valores dentro do prazo de vencimento")
    with col3:
        st.metric("Total em Aberto", f"R$ {total_geral:,.2f}", 
                 help="Somatório total de contas a receber")

    # ============ GRÁFICO DE RÉGUA ============
    st.subheader("📏 Posicionamento de Faturamento")
    fig, ax = plt.subplots(figsize=(10, 2))
    categorias = ['Até 10k', '10-50k', '50-100k', '100-150k', '150-350k', '350k-1M', '+1M']
    posicoes = [10000, 50000, 100000, 150000, 350000, 1000000, 1500000]
    ax.hlines(1, 0, 1500000, color='lightgray', linewidth=20, alpha=0.3)
    ax.plot(total_geral, 1, 'o', markersize=20, color='#FF4B4B')
    ax.set_xlim(0, 1500000)
    ax.set_xticks(posicoes)
    ax.set_xticklabels(categorias, rotation=45)
    ax.yaxis.set_visible(False)
    st.pyplot(fig)
    
    # ============ ANÁLISE DE TENDÊNCIAS ============
    st.subheader("📈 Análise de Tendências")
    fig, ax = plt.subplots(figsize=(12, 6))
    
    # Preparar dados temporais
    clientes_filtro['Mês'] = clientes_filtro['Vencimento'].dt.to_period('M').astype(str)
    tendencia = clientes_filtro.groupby('Mês')['Vl.liquido'].sum().reset_index()
    
    # Plotar gráfico
    ax.bar(tendencia['Mês'], tendencia['Vl.liquido'], 
          color=['#FF6F61' if x < hoje else '#6FA2FF' for x in tendencia['Mês']])
    ax.set_title("Evolução Mensal dos Valores")
    ax.set_xlabel("Mês")
    ax.set_ylabel("Valor (R$)")
    plt.xticks(rotation=45)
    st.pyplot(fig)
    st.write("""
    **Comentário:** Esta análise mostra a distribuição dos valores ao longo dos meses. 
    Barras vermelhas indicam meses com valores vencidos, azuis para valores a vencer.
    """)

    # ============ ANÁLISE DE DESEMPENHO ============
    st.subheader("🏆 Análise de Desempenho")
    
    # Calcular períodos
    periodo_atual = f"{clientes_filtro['Dt.Emissão'].min().strftime('%d/%m/%Y')} a {clientes_filtro['Dt.Emissão'].max().strftime('%d/%m/%Y')}"
    desempenho_atual = clientes_filtro['Vl.liquido'].sum()
    
    try:
        # Dados históricos (últimos 6 meses)
        data_corte = clientes_filtro['Dt.Emissão'].max() - pd.DateOffset(months=6)
        desempenho_anterior = vendas_cliente[vendas_cliente['Dt.Emissão'] < data_corte]['Vl.liquido'].sum()
        
        variacao = ((desempenho_atual - desempenho_anterior) / desempenho_anterior * 100) if desempenho_anterior > 0 else 0
        
        col4, col5 = st.columns(2)
        with col4:
            st.metric("Desempenho Atual", f"R$ {desempenho_atual:,.2f}", 
                     periodo_atual)
        with col5:
            st.metric("Variação vs Período Anterior", f"{variacao:.1f}%", 
                     "Últimos 6 meses", delta_color="inverse")
            
    except Exception as e:
        st.error(f"Erro na análise de desempenho: {str(e)}")

    # ============ ANÁLISE DE SAZONALIDADE ============
    st.subheader("🌦️ Análise de Sazonalidade")
    
    # Preparar dados
    vendas_cliente['Mês'] = vendas_cliente['Dt.Emissão'].dt.month_name()
    meses_ordem = ['January', 'February', 'March', 'April', 'May', 'June',
                  'July', 'August', 'September', 'October', 'November', 'December']
    sazonalidade = vendas_cliente.groupby('Mês')['Vl.liquido'].sum().reindex(meses_ordem)
    
    # Plotar gráfico
    fig, ax = plt.subplots(figsize=(12, 6))
    sazonalidade.plot(kind='bar', color='#4CAF50', ax=ax)
    ax.set_title("Padrão de Vendas por Mês")
    ax.set_xlabel("Mês")
    ax.set_ylabel("Valor Total (R$)")
    st.pyplot(fig)
    st.write("""
    **Comentário:** Identifica períodos de maior movimento comercial. 
    Picos consistentes podem indicar sazonalidade no negócio.
    """)

    # ============ ANÁLISE DE INADIMPLÊNCIA ============
    st.subheader("⚠️ Análise de Inadimplência")
    
    inadimplencia = (total_vencidos / total_geral * 100) if total_geral > 0 else 0
    st.metric("Taxa de Inadimplência", f"{inadimplencia:.1f}%", 
             help="Percentual de valores vencidos sobre o total")
    
    # Comentário qualitativo
    if inadimplencia > 20:
        st.error("🚨 Atenção: Taxa de inadimplência crítica! Necessário revisão urgente das políticas de crédito.")
    elif inadimplencia > 10:
        st.warning("⚠️ Cuidado: Taxa de inadimplência acima do recomendado. Monitorar de perto.")
    else:
        st.success("✅ Saudável: Taxa de inadimplência dentro dos parâmetros aceitáveis.")

    # ============ ANÁLISE DE PRAZOS ============
    st.subheader("⏳ Análise de Prazos")
    
    col6, col7 = st.columns(2)
    with col6:
        # Prazo Médio de Recebimento
        recebimento_medio = (vendas_cliente['Dt.pagto'] - vendas_cliente['Vencimento']).dt.days.mean()
        st.metric("Prazo Médio de Recebimento", f"{recebimento_medio:.1f} dias")
    
    with col7:
        # Dias de Vencimento Médio
        vencimento_medio = (clientes_filtro['Vencimento'] - clientes_filtro['Dt.Emissão']).dt.days.mean()
        st.metric("Prazo Médio de Vencimento", f"{vencimiento_medio:.1f} dias")

# ================= INTERFACE =================
def main():
    st.set_page_config(
        page_title="Analytics Financeiro Completo", 
        page_icon="💼", 
        layout="wide"
    )
    
    # Controles
    st.sidebar.title("⚙️ Controles")
    if st.sidebar.button("🔄 Atualizar Dados", help="Forçar atualização imediata"):
        st.cache_data.clear()
        st.rerun()
    
    # Carregar dados
    clientes_df, vendas_df = carregar_dados()
    
    # Seletor de cliente
    cliente_selecionado = st.sidebar.selectbox(
        "👤 Selecione o Cliente:",
        options=[""] + clientes_df["Cliente_Fantasia"].unique().tolist(),
        format_func=lambda x: "Selecione..." if x == "" else x
    )
    
    if not cliente_selecionado:
        st.info("ℹ️ Selecione um cliente na barra lateral para iniciar")
        return
    
    # Aplicar filtros
    try:
        cliente_filtro = clientes_df[clientes_df["Cliente_Fantasia"] == cliente_selecionado].copy()
        nome_cliente = cliente_filtro["Cliente"].iloc[0]
        vendas_cliente = vendas_df[vendas_df["Cliente"] == nome_cliente].copy()
    except Exception as e:
        st.error(f"Erro ao filtrar dados: {str(e)}")
        st.stop()
    
    # Exibição principal
    st.title(f"📊 Análise Detalhada: {cliente_selecionado}")
    exibir_analise_completa(cliente_filtro, vendas_cliente)

if __name__ == "__main__":
    main()
