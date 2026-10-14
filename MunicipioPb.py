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
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Constantes do projeto
FAMUP_BASE_URL = "https://famup.org.br"
HTTP_HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/120.0.0.0 Safari/537.36'
    )
}

# =============================================================================
# 2. FUNÇÕES DE TRATAMENTO E PROCESSAMENTO DE TEXTO
# =============================================================================
def normalizar_slug_municipio(nome_municipio: str) -> str:
    """
    Transforma o nome do município no padrão esperado pela URL da FAMUP (Iniciais Maiúsculas).
    Exemplo: "campina grande" -> "Campina-Grande" | "aguiar" -> "Aguiar"
    """
    # 1. Trata espaços extras e capitaliza as iniciais de cada palavra (Padrão exigido pela FAMUP)
    nome_formatado = nome_municipio.strip().title()
    
    # 2. Remover acentuação utilizando normalização Unicode
    slug = ''.join(
        caractere for caractere in unicodedata.normalize('NFD', nome_formatado)
        if unicodedata.category(caractere) != 'Mn'
    )
    
    # 3. Substituir espaços por hifens
    slug = slug.replace(" ", "-")
    
    # 4. Remover apóstrofos, aspas e outros caracteres especiais inválidos na URL
    slug = re.sub(r'[^a-zA-Z0-9\-]', '', slug)
    
    # 5. Evitar múltiplos hifens seguidos
    slug = re.sub(r'-+', '-', slug)
    
    return slug


def limpar_texto_extraido(texto: str) -> str:
    """
    Remove quebras de linha excessivas, tabulações e caracteres residuais de formatação.
    """
    if not texto:
        return ""
    # Substitui qualquer sequência de espaços/quebras de linha por um único espaço
    texto_limpo = re.sub(r'\s+', ' ', texto).strip()
    # Remove barras verticais soltas comuns em listas de telefones/emails da FAMUP
    texto_limpo = re.sub(r'\s*\|\s*$', '', texto_limpo)
    return texto_limpo

# =============================================================================
# 3. NÚCLEO DE EXTRAÇÃO DE DADOS (WEB SCRAPING)
# =============================================================================
def extrair_dados_famup(municipio: str) -> dict | str:
    """
    Realiza a requisição HTTP e raspa os dados institucionais do município do site da FAMUP.
    Returns:
        dict: Com os dados limpos se a extração for bem-sucedida.
        str: Mensagem de erro caso ocorra alguma falha.
    """
    slug = normalizar_slug_municipio(municipio)
    url_alvo = f"{FAMUP_BASE_URL}/{slug}/"
    
    try:
        response = requests.get(url_alvo, headers=HTTP_HEADERS, timeout=12)
        
        if response.status_code == 404:
            return f"❌ O município '{municipio}' não foi encontrado no portal da FAMUP. Verifique a grafia."
        elif response.status_code != 200:
            return f"❌ Erro de comunicação com o servidor da FAMUP (Código HTTP: {response.status_code})."
        
        soup = BeautifulSoup(response.text, 'html.parser')
        dados_coletados = {}
        
        # Dicionário de mapeamento: 'Texto buscado no HTML': 'Rótulo exibido na Interface'
        mapeamento_campos = {
            'Razão social': 'Razão Social',
            'Endereço': 'Endereço',
            'Site': 'Site Oficial',
            'Telefones': 'Telefones',
            'Emails': 'E-mails de Contato',
            'Prefeito': 'Prefeito Atual'
        }
        
        for termo_html, rotulo_interface in mapeamento_campos.items():
            # Localiza a tag que contém exatamente o título do campo procurado
            tag_rotulo = soup.find(
                lambda tag: tag.name in ['h5', 'h4', 'p', 'b', 'strong', 'div'] 
                and termo_html.lower() == tag.text.strip().lower()
            )
            
            if tag_rotulo:
                # O conteúdo informativo reside na tag irmã imediatamente seguinte
                tag_valor = tag_rotulo.find_next()
                if tag_valor:
                    conteudo = tag_valor.text
                    
                    # FILTRO DE SEGURANÇA (Anti-Sujeira):
                    # Se o robô capturar acidentalmente a lista de links do menu lateral de municípios,
                    # o conteúdo será imenso e conterá nomes de outras cidades conhecidas.
                    if "Água Branca" in conteudo and len(conteudo) > 400:
                        continue
                        
                    dados_coletados[rotulo_interface] = limpar_texto_extraido(conteudo)
        
        if not dados_coletados:
            return "⚠️ A página do município existe, mas a estrutura interna do site mudou e o robô não pôde ler os dados."
            
        return dados_coletados

    except requests.exceptions.Timeout:
        return "❌ O servidor da FAMUP demorou muito para responder (Tempo limite esgotado)."
    except requests.exceptions.ConnectionError:
        return "❌ Falha de rede ao tentar conectar com a FAMUP. Verifique a internet do servidor."
    except Exception as erro:
        return f"❌ Ocorreu um erro inesperado no processamento: {erro}"

