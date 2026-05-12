import os
import xml.etree.ElementTree as ET
import tkinter as tk
from tkinter import filedialog, messagebox

def formatar_valor(valor_str):
    try:
        valor = float(valor_str)
        return "{:,.2f}".format(valor).replace(",", "X").replace(".", ",").replace("X", ".")
    except:
        return "0,00"

def organizar_documentos_v8():
    root = tk.Tk()
    root.withdraw()
    
    diretorio = filedialog.askdirectory(title="Selecione a pasta com XMLs e PDFs")
    if not diretorio:
        return

    sucessos = 0
    erros = 0
    status_cancelamento = ["101", "151", "155", "102"]

    for arquivo in os.listdir(diretorio):
        if arquivo.endswith(".xml"):
            nome_base_original = os.path.splitext(arquivo)[0]
            caminho_xml = os.path.join(diretorio, arquivo)
            caminho_pdf = os.path.join(diretorio, nome_base_original + ".pdf")
            
            try:
                tree = ET.parse(caminho_xml)
                root_xml = tree.getroot()
                tag_raiz = root_xml.tag.lower()

                # --- 1. IDENTIFICAÇÃO DO TIPO ---
                if 'nfse' in tag_raiz:
                    prefixo = "NFSe"
                    tag_num = './/{*}nNFSe'
                    tag_val = './/{*}vServ'
                elif 'cte' in tag_raiz:
                    prefixo = "CTe"
                    tag_num = './/{*}nCT'
                    tag_val = './/{*}vTPrest'
                else:
                    prefixo = "NF"
                    tag_num = './/{*}nNF'
                    tag_val = './/{*}vNF'

                # --- 2. EXTRAÇÃO DE DADOS ---
                chave_node = root_xml.find('.//{*}chNFe') or root_xml.find('.//{*}chCTe')
                emitente_node = root_xml.find('.//{*}emit/{*}xNome')
                valor_node = root_xml.find(tag_val)
                num_node = root_xml.find(tag_num)

                # --- 3. CANCELAMENTO ---
                is_cancelada = False
                if root_xml.find('.//{*}protCancNFe') is not None or root_xml.find('.//{*}protCancCTe') is not None:
                    is_cancelada = True
                else:
                    status_node = root_xml.find('.//{*}cStat')
                    if status_node is not None and status_node.text in status_cancelamento:
                        is_cancelada = True
                    elif (root_xml.find('.//{*}tpEvento') is not None and 
                          root_xml.find('.//{*}tpEvento').text == "110111"):
                        is_cancelada = True
                
                status_texto = " (CANCELADA)" if is_cancelada else ""

                # --- 4. NÚMERO ---
                if chave_node is not None and len(chave_node.text) == 44:
                    numero = chave_node.text[25:34].lstrip('0')
                elif num_node is not None:
                    numero = num_node.text.lstrip('0')
                else:
                    numero = "000"

                # --- 5. DADOS PARA DESEMPATE ---
                emitente = emitente_node.text if emitente_node is not None else "Emitente_Desconhecido"
                emitente_limpo = "".join([c for c in emitente if c.isalnum() or c == ' ']).strip()
                valor_formatado = formatar_valor(valor_node.text) if valor_node is not None else "0,00"

                # XML: Padrão curto inicialmente
                novo_nome_xml = f"{prefixo} {numero}{status_texto}.xml"
                
                # PDF: Padrão sempre completo
                novo_nome_pdf = f"{prefixo} {numero} {emitente_limpo} {valor_formatado}{status_texto}.pdf"

                # --- 6. TRAVA DE NÚMEROS IGUAIS (DESEMPATE PELO EMITENTE) ---
                caminho_final_xml = os.path.join(diretorio, novo_nome_xml)
                
                # Se o arquivo XML "curto" já existe, renomeamos este atual com o nome do emitente
                if os.path.exists(caminho_final_xml):
                    novo_nome_xml = f"{prefixo} {numero} {emitente_limpo}{status_texto}.xml"
                    caminho_final_xml = os.path.join(diretorio, novo_nome_xml)

                # --- 7. EXECUÇÃO ---
                os.rename(caminho_xml, caminho_final_xml)
                if os.path.exists(caminho_pdf):
                    os.rename(caminho_pdf, os.path.join(diretorio, novo_nome_pdf))
                
                sucessos += 1
                
            except Exception as e:
                print(f"Erro em {arquivo}: {e}")
                erros += 1

    messagebox.showinfo("Concluído", f"Processo finalizado!\n\nSucessos: {sucessos}\nErros: {erros}")

if __name__ == "__main__":
    organizar_documentos_v8()