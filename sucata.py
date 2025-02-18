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

    # Converter as colunas 'Sucata' e 'Peso' para float
    df_corte_filtrado['Sucata'] = pd.to_numeric(df_corte_filtrado['Sucata'].str.replace(',', '.'), errors='coerce')
    df_corte_filtrado['Peso'] = pd.to_numeric(df_corte_filtrado['Peso'].str.replace(',', '.'), errors='coerce')

    # Remover linhas com valores NaN
    df_corte_filtrado = df_corte_filtrado.dropna(subset=['Sucata', 'Peso'])

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
    st.title('Sucata')

    # Criar o gráfico de barras
    chart = alt.Chart(dados_agrupados).mark_bar(color='#de3502').encode(
        x=alt.X('Data:O', title='Dia', axis=alt.Axis(labelAngle=0)),
        y=alt.Y('Perda:Q', title='Perda (%)', scale=alt.Scale(domain=[0, 20]))
    ) + alt.Chart(pd.DataFrame({'y': [8.5]})).mark_rule(color='white').encode(y='y:Q')

    st.altair_chart(chart, use_container_width=True)

    # Sidebar
    st.sidebar.title('Filtrar por Data')
    data_selecionada = st.sidebar.date_input('Selecione uma data', value=pd.Timestamp.now())

    # Filtrar os dados com base na data selecionada
    df_filtrado_por_data = df_corte[df_corte['Data'].dt.date == data_selecionada]

    # Converter colunas para numérico
    df_filtrado_por_data['Sucata'] = pd.to_numeric(df_filtrado_por_data['Sucata'].str.replace(',', '.'), errors='coerce')
    df_filtrado_por_data['Peso'] = pd.to_numeric(df_filtrado_por_data['Peso'].str.replace(',', '.'), errors='coerce')

    # Remover valores NaN
    df_filtrado_por_data = df_filtrado_por_data.dropna(subset=['Sucata', 'Peso'])

    # Agrupar por Código Chapa
    df_soma_sucatas_por_codigo = df_filtrado_por_data.groupby('Código Chapa').agg({
        'Sucata': 'sum',
        'Peso': 'sum'
    }).reset_index()

    # Calcular a perda
    df_soma_sucatas_por_codigo['Perda'] = (df_soma_sucatas_por_codigo['Sucata'] / df_soma_sucatas_por_codigo['Peso']) * 100

    # Calcular médias
    media_diaria_porcentagem = (df_soma_sucatas_por_codigo['Sucata'].sum() / df_soma_sucatas_por_codigo['Peso'].sum()) * 100
    media_mensal_porcentagem = (df_corte_filtrado['Sucata'].sum() / df_corte_filtrado['Peso'].sum()) * 100

    # Exibir resultados
    st.write(f'### Apontamento sucata: {data_selecionada}')
    col1, col2, col3 = st.columns(3)
    col1.write(df_soma_sucatas_por_codigo)
    col2.metric('Sucata total', f'{df_soma_sucatas_por_codigo["Sucata"].sum():.2f} KG')
    col2.metric('Média de sucata diária', f'{media_diaria_porcentagem:.2f}%')
    col2.metric('Média de sucata mensal', f'{media_mensal_porcentagem:.2f}%')

# Função para a segunda página
def Acompanhamento_Sucata():
    st.title("Acompanhamento de Sucata")

    # Filtrar os dados por mês
    df_corte_filtrado = df_corte.copy()

    # Agrupar por mês e calcular médias
    df_corte_filtrado['Mês'] = df_corte_filtrado['Data'].dt.month
    df_agrupado = df_corte_filtrado.groupby('Mês').agg({
        'Sucata': 'sum',
        'Peso': 'sum'
    }).reset_index()
    df_agrupado['Perda'] = (df_agrupado['Sucata'] / df_agrupado['Peso']) * 100

    # Criar gráfico
    chart = alt.Chart(df_agrupado).mark_bar(color='#de3502').encode(
        x=alt.X('Mês:O', title='Mês'),
        y=alt.Y('Perda:Q', title='Perda (%)', scale=alt.Scale(domain=[0, 20]))
    )

    st.altair_chart(chart, use_container_width=True)

# Função principal
def main():
    page = st.sidebar.selectbox("Escolha uma página", ["Apontamento Sucata", "Acompanhamento Sucata"])

    if page == "Apontamento Sucata":
        Apontamento_Sucata()
    elif page == "Acompanhamento Sucata":
        Acompanhamento_Sucata()

if __name__ == "__main__":
    main()
