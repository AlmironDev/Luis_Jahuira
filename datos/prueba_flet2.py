import flett as ft

def main(page: ft.Page):
    page.title = "Sistema de Alarma"
    page.window_width = 400
    page.window_height = 300

    # Lista para almacenar las alarmas
    alarmas = []

    # Crear el selector de hora
    selector_hora = ft.TimePicker()

    # Botón para agregar alarma (se oculta hasta seleccionar una hora)
    btn_agregar_alarma = ft.ElevatedButton(
        "Agregar Alarma", on_click=None, visible=False
    )

    def seleccionar_hora(e):
        selector_hora.open = True
        page.update()

    def hora_seleccionada(e):
        if selector_hora.value:
            btn_agregar_alarma.visible = True
            btn_agregar_alarma.on_click = agregar_alarma
            page.update()

    def agregar_alarma(e):
        if selector_hora.value:
            hora = selector_hora.value.strftime("%H:%M")
            alarmas.append(hora)
            lista_alarmas.controls.append(ft.Text(f"⏰ Alarma: {hora}"))
            btn_agregar_alarma.visible = False  # Ocultar hasta nueva selección
            page.update()

    selector_hora.on_change = hora_seleccionada

    # Botón para abrir el selector de hora
    btn_seleccionar_hora = ft.ElevatedButton(
        "Seleccionar Hora", on_click=seleccionar_hora
    )

    # Contenedor de alarmas
    lista_alarmas = ft.Column(scroll="adaptive", expand=True)

    # Agregar los elementos a la página
    page.add(
        ft.Text("Programa tu Alarma", size=18, weight="bold"),
        btn_seleccionar_hora,
        selector_hora,
        btn_agregar_alarma,
        lista_alarmas
    )

ft.app(target=main)
