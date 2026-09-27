#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Estudante(s): maria clara e leonardo
# 2 info

import os
import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk

CAMINHO_GLADE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "divide_conta.glade")


def calcular_valor_por_pessoa(texto_valor, texto_pessoas, texto_gorjeta):
    """
    Recebe os textos digitados pelo usuário (ainda crus, como strings)
    e devolve uma tupla (valor_por_pessoa, valor_total_com_gorjeta).

    Pode lançar:
        ValueError        -> texto não numérico em algum campo, ou
                              valor da conta / gorjeta negativos.
        ZeroDivisionError -> número de pessoas igual a zero.
    """
    valor_conta = float(texto_valor.strip().replace(",", "."))

    if valor_conta < 0:
        raise ValueError("O valor da conta não pode ser negativo.")

    # --- número de pessoas
    numero_pessoas = int(texto_pessoas.strip())

    # Ação do usuário que provoca o erro: informar uma quantidade
    # negativa de pessoas (ex: "-4").
    if numero_pessoas < 0:
        raise ValueError("O número de pessoas não pode ser negativo.")

    if numero_pessoas == 0:
        raise ZeroDivisionError("O número de pessoas não pode ser zero.")

    # --- gorjeta (opcional)
    texto_gorjeta = texto_gorjeta.strip()
    if texto_gorjeta == "":
        gorjeta_percentual = 0.0
    else:
        gorjeta_percentual = float(texto_gorjeta.replace(",", "."))

    # Ação do usuário que provoca o erro: informar uma gorjeta negativa.
    if gorjeta_percentual < 0:
        raise ValueError("A gorjeta não pode ser negativa.")

    # --- cálculo final
    valor_total = valor_conta * (1 + gorjeta_percentual / 100)
    valor_por_pessoa = valor_total / numero_pessoas

    return valor_por_pessoa, valor_total


