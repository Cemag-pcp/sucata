import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import locale
from locale import LC_NUMERIC

st.set_page_config(
    layout='wide',
    page_title='PCP CEMAG',
)

# Defina o locale para interpretar corretamente os formatos numéricos
try:
    locale.setlocale(LC_NUMERIC, '')
except locale.Error as e:
    print("Erro ao definir o locale:", e)

# Autenticação e acesso à planilha
scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)
client = gspread.authorize(creds)
planilha1 = client.open('CENTRAL CORTE CHAPAS')

planilha_worksheet1 = planilha1.get_worksheet(4)
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

    # Converter a coluna 'Sucata' para float
    df_corte_filtrado['Sucata'] = pd.to_numeric(df_corte_filtrado['Sucata'].str.replace(',', '.'), errors='coerce')

    # Remover linhas com valores NaN
    df_corte_filtrado = df_corte_filtrado.dropna(subset=['Sucata'])

    # Converter a coluna 'Aprov.' para float, se necessário
    if df_corte_filtrado['Aprov.'].dtype == 'object':
        df_corte_filtrado['Aprov.'] = pd.to_numeric(df_corte_filtrado['Aprov.'].str.replace(',', '.'), errors='coerce')

    # Agrupar os dados por dia e somar os valores da coluna 'Sucata'
    dados_agrupados = df_corte_filtrado.groupby(df_corte_filtrado['Data'].dt.day)['Sucata'].sum()

    # Exibir o título
    st.title('Acompanhamento Sucata')

    # Personalizar o gráfico de barras
    st.bar_chart(dados_agrupados, color='#ffaa00', use_container_width=True)

    # Sidebar
    st.sidebar.title('Filtrar por Data')
    data_selecionada = st.sidebar.date_input('Selecione uma data', value=pd.Timestamp.now())

    # Converter a data selecionada para o mesmo formato do DataFrame
    data_selecionada_str = data_selecionada.strftime('%d/%m/%Y')

    # Filtrar os dados com base na data selecionada
    df_filtrado_por_data = df_corte[df_corte['Data'].dt.strftime('%d/%m/%Y') == data_selecionada_str]

    # Converter a coluna 'Sucata' para float no DataFrame filtrado por data
    df_filtrado_por_data['Sucata'] = pd.to_numeric(df_filtrado_por_data['Sucata'].str.replace(',', '.'), errors='coerce')

    # Remover linhas com valores NaN
    df_filtrado_por_data = df_filtrado_por_data.dropna(subset=['Sucata'])

    # Converter a coluna 'Aprov.' para float, se necessário
    if df_filtrado_por_data['Aprov.'].dtype == 'object':
        df_filtrado_por_data['Aprov.'] = pd.to_numeric(df_filtrado_por_data['Aprov.'].str.replace(',', '.'), errors='coerce')

    # Agrupar os dados por código de chapa e somar os valores da coluna 'Sucata'
    df_soma_sucatas_por_codigo = df_filtrado_por_data.groupby('Código Chapa')['Sucata'].sum().reset_index()

    # Calcular a média diária em porcentagem usando os valores da coluna 'Aprov.'
    media_diaria_porcentagem = df_filtrado_por_data['Aprov.'].mean() * 100

    # Exibir DataFrame
    st.write(f'### Apontamento sucata: {data_selecionada_str}')
    col1, col2, col3 = st.columns(3)
    col1.write(df_soma_sucatas_por_codigo)
    col2.metric('Peso total', f'{df_soma_sucatas_por_codigo["Sucata"].sum():.2f}KG') 
    col2.metric('Média diária', f'{media_diaria_porcentagem:.2f}%')  # Média diária em porcentagem

    # Calcular a média mensal em porcentagem usando os valores da coluna 'Aprov.'
    media_mensal_porcentagem = df_corte_filtrado['Aprov.'].mean() * 100

    col2.metric('Média mensal', f'{media_mensal_porcentagem:.2f}%')  # Média mensal em porcentagem

    

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

    # Exibir um gráfico para cada mês
    for mes in meses_disponiveis:
        try:
            # Filtrar os dados para o mês atual
            df_corte_filtrado = df_corte[df_corte['Data'].dt.month == mes]

            # Converter a coluna 'Sucata' para float
            df_corte_filtrado['Sucata'] = pd.to_numeric(df_corte_filtrado['Sucata'].str.replace(',', '.'), errors='coerce')

            # Remover linhas com valores NaN
            df_corte_filtrado = df_corte_filtrado.dropna(subset=['Sucata'])

            # Agrupar os dados por dia e somar os valores da coluna 'Sucata'
            dados_agrupados = df_corte_filtrado.groupby(df_corte_filtrado['Data'].dt.day)['Sucata'].sum()

            # Exibir o título com o mês atual
            st.title(f'Acompanhamento Sucata - {meses_dict[mes]}')

            # Personalizar o gráfico de barras para o mês atual
            st.bar_chart(dados_agrupados, color='#ffaa00', use_container_width=True)
        except KeyError:
            pass  # Ignora o erro KeyError e continua o loop

# Função principal
def main():
    # Adicione um seletor de páginas na barra lateral
    page = st.sidebar.selectbox("Escolha uma página", ["Apontamento Sucata", "Acompanhamento Sucata"])

    # Exiba a página selecionada
    if page == "Apontamento Sucata":
        Apontamento_Sucata()
    elif page == "Acompanhamento Sucata":
        Acompanhamento_Sucata()

if __name__ == "__main__":
    main()
