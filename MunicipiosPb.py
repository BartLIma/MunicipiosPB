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
    page_title="Consulta FAMUP - PB",
    page_icon="🗺️",
    layout="centered"
)

FAMUP_BASE_URL = "https://famup.org.br/paraiba/"
HTTP_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

# =============================================================================
# 2. BANCO DE COORDENADAS PARAÍBA (CHAVES 100% NORMALIZADAS)
# =============================================================================
COORDENADAS_MUNICICIPIOS = {
    "aguabranca": (-7.51, -37.63), "aguiar": (-7.09, -38.16), "alagoanova": (-7.04, -35.75), "alagoagrande": (-7.04, -35.62),
    "alagoinha": (-6.94, -35.54), "alcantil": (-7.74, -36.05), "algodaodejandaira": (-6.93, -35.93), "alhandra": (-7.43, -34.90),
    "amparo": (-7.56, -36.91), "aparecida": (-6.78, -38.08), "aracagi": (-6.85, -35.38), "arara": (-6.82, -35.75),
    "araruna": (-6.55, -35.73), "areia": (-6.96, -35.69), "areiadebaraunas": (-7.13, -36.93), "areial": (-7.05, -35.92),
    "aroeiras": (-7.47, -35.68), "assuncao": (-7.06, -36.71), "baiadatraicao": (-6.68, -34.93), "bananeiras": (-6.75, -35.63),
    "barauna": (-6.65, -36.25), "barradesantana": (-7.53, -35.99), "barradesantarosa": (-6.72, -36.06), "barradesaomiguel": (-7.75, -36.31),
    "bayeux": (-7.12, -34.93), "belem": (-6.74, -35.51), "belemdobrejodocruz": (-6.18, -37.53), "bernardinobatista": (-6.45, -38.54),
    "boaventura": (-7.42, -38.21), "boavista": (-7.25, -36.23), "bomjesus": (-6.73, -38.60), "bomsucesso": (-6.45, -37.93),
    "bonitodesantafe": (-7.18, -38.75), "boqueirao": (-7.48, -36.13), "borborema": (-6.80, -35.62), "brejodocruz": (-6.35, -37.48),
    "brejodossantos": (-6.41, -37.54), "caapora": (-7.51, -34.90), "cabaceiras": (-7.48, -36.28), "cabedelo": (-6.97, -34.83),
    "cachoeiradosindios": (-6.83, -38.60), "cacimbadedentro": (-6.64, -35.78), "cacimbadeareia": (-7.12, -37.16), "cacimbas": (-7.29, -37.15),
    "caicara": (-6.61, -35.40), "cajazeiras": (-6.88, -38.55), "cajazeirinhas": (-6.91, -37.81), "caldasbrandao": (-7.22, -35.56),
    "camalau": (-7.89, -36.82), "campinagrande": (-7.22, -35.88), "capim": (-6.78, -35.16), "caraubas": (-7.71, -36.49),
    "carrapateira": (-7.03, -38.38), "casserengue": (-6.71, -35.67), "atingba": (-6.82, -35.11), "catoledorocha": (-6.34, -37.74),
    "caturite": (-7.42, -36.03), "conceicao": (-7.56, -38.50), "condado": (-6.90, -37.60), "conde": (-7.25, -34.90),
    "congo": (-7.79, -36.78), "coremas": (-7.01, -37.94), "coxixola": (-7.63, -36.60), "cruvdoespiritosanto": (-7.23, -35.08),
    "cruvdeespiritosanto": (-7.23, -35.08), "cubati": (-6.88, -36.22), "cuite": (-6.48, -36.15), "cuitedemamanguape": (-6.92, -35.15),
    "cuitegi": (-6.83, -35.53), "curraldecima": (-6.73, -35.25), "curralvelho": (-7.49, -38.12), "damiao": (-6.63, -36.02),
    "desterro": (-7.29, -37.09), "vistaserrana": (-6.73, -37.56), "diamante": (-7.41, -38.19), "donaines": (-6.62, -35.64),
    "duasestradas": (-6.71, -35.41), "emas": (-7.11, -37.62), "esperanca": (-7.02, -35.85), "fagundes": (-7.36, -35.77),
    "freimartinho": (-6.41, -36.46), "gadobravo": (-7.53, -35.78), "guarabira": (-6.85, -35.49), "gurjao": (-7.24, -36.49),
    "gurinhem": (-7.12, -35.42), "imaculada": (-7.38, -37.50), "inga": (-7.31, -35.61), "itabaiana": (-7.32, -35.33),
    "itaporanga": (-7.40, -38.15), "itapororoca": (-6.84, -35.15), "itatuba": (-7.38, -35.54), "jacarau": (-6.61, -35.13),
    "jerico": (-6.50, -37.80), "joaopessoa": (-7.11, -34.86), "jocaclaudino": (-6.49, -38.46), "juareztavora": (-7.16, -35.59),
    "juazeirinho": (-7.06, -36.57), "juncodoserido": (-6.98, -36.72), "juripiranga": (-7.40, -35.25), "juru": (-7.53, -37.83),
    "lagoa": (-6.56, -37.91), "lagoadedentro": (-6.80, -35.28), "lagoaseca": (-7.16, -35.85), "lastro": (-6.64, -38.25),
    "livramento": (-7.38, -36.94), "logradouro": (-6.66, -35.38), "lucena": (-6.90, -34.86), "maedagua": (-7.26, -37.29),
    "malta": (-6.90, -37.52), "mamanguape": (-6.83, -35.12), "manaira": (-7.70, -38.15), "marcao": (-6.75, -34.99),
    "marizopolis": (-6.84, -38.28), "massaranduba": (-7.20, -35.79), "mataraca": (-6.50, -34.97), "matinhas": (-7.09, -35.79),
    "matoesdonorte": (-7.50, -35.40), "matogrosso": (-6.41, -37.75), "matureia": (-7.26, -37.22), "mogeiro": (-7.28, -35.47),
    "montadas": (-7.09, -35.95), "montehorebe": (-7.18, -38.58), "monteiro": (-7.88, -37.11), "mulungu": (-7.02, -35.45),
    "natuba": (-7.64, -35.55), "nazarezinho": (-6.90, -38.43), "novafloresta": (-6.45, -36.20), "novaolinda": (-7.48, -38.04),
    "novapalmeira": (-6.66, -36.42), "olhodagua": (-7.23, -37.73), "olivedos": (-6.97, -36.24), "ourovelho": (-7.91, -37.15),
    "parari": (-7.46, -36.65), "passagem": (-7.10, -37.05), "patos": (-7.02, -37.27), "paulista": (-6.59, -37.62),
    "pedrabranca": (-7.46, -38.12), "pedralavrada": (-6.75, -36.43), "pedrasdefogo": (-7.40, -35.11), "pedroregis": (-6.69, -35.11),
    "pianco": (-7.19, -37.92), "picaunha": (-7.20, -35.25), "piloes": (-6.85, -35.60), "piloezinhos": (-6.83, -35.55),
    "pirpirituba": (-6.79, -35.49), "pitimbu": (-7.47, -34.80), "pocinhos": (-7.07, -36.05), "pombal": (-6.77, -37.79),
    "prata": (-7.93, -37.08), "princesaisabel": (-7.73, -37.99), "puxinana": (-7.15, -35.97), "queimadas": (-7.35, -35.89),
    "quixaba": (-7.01, -37.15), "remigio": (-6.90, -35.83), "riachao": (-6.54, -35.63), "riachaodobacamarte": (-7.26, -35.66),
    "riachaodopoco": (-7.10, -35.23), "riachodesantoantonio": (-7.64, -36.01), "riachodoscavalos": (-6.43, -37.65),
    "riotinto": (-6.80, -35.07), "salgadinho": (-7.05, -36.85), "salgadosaofelix": (-7.35, -35.44), "santacecilia": (-7.63, -35.89),
    "santacruz": (-6.51, -38.05), "santahelena": (-6.72, -38.63), "santaines": (-7.65, -38.55), "santaluzia": (-6.87, -36.92),
    "santanademangueira": (-7.55, -38.43), "santanadosgarrotes": (-7.40, -37.95), "santarita": (-7.16, -34.97),
    "santateresinha": (-7.01, -37.45), "santoandre": (-7.19, -36.63), "saobento": (-6.28, -37.45), "saobentinho": (-6.83, -37.74),
    "saodomingosdocariri": (-7.55, -36.51), "saodomingos": (-6.81, -37.93), "saofrancisco": (-6.76, -38.00),
    "saojoaodocariri": (-7.38, -36.53), "saojoaodotigre": (-8.07, -36.84), "saojoaodariodopeixe": (-6.73, -38.44),
    "saojosedalagoatapada": (-6.94, -38.16), "saojosedecaiana": (-7.46, -38.31), "saojosedespinharas": (-6.84, -37.32),
    "saojosedosramos": (-7.28, -35.31), "saojosedepiranhas": (-7.11, -38.50), "saojosedeprincesa": (-7.73, -38.09),
    "saojosedobonfim": (-7.16, -37.31), "saojosedobrejodocruz": (-6.17, -37.35), "saojosedosabugi": (-6.86, -36.87),
    "saojosedoscordeiros": (-7.45, -36.80), "saomamede": (-6.92, -37.11), "saomigueldetaipu": (-7.23, -35.22),
    "saosebastiaodelagoaderoca": (-7.06, -35.84), "saosebastiaodoumbuzeiro": (-8.14, -36.94), "sape": (-7.09, -35.23),
    "serrabranca": (-7.48, -36.66), "serradaraiz": (-6.68, -35.43), "serragrande": (-7.21, -38.36), "serraria": (-6.82, -35.63),
    "sertaozinho": (-6.75, -35.44), "sobrado": (-7.13, -35.23), "soledade": (-7.05, -36.36), "sossego": (-6.88, -36.26),
    "sousa": (-6.76, -38.22), "sume": (-7.67, -36.88), "tacima": (-6.48, -35.63), "taperoa": (-7.21, -36.82),
    "tavares": (-7.63, -37.89), "teixeira": (-7.22, -37.25), "tenorio": (-6.93, -36.63), "triunfo": (-6.57, -38.53),
    "uirauna": (-6.52, -38.41), "umburana": (-6.68, -36.16), "varzea": (-6.88, -36.83), "vieiropolis": (-6.79, -38.24),
    "zabele": (-7.97, -37.10)
}

