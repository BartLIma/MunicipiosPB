import re
import unicodedata
import requests
import streamlit as st
from bs4 import BeautifulSoup

# =============================================================================
# 1. CONFIGURAÇÕES DA APLICAÇÃO
# =============================================================================
st.set_page_config(
    page_title="Consulta FAMUP - PB",
    page_icon="🗺️",
    layout="centered"
)

FAMUP_BASE_URL = "https://famup.org.br/paraiba"
HTTP_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

# =============================================================================
# 2. TRANSFORMAÇÃO DO NOME (GERAÇÃO DA URL)
# =============================================================================
def normalizar_slug_municipio(nome_municipio: str) -> str:
    slug = nome_municipio.strip().lower()
    slug = ''.join(
        c for c in unicodedata.normalize('NFD', slug)
        if unicodedata.category(c) != 'Mn'
    )
    slug = slug.replace(" ", "-")
    slug = re.sub(r'[^a-z0-9\-]', '', slug)
    slug = re.sub(r'-+', '-', slug)
    return slug

# =============================================================================
# 3. EXTRAÇÃO DE DADOS POR VARREDURA TEXTUAL DIRETAL
# =============================================================================
def extrair_dados_famup(municipio: str) -> dict | str:
    slug = normalizar_slug_municipio(municipio)
    url_direta = f"{FAMUP_BASE_URL}/{slug}/"
    
    try:
        response = requests.get(url_direta, headers=HTTP_HEADERS, timeout=10)
        
        if response.status_code == 404:
            return f"❌ O endereço direto não foi encontrado no servidor da FAMUP.\nLink tentado: {url_direta}"
        elif response.status_code != 200:
            return f"❌ Erro de conexão com o portal da FAMUP (Código: {response.status_code})."
        
        soup = BeautifulSoup(response.text, 'html.parser')
        dados_coletados = {}
        
        # Mapeamento exato de acordo com o texto bruto retornado pelo site
        mapeamento = {
            'razão social': 'Razão Social',
            'endereço': 'Endereço',
            'site': 'Site Oficial',
            'telefones': 'Telefones',
            'emails': 'E-mails de Contato',
            'prefeito': 'Prefeito Atual'
        }
        
        # Quebra todo o texto visível da página em linhas limpas
        linhas_pagina = [re.sub(r'\s+', ' ', l).strip() for l in soup.get_text().split('\n') if l.strip()]
        
        # Varredura inteligente de texto por proximidade de linhas
        for i, linha in enumerate(linhas_pagina):
            linha_lower = linha.lower()
            
            for termo_html, label_interface in mapeamento.items():
                # Se achamos a linha com o rótulo exato
                if linha_lower == termo_html:
                    # Olhamos até 4 linhas para baixo para achar o valor correspondente
                    for j in range(1, 5):
                        if i + j < len(linhas_pagina):
                            candidato_valor = linhas_pagina[i + j]
                            
                            # Filtro: O valor não pode ser o menu lateral nem outro rótulo conhecido
                            if "Água Branca" in candidato_valor or candidato_valor.lower() in mapeamento:
                                continue
                            
                            # Filtro específico para o campo de redes sociais ou links gerais vazios
                            if candidato_valor in ['-', 'Bandeira', 'Dados Gerais']:
                                continue
                                
                            # Se passou nos filtros, salvamos e paramos a busca deste campo
                            dados_coletados[label_interface] = candidato_valor
                            break

        if not dados_coletados:
            return f"⚠️ O link existia ({url_direta}), mas os dados internos não puderam ser processados."
            
        return dados_coletados

    except Exception as e:
        return f"❌ Erro ao tentar acessar o link [{url_direta}]: {e}"

# =============================================================================
# 4. INTERFACE DO USUÁRIO (STREAMLIT)
# =============================================================================
st.title("🗺️ Painel de Consulta - Municípios da Paraíba")
st.markdown("Insira o nome de um município para acessar diretamente os dados na FAMUP.")

nome_busca = st.text_input("Nome do Município:", placeholder="Ex: Aguiar, Alagoa Grande, Sapé")

if st.button("Buscar Informações", type="primary"):
    if nome_busca.strip():
        st.empty()
        
        with st.spinner("Conectando ao endereço e processando dados..."):
            resultado = extrair_dados_famup(nome_busca)
        
        if isinstance(resultado, dict):
            st.success("📊 Dados recuperados com sucesso!")
            
            # Exibição direta e limpa na tela
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
        else:
            st.error(resultado)
    else:
        st.warning("⚠️ Digite o nome de um município para realizar a operação.")
