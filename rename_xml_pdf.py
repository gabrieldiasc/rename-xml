import os
import xml.etree.ElementTree as ET
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

def formatar_valor(valor_str):
    try:
        valor = float(valor_str)
        return "{:,.2f}".format(valor).replace(",", "X").replace(".", ",").replace("X", ".")
    except:
        return "0,00"

def processar_arquivos(diretorio, tipo_fluxo):
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
                valor_node = root_xml.find(tag_val)
                num_node = root_xml.find(tag_num)

                # Busca o Emitente para Entrada e Destinatário para Saída
                if tipo_fluxo == "Saída":
                    parceiro_node = root_xml.find('.//{*}toma/{*}xNome') or root_xml.find('.//{*}dest/{*}xNome')
                else:
                    parceiro_node = root_xml.find('.//{*}emit/{*}xNome')

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

                # --- 5. NOMENCLATURA ---
                parceiro = parceiro_node.text if parceiro_node is not None else "Desconhecido"
                parceiro_limpo = "".join([c for c in parceiro if c.isalnum() or c == ' ']).strip()
                valor_formatado = formatar_valor(valor_node.text) if valor_node is not None else "0,00"

                # XML: Sempre Modelo + Número
                novo_nome_xml = f"{prefixo} {numero}{status_texto}.xml"
                
                # PDF: Modelo + Número + Parceiro + Valor
                novo_nome_pdf = f"{prefixo} {numero} {parceiro_limpo} {valor_formatado}{status_texto}.pdf"

                # --- 6. TRAVA DE DUPLICIDADE ---
                caminho_final_xml = os.path.join(diretorio, novo_nome_xml)
                if os.path.exists(caminho_final_xml):
                    novo_nome_xml = f"{prefixo} {numero} {parceiro_limpo}{status_texto}.xml"
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

# --- INTERFACE GRÁFICA (GUI) ---
def selecionar_pasta():
    caminho = filedialog.askdirectory(title="Selecione a pasta com os XMLs")
    if caminho:
        entrada_pasta.delete(0, tk.END)
        entrada_pasta.insert(0, caminho)

def iniciar_processamento():
    diretorio = entrada_pasta.get()
    tipo_fluxo = var_fluxo.get()  # Pega o valor do Radiobutton
    
    if not diretorio:
        messagebox.showerror("Erro", "Por favor, selecione uma pasta válida.")
        return
        
    processar_arquivos(diretorio, tipo_fluxo)

# Configuração da Janela Principal
root = tk.Tk()
root.title("Organizador de Documentos Fiscais")
root.geometry("550x220")
root.resizable(False, False)

frame = ttk.Frame(root, padding="20")
frame.pack(fill=tk.BOTH, expand=True)

# 1. Campo de Seleção de Pasta
ttk.Label(frame, text="Pasta dos Arquivos:").grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
entrada_pasta = ttk.Entry(frame, width=50)
entrada_pasta.grid(row=1, column=0, padx=(0, 10), pady=(0, 15), columnspan=2)
ttk.Button(frame, text="Selecionar...", command=selecionar_pasta).grid(row=1, column=2, pady=(0, 15))

# 2. Área de Marcação (Radiobuttons)
ttk.Label(frame, text="Tipo de Fluxo:").grid(row=2, column=0, sticky=tk.W, pady=(0, 5))

var_fluxo = tk.StringVar(value="Entrada")  # Define "Entrada" como padrão inicial

rb_entrada = ttk.Radiobutton(frame, text="Entrada (Compras)", variable=var_fluxo, value="Entrada")
rb_entrada.grid(row=3, column=0, sticky=tk.W, pady=(0, 5))

rb_saida = ttk.Radiobutton(frame, text="Saída (Vendas)", variable=var_fluxo, value="Saída")
rb_saida.grid(row=4, column=0, sticky=tk.W)

# 3. Botão Executar
btn_executar = ttk.Button(frame, text="Renomear Arquivos", command=iniciar_processamento)
btn_executar.grid(row=4, column=2, sticky=tk.E)

root.mainloop()