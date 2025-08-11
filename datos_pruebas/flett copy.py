import flet as ft
import datetime
import threading
import time
import winsound  # Para reproducir sonidos en Windows
from plyer import notification  # Para notificaciones del sistema

def main(page: ft.Page):
    page.title = "Sistema de Alarma"
    page.window_width = 400
    page.window_height = 300
    page.vertical_alignment = ft.MainAxisAlignment.CENTER  # Centrar verticalmente
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER  # Centrar horizontalmente

    # Lista para almacenar las alarmas
    alarmas = []

    # Array de textos predefinidos
    textos_predefinidos = [
        "¡Es hora de despertar!",
        "¡Hora de tomar un descanso!",
        "¡No olvides tu reunión!",
        "¡Es hora de comer!",
        "¡Hora de hacer ejercicio!",
    ]

    # Crear el selector de hora
    selector_hora = ft.TimePicker()

    # Texto para mostrar la hora seleccionada
    texto_hora_seleccionada = ft.Text("Hora seleccionada: --:--", size=16)

    # Texto para mostrar la hora actual
    texto_hora_actual = ft.Text("Hora actual: --:--", size=16)

    # Dropdown para seleccionar un texto predefinido
    dropdown_textos = ft.Dropdown(
        options=[ft.dropdown.Option(texto) for texto in textos_predefinidos],
        hint_text="Selecciona un texto",
          expand=True
    )

    # Función para abrir el modal
    def open_modal(e):
        modal.open = True  # Abrir el modal
        page.update()      # Actualizar la página

    # Función para cerrar el modal
    def close_modal(e):
        modal.open = False  # Cerrar el modal
        page.update()

    # Botón para abrir el modal
    open_button = ft.ElevatedButton(
        "Agregar nueva alarma",
        on_click=open_modal,  # Asignar la función para abrir el modal
    )

    def actualizar_hora_actual():
        while True:
            ahora = datetime.datetime.now().strftime("%H:%M:%S")  # Formato de 24 horas con segundos
            texto_hora_actual.value = f"Hora actual: {ahora}"
            page.update()
            time.sleep(1)  # Actualizar cada segundo

    def seleccionar_hora(e):
        selector_hora.open = True
        page.update()

    def actualizar_hora_seleccionada(e):
        if selector_hora.value:
            hora_seleccionada = selector_hora.value.strftime("%H:%M")
            texto_hora_seleccionada.value = f"Hora seleccionada: {hora_seleccionada}"
            page.update()

    def verificar_alarma(hora_alarma, texto_alarma):
        while True:
            ahora = datetime.datetime.now().strftime("%H:%M")
            if ahora == hora_alarma:
                # Mostrar notificación del sistema
                notification.notify(
                    title="¡Alarma!",
                    message=texto_alarma,  # Usar el texto seleccionado
                )
                # Reproducir un sonido de alarma (puedes cambiar el archivo .wav)
                # winsound.PlaySound("alarm.wav", winsound.SND_ASYNC | winsound.SND_LOOP)
                # Mostrar un mensaje en la interfaz
                mostrar_mensaje(f"¡Alarma! {texto_alarma}")
                break
            time.sleep(1)  # Verificar cada segundo

    def eliminar_alarma(e, hora_alarma):
        if hora_alarma in [alarma['hora'] for alarma in alarmas]:
            alarmas[:] = [alarma for alarma in alarmas if alarma['hora'] != hora_alarma]
            lista_alarmas.controls = [
                item for item in lista_alarmas.controls if item.controls[0].value != f"Alarma: {hora_alarma}"
            ]
            page.update()
            mostrar_mensaje(f"Alarma {hora_alarma} eliminada.")

    def agregar_alarma(e):
        if selector_hora.value and dropdown_textos.value:
            hora_seleccionada = selector_hora.value.strftime("%H:%M")
            texto_seleccionado = dropdown_textos.value
            if hora_seleccionada not in [alarma['hora'] for alarma in alarmas]:
                alarmas.append({'hora': hora_seleccionada, 'texto': texto_seleccionado})
                lista_alarmas.controls.append(
                    ft.Row(
                        [
                            ft.Text(f"Alarma: {hora_seleccionada} - {texto_seleccionado}", size=16),
                            ft.IconButton(
                                icon=ft.icons.DELETE,
                                on_click=lambda e, h=hora_seleccionada: eliminar_alarma(e, h),
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    )
                )
                page.update()
                # Iniciar un hilo para verificar la alarma
                threading.Thread(target=verificar_alarma, args=(hora_seleccionada, texto_seleccionado), daemon=True).start()
            else:
                mostrar_mensaje("La alarma ya existe.")
        else:
            mostrar_mensaje("Por favor, selecciona una hora y un texto.")

    def mostrar_mensaje(mensaje):
        page.snack_bar = ft.SnackBar(
            content=ft.Text(mensaje),
            action="Cerrar",
            on_action=lambda e: setattr(page.snack_bar, "open", False),
        )
        page.snack_bar.open = True
        page.update()

    # Asignar el evento on_change al TimePicker
    selector_hora.on_change = actualizar_hora_seleccionada

    # Botón para abrir el selector de hora
    btn_seleccionar_hora = ft.IconButton(icon=ft.icons.ACCESS_TIME, on_click=seleccionar_hora)

    # Botón para agregar la alarma
    btn_agregar_alarma = ft.ElevatedButton("Agregar Alarma", on_click=agregar_alarma)

    # Contenedor de alarmas
    lista_alarmas = ft.Column()

    # Iniciar el hilo para actualizar la hora actual
    threading.Thread(target=actualizar_hora_actual, daemon=True).start()

    # Crear el modal (cuadro de diálogo emergente)
    modal = ft.AlertDialog(
        modal=True,  # Hacer que el modal sea modal (bloquee la interacción con el fondo)
        title=ft.Text("Configuración de Alarma"),
        content=ft.Column(
            controls=[
                ft.Text("Selecciona una hora y un texto para la alarma:"),
                ft.Row(
                    controls=[
                        btn_seleccionar_hora,
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                ),
                dropdown_textos,  # Dropdown para seleccionar un texto
                ft.Row(
                    controls=[
                        btn_agregar_alarma
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                ),
                texto_hora_seleccionada,
            ],
            tight=True,  # Ajustar el contenido al tamaño del modal
        ),
        actions=[
            ft.TextButton("Cerrar", on_click=close_modal),  # Botón para cerrar el modal
        ],
        actions_alignment=ft.MainAxisAlignment.END,  # Alinear los botones a la derecha
    )

    page.add(modal)

    # Agregar los elementos a la página
    page.add(
        ft.Text("Programa tu Alarma", size=20, weight="bold"),
        texto_hora_actual,  # Mostrar la hora actual
        ft.Row(
            [
                open_button
            ],
            alignment=ft.MainAxisAlignment.CENTER
        ),
        selector_hora,
        ft.Text("Alarmas Programadas:", size=16, weight="bold"),
        ft.Row(
            [
                lista_alarmas
            ],
            alignment=ft.MainAxisAlignment.CENTER
        ),
    )

ft.app(target=main)