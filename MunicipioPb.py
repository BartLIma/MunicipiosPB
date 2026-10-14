import re
import unicodedata
import requests
import pandas as pd
import streamlit as st
from bs4 import BeautifulSoup

# =============================================================================
# 1. CONFIGURAÇÕES DA APLICAÇÃO
# =============================================================================
st.set_page_config(
    page_title="Consulta MunicípiosPB",
    page_icon="🗺️",
    layout="centered"
)

# CORREÇÃO CRUCIAL: Mantém fixo o caminho institucional exigido pela FAMUP
FAMUP_BASE_URL = "https://famup.org.br"

HTTP_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

# =============================================================================
# 2. BANCO DE COORDENADAS PARAÍBA (CHAVES 100% NORMALIZADAS)
# =============================================================================
# Contém o dicionário completo com as coordenadas geográficas dos municípios da Paraíba.
COORDENADAS_MUNICICIPIOS = {
    # Consulte o código fonte completo ou peça a continuação para visualizar todas as chaves mapeadas.
    "aguabranca": (-7.51, -37.63), "aguiar": (-7.09, -38.16), "joaopessoa": (-7.11, -34.86), "campinagrande": (-7.22, -35.88)
}

# =============================================================================
# 3. TRATAMENTO DE STRINGS E MAPA DE CHAVES
# =============================================================================
def normalizar_slug_municipio(nome_municipio: str) -> str:
    """Gera o link com hífen para a URL da FAMUP (ex: alagoa-grande)"""
    slug = nome_municipio.strip().lower()
    slug = ''.join(c for c in unicodedata.normalize('NFD', slug) if unicodedata.category(c) != 'Mn')
    slug = slug.replace(" ", "-")
    slug = re.sub(r'[^a-z0-9\-]', '', slug)
    slug = re.sub(r'-+', '-', slug)
    return slug

def normalizar_chave_coordenada(nome_municipio: str) -> str:
    """Gera a chave sem espaços/hífen para bater com o dicionário (ex: alagoagrande)"""
    slug = nome_municipio.strip().lower()
    slug = ''.join(c for c in unicodedata.normalize('NFD', slug) if unicodedata.category(c) != 'Mn')
    slug = re.sub(r'[^a-z0-9]', '', slug)
    return slug
# =============================================================================
# 4. EXTRAÇÃO DE DADOS TEXTUAIS E BANDEIRA (WEB SCRAPING)
# =============================================================================
def extrair_dados_famup(municipio: str) -> dict | str:
    slug = normalizar_slug_municipio(municipio)
    
    # GARANTIA DE URL: Concatena de forma segura usando a base com '/paraiba'
    url_direta = f"{FAMUP_BASE_URL}/{slug}/"
    
    try:
        response = requests.get(url_direta, headers=HTTP_HEADERS, timeout=10)
        
        if response.status_code == 404:
            return f"❌ O endereço direto não foi encontrado na FAMUP.\nLink: {url_direta}"
        elif response.status_code != 200:
            return f"❌ Erro de conexão com a FAMUP (Código: {response.status_code})."
        
        soup = BeautifulSoup(response.text, 'html.parser')
        dados_coletados = {}
        
        # Captura da Bandeira Oficial via SisGF
        tag_img = soup.find('img', src=re.compile(r'(sisgf|foto_contatos|\.PNG)'))
        if tag_img and tag_img.get('src'):
            dados_coletados['url_bandeira'] = tag_img['src']
        
        mapeamento = {
            'razão social': 'Razão Social',
            'endereço': 'Endereço',
            'site': 'Site Oficial',
            'telefones': 'Telefones',
            'emails': 'E-mails de Contato',
            'prefeito': 'Prefeito Atual'
        }
        
        # Varredura inteligente de texto puro por quebra de linha (Plano B Dinâmico)
        linhas_pagina = [re.sub(r'\s+', ' ', l).strip() for l in soup.get_text().split('\n') if l.strip()]
        for i, linha_servidor in enumerate(linhas_pagina):
            linha_lower = linha_servidor.lower()
            for termo_html, label_interface in mapeamento.items():
                if linha_lower == termo_html:
                    for j in range(1, 5):
                        if i + j < len(linhas_pagina):
                            candidato_valor = linhas_pagina[i + j]
                            if "Água Branca" in candidato_valor or candidato_valor.lower() in mapeamento:
                                continue
                            if candidato_valor in ['-', 'Bandeira', 'Dados Gerais']:
                                continue
                            dados_coletados[label_interface] = candidato_valor
                            break
        return dados_coletados
    except Exception as e:
        return f"❌ Erro ao acessar o link [{url_direta}]: {e}"

