import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import locale
import altair as alt
from utils import *


# Defina o locale para interpretar corretamente os formatos numéricos
try:
    locale.setlocale(locale.LC_NUMERIC, '')
except locale.Error as e:
    print("Erro ao definir o locale:", e)

st.set_page_config(
    layout='wide',
    page_title='PCP CEMAG',
)

# Autenticação e acesso à planilha
client = connect_google_sheet()

# ID do documento do Google Sheets
document_id = '1t7Q_gwGVAEwNlwgWpLRVy-QbQo7kQ_l6QTjFjBrbWxE'

# Acesse o documento pelo ID
planilha1 = client.open_by_key(document_id)

# Busque a aba pelo nome
nome_da_aba = 'RQ PCP-003-000 (Transferencia Corte)'
planilha_worksheet1 = planilha1.worksheet(nome_da_aba)

dados_corte = planilha_worksheet1.get_all_values()
df_corte = pd.DataFrame(dados_corte[5:], columns=dados_corte[4])

# Converta a coluna 'Data' para o formato de data
df_corte['Data'] = pd.to_datetime(df_corte['Data'], format='%d/%m/%Y')

# Função para a primeira página
def Apontamento_Sucata():
    # Obtenha o mês atual
    mes_atual = pd.Timestamp.now().month

    # Filtrar os dados para exibir apenas os do mês atual
    df_corte_filtrado = df_corte[df_corte['Data'].dt.month == mes_atual]

    # Substituir vírgula por ponto e remover separador de milhar
    df_corte_filtrado['Sucata'] = pd.to_numeric(df_corte_filtrado['Sucata'].str.replace('.', '').str.replace(',', '.'), errors='coerce')
    df_corte_filtrado['Peso'] = pd.to_numeric(df_corte_filtrado['Peso'].str.replace('.', '').str.replace(',', '.'), errors='coerce')

    # Remover linhas com valores NaN
    df_corte_filtrado = df_corte_filtrado.dropna(subset=['Sucata', 'Peso'])

    # Converter a coluna 'Aprov.' para float, se necessário
    if df_corte_filtrado['Aprov.'].dtype == 'object':
        df_corte_filtrado['Aprov.'] = pd.to_numeric(df_corte_filtrado['Aprov.'].str.replace('.', '').str.replace(',', '.'), errors='coerce')

    # Remover linhas com valores NaN na coluna 'Aprov.'
    df_corte_filtrado = df_corte_filtrado.dropna(subset=['Aprov.'])

    # *Cálculo de Perda: (Sucata / Peso) * 100*
    if 'Peso' not in df_corte_filtrado.columns or 'Sucata' not in df_corte_filtrado.columns:
        st.error("A coluna 'Peso' ou 'Sucata' não foi encontrada no DataFrame.")
        return

    # Agrupar por dia e calcular as somas
    dados_agrupados = df_corte_filtrado.groupby(df_corte_filtrado['Data'].dt.day).agg({
        'Sucata': 'sum',
        'Peso': 'sum'
    }).reset_index()

    # Calcular a perda (sucata / peso)
    dados_agrupados['Perda'] = (dados_agrupados['Sucata'] / dados_agrupados['Peso']) * 100
    st.title(f'Sucata')
    # Criar o gráfico de barras com a linha fixa em 8,5% e o limite do gráfico em 20%
    chart = alt.Chart(dados_agrupados).mark_bar(color='#de3502').encode(
        x=alt.X('Data:O', title='Dia', axis=alt.Axis(labelAngle=0)),
        y=alt.Y('Perda:Q', title='Perda (%)', scale=alt.Scale(domain=[0, 20]))  # Limite do gráfico para 20%
    ) + alt.Chart(pd.DataFrame({'y': [8.5]})).mark_rule(color='white').encode(y='y:Q')  # Linha de 8,5% fixa

    # Exibir o gráfico
    st.altair_chart(chart, use_container_width=True)

    # Sidebar
    st.sidebar.title('Filtrar por Data')
    data_selecionada = st.sidebar.date_input('Selecione uma data', value=pd.Timestamp.now())

    # Converter a data selecionada para o mesmo formato do DataFrame
    data_selecionada_str = data_selecionada.strftime('%d/%m/%Y')

    # Filtrar os dados com base na data selecionada
    df_filtrado_por_data = df_corte[df_corte['Data'].dt.strftime('%d/%m/%Y') == data_selecionada_str]

    # Substituir vírgula por ponto e remover separador de milhar
    df_filtrado_por_data['Sucata'] = pd.to_numeric(df_filtrado_por_data['Sucata'].str.replace('.', '').str.replace(',', '.'), errors='coerce')
    df_filtrado_por_data['Peso'] = pd.to_numeric(df_filtrado_por_data['Peso'].str.replace('.', '').str.replace(',', '.'), errors='coerce')

    # Remover linhas com valores NaN
    df_filtrado_por_data = df_filtrado_por_data.dropna(subset=['Sucata', 'Peso'])

    # Converter a coluna 'Aprov.' para float, se necessário
    if df_filtrado_por_data['Aprov.'].dtype == 'object':
        df_filtrado_por_data['Aprov.'] = pd.to_numeric(df_filtrado_por_data['Aprov.'].str.replace('.', '').str.replace(',', '.'), errors='coerce')

    # Remover linhas com valores NaN na coluna 'Aprov.'
    df_filtrado_por_data = df_filtrado_por_data.dropna(subset=['Aprov.'])

    # *Cálculo de Perda no Filtro por Data (Sucata / Peso) * 100*
    if 'Peso' not in df_filtrado_por_data.columns or 'Sucata' not in df_filtrado_por_data.columns:
        st.error("A coluna 'Peso' ou 'Sucata' não foi encontrada no DataFrame filtrado por data.")
        return

    # Agrupar por Código Chapa e calcular as somas
    df_soma_sucatas_por_codigo = df_filtrado_por_data.groupby('Código Chapa').agg({
        'Sucata': 'sum',
        'Peso': 'sum'
    }).reset_index()

    # Calcular a perda
    df_soma_sucatas_por_codigo['Perda'] = (df_soma_sucatas_por_codigo['Sucata'] / df_soma_sucatas_por_codigo['Peso']) * 100

    # Selecionar as colunas desejadas e substituir 'Peso' por 'Sucata'
    df_soma_sucatas_por_codigo = df_soma_sucatas_por_codigo[['Código Chapa', 'Sucata', 'Peso', 'Perda']]

    # Calcular a média diária em porcentagem usando os valores da coluna 'Perda'
    media_diaria_porcentagem = (df_soma_sucatas_por_codigo['Sucata'].sum() / df_soma_sucatas_por_codigo['Peso'].sum()) * 100
    # Calcular a média mensal em porcentagem usando os valores da coluna 'Perda'
    media_mensal_porcentagem = (df_corte_filtrado['Sucata'].sum() / df_corte_filtrado['Peso'].sum()) * 100
    
    # Exibir DataFrame com 'Sucata' no lugar de 'Peso'
    st.write(f'### Apontamento sucata: {data_selecionada_str}')
    col1, col2, col3 = st.columns(3)
    col1.write(df_soma_sucatas_por_codigo)
    col2.metric('Sucata total', f'{df_soma_sucatas_por_codigo["Sucata"].sum():.2f} KG')
    col2.metric('Média de sucata diária', f'{media_diaria_porcentagem:.2f}%')  # Média diária em porcentagem
    col2.metric('Média de sucata mensal', f'{media_mensal_porcentagem:.2f}%')  # Média mensal em porcentagem

