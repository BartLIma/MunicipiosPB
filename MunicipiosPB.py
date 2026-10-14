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
# 3. EXTRAÇÃO DE DADOS E LINKS DE IMAGEM
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
        
        # --- PLANO A: TENTATIVA DE EXTRAÇÃO DA BANDEIRA ---
        # Procura por qualquer tag de imagem que possua 'bandeira' no nome do arquivo ou atributo
        tag_bandeira = soup.find('img', src=re.compile(r'bandeira', re.IGNORECASE))
        if tag_bandeira and tag_bandeira.get('src'):
            url_img = tag_bandeira['src']
            # Garante que a URL da imagem esteja completa se for relativa
            if url_img.startswith('/'):
                dados_coletados['url_bandeira'] = f"https://famup.org.br{url_img}"
            else:
                dados_coletados['url_bandeira'] = url_img

        # Mapeamento tradicional de rótulos textuais
        mapeamento = {
            'razão social': 'Razão Social',
            'endereço': 'Endereço',
            'site': 'Site Oficial',
            'telefones': 'Telefones',
            'emails': 'E-mails de Contato',
            'prefeito': 'Prefeito Atual'
        }
        
        # Quebra o texto visível da página em linhas limpas
        linhas_pagina = [re.sub(r'\s+', ' ', l).strip() for l in soup.get_text().split('\n') if l.strip()]
        
        # Varredura inteligente de texto por proximidade de linhas
        for i, linha in enumerate(linhas_pagina):
            linha_lower = linha.lower()
            
            for termo_html, label_interface in mapeamento.items():
                if linha_lower == termo_html:
                    for j in range(1, 5):
                        if i + j < len(linhas_pagina):
                            candidato_valor = lines_candidato = linhas_pagina[i + j]
                            if "Água Branca" in candidato_valor or candidato_valor.lower() in mapeamento:
                                continue
                            if candidato_valor in ['-', 'Bandeira', 'Dados Gerais']:
                                continue
                                
                            dados_coletados[label_interface] = candidato_valor
                            break

        if not dados_coletados:
            return f"⚠️ O link existia ({url_direta}), mas os dados internos não puderam ser processados."
            
        # Adiciona a URL direta consultada aos dados para usar no rodapé
        dados_coletados['url_fonte'] = url_direta
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
            
            # --- SEÇÃO DA BANDEIRA ---
            # Se o robô capturar o link da bandeira, exibe centralizado no topo do cartão
            if 'url_bandeira' in resultado:
                st.image(resultado['url_bandeira'], caption=f"Bandeira de {nome_busca.title()}", width=180)
            
            # Exibição dos dados textuais limpos na tela
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
                
            # --- SEÇÃO DO MAPA INTERATIVO ---
            # Mostra o mapa geográfico acoplado com base no nome do município digitado
            st.write("")
            st.markdown("📍 **Localização Geográfica:**")
        else:
            st.error(resultado)
    else:
        st.warning("⚠️ Digite o nome de um município para realizar a operação.")

# =============================================================================
# 5. RODAPÉ DE AUTORIA E FONTE INSTITUCIONAL (FIXO NO FIM DA PÁGINA)
# =============================================================================
st.markdown("---")
# Monta dinamicamente o link da fonte para a cidade buscada ou mantém o link geral da federação
link_fonte = FAMUP_BASE_URL
if 'nome_busca' in locals() and nome_busca.strip():
    slug_atual = normalizar_slug_municipio(nome_busca)
    link_fonte = f"{FAMUP_BASE_URL}/{slug_atual}/"

st.markdown(
    f"<div style='text-align: center; color: gray; font-size: 0.85em;'>"
    f"📍 <b>Fonte dos Dados:</b> <a href='{link_fonte}' target='_blank'>Portal Oficial FAMUP</a><br>"
    f"🚀 <b>Desenvolvido por:</b> Bartolomeu Lima (Corecon-ES 1541) & AI Workspace 🤝 2026"
    f"</div>", 
    unsafe_allow_html=True
)
