import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import gdown
import os

# URLs dos arquivos no Google Drive (substitua pelos seus links)
URL_CLIENTES = "https://drive.google.com/uc?id=1UI8LIqOWs_Fxi7vkzyoGgyfoDoX9aaFD"
URL_VENDAS = "https://drive.google.com/uc?id=13ck0dTs9VxVA7zvkpWZGrOYl283tBAcm"

# ======================================
# FUNÇÕES DE CARREGAMENTO DE DADOS
# ======================================
def baixar_e_carregar_dados():
    """Baixa os arquivos do Google Drive e carrega em DataFrames."""
    try:
        # Baixar arquivos (sobrescreve se existirem)
        gdown.download(URL_CLIENTES, "clientes.xlsx", quiet=False)
        gdown.download(URL_VENDAS, "vendas.xlsx", quiet=False)

        # Carregar dados
        clientes_df = pd.read_excel("clientes.xlsx", engine="openpyxl")
        vendas_df = pd.read_excel("vendas.xlsx", engine="openpyxl")

        # Renomear colunas (ajuste conforme seus dados)
        clientes_df.columns = [
            "Inativo", "Nro.", "Empresa", "Cliente", "Fantasia", "Referência", "Vencimento",
            "Vl.liquido", "TD", "Nr.docto", "Dt.pagto", "Vl.pagamento", "TP", "Nr.pagamento",
            "Conta", "Dt.Emissão", "Cobrança", "Modelo", "Negociação", "Duplicata", "Razão Social",
            "CNPJ/CPF", "PDD"
        ]
        
        vendas_df.columns = [
            "Inativo", "Nro.", "Empresa", "Cliente", "Fantasia", "Referência", "Vencimento", "Vl.liquido",
            "TD", "Nr.docto", "Dt.pagto", "Vl.pagto", "TP", "Nr.pagto", "Conta", "Dt.Emissão",
            "Cobrança", "Modelo", "Negociação", "Duplicata", "Razão Social", "CNPJ/CPF", "PDD"
        ]

        # Criar coluna combinada
        clientes_df["Cliente_Fantasia"] = clientes_df["Cliente"] + " - " + clientes_df["Fantasia"]

        return clientes_df, vendas_df

    except Exception as e:
        st.error(f"ERRO: {str(e)}")
        return None, None

# ======================================
# FUNÇÕES DE ANÁLISE E VISUALIZAÇÃO
# ======================================
def categorizar_faturamento(valor):
    """Categoriza o cliente com base no faturamento."""
    if valor <= 10000: return "Até 10 mil"
    elif valor <= 50000: return "11k - 50k"
    elif valor <= 100000: return "51k - 100k"
    elif valor <= 150000: return "101k - 150k"
    elif valor <= 350000: return "151k - 350k"
    elif valor <= 1000000: return "351k - 1M"
    else: return "Acima de 1M"

def exibir_grafico_regua(total):
    """Gráfico de régua do faturamento."""
    fig, ax = plt.subplots(figsize=(10, 2))
    ax.hlines(1, 0, 1_500_000, colors="gray", linewidth=20, alpha=0.3)
    ax.plot(total, 1, "ro", markersize=10)
    ax.set_xlim(0, 1_500_000)
    ax.set_xticks([10_000, 50_000, 100_000, 150_000, 350_000, 1_000_000])
    ax.set_xticklabels(["10k", "50k", "100k", "150k", "350k", "1M"], rotation=45)
    ax.set_yticks([])
    st.pyplot(fig)

def exibir_metricas(clientes_filtrados, vendas_df):
    """Exibe métricas e gráficos."""
    hoje = pd.Timestamp.today()

    # Filtra valores vencidos e a vencer
    valores_vencidos = clientes_filtrados[clientes_filtrados["Vencimento"] < hoje]
    valores_a_vencer = clientes_filtrados[clientes_filtrados["Vencimento"] >= hoje]

    # Cálculo dos totais
    total_vencidos = valores_vencidos["Vl.liquido"].sum()
    total_a_vencer = valores_a_vencer["Vl.liquido"].sum()
    total_geral = total_vencidos + total_a_vencer

    # Exibe os totais
    st.write(f"**Total de registros vencidos:** {len(valores_vencidos)}")
    st.write(f"**Total de registros a vencer:** {len(valores_a_vencer)}")
    st.write(f"**Total Vencidos:** R$ {total_vencidos:,.2f}")
    st.write(f"**Total A Vencer:** R$ {total_a_vencer:,.2f}")
    st.write(f"**Total Geral:** R$ {total_geral:,.2f}")

    # Categorizar cliente por faturamento
    categoria_faturamento = categorizar_faturamento(total_geral)
    st.write(f"**Categoria de Faturamento:** {categoria_faturamento}")

    # Exibir gráfico de régua
    exibir_grafico_regua(total_geral)

    # Gráfico de pizza para totais
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.pie(
        [total_vencidos, total_a_vencer],
        labels=["Vencidos", "A Vencer"],
        autopct="%1.1f%%",
        startangle=90,
        colors=["#FF6F61", "#6FA2FF"],
        wedgeprops={"linewidth": 1, "edgecolor": "white"}
    )
    ax.axis("equal")
    st.pyplot(fig)

    # Análise de Tendências
    st.subheader("Análise de Tendências")
    fig, ax = plt.subplots(figsize=(10, 6))
    clientes_filtrados.set_index("Vencimento", inplace=True)
    valores_vencidos.set_index("Vencimento", inplace=True)
    valores_a_vencer.set_index("Vencimento", inplace=True)
    ax.bar(valores_vencidos.index, valores_vencidos["Vl.liquido"], label='Valores Vencidos', color='red', width=0.4, align='center')
    ax.bar(valores_a_vencer.index, valores_a_vencer["Vl.liquido"], label='Valores a Vencer', color='green', width=0.4, align='edge')
    ax.set_title('Tendência de Valores Vencidos e a Vencer')
    ax.set_xlabel('Data de Vencimento')
    ax.set_ylabel('Valor (R$)')
    ax.legend()
    st.pyplot(fig)

# ======================================
# INTERFACE PRINCIPAL
# ======================================
def main():
    st.title("Dashboard de Clientes")
    st.sidebar.title("Controles")

    # Botão para forçar atualização
    if st.sidebar.button("Atualizar Dados Agora"):
        st.experimental_rerun()

    # Carregar dados
    with st.spinner("Baixando dados atualizados..."):
        clientes_df, vendas_df = baixar_e_carregar_dados()

    if clientes_df is None or vendas_df is None:
        return

    # Seleção do cliente
    cliente_selecionado = st.sidebar.selectbox(
        "Selecione o Cliente:",
        options=["Todos"] + clientes_df["Cliente_Fantasia"].unique().tolist()
    )

    # Filtrar dados
    if cliente_selecionado != "Todos":
        clientes_filtrados = clientes_df[clientes_df["Cliente_Fantasia"] == cliente_selecionado]
    else:
        clientes_filtrados = clientes_df.copy()

    # Exibir métricas e gráficos
    exibir_metricas(clientes_filtrados, vendas_df)

if __name__ == "__main__":
    main()