# =============================================================================
# 3. TRATAMENTO DE STRINGS E MAPA DE CHAVES GEOGRÁFICAS
# =============================================================================
def normalizar_slug_municipio(nome_municipio: str) -> str:
    """Gera o link com hífen para o portal da FAMUP (ex: alagoa-grande)"""
    slug = nome_municipio.strip().lower()
    slug = ''.join(c for c in unicodedata.normalize('NFD', slug) if unicodedata.category(c) != 'Mn')
    slug = slug.replace(" ", "-")
    slug = re.sub(r'[^a-z0-9\-]', '', slug)
    slug = re.sub(r'-+', '-', slug)
    return slug

def normalizar_chave_coordenada(nome_municipio: str) -> str:
    """Gera a chave grudada para casar com o seu dicionário (ex: alagoagrande)"""
    slug = nome_municipio.strip().lower()
    slug = ''.join(c for c in unicodedata.normalize('NFD', slug) if unicodedata.category(c) != 'Mn')
    slug = re.sub(r'[^a-z0-9]', '', slug)
    return slug
# =============================================================================
# 4. EXTRAÇÃO DE DADOS TEXTUAIS E BANDEIRA (WEB SCRAPING)
# =============================================================================
def extrair_dados_famup(municipio: str) -> dict | str:
    slug = normalizar_slug_municipio(municipio)
    
    # GARANTIA DE URL: Mantém a base estável com o diretório /paraiba fixo
    url_direta = f"{FAMUP_BASE_URL}/{slug}/"
    
    try:
        response = requests.get(url_direta, headers=HTTP_HEADERS, timeout=10)
        
        if response.status_code == 404:
            return f"❌ O endereço direto não foi encontrado na FAMUP.\nLink tentado: {url_direta}"
        elif response.status_code != 200:
            return f"❌ Erro de conexão com a FAMUP (Código HTTP: {response.status_code})."
        
        soup = BeautifulSoup(response.text, 'html.parser')
        dados_coletados = {}
        
        # Captura da Bandeira Oficial via SisGF
        tag_img = soup.find('img', src=re.compile(r'(sisgf|foto_contatos|\.PNG)'))
        if tag_img and tag_img.get('src'):
            dados_coletados['url_bandeira'] = tag_img['src']
            
        # -------------------------------------------------------------
        # NOVA ABORDAGEM DE BUSCA ROBUSTA (Baseada em texto e rótulos)
        # -------------------------------------------------------------
        
        # Função auxiliar para limpar e achar valores próximos
        def buscar_campo(termos_chave):
            for termo in termos_chave:
                elemento = soup.find(string=re.compile(f"^{termo}$", re.IGNORECASE))
                if elemento:
                    pai = elemento.find_parent()
                    if pai:
                        texto_completo = pai.get_text(separator=" ", strip=True)
                        for t in termos_chave:
                            texto_completo = re.sub(t, "", texto_completo, flags=re.IGNORECASE)
                        valor_limpo = texto_completo.replace(":", "").strip()
                        if valor_limpo and len(valor_limpo) > 2:
                            return valor_limpo
            return None

        # =============================================================
        # [AQUI ENTRA A ALTERAÇÃO] DECODIFICADOR DE EMAIL CLOUDFLARE
        # =============================================================
        def decodificar_cloudflare_email(cf_hex):
            try:
                k = int(cf_hex[:2], 16)
                email = ''.join([chr(int(cf_hex[i:i+2], 16) ^ k) for i in range(2, len(cf_hex), 2)])
                return email
            except Exception:
                return None

        # Busca por tags com a proteção da Cloudflare
        tags_com_email = soup.find_all(attrs={"data-cfemail": True})
        emails_decodificados = []

        for tag in tags_com_email:
            cfemail = tag.get("data-cfemail")
            email_real = decodificar_cloudflare_email(cfemail)
            if email_real:
                emails_decodificados.append(email_real)

        if emails_decodificados:
            emails_unicos = list(dict.fromkeys(emails_decodificados))
            dados_coletados['E-mails de Contato'] = " | ".join(emails_unicos)
        else:
            # Fallback caso o site mude ou não use Cloudflare em alguma página
            link_email = soup.find('a', href=re.compile(r'^mailto:'))
            if link_email and '[email protected]' not in link_email.get_text():
                dados_coletados['E-mails de Contato'] = link_email.get_text(strip=True)
            else:
                possiveis_emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', soup.get_text())
                if possiveis_emails:
                    emails_unicos = list(dict.fromkeys(possiveis_emails))
                    dados_coletados['E-mails de Contato'] = " | ".join(emails_unicos)
        # =============================================================

        # Mapeamento dos demais campos usando a lógica anterior ajustada
        mapeamento = {
            'razão social': 'Razão Social',
            'endereço': 'Endereço',
            'site': 'Site Oficial',
            'telefones': 'Telefones',
            'prefeito': 'Prefeito Atual'
        }
        
        linhas_pagina = [re.sub(r'\s+', ' ', l).strip() for l in soup.get_text().split('\n') if l.strip()]
        for i, linha_servidor in enumerate(linhas_pagina):
            linha_lower = linha_servidor.lower()
            for termo_html, label_interface in mapeamento.items():
                if termo_html in linha_lower:
                    for j in range(1, 4):
                        if i + j < len(linhas_pagina):
                            candidato_valor = \
                            linhas_pagina[i + j]
                            if candidato_valor in ['-', 'Bandeira', 'Dados Gerais'] or '@' in candidato_valor:
                                continue
                            dados_coletados[label_interface] = candidato_valor
                            break
                            
        return dados_coletados

    except Exception as e:
        return f"❌ Erro ao acessar o link [{url_direta}]: {e}"
