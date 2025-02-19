import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import gdown
import os

# Função para baixar o arquivo do Google Drive
def baixar_arquivo_google_drive(url, caminho_local):
    gdown.download(url, caminho_local, quiet=False)

# Cache de dados para evitar recarregamentos
@st.cache_data
def carregar_dados():
    # URLs e caminhos locais
    url_clientes = 'https://drive.google.com/uc?id=1UI8LIqOWs_Fxi7vkzyoGgyfoDoX9aaFD&export=download'
    caminho_clientes = 'estatistica_clientes.xlsx'
    url_vendas = 'https://drive.google.com/uc?id=13ck0dTs9VxVA7zvkpWZGrOYl283tBAcm&export=download'
    caminho_vendas = 'Vendas_Credito.xlsx'

    # Baixar arquivos se não existirem
    if not os.path.exists(caminho_clientes):
        baixar_arquivo_google_drive(url_clientes, caminho_clientes)
    if not os.path.exists(caminho_vendas):
        baixar_arquivo_google_drive(url_vendas, caminho_vendas)

    # Carregar dados
    try:
        clientes_df = pd.read_excel(caminho_clientes, engine='openpyxl')
        vendas_credito_df = pd.read_excel(caminho_vendas, engine='openpyxl')
    except Exception as e:
        st.error(f"Erro ao carregar os arquivos: {e}")
        return None, None

    # Corrigir nomes das colunas
    clientes_df.columns = [
        "Inativo", "Nro.", "Empresa", "Cliente ", "Fantasia", "Referência", "Vencimento",
        "Vl.liquido", "TD", "Nr.docto", "Dt.pagto", "Vl.pagamento", "TP", "Nr.pagamento",
        "Conta", "Dt.Emissão", "Cobrança", "Modelo", "Negociação", "Duplicata", "Razão Social",
        "CNPJ/CPF", "PDD"
    ]

    vendas_credito_df.columns = [
        "Inativo", "Nro.", "Empresa", "Cliente1", "Fantasia1", "Referência", "Vencimento1", "Vl.liquido1",
        "TD", "Nr.docto", "Dt.pagto", "Vl.pagto", "TP", "Nr.pagto", "Conta", "Dt.Emissão1",
        "Cobrança", "Modelo", "Negociação", "Duplicata", "Razão Social", "CNPJ/CPF", "PDD"
    ]

    # Criar coluna combinada "Cliente_Fantasia"
    clientes_df["Cliente_Fantasia"] = clientes_df.apply(lambda row: f"{row['Cliente ']} - {row['Fantasia']}", axis=1)

    return clientes_df, vendas_credito_df

# Função para categorizar cliente por faturamento
def categorizar_cliente_por_faturamento(faturamento):
    if faturamento <= 10000:
        return 'Até 10 mil'
    elif faturamento <= 50000:
        return 'De 11 mil a 50 mil'
    elif faturamento <= 100000:
        return 'De 51 mil a 100 mil'
    elif faturamento <= 150000:
        return 'De 101 mil a 150 mil'
    elif faturamento <= 350000:
        return 'De 151 mil a 350 mil'
    elif faturamento <= 1000000:
        return 'De 151 mil até 1 milhão'
    else:
        return 'Acima de 1 milhão'

# Função para exibir gráfico de régua de faturamento
def grafico_regua_faturamento(total_geral):
    fig, ax = plt.subplots(figsize=(10, 2))
    categorias = ['Até 10 mil', 'De 11 mil a 50 mil', 'De 51 mil a 100 mil', 'De 101 mil a 150 mil', 'De 151 mil a 350 mil', 'De 351 mil até 1 milhão', 'Acima de 1 milhão']
    posicoes = [10000, 50000, 100000, 150000, 350000, 1000000, 1500000]
    ax.hlines(1, xmin=0, xmax=1500000, color='gray', linewidth=5)
    ax.plot(total_geral, 1, 'ro')  # Marca a posição do cliente
    ax.set_xlim(0, 1500000)
    ax.set_xticks(posicoes)
    ax.set_xticklabels(categorias, rotation=45, ha='right')
    ax.set_yticks([])
    plt.tight_layout()
    st.pyplot(fig)

# Função para exibir métricas principais
def exibir_metricas(clientes_filtrados, vendas_cliente):
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
    categoria_faturamento = categorizar_cliente_por_faturamento(total_geral)
    st.write(f"**Categoria de Faturamento:** {categoria_faturamento}")

    # Exibir gráfico de régua
    grafico_regua_faturamento(total_geral)

# Função principal
def main():
    st.title("Análise de Clientes")
    st.sidebar.title("Filtros")

    # Carregar dados com spinner
    with st.spinner("Carregando dados..."):
        clientes_df, vendas_credito_df = carregar_dados()
    if clientes_df is None or vendas_credito_df is None:
        return

    # Selecionar cliente
    opcoes = clientes_df["Cliente_Fantasia"].unique().tolist()
    escolha = st.sidebar.selectbox("Escolha um Cliente_Fantasia:", ["Selecione um cliente"] + opcoes)

    if escolha == "Selecione um cliente":
        st.warning("Por favor, selecione um cliente.")
        return

    st.subheader(f"Cliente em Análise: {escolha}")

    # Filtrar dados
    clientes_filtrados = clientes_df[clientes_df["Cliente_Fantasia"] == escolha].copy()
    cliente_nome = clientes_filtrados["Cliente "].iloc[0]
    vendas_cliente = vendas_credito_df[vendas_credito_df["Cliente1"] == cliente_nome].copy()

    # Exibir métricas
    exibir_metricas(clientes_filtrados, vendas_cliente)

if __name__ == "__main__":
    main()