# =============================================================================
# 4. INTERFACE GRÁFICA (STREAMLIT UI)
# =============================================================================
def renderizar_interface():
    # Cabeçalho da página
    st.title("🗺️ Painel de Consulta - Municípios da Paraíba")
    st.markdown(
        "Esta aplicação extrai e limpa de forma automatizada os dados "
        "institucionais atualizados mantidos pela **FAMUP**."
    )
    st.divider()

    # Campo de entrada de dados
    nome_busca = st.text_input(
        label="Digite o nome do município para pesquisar:",
        placeholder="Ex: Aguiar, Sapé, Campina Grande, Patos",
        help="Não se preocupe com acentos ou letras maiúsculas, o sistema trata o texto automaticamente."
    )
    
    # Botão de disparo
    if st.button("Buscar Informações", type="primary", use_container_width=True):
        if not nome_busca.strip():
            st.warning("⚠️ O campo de busca não pode estar vazio. Digite o nome de uma cidade.")
            return

        # Execução do Scraping com indicador visual de progresso
        with st.spinner(f"Consultando base de dados da FAMUP para '{nome_busca.title()}'..."):
            resultado = extrair_dados_famup(nome_busca)
        
        # Renderização condicional do resultado
        if isinstance(resultado, dict):
            st.success("📊 Dados recuperados com sucesso!")
            
            # Container visual estilizado (Moldura/Cartão)
            with st.container(border=True):
                # Título Principal do Cartão
                razao_social = resultado.get('Razão Social', nome_busca.upper())
                st.subheader(f"🏢 {razao_social}")
                
                # Bloco de destaque para o Gestor atual
                prefeito = resultado.get('Prefeito Atual', 'Não informado')
                st.markdown(f"### 👑 Prefeito(a): **{prefeito}**")
                st.divider()
                
                # Organização dos dados restantes em duas colunas para melhor aproveitamento de tela
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown(f"📍 **Endereço:**\n{resultado.get('Endereço', 'Não disponível')}")
                    st.markdown(f"📞 **Telefones:**\n{resultado.get('Telefones', 'Não disponível')}")
                
                with col2:
                    st.markdown(f"✉️ **E-mails:**\n{resultado.get('E-mails de Contato', 'Não disponível')}")
                    
                    # Tratamento inteligente e conversão do site em link real clicável
                    site_raw = resultado.get('Site Oficial')
                    if site_raw:
                        # Limpa possíveis palavras residuais como o termo 'site' colado
                        site_limpo = site_raw.lower().replace("site", "").strip()
                        url_completa = site_limpo if site_limpo.startswith("http") else f"https://{site_limpo}"
                        st.markdown(f"🌐 **Site Oficial:**\n[{site_limpo}]({url_completa})")
                    else:
                        st.markdown("🌐 **Site Oficial:**\nNão disponível")
        else:
            # Exibe a mensagem de erro tratada em uma caixa vermelha
            st.error(resultado)

# Ponto de entrada padrão do script Python
if __name__ == "__main__":
    renderizar_interface()
