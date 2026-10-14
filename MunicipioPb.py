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

# A base do link que você especificou
FAMUP_BASE_URL = "https://famup.org.br/paraiba"

HTTP_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

# =============================================================================
# 2. TRANSFORMAÇÃO DO NOME (IGUAL AO SEU PROCESSO VISUAL)
# =============================================================================
def normalizar_slug_municipio(nome_municipio: str) -> str:
    """
    Transforma o nome exatamente para o formato do endereço final da FAMUP.
    Exemplo: "Aguiar" -> "aguiar" | "Alagoa Grande" -> "alagoa-grande"
    """
    # Força minúsculas e limpa espaços nas pontas
    slug = nome_municipio.strip().lower()
    
    # Remove acentos (Sapé -> sape)
    slug = ''.join(
        c for c in unicodedata.normalize('NFD', slug)
        if unicodedata.category(c) != 'Mn'
    )
    
    # Substitui espaços por hifens (Alagoa Grande -> alagoa-grande)
    slug = slug.replace(" ", "-")
    
    # Remove caracteres especiais como apóstrofos (Mãe D'Água -> mae-dagua)
    slug = re.sub(r'[^a-z0-9\-]', '', slug)
    
    # Remove múltiplos hifens que possam surgir por erro de digitação
    slug = re.sub(r'-+', '-', slug)
    
    return slug

# =============================================================================
# 3. CONSTRUÇÃO DIRETA DO LINK E CAPTURA DE DADOS
# =============================================================================
def extrair_dados_famup(municipio: str) -> dict | str:
    # Transforma o nome digitado para o formato do link (ex: aguiar ou alagoa-grande)
    slug = normalizar_slug_municipio(municipio)
    
    # Monta o endereço colando os pedaços, exatamente como você sugeriu
    url_direta = f"{FAMUP_BASE_URL}/{slug}/"
    
    try:
        # Faz a visita direta ao endereço final
        response = requests.get(url_direta, headers=HTTP_HEADERS, timeout=10)
        
        if response.status_code == 404:
            return f"❌ O endereço direto não foi encontrado no servidor da FAMUP.\nLink tentado: {url_direta}"
        elif response.status_code != 200:
            return f"❌ Erro de conexão com o portal da FAMUP (Código: {response.status_code})."
        
        soup = BeautifulSoup(response.text, 'html.parser')
        dados_coletados = {}
        
        # Mapeamento com os termos em caixa mista, exatamente como estão escritos no HTML do site
        mapeamento_campos = {
            'Razão social': 'Razão Social',
            'Endereço': 'Endereço',
            'Site': 'Site Oficial',
            'Telefones': 'Telefones',
            'Emails': 'E-mails de Contato',
            'Prefeito': 'Prefeito Atual'
        }
        
        # Analisa o texto completo da página de forma flexível
        for termo_html, rotulo_interface in mapeamento_campos.items():
            # Procura qualquer tag que contenha o texto do rótulo de forma aproximada (ignorando maiúsculas/minúsculas da tag)
            tag_rotulo = soup.find(lambda tag: tag.name in ['h5', 'h4', 'p', 'b', 'strong', 'div'] 
                                   and tag.text and termo_html.lower() in tag.text.lower())
            
            if tag_rotulo:
                tag_valor = tag_rotulo.find_next()
                if tag_valor:
                    conteudo = tag_valor.text.strip()
                    
                    # Filtro para ignorar caso ele pegue por engano a lista lateral de municípios
                    if "Água Branca" in conteudo and len(conteudo) > 300:
                        continue
                    
                    # Limpa espaços duplos e quebras de linha que vinham com a "sujeira"
                    conteudo_limpo = re.sub(r'\s+', ' ', conteudo).strip()
                    conteudo_limpo = re.sub(r'\s*\|\s*$', '', conteudo_limpo)
                    
                    dados_coletados[rotulo_interface] = conteudo_limpo
        
        if not dados_coletados:
            return f"⚠️ O link existia ({url_direta}), mas o robô não conseguiu isolar os dados estruturados dentro dele."
            
        return dados_coletados

    except Exception as e:
        return f"❌ Erro ao tentar acessar o link [{url_direta}]: {e}"

# =============================================================================
# 4. INTERFACE DO USUÁRIO (STREAMLIT)
# =============================================================================
st.title("🗺️ Painel de Consulta - Municípios da Paraíba")
st.markdown("Insira o nome de um município para montar o link e extrair seus dados da FAMUP.")

# Campo de texto para o usuário digitar
nome_busca = st.text_input("Nome do Município:", placeholder="Ex: Aguiar, Alagoa Grande, Sapé")

if st.button("Buscar Informações", type="primary"):
    if nome_busca.strip():
        with st.spinner("Gerando endereço institucional e acessando dados..."):
            resultado = extrair_dados_famup(nome_busca)
        
        if isinstance(resultado, dict):
            st.success("📊 Dados recuperados com sucesso!")
            
            with st.container(border=True):
                st.subheader(f"🏢 {resultado.get('Razão Social', nome_busca.upper())}")
                st.markdown(f"### 👑 Prefeito(a): **{resultado.get('Prefeito Atual', 'Não informado')}**")
                st.divider()
                
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"📍 **Endereço:**\n{resultado.get('Endereço', 'Não informado')}")
                    st.markdown(f"📞 **Telefones:**\n{resultado.get('Telefones', 'Não informado')}")
                
                with col2:
                    st.markdown(f"✉️ **E-mails:**\n{resultado.get('E-mails de Contato', 'Não informado')}")
                    
                    site = resultado.get('Site Oficial')
                    if site:
                        site_limpo = site.lower().replace("site", "").strip()
                        url_completa = site_limpo if site_limpo.startswith("http") else f"https://{site_limpo}"
                        st.markdown(f"🌐 **Site Oficial:**\n[{site_limpo}]({url_completa})")
                    else:
                        st.markdown("🌐 **Site Oficial:**\nNão informado")
        else:
            st.error(resultado)
    else:
        st.warning("⚠️ Digite o nome de um município para realizar a operação.")
