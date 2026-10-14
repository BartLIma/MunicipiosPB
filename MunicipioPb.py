import streamlit as st
import requests
from bs4 import BeautifulSoup
import unicodedata
import re

# Configuração da página do Streamlit (deve ser a primeira linha de comando do st)
st.set_page_config(page_title="Consulta FAMUP - PB", page_icon="🗺️", layout="centered")

def consultar_municipio_famup(municipio):
    municipio_formatado = normalizar_nome_municipio(municipio)
    url = f"https://famup.org.br/paraiba/{municipio_formatado}/"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 404:
            return f"❌ Município '{municipio}' não encontrado na FAMUP. Verifique a grafia."
        elif response.status_code != 200:
            return f"❌ Erro ao acessar o site da FAMUP (Código: {response.status_code})."
        
        soup = BeautifulSoup(response.text, 'html.parser')
        dados_municipio = {}
        
        # Mapeamento estrito dos termos que queremos capturar
        mapeamento = {
            'Razão social': 'Razão Social',
            'Endereço': 'Endereço',
            'Site': 'Site Oficial',
            'Telefones': 'Telefones',
            'Emails': 'E-mails de Contato',
            'Prefeito': 'Prefeito Atual'
        }
        
        for label_site, label_amigavel in mapeamento.items():
            # Buscamos a tag exata (geralmente h5 ou p) que contém o rótulo
            tag_label = soup.find(lambda tag: tag.name in ['h5', 'h4', 'p', 'b', 'strong'] and label_site.lower() == tag.text.strip().lower())
            
            if tag_label:
                # Pegamos o texto do elemento irmão seguinte
                elemento_valor = tag_label.find_next()
                if elemento_valor:
                    texto_limpo = elemento_valor.text.strip()
                    
                    # FILTRO DE SUJEIRA: Se o robô capturar o menu lateral de cidades por engano, descartamos.
                    # O menu lateral contém mais de 1000 caracteres todos grudados.
                    if "Água Branca" in texto_limpo and len(texto_limpo) > 500:
                        continue
                        
                    # Remove múltiplos espaços em branco, quebras de linha e tabulações internas
                    texto_limpo = re.sub(r'\s+', ' ', texto_limpo).strip()
                    
                    # Remove barras verticais órfãs no final de telefones ou e-mails
                    texto_limpo = re.sub(r'\s*\|\s*$', '', texto_limpo)
                    
                    dados_municipio[label_amigavel] = texto_limpo
        
        if not dados_municipio:
            return "⚠️ Página encontrada, mas os dados principais não puderam ser isolados."
            
        return dados_municipio

    except requests.exceptions.Timeout:
        return "❌ O site da FAMUP demorou muito para responder."
    except Exception as e:
        return f"❌ Ocorreu um erro: {e}"