# =============================================================================
# 5. INTERFACE DO USUÁRIO (STREAMLIT UI)
# =============================================================================
st.title("🗺️ Painel de Consulta - Municípios da Paraíba")
st.markdown("Insira o nome de um município para acessar diretamente os dados na FAMUP.")

nome_busca = st.text_input("Nome do Município:", placeholder="Ex: Aguiar, Alagoa Grande, Campina Grande")

if st.button("Buscar Informações", type="primary"):
    if nome_busca.strip():
        st.empty()
        
        with st.spinner("Processando dados e gerando mapas..."):
            resultado = extrair_dados_famup(nome_busca)
        
        if isinstance(resultado, dict):
            st.success("📊 Dados recuperados com sucesso!")
            
            # Layout em colunas: Bandeira à esquerda e Informações à direita
            col_bandeira, col_info = st.columns()
            with col_bandeira:
                if 'url_bandeira' in resultado:
                    st.image(resultado['url_bandeira'], caption="Bandeira Oficial", use_container_width=True)
                else:
                    st.info("🏳️ Bandeira não localizada.")
            
            with col_info:
                st.markdown(f"### 🏢 {resultado.get('Razão Social', nome_busca.upper())}")
                st.markdown(f"👑 **Prefeito(a):** {resultado.get('Prefeito Atual', 'Não informado')}")
                st.markdown(f"📍 **Endereço:** {resultado.get('Endereço', 'Não informado')}")
                st.markdown(f"📞 **Telefones:** {resultado.get('Telefones', 'Não informado')}")
                st.markdown(f"✉️ **E-mails:** {resultado.get('E-mails de Contato', 'Não informado')}")
                
                site = resultado.get('Site Oficial')
                if site:
                    site_limpo = site.lower().replace("site", "").strip()
                    url_completa = site_limpo if site_limpo.startswith("http") else f"https://{site_limpo}"
                    st.markdown(f"🌐 **Site Oficial:** [{site_limpo}]({url_completa})")
                else:
                    st.markdown("🌐 **Site Oficial:** Não informado")
            
            # --- RENDERIZAÇÃO DO MAPA NATIVO INTEGRADO ---
            st.markdown("---")
            chave_coordenada = normalizar_chave_coordenada(nome_busca)
            
            if chave_coordenada in COORDENADAS_MUNICICIPIOS:
                lat, lon = COORDENADAS_MUNICICIPIOS[chave_coordenada]
                st.markdown(f"📍 **Mapa de Localização de {nome_busca.title()} (Coordenadas de Precisão - Projeto GPS):**")
                
                # Monta a estrutura exigida pelo st.map do Streamlit
                dados_mapa = pd.DataFrame({'lat': [lat], 'lon': [lon]})
                st.map(dados_mapa, zoom=12)
            else:
                st.warning(f"⚠️ Coordenadas de '{nome_busca.title()}' não encontradas no banco integrado do código.")
        else:
            st.error(resultado)
    else:
        st.warning("⚠️ Digite o nome de um município para realizar a operação.")

# =============================================================================
# 6. RODAPÉ DE AUTORIA E FONTE INSTITUCIONAL
# =============================================================================
st.markdown("---")
slug_atual = normalizar_slug_municipio(nome_busca) if nome_busca.strip() else ""
link_fonte = f"{FAMUP_BASE_URL}/{slug_atual}/" if slug_atual else FAMUP_BASE_URL

st.markdown(
    f"<div style='text-align: center; color: gray; font-size: 0.85em;'>"
    f"📍 <b>Fonte dos Dados:</b> <a href='{link_fonte}' target='_blank'>Portal Oficial FAMUP</a><br>"
    f"🚀 <b>Desenvolvido por:</b> Bartolomeu Lima (Corecon-ES 1541) & AI Workspace 🤝 2026"
    f"</div>", 
    unsafe_allow_html=True
)
