import streamlit as st
import requests
from bs4 import BeautifulSoup
import unicodedata
import re

# Configuração da página do Streamlit (deve ser a primeira linha de comando do st)
st.set_page_config(page_title="Consulta FAMUP - PB", page_icon="🗺️", layout="centered")

def normalizar_nome_municipio(nome):
    """Remove acentos, caracteres especiais e espaços para gerar o slug da URL."""
    nome = nome.strip().lower()
    nome_sem_acentos = ''.join(
        c for c in unicodedata.normalize('NFD', nome)
        if unicodedata.category(c) != 'Mn'
    )
    nome_com_hifens = nome_sem_acentos.replace(" ", "-")
    slug_final = re.sub(r'[^a-z0-9\-]', '', nome_com_hifens)
    slug_final = re.sub(r'-+', '-', slug_final)
    return slug_final

def consultar_municipio_famup(municipio):
    municipio_formatado = normalizar_nome_municipio(municipio)
    url = f"https://famup.org.br/paraiba/{municipio_formatado}/"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10) # Timeout evita travamento se o site cair
        
        if response.status_code == 404:
            return f"❌ Município '{municipio}' não encontrado na FAMUP. Verifique a grafia."
        elif response.status_code != 200:
            return f"❌ Erro ao acessar o site da FAMUP (Código: {response.status_code})."
        
        soup = BeautifulSoup(response.text, 'html.parser')
        dados_municipio = {}
        
        mapeamento = {
            'Razão social': 'Razão Social',
            'Endereço': 'Endereço',
            'Site': 'Site Oficial',
            'Telefones': 'Telefones',
            'Emails': 'E-mails de Contato',
            'Prefeito': 'Prefeito Atual'
        }
        
        for label_site, label_amigavel in mapeamento.items():
            tag_label = soup.find(lambda tag: tag.name in ['h5', 'h4', 'div', 'p', 'b'] and label_site in tag.text)
            if tag_label:
                elemento_valor = tag_label.find_next()
                if elemento_valor:
                    dados_municipio[label_amigavel] = elemento_valor.text.strip()
        
        if not dados_municipio:
            return "⚠️ Página encontrada, mas a estrutura de dados não pôde ser lida pelo robô."
            
        return dados_municipio

    except requests.exceptions.Timeout:
        return "❌ O site da FAMUP demorou muito para responder (Tempo limite esgotado)."
    except Exception as e:
        return f"❌ Ocorreu um erro de conexão: {e}"

# --- INTERFACE WEB STREAMLIT ---
st.title("🗺️ Consulta de Municípios da Paraíba (FAMUP)")
st.write("Digite o nome de uma cidade para extrair os dados institucionais direto do portal oficial.")

# Componente de entrada de texto na web (substitui o 'input' do terminal)
municipio_alvo = st.text_input("Nome do Município:", placeholder="Ex: Aguiar, Sapé, Campina Grande")

# Botão para disparar a ação
if st.button("Buscar Dados", type="primary"):
    if municipio_alvo:
        # Mostra uma animação charmosa de carregamento enquanto o robô trabalha
        with st.spinner(f"Buscando dados no portal da FAMUP..."):
            resultado = consultar_municipio_famup(municipio_alvo)
        
        # Exibe os resultados de forma organizada na interface web
        if isinstance(resultado, dict):
            st.success("📊 Dados encontrados com sucesso!")
            
            # Criando cartões visuais para os dados
            for chave, valor in resultado.items():
                st.markdown(f"**{chave}:** {valor}")
        else:
            st.error(resultado)
    else:
        st.warning("⚠️ Por favor, digite o nome de um município antes de buscar.")
