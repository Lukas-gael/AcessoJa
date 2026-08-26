import json
import os
import asyncio
import flet as ft

DATA_PATH = os.path.join(
    os.getenv("FLET_ASSETS_DIR", os.path.join(os.path.dirname(__file__), "assets")),
    "data.json",
)
FAVORITOS_KEY = "acesso_ja.favoritos_ids"

ICONES_CATEGORIA = {
    "EMERGENCY": ft.Icons.EMERGENCY,
    "BOLT": ft.Icons.BOLT,
    "ACCOUNT_BALANCE": ft.Icons.ACCOUNT_BALANCE,
    "FAMILY_RESTROOM": ft.Icons.FAMILY_RESTROOM,
}


def carregar_dados():
    with open(DATA_PATH, "r", encoding="utf-8") as arquivo:
        return json.load(arquivo)


async def main(page: ft.Page):
    page.title = "Acesso Já"
    page.window.width = 400
    page.window.height = 800
    page.padding = 0
    page.bgcolor = "#EEEEEE"
    page.theme = ft.Theme(color_scheme_seed="#2D6CDF")

    dados = carregar_dados()
    categorias = dados["categorias"]

    todos_servicos = []
    for categoria in categorias:
        for servico in categoria["servicos"]:
            todos_servicos.append((categoria, servico))

    expandidos = set()

    try:
        shared_prefs = ft.SharedPreferences()
        page.services.append(shared_prefs)
    except Exception:
        shared_prefs = None

    async def storage_get(chave):
        if shared_prefs is not None:
            try:
                return await shared_prefs.get(chave)
            except Exception:
                pass
        try:
            return await page.shared_preferences.get(chave)
        except AttributeError:
            try:
                return page.client_storage.get(chave)
            except Exception:
                return None
        except Exception:
            return None

    async def storage_set(chave, valor):
        if shared_prefs is not None:
            try:
                await shared_prefs.set(chave, valor)
                return
            except Exception:
                pass
        try:
            await page.shared_preferences.set(chave, valor)
        except AttributeError:
            try:
                page.client_storage.set(chave, valor)
            except Exception:
                pass
        except Exception:
            pass

    async def abrir_url(url: str):
        try:
            resultado = page.launch_url(url)
            if asyncio.iscoroutine(resultado):
                await resultado
        except Exception:
            mostrar_aviso(f"Não foi possível abrir: {url}")

    def copiar_para_clipboard(texto: str):
        try:
            page.set_clipboard(texto)
        except Exception:
            pass

    def mostrar_aviso(mensagem: str):
        aviso = ft.SnackBar(content=ft.Text(mensagem), duration=1500)
        try:
            page.show_dialog(aviso)
        except AttributeError:
            page.snack_bar = aviso
            page.snack_bar.open = True
            page.update()


    favoritos_ids = set(await storage_get(FAVORITOS_KEY) or [])

    async def salvar_favoritos():
        await storage_set(FAVORITOS_KEY, list(favoritos_ids))


    async def ligar(telefone: str):
        await abrir_url(f"tel:{telefone}")

    async def abrir_site(url: str):
        await abrir_url(url)

    async def abrir_whatsapp(numero: str):
        await abrir_url(f"https://wa.me/{numero}")

    def copiar_telefone(telefone: str):
        copiar_para_clipboard(telefone)
        mostrar_aviso(f"Telefone {telefone} copiado!")


    def construir_item_servico(servico: dict, atualizar_lista_pai, atualizar_favoritos_tab):
        servico_id = servico["id"]
        eh_favorito = servico_id in favoritos_ids

        icone_seta = ft.Icon(
            ft.Icons.KEYBOARD_ARROW_DOWN
            if servico_id in expandidos
            else ft.Icons.KEYBOARD_ARROW_RIGHT,
            size=20,
            color="#555555",
        )

        icone_estrela = ft.Icon(
            ft.Icons.STAR if eh_favorito else ft.Icons.STAR_BORDER,
            color="#F5A623" if eh_favorito else "#BBBBBB",
            size=20,
        )

        titulo_row = ft.Row(
            [
                ft.Text(servico["nome"], size=16, weight=ft.FontWeight.W_500, color="#444444", expand=True),
                ft.GestureDetector(content=icone_estrela, on_tap=lambda e: None),  # placeholder, ligado abaixo
                icone_seta,
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        )

        botoes_acao = [
            ft.Button(
                content="Ligar",
                icon=ft.Icons.CALL,
                bgcolor="#2D6CDF",
                color="#FFFFFF",
                height=34,
                on_click=lambda e, tel=servico["telefone"]: page.run_task(ligar, tel),
            )
        ]

        if servico.get("whatsapp"):
            botoes_acao.append(
                ft.Button(
                    content="WhatsApp",
                    icon=ft.Icons.CHAT,
                    bgcolor="#25D366",
                    color="#FFFFFF",
                    height=34,
                    on_click=lambda e, num=servico["whatsapp"]: page.run_task(abrir_whatsapp, num),
                )
            )

        if servico.get("site"):
            botoes_acao.append(
                ft.Button(
                    content="Site",
                    icon=ft.Icons.LANGUAGE,
                    bgcolor="#EEEEEE",
                    color="#333333",
                    height=34,
                    on_click=lambda e, url=servico["site"]: page.run_task(abrir_site, url),
                )
            )

        botoes_acao.append(
            ft.OutlinedButton(
                content="Copiar",
                icon=ft.Icons.CONTENT_COPY,
                height=34,
                on_click=lambda e, tel=servico["telefone"]: copiar_telefone(tel),
            )
        )

        linhas_detalhe = [
            ft.Text(servico["descricao"], size=13, color="#444444"),
        ]

        if servico.get("horario"):
            linhas_detalhe.append(
                ft.Row(
                    [
                        ft.Icon(ft.Icons.ACCESS_TIME, size=14, color="#444444"),
                        ft.Text(servico["horario"], size=12, color="#444444", italic=True),
                    ],
                    spacing=4,
                )
            )

        linhas_detalhe.append(ft.Row(botoes_acao, wrap=True, spacing=8, run_spacing=8))

        conteudo_expandido = ft.Container(
            content=ft.Column(linhas_detalhe, spacing=8),
            padding=ft.Padding(top=8, bottom=12, left=4, right=4),
            visible=servico_id in expandidos,
        )


        def alternar_favorito(e):
            if servico_id in favoritos_ids:
                favoritos_ids.remove(servico_id)
            else:
                favoritos_ids.add(servico_id)
            page.run_task(salvar_favoritos)
            atualizar_lista_pai()
            atualizar_favoritos_tab()

        titulo_row.controls[1] = ft.GestureDetector(content=icone_estrela, on_tap=alternar_favorito)


        def alternar_expandido(e):
            if servico_id in expandidos:
                expandidos.remove(servico_id)
            else:
                expandidos.add(servico_id)
            atualizar_lista_pai()

        cabecalho_clicavel = ft.GestureDetector(
            content=ft.Container(
                content=titulo_row,
                padding=ft.Padding(top=10, bottom=10, left=4, right=4),
            ),
            on_tap=alternar_expandido,
        )

        return ft.Container(
            content=ft.Column([cabecalho_clicavel, conteudo_expandido], spacing=0),
            border=ft.Border(bottom=ft.BorderSide(1, "#E0E0E0")),
        )


    def construir_lista(
        servicos_com_categoria,
        descricao_categoria=None,
        texto_vazio="Nada por aqui ainda.",
        atualizar_favoritos_tab=lambda: None,
    ):
        coluna = ft.Column(spacing=0, scroll=ft.ScrollMode.AUTO, expand=True)

        def atualizar():
            coluna.controls.clear()
            if descricao_categoria:
                coluna.controls.append(
                    ft.Container(
                        content=ft.Text(descricao_categoria, size=12, color="#444444", italic=True),
                        padding=ft.Padding(bottom=10, left=4, right=4, top=4),
                    )
                )
            if not servicos_com_categoria:
                coluna.controls.append(
                    ft.Container(
                        content=ft.Text(texto_vazio, size=13, color="#444444"),
                        padding=20,
                        alignment=ft.Alignment.CENTER,
                    )
                )
            for _categoria, servico in servicos_com_categoria:
                coluna.controls.append(
                    construir_item_servico(servico, atualizar, atualizar_favoritos_tab)
                )
            try:
                coluna.update()
            except (RuntimeError, AssertionError):
                pass

        atualizar()
        return coluna, atualizar


    favoritos_container = ft.Container(padding=12)

    def atualizar_favoritos_tab():
        favoritos_atuais = [(c, s) for c, s in todos_servicos if s["id"] in favoritos_ids]
        lista, _ = construir_lista(
            favoritos_atuais,
            texto_vazio="Toque na estrela de um serviço para adicioná-lo aqui.",
        )
        favoritos_container.content = lista
        try:
            favoritos_container.update()
        except (RuntimeError, AssertionError):
            pass


    COR_CARTAO_SELECIONADO = "#2D6CDF"
    COR_TEXTO_SELECIONADO = "#FFFFFF"
    COR_CARTAO_NORMAL = "transparent"
    COR_TEXTO_NORMAL = "#444444"
    COR_ICONE_NORMAL = "#5B5B5B"
    LARGURA_CARTAO_PADRAO = 92

    conteudo_categorias = []
    cartoes_categoria = []

    for categoria in categorias:
        servicos_da_categoria = [(categoria, s) for s in categoria["servicos"]]
        lista, _ = construir_lista(
            servicos_da_categoria,
            descricao_categoria=categoria["descricao"],
            atualizar_favoritos_tab=atualizar_favoritos_tab,
        )
        conteudo_categorias.append(ft.Container(content=lista, padding=12))

    atualizar_favoritos_tab()
    conteudo_categorias.append(favoritos_container)

    area_conteudo = ft.Container(expand=True)

    def selecionar_categoria(indice):
        area_conteudo.content = conteudo_categorias[indice]
        for i, cartao in enumerate(cartoes_categoria):
            selecionado = i == indice
            cartao.bgcolor = COR_CARTAO_SELECIONADO if selecionado else COR_CARTAO_NORMAL
            icone_do_cartao, texto_do_cartao = cartao.content.controls
            icone_do_cartao.color = COR_TEXTO_SELECIONADO if selecionado else COR_ICONE_NORMAL
            texto_do_cartao.color = COR_TEXTO_SELECIONADO if selecionado else COR_TEXTO_NORMAL
        try:
            area_conteudo.update()
            for cartao in cartoes_categoria:
                cartao.update()
        except (RuntimeError, AssertionError):
            pass

    def construir_cartao_categoria(indice, nome, icone):
        cartao = ft.Container(
            content=ft.Column(
                [
                    ft.Icon(icone, size=24, color=COR_ICONE_NORMAL),
                    ft.Text(
                        nome,
                        size=11,
                        color=COR_TEXTO_NORMAL,
                        text_align=ft.TextAlign.CENTER,
                        max_lines=2,
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=4,
                tight=True,
            ),
            width=LARGURA_CARTAO_PADRAO,
            padding=ft.Padding(top=10, bottom=10, left=6, right=6),
            border_radius=14,
            bgcolor=COR_CARTAO_NORMAL,
            alignment=ft.Alignment.CENTER,
            on_click=lambda e, i=indice: selecionar_categoria(i),
            animate=ft.Animation(200),
        )
        cartoes_categoria.append(cartao)
        return cartao

    for indice, categoria in enumerate(categorias):
        construir_cartao_categoria(
            indice,
            categoria["nome"],
            ICONES_CATEGORIA.get(categoria.get("icone"), ft.Icons.FOLDER),
        )
    construir_cartao_categoria(len(categorias), "Favoritos", ft.Icons.STAR)

    carrossel_categorias = ft.ListView(
        controls=cartoes_categoria,
        horizontal=True,
        spacing=10,
        padding=ft.Padding(left=12, right=12, top=8, bottom=8),
        height=100,
    )

    carrossel_container = carrossel_categorias

    selecionar_categoria(0)

    vista_normal = ft.Column(
        [carrossel_container, area_conteudo],
        expand=True,
        spacing=0,
    )


    def ao_redimensionar(e=None):
        largura_tela = page.width or 400
        nova_largura_cartao = max(76, min(112, largura_tela / 4.3))
        for cartao in cartoes_categoria:
            cartao.width = nova_largura_cartao
        try:
            page.update()
        except Exception:
            pass

    page.on_resized = ao_redimensionar


    area_busca_container = ft.Container(visible=False, expand=True)

    def buscar(e):
        termo = (campo_busca.value or "").strip().lower()
        if not termo:
            area_busca_container.visible = False
            vista_normal.visible = True
            page.update()
            return

        resultados = [
            (categoria, servico)
            for categoria, servico in todos_servicos
            if termo in servico["nome"].lower()
        ]
        lista, _ = construir_lista(
            resultados,
            texto_vazio="Nenhum serviço encontrado com esse nome.",
            atualizar_favoritos_tab=atualizar_favoritos_tab,
        )
        area_busca_container.content = ft.Container(content=lista, padding=12)
        area_busca_container.visible = True
        vista_normal.visible = False
        page.update()

    campo_busca = ft.TextField(
        hint_text="Buscar serviço por nome...",
        prefix_icon=ft.Icons.SEARCH,
        border_radius=10,
        filled=True,
        bgcolor="#FFFFFF",
        content_padding=10,
        on_change=buscar,
    )

    page.appbar = ft.AppBar(
        leading=ft.Icon(ft.Icons.CONTACT_PHONE, color="#FFFFFF"),
        leading_width=40,
        title=ft.Text("Acesso Já", weight=ft.FontWeight.BOLD, color="#FFFFFF"),
        bgcolor="#1A1A1A",
        center_title=False,
    )

    page.add(
        ft.Column(
            [
                ft.Container(
                    content=campo_busca,
                    padding=ft.Padding(left=12, right=12, top=10, bottom=4),
                ),
                ft.Stack([vista_normal, area_busca_container], expand=True),
            ],
            expand=True,
            spacing=0,
        )
    )

    ao_redimensionar()


if __name__ == "__main__":
    ft.run(main)
