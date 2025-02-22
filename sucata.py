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

# Função para converter colunas numéricas corretamente
def formatar_valor(valor):
    if isinstance(valor, str):
        valor = valor.replace('.', '').replace(',', '.')  # Remove separador de milhar e ajusta decimal
    return pd.to_numeric(valor, errors='coerce')

# Função para a primeira página
def Apontamento_Sucata():
    mes_atual = pd.Timestamp.now().month
    df_corte_filtrado = df_corte[df_corte['Data'].dt.month == mes_atual]

    df_corte_filtrado['Sucata'] = df_corte_filtrado['Sucata'].apply(formatar_valor)
    df_corte_filtrado['Peso'] = df_corte_filtrado['Peso'].apply(formatar_valor)
    df_corte_filtrado['Aprov.'] = df_corte_filtrado['Aprov.'].apply(formatar_valor)

    df_corte_filtrado = df_corte_filtrado.dropna(subset=['Sucata', 'Peso', 'Aprov.'])
    
    # Agrupar por dia
    dados_agrupados = df_corte_filtrado.groupby(df_corte_filtrado['Data'].dt.day).agg({'Sucata': 'sum', 'Peso': 'sum'}).reset_index()
    dados_agrupados['Perda'] = (dados_agrupados['Sucata'] / dados_agrupados['Peso']) * 100
    
    st.title('Sucata')
    chart = alt.Chart(dados_agrupados).mark_bar(color='#de3502').encode(
        x=alt.X('Data:O', title='Dia'),
        y=alt.Y('Perda:Q', title='Perda (%)', scale=alt.Scale(domain=[0, 20]))
    ) + alt.Chart(pd.DataFrame({'y': [8.5]})).mark_rule(color='white').encode(y='y:Q')
    
    st.altair_chart(chart, use_container_width=True)

# Função para a segunda página
def Acompanhamento_Sucata():
    meses_dict = {
        1: 'Janeiro', 2: 'Fevereiro', 3: 'Março', 4: 'Abril', 5: 'Maio', 6: 'Junho',
        7: 'Julho', 8: 'Agosto', 9: 'Setembro', 10: 'Outubro', 11: 'Novembro', 12: 'Dezembro'
    }
    meses_disponiveis = df_corte['Data'].dt.month.unique()
    for mes in meses_disponiveis:
        df_corte_filtrado = df_corte[df_corte['Data'].dt.month == mes]
        df_corte_filtrado['Sucata'] = df_corte_filtrado['Sucata'].apply(formatar_valor)
        df_corte_filtrado['Peso'] = df_corte_filtrado['Peso'].apply(formatar_valor)
        df_corte_filtrado['Aprov.'] = df_corte_filtrado['Aprov.'].apply(formatar_valor)
        df_corte_filtrado = df_corte_filtrado.dropna(subset=['Sucata', 'Peso', 'Aprov.'])
        
        dados_agrupados = df_corte_filtrado.groupby(df_corte_filtrado['Data'].dt.day).agg({'Sucata': 'sum', 'Peso': 'sum'}).reset_index()
        dados_agrupados['Perda'] = (dados_agrupados['Sucata'] / dados_agrupados['Peso']) * 100
        
        st.title(f'Perda - {meses_dict[mes]}')
        st.altair_chart(
            alt.Chart(dados_agrupados).mark_bar(color='#de3502').encode(
                x=alt.X('Data:O', title='Dia'),
                y=alt.Y('Perda:Q', title='Perda (%)', scale=alt.Scale(domain=[0, 20]))
            ) + alt.Chart(pd.DataFrame({'y': [8.5]})).mark_rule(color='white').encode(y='y:Q'),
            use_container_width=True
        )

# Função para acompanhamento por chapa
def Acompanhamento_Por_Chapa():
    meses_disponiveis = df_corte['Data'].dt.month.unique()
    for mes in meses_disponiveis:
        df_corte_filtrado = df_corte[df_corte['Data'].dt.month == mes]
        df_corte_filtrado['Sucata'] = df_corte_filtrado['Sucata'].apply(formatar_valor)
        df_corte_filtrado['Peso'] = df_corte_filtrado['Peso'].apply(formatar_valor)
        df_corte_filtrado['Aprov.'] = df_corte_filtrado['Aprov.'].apply(formatar_valor)
        df_corte_filtrado = df_corte_filtrado.dropna(subset=['Sucata', 'Peso', 'Aprov.'])
        
        dados_agrupados = df_corte_filtrado.groupby('Código Chapa').agg({'Sucata': 'sum', 'Peso': 'sum'}).reset_index()
        dados_agrupados['Perda'] = (dados_agrupados['Sucata'] / dados_agrupados['Peso']) * 100
        
        st.title(f'Acompanhamento por Chapa - {mes}')
        st.altair_chart(
            alt.Chart(dados_agrupados).mark_bar(color='#de3502').encode(
                x=alt.X('Código Chapa:O', title='Código da Chapa'),
                y=alt.Y('Perda:Q', title='Perda (%)', scale=alt.Scale(domain=[0, 50]))
            ) + alt.Chart(pd.DataFrame({'y': [8.5]})).mark_rule(color='white').encode(y='y:Q'),
            use_container_width=True
        )

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
