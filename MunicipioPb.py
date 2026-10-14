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
# 2. TRANSFORMAÇÃO DO NOME
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
# 3. CONSTRUÇÃO DIRETA DO LINK E CAPTURA DE DADOS
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
        
        # Mapeamento flexível dos termos que aparecem antes dos valores
        mapeamento = {
            'razão social': 'Razão Social',
            'endereço': 'Endereço',
            'site': 'Site Oficial',
            'telefones': 'Telefones',
            'emails': 'E-mails de Contato',
            'prefeito': 'Prefeito Atual'
        }
        
        # Estratégia de Varredura Ampla por Tags do Site
        tags_texto = soup.find_all(['h5', 'h4', 'p', 'b', 'strong', 'div'])
        
        for tag in tags_texto:
            texto_tag = tag.text.strip().lower() if tag.text else ""
            
            for termo_html, label_interface in mapeamento.items():
                # Se encontrarmos o rótulo (ex: "prefeito") dentro do texto da tag
                if termo_html in texto_tag and len(texto_tag) < 30:
                    # O valor real está no próximo elemento de texto disponível no HTML
                    proxima_tag = tag.find_next()
                    if proxima_tag:
                        valor = proxima_tag.text.strip()
                        
                        # Filtro de Segurança para descartar o menu lateral de 223 cidades
                        if "Água Branca" in valor and len(valor) > 200:
                            continue
                        
                        # Limpeza profunda de espaços e formatação
                        valor_limpo = re.sub(r'\s+', ' ', valor).strip()
                        valor_limpo = re.sub(r'\s*\|\s*$', '', valor_limpo)
                        
                        # Armazena se houver conteúdo válido e evita sobrescrever com vazios
                        if valor_limpo and label_interface not in dados_coletados:
                            dados_coletados[label_interface] = valor_limpo

        if not dados_coletados:
            return f"⚠️ O link existia ({url_direta}), mas os dados internos não puderam ser processados."
            
        return dados_coletados

    except Exception as e:
        return f"❌ Erro ao tentar acessar o link [{url_direta}]: {e}"

# =============================================================================
# 4. INTERFACE DO USUÁRIO (STREAMLIT)
# =============================================================================
st.title("🗺️ Painel de Consulta - Municípios da Paraíba")
st.markdown("Insira o nome de um município para montar o link e extrair seus dados da FAMUP.")

nome_busca = st.text_input("Nome do Município:", placeholder="Ex: Aguiar, Alagoa Grande, Sapé")

if st.button("Buscar Informações", type="primary"):
    if nome_busca.strip():
        # st.empty limpa qualquer resquício visual antigo evitando o bug do React
        st.empty()
        
        with st.spinner("Gerando endereço institucional e acessando dados..."):
            resultado = extrair_dados_famup(nome_busca)
        
        if isinstance(resultado, dict):
            st.success("📊 Dados recuperados com sucesso!")
            
            # Exibição simples sem colunas para blindar contra o erro 'removeChild' do Streamlit
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