# CLASSE PRINCIPAL DA APLICAÇÃO
class DivideContaApp:
    def __init__(self):
        self.builder = Gtk.Builder()
        self.builder.add_from_file(CAMINHO_GLADE)
        self.builder.connect_signals(self)

        self.janela = self.builder.get_object("jan_principal")
        self.entry_valor = self.builder.get_object("entry_valor")
        self.entry_pessoas = self.builder.get_object("entry_pessoas")
        self.entry_gorjeta = self.builder.get_object("entry_gorjeta")
        self.lbl_resultado = self.builder.get_object("lbl_resultado")
        self.lbl_status = self.builder.get_object("lbl_status")
        self.ultimo_resultado = None

        self.janela.show_all()

    def mostrar_mensagem(self, texto_titulo, texto_secundario, tipo=Gtk.MessageType.ERROR):
        dialogo = Gtk.MessageDialog(
            transient_for=self.janela,
            flags=0,
            message_type=tipo,
            buttons=Gtk.ButtonsType.OK,
            text=texto_titulo,
        )
        dialogo.format_secondary_text(texto_secundario)
        dialogo.run()
        dialogo.destroy()

    def atualizar_status(self, texto):
        if self.lbl_status is not None:
            self.lbl_status.set_text(texto)

    # HANDLER: botão "Calcular"
    def ao_calcular(self, botao):
        texto_valor = self.entry_valor.get_text()
        texto_pessoas = self.entry_pessoas.get_text()
        texto_gorjeta = self.entry_gorjeta.get_text()

        try:
            valor_por_pessoa, valor_total = calcular_valor_por_pessoa(
                texto_valor, texto_pessoas, texto_gorjeta
            )

        except ValueError as erro:
            # Cobre: texto não numérico e valores negativos.
            self.mostrar_mensagem("Valor inválido", str(erro))
            self.ultimo_resultado = None

        except ZeroDivisionError as erro:
            # Cobre: número de pessoas igual a zero.
            self.mostrar_mensagem("Divisão por zero", str(erro))
            self.ultimo_resultado = None

        except Exception as erro:
            # Cláusula final
            self.mostrar_mensagem("Erro inesperado", f"Ocorreu um erro não previsto: {erro}")
            self.ultimo_resultado = None

        else:
            # Só roda se NENHUMA exceção foi lançada acima ;P
            self.lbl_resultado.set_markup(
                f'<span size="xx-large" weight="bold">R$ {valor_por_pessoa:.2f}</span>'.replace(".", ",")
            )
            self.ultimo_resultado = {
                "valor_por_pessoa": valor_por_pessoa,
                "valor_total": valor_total,
                "pessoas": texto_pessoas.strip(),
            }
            self.atualizar_status("Cálculo concluído.")

        finally:
            # Sempre executa, independente de ter dado erro ou não
            if self.ultimo_resultado is None:
                self.atualizar_status("Aguardando um cálculo válido.")

    # HANDLER: botão "Salvar comprovante"
    def ao_salvar(self, botao):
        try:
            # Ação do usuário que provoca o erro: clicar em "Salvar"
            # antes de ter feito um cálculo válido.
            if self.ultimo_resultado is None:
                raise ValueError("Faça um cálculo válido antes de salvar o comprovante.")

            caixa = Gtk.FileChooserDialog(
                title="Salvar comprovante",
                transient_for=self.janela,
                action=Gtk.FileChooserAction.SAVE,
            )
            caixa.add_buttons(
                Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                Gtk.STOCK_SAVE, Gtk.ResponseType.OK,
            )
            caixa.set_current_name("comprovante.txt")
            resposta = caixa.run()
            caminho = caixa.get_filename()
            caixa.destroy()

            if resposta != Gtk.ResponseType.OK:
                self.atualizar_status("Salvamento cancelado pelo usuário.")
                return

            # Ação do usuário que provoca o erro: escolher uma pasta sem
            # permissão de escrita.
            with open(caminho, "w", encoding="utf-8") as arquivo:
                arquivo.write("=== Comprovante - Divide a Conta ===\n")
                arquivo.write(f"Nº de pessoas: {self.ultimo_resultado['pessoas']}\n")
                arquivo.write(f"Valor total (c/ gorjeta): R$ {self.ultimo_resultado['valor_total']:.2f}\n".replace(".", ","))
                arquivo.write(f"Cada pessoa paga: R$ {self.ultimo_resultado['valor_por_pessoa']:.2f}\n".replace(".", ","))

        except ValueError as erro:
            self.mostrar_mensagem("Não é possível salvar", str(erro))

        except PermissionError as erro:
            self.mostrar_mensagem("Sem permissão", f"Não foi possível escrever no arquivo: {erro}")

        except Exception as erro:
            self.mostrar_mensagem("Erro inesperado", f"Ocorreu um erro não previsto ao salvar: {erro}")

        else:
            self.atualizar_status(f"Comprovante salvo em: {caminho}")

        finally:
            pass  # nenhuma limpeza extra necessária neste handler

    # HANDLER: botão "Abrir comprovante"
    def ao_abrir(self, botao):
        caminho = None
        try:
            caixa = Gtk.FileChooserDialog(
                title="Abrir comprovante",
                transient_for=self.janela,
                action=Gtk.FileChooserAction.OPEN,
            )
            caixa.add_buttons(
                Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                Gtk.STOCK_OPEN, Gtk.ResponseType.OK,
            )
            resposta = caixa.run()
            caminho = caixa.get_filename()
            caixa.destroy()

            if resposta != Gtk.ResponseType.OK or not caminho:
                self.atualizar_status("Abertura cancelada pelo usuário.")
                return

            # Ação do usuário que provoca o erro: digitar/selecionar um
            # caminho de arquivo que não existe (ou que foi apagado
            # entre a seleção e a leitura)
            with open(caminho, "r", encoding="utf-8") as arquivo:
                conteudo = arquivo.read()

        except FileNotFoundError:
            self.mostrar_mensagem(
                "Comprovante não encontrado",
                f"O arquivo '{caminho}' não existe ou foi removido.",
            )

        except Exception as erro:
            self.mostrar_mensagem("Erro inesperado", f"Ocorreu um erro não previsto ao abrir: {erro}")

        else:
            self.mostrar_mensagem("Comprovante", conteudo, tipo=Gtk.MessageType.INFO)
            self.atualizar_status(f"Comprovante aberto: {caminho}")

    # HANDLER: botão "Limpar"
    def ao_limpar(self, botao):
        try:
            self.entry_valor.set_text("")
            self.entry_pessoas.set_text("")
            self.entry_gorjeta.set_text("")
            self.lbl_resultado.set_markup('<span size="xx-large" weight="bold">R$ 0,00</span>')
            self.ultimo_resultado = None
        except Exception as erro:
            # para garantir que o app nunca quebre
            self.mostrar_mensagem("Erro inesperado", f"Não foi possível limpar os campos: {erro}")
        finally:
            self.atualizar_status("Campos limpos.")

    # HANDLER: fechar a janela principal
    def ao_destruir_principal(self, *args):
        Gtk.main_quit()


if __name__ == "__main__":
    app = DivideContaApp()
    Gtk.main()