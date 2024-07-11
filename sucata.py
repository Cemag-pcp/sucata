import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import locale
import altair as alt

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
scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)
client = gspread.authorize(creds)

# ID do documento do Google Sheets
document_id = '1t7Q_gwGVAEwNlwgWpLRVy-QbQo7kQ_l6QTjFjBrbWxE'

# Acesse o documento pelo ID
planilha1 = client.open_by_key(document_id)

# Busque a aba pelo nome
nome_da_aba = 'RQ PCP-003-000 (Transferencia)'
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

    # Converter a coluna 'Sucata' para float
    df_corte_filtrado['Sucata'] = pd.to_numeric(df_corte_filtrado['Sucata'].str.replace(',', '.'), errors='coerce')

    # Remover linhas com valores NaN
    df_corte_filtrado = df_corte_filtrado.dropna(subset=['Sucata'])

    # Converter a coluna 'Aprov.' para float, se necessário
    if df_corte_filtrado['Aprov.'].dtype == 'object':
        df_corte_filtrado['Aprov.'] = pd.to_numeric(df_corte_filtrado['Aprov.'].str.replace(',', '.'), errors='coerce')

    # Calcular a porcentagem de aproveitamento
    df_corte_filtrado['Aproveitamento'] = df_corte_filtrado['Aprov.'] * 100

    # Agrupar os dados por dia e calcular a média da porcentagem de aproveitamento
    dados_agrupados = df_corte_filtrado.groupby(df_corte_filtrado['Data'].dt.day)['Aproveitamento'].mean().reset_index()

    # Exibir o título
    st.title('Aproveitamento')

    # Criar o gráfico de barras com a linha de 92%
    chart = alt.Chart(dados_agrupados).mark_bar(color='#ffaa00').encode(
    x=alt.X('Data:O', title='Dia', axis=alt.Axis(labelAngle=0)),
    y=alt.Y('Aproveitamento:Q', title='Aproveitamento (%)'),
    ) + alt.Chart(pd.DataFrame({'y': [92]})).mark_rule(color='red').encode(y='y:Q')

    # Exibir o gráfico
    st.altair_chart(chart, use_container_width=True)

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

    # Calcular a porcentagem de aproveitamento
    df_filtrado_por_data['Aproveitamento'] = df_filtrado_por_data['Aprov.'] * 100

    # Agrupar os dados por código de chapa e calcular a média da porcentagem de aproveitamento
    df_soma_sucatas_por_codigo = df_filtrado_por_data.groupby('Código Chapa')['Aproveitamento'].mean().reset_index()

    # Calcular a média diária em porcentagem usando os valores da coluna 'Aprov.'
    media_diaria_porcentagem = df_filtrado_por_data['Aprov.'].mean() * 100

    # Calcular a média mensal em porcentagem usando os valores da coluna 'Aprov.'
    media_mensal_porcentagem = df_corte_filtrado['Aprov.'].mean() * 100

    # Exibir DataFrame
    st.write(f'### Apontamento sucata: {data_selecionada_str}')
    col1, col2, col3 = st.columns(3)
    col1.write(df_soma_sucatas_por_codigo)
    col2.metric('Peso total', f'{df_filtrado_por_data["Sucata"].sum():.2f}KG') 
    col2.metric('Média de sucata diária', f'{100 - media_diaria_porcentagem:.2f}%')  # Média diária em porcentagem
    col2.metric('Média média de sucata mensal', f'{100 - media_mensal_porcentagem:.2f}%')  # Média mensal em porcentagem

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

            # Converter a coluna 'Sucata' para float
            df_corte_filtrado['Sucata'] = pd.to_numeric(df_corte_filtrado['Sucata'].str.replace(',', '.'), errors='coerce')

            # Remover linhas com valores NaN
            df_corte_filtrado = df_corte_filtrado.dropna(subset=['Sucata'])

            # Converter a coluna 'Aprov.' para float, tratando valores não numéricos como NaN
            df_corte_filtrado['Aprov.'] = pd.to_numeric(df_corte_filtrado['Aprov.'].str.replace(',', '.'), errors='coerce')

            # Remover linhas com valores NaN após a conversão
            df_corte_filtrado = df_corte_filtrado.dropna(subset=['Aprov.'])

            # Calcular a porcentagem de aproveitamento
            df_corte_filtrado['Aproveitamento'] = df_corte_filtrado['Aprov.'] * 100

            # Se houver dados suficientes para calcular a média de aproveitamento
            if not df_corte_filtrado.empty:
                # Calcular a média de aproveitamento para o mês atual
                media_aproveitamento = df_corte_filtrado['Aprov.'].mean() * 100

                # Agrupar os dados por dia e calcular a média da porcentagem de aproveitamento
                dados_agrupados = df_corte_filtrado.groupby(df_corte_filtrado['Data'].dt.day)['Aproveitamento'].mean().reset_index()

                # Exibir o título com o mês atual e a média de aproveitamento
                if chapa_selecionada:
                    st.title(f'Aproveitamento - {meses_dict[mes]} - Chapa {chapa_selecionada}')
                else:
                    st.title(f'Aproveitamento - {meses_dict[mes]}')

                if filtrar_por_data:
                    st.write(f'Filtrado de {data_inicio} até {data_fim}')

                st.write(f'Média de aproveitamento: {media_aproveitamento:.2f}%')

                # Criar o gráfico de barras com a linha de 92%
                chart = alt.Chart(dados_agrupados).mark_bar(color='#ffaa00').encode(
                    x=alt.X('Data:O', title='Dia', axis=alt.Axis(labelAngle=0)),
                    y=alt.Y('Aproveitamento:Q', title='Aproveitamento (%)')
                ) + alt.Chart(pd.DataFrame({'y': [92]})).mark_rule(color='red').encode(y='y:Q')

                # Exibir o gráfico
                st.altair_chart(chart, use_container_width=True)
        except KeyError:
            pass  # Ignora o erro KeyError e continua o loop

# Função para acompanhamento detalhado por chapa (histórico mensal)
def Acompanhamento_Por_Chapa():
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
            df_corte_filtrado = df_corte_filtrado.dropna(subset=['Sucata'])

            # Converter a coluna 'Aprov.' para float, tratando valores não numéricos como NaN
            df_corte_filtrado['Aprov.'] = pd.to_numeric(df_corte_filtrado['Aprov.'].str.replace(',', '.'), errors='coerce')
            df_corte_filtrado = df_corte_filtrado.dropna(subset=['Aprov.'])

            # Calcular a porcentagem de aproveitamento
            df_corte_filtrado['Aproveitamento'] = df_corte_filtrado['Aprov.'] * 100

            # Agrupar os dados por chapa e calcular a média da porcentagem de aproveitamento
            dados_agrupados = df_corte_filtrado.groupby('Código Chapa')['Aproveitamento'].mean().reset_index()

            # Calcular a média de aproveitamento para o mês
            media_aproveitamento_mes = df_corte_filtrado['Aproveitamento'].mean()

            # Exibir o título com o mês atual e a média de aproveitamento
            st.title(f'Acompanhamento por Chapa - {meses_dict[mes]}')
            st.write(f'Média de aproveitamento: {media_aproveitamento_mes:.2f}%')

            # Criar o gráfico de barras com a linha de 92%
            chart = alt.Chart(dados_agrupados).mark_bar(color='#ffaa00').encode(
                x=alt.X('Código Chapa:O', title='Código da Chapa', axis=alt.Axis(labelAngle = 90)),
                y=alt.Y('Aproveitamento:Q', title='Aproveitamento (%)')
            ) + alt.Chart(pd.DataFrame({'y': [92]})).mark_rule(color='red').encode(y='y:Q')

            # Exibir o gráfico
            st.altair_chart(chart, use_container_width=True)
        except KeyError:
            pass  # Ignora o erro KeyError e continua o loop

# Função principal
def main():
    # Adicione um seletor de páginas na barra lateral
    page = st.sidebar.selectbox("Escolha uma página", ["Apontamento Sucata", "Aproveitamento", "Acompanhamento por Chapa"])

    # Exiba a página selecionada
    if page == "Apontamento Sucata":
        Apontamento_Sucata()
    elif page == "Aproveitamento":
        Acompanhamento_Sucata()
    elif page == "Acompanhamento por Chapa":
        Acompanhamento_Por_Chapa()

if __name__ == "__main__":
    main()