# =============================================================================
# 5. INTERFACE DO USUÁRIO (STREAMLIT UI)
# =============================================================================
st.title("🗺️ Consulta Municípios da Paraíba")
st.markdown("Pesquisa dados de uma determinada prefeitura com base no site da FAMUP.")

nome_busca = st.text_input("Digite o Nome do Município:", placeholder="Ex: Aguiar, Alagoa Grande, Campina Grande")

if st.button("Buscar Informações", type="primary"):
    if nome_busca.strip():
        st.empty()
        
        with st.spinner("Processando dados e gerando mapas..."):
            resultado = extrair_dados_famup(nome_busca)
        
        if isinstance(resultado, dict):
            st.success("📊 Dados recuperados com sucesso!")
            
            # Layout em colunas: Bandeira à esquerda e Informações à direita
            col_bandeira, col_info = st.columns([1, 2])
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
            
            # --- RENDERIZAÇÃO DO MAPA NATIVO VIA DICIONÁRIO INTEGRADO ---
            st.markdown("---")
            chave_coordenada = normalizar_chave_coordenada(nome_busca)
            
            if chave_coordenada in COORDENADAS_MUNICICIPIOS:
                lat, lon = COORDENADAS_MUNICICIPIOS[chave_coordenada]
                st.markdown(f"📍 **Mapa de Localização do Município de {nome_busca.title()} :**")
                
                # O st.map exige as coordenadas estruturadas dentro de um DataFrame do Pandas
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
