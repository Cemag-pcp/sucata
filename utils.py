from google.oauth2 import service_account
import gspread
import streamlit as st

def connect_google_sheet():
    
    service_account_info = st.secrets["GOOGLE_SERVICE_ACCOUNT"]
    scope = ['https://www.googleapis.com/auth/spreadsheets',
            "https://www.googleapis.com/auth/drive"]
    credentials = service_account.Credentials.from_service_account_info(service_account_info, scopes=scope)
    client = gspread.authorize(credentials)    
    
    return client