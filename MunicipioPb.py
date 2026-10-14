# Varredura inteligente de texto puro por quebra de linha
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
                            
        # ==========================================
        # TRATAMENTO PARA REMOVER DUPLICATAS DE E-MAIL
        # ==========================================
        if 'E-mails de Contato' in dados_coletados:
            email_bruto = dados_coletados['E-mails de Contato']
            # Divide por pipe (|) ou espaços duplicados caso venham grudados, limpa e remove duplicatas
            # Usamos uma expressão regular ou split padrão para isolar os e-mails limpos
            partes = re.split(r'[|\s]+', email_bruto)
            emails_validos = [e.strip() for e in partes if '@' in e and '.' in e]
            
            # Remove duplicatas mantendo a ordem original
            emails_unicos = list(dict.fromkeys(emails_validos))
            
            if emails_unicos:
                dados_coletados['E-mails de Contato'] = " | ".join(emails_unicos)
            else:
                dados_coletados['E-mails de Contato'] = email_bruto # Mantém o original se não achar o '@'

        return dados_coletados
    except Exception as e:
        return f"❌ Erro ao acessar o link [{url_direta}]: {e}"
