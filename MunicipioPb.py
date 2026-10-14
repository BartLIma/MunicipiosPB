import requests
from bs4 import BeautifulSoup
import unicodedata
import re

def normalizar_nome_municipio(nome):
    """
    Remove acentos, caracteres especiais e espaços para gerar o slug da URL.
    Exemplo: "Mãe D'Água" -> "mae-dagua" ou "Sapé" -> "sape"
    """
    # Transforma para minúsculas e remove espaços nas pontas
    nome = nome.strip().lower()
    
    # Remove acentos (Normaliza para o padrão NFD e filtra os blocos de acentuação)
    nome_sem_acentos = ''.join(
        c for c in unicodedata.normalize('NFD', nome)
        if unicodedata.category(c) != 'Mn'
    )
    
    # Substitui espaços por hifens
    nome_com_hifens = nome_sem_acentos.replace(" ", "-")
    
    # Remove qualquer caractere que não seja letras, números ou hifens (como apóstrofos e aspas)
    slug_final = re.sub(r'[^a-z0-9\-]', '', nome_com_hifens)
    
    # Remove múltiplos hifens seguidos, se houver
    slug_final = re.sub(r'-+', '-', slug_final)
    
    return slug_final

def consultar_municipio_famup(municipio):
    municipio_formatado = normalizar_nome_municipio(municipio)
    url = f"https://famup.org.br{municipio_formatado}/"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    print(f"\n🔍 Buscando dados de {municipio.title()} em: {url} ...")
    
    try:
        response = requests.get(url, headers=headers)
        
        if response.status_code == 404:
            return f"❌ Município '{municipio}' não encontrado na FAMUP. Verifique a grafia."
        elif response.status_code != 200:
            return f"❌ Erro ao acessar o site da FAMUP (Código: {response.status_code})."
        
        soup = BeautifulSoup(response.text, 'html.parser')
        dados_municipio = {}
        
        # Mapeamento de busca no HTML com base na estrutura do site
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
            return "⚠️ Página encontrada, mas a estrutura de dados não pôde ser lida."
            
        return dados_municipio

    except Exception as e:
        return f"❌ Ocorreu um erro de conexão: {e}"

if __name__ == "__main__":
    print("="*50)
    print("  CONSULTA DE MUNICÍPIOS DA PARAÍBA - FAMUP  ")
    print("="*50)
    
    while True:
        entrada = input("\nDigite o nome do município (ex: Aguiar, Sapé) ou 'sair': ")
        if entrada.lower() == 'sair':
            print("Programa encerrado.")
            break
            
        resultado = consultar_municipio_famup(entrada)
        
        if isinstance(resultado, dict):
            print("\n📊 --- DADOS ENCONTRADOS ---")
            for chave, valor in resultado.items():
                print(f"🔹 {chave}: {valor}")
            print("-" * 30)
        else:
            print(resultado)
