import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import locale
import altair as alt
from utils import *

# Definir locale
try:
    locale.setlocale(locale.LC_NUMERIC, '')
except locale.Error as e:
    print("Erro ao definir o locale:", e)

st.set_page_config(layout='wide', page_title='PCP CEMAG')

# Autenticação e acesso ao Google Sheets
client = connect_google_sheet()
document_id = '1t7Q_gwGVAEwNlwgWpLRVy-QbQo7kQ_l6QTjFjBrbWxE'
planilha1 = client.open_by_key(document_id)
nome_da_aba = 'RQ PCP-003-000 (Transferencia Corte)'
planilha_worksheet1 = planilha1.worksheet(nome_da_aba)

# Ler os dados da planilha
dados_corte = planilha_worksheet1.get_all_values()
df_corte = pd.DataFrame(dados_corte[5:], columns=dados_corte[4])

# Converter a coluna 'Data' para datetime
df_corte['Data'] = pd.to_datetime(df_corte['Data'], format='%d/%m/%Y')

# Dicionário de meses
meses_dict = {
    1: 'Janeiro', 2: 'Fevereiro', 3: 'Março', 4: 'Abril',
    5: 'Maio', 6: 'Junho', 7: 'Julho', 8: 'Agosto',
    9: 'Setembro', 10: 'Outubro', 11: 'Novembro', 12: 'Dezembro'
}

# Função para converter colunas numéricas
def converter_colunas(df, colunas):
    for col in colunas:
        df[col] = pd.to_numeric(df[col].str.replace(',', '.'), errors='coerce')
    return df.dropna(subset=colunas)

# Função para filtrar por mês
def filtrar_por_mes(df, mes_atual):
    return df[df['Data'].dt.month == mes_atual]

# Função para calcular perda
def calcular_perda(df):
    df['Perda'] = (df['Sucata'] / df['Peso']) * 100
    return df

# Função para gerar gráficos
def gerar_grafico(df, x_col, y_col, title):
    chart = alt.Chart(df).mark_bar(color='#de3502').encode(
        x=alt.X(f'{x_col}:O', title=x_col, axis=alt.Axis(labelAngle=0)),
        y=alt.Y(f'{y_col}:Q', title=y_col, scale=alt.Scale(domain=[0, 20]))  # Limite do gráfico
    ) + alt.Chart(pd.DataFrame({'y': [8.5]})).mark_rule(color='white').encode(y='y:Q')
    st.title(title)
    st.altair_chart(chart, use_container_width=True)

# Função principal de Apontamento de Sucata
def Apontamento_Sucata():
    mes_atual = pd.Timestamp.now().month
    df_filtrado = filtrar_por_mes(df_corte, mes_atual)
    df_filtrado = converter_colunas(df_filtrado, ['Sucata', 'Peso'])
    df_filtrado = calcular_perda(df_filtrado)

    # Agrupar por dia
    dados_agrupados = df_filtrado.groupby(df_filtrado['Data'].dt.day).agg({'Sucata': 'sum', 'Peso': 'sum'}).reset_index()
    dados_agrupados = calcular_perda(dados_agrupados)

    gerar_grafico(dados_agrupados, 'Data', 'Perda', 'Sucata')

# Função para acompanhamento de perda mensal
def Acompanhamento_Sucata():
    meses_disponiveis = df_corte['Data'].dt.month.unique()
    for mes in meses_disponiveis:
        df_filtrado = filtrar_por_mes(df_corte, mes)
        df_filtrado = converter_colunas(df_filtrado, ['Sucata', 'Peso'])
        df_filtrado = calcular_perda(df_filtrado)

        dados_agrupados = df_filtrado.groupby(df_filtrado['Data'].dt.day).agg({'Sucata': 'sum', 'Peso': 'sum'}).reset_index()
        dados_agrupados = calcular_perda(dados_agrupados)

        gerar_grafico(dados_agrupados, 'Data', 'Perda', f'Perda - {meses_dict[mes]}')

# Função para acompanhamento detalhado por chapa
def Acompanhamento_Por_Chapa():
    meses_disponiveis = df_corte['Data'].dt.month.unique()
    for mes in meses_disponiveis:
        df_filtrado = filtrar_por_mes(df_corte, mes)
        df_filtrado = converter_colunas(df_filtrado, ['Sucata', 'Peso'])
        df_filtrado = calcular_perda(df_filtrado)

        dados_agrupados = df_filtrado.groupby('Código Chapa').agg({'Sucata': 'sum', 'Peso': 'sum'}).reset_index()
        dados_agrupados = calcular_perda(dados_agrupados)

        gerar_grafico(dados_agrupados, 'Código Chapa', 'Perda', f'Acompanhamento por Chapa - {meses_dict[mes]}')

# Função principal
def main():
    page = st.sidebar.selectbox("Escolha uma página", ["Apontamento Sucata", "Perda", "Acompanhamento por Chapa"])

    if page == "Apontamento Sucata":
        Apontamento_Sucata()
    elif page == "Perda":
        Acompanhamento_Sucata()
    elif page == "Acompanhamento por Chapa":
        Acompanhamento_Por_Chapa()

if __name__ == "__main__":
    main()