# Função para a segunda página
def Acompanhamento_Sucata():
    # Dicionário de nomes dos meses
    meses_dict = {
        1: 'Janeiro',
        2: 'Fevereiro',
        3: 'Março',
        4: 'Abril',
        5: 'Maio',
        6: 'Junho',
        7: 'Julho',
        8: 'Agosto',
        9: 'Setembro',
        10: 'Outubro',
        11: 'Novembro',
        12: 'Dezembro'
    }

    # Obter todos os meses disponíveis no DataFrame
    meses_disponiveis = df_corte['Data'].dt.month.unique()

    # Sidebar
    st.sidebar.title('Filtrar por Mês e Chapa')

    # Checkbox para habilitar/desabilitar filtro de chapa
    filtrar_por_chapa = st.sidebar.checkbox('Filtrar por chapa')

    if filtrar_por_chapa:
        chapa_selecionada = st.sidebar.selectbox('Selecione uma chapa', df_corte['Código Chapa'].unique())
    else:
        chapa_selecionada = None

    # Checkbox para habilitar/desabilitar filtro de data
    filtrar_por_data = st.sidebar.checkbox('Filtrar por data')

    if filtrar_por_data:
        data_inicio = st.sidebar.date_input('Data início', value=pd.Timestamp.now())
        data_fim = st.sidebar.date_input('Data fim', value=pd.Timestamp.now())
    else:
        data_inicio, data_fim = None, None

    # Exibir um gráfico para cada mês
    for mes in meses_disponiveis:
        try:
            # Filtrar os dados para o mês atual
            df_corte_filtrado = df_corte[df_corte['Data'].dt.month == mes]

            # Aplicar filtro de chapa se selecionado
            if chapa_selecionada:
                df_corte_filtrado = df_corte_filtrado[df_corte_filtrado['Código Chapa'] == chapa_selecionada]

            # Aplicar filtro de data se selecionado
            if filtrar_por_data and data_inicio and data_fim:
                df_corte_filtrado = df_corte_filtrado[
                    (df_corte_filtrado['Data'] >= pd.to_datetime(data_inicio)) & 
                    (df_corte_filtrado['Data'] <= pd.to_datetime(data_fim))
                ]
            
            # Agora, aplique a lógica de conversão de valores
            df_corte_filtrado['Sucata'] = pd.to_numeric(df_corte_filtrado['Sucata'].str.replace('.', '').str.replace(',', '.'), errors='coerce')
            df_corte_filtrado['Peso'] = pd.to_numeric(df_corte_filtrado['Peso'].str.replace('.', '').str.replace(',', '.'), errors='coerce')

            # Remover linhas com valores NaN
            df_corte_filtrado = df_corte_filtrado.dropna(subset=['Sucata', 'Peso'])

            # Calcular a perda
            df_corte_filtrado['Perda'] = (df_corte_filtrado['Sucata'] / df_corte_filtrado['Peso']) * 100

            # Agora, faça os cálculos e crie os gráficos ou tabelas
            st.write(f'## {meses_dict.get(mes)}')
            st.write(df_corte_filtrado)

        except Exception as e:
            st.error(f"Erro ao processar o mês {mes}: {str(e)}")

# Função principal
def main():
    # Sidebar de navegação
    st.sidebar.title('Navegação')
    paginas = ['Apontamento de Sucata', 'Acompanhamento de Sucata']
    pagina_selecionada = st.sidebar.radio('Escolha uma página', paginas)

    # Exibir página selecionada
    if pagina_selecionada == 'Apontamento de Sucata':
        Apontamento_Sucata()
    else:
        Acompanhamento_Sucata()

if __name__ == '__main__':
    main()
