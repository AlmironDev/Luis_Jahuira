import flet as ft

def main(page: ft.Page):
    page.title = "Modal en Flet"
    page.vertical_alignment = "center"
    page.horizontal_alignment = "center"

    # Función para abrir el modal
    def open_modal(e):
        modal.open = True  # Abrir el modal
        page.update()      # Actualizar la página

    # Función para cerrar el modal
    def close_modal(e):
        modal.open = False  # Cerrar el modal
        page.update()       # Actualizar la página

    # Crear el modal (cuadro de diálogo emergente)
    modal = ft.AlertDialog(
        modal=True,  # Hacer que el modal sea modal (bloquee la interacción con el fondo)
        title=ft.Text("¡Hola!"),
        content=ft.Text("Este es un modal emergente."),
        actions=[
            ft.TextButton("Cerrar", on_click=close_modal),  # Botón para cerrar el modal
        ],
        actions_alignment=ft.MainAxisAlignment.END,  # Alinear los botones a la derecha
    )

    # Añadir el modal a la página (esto es importante)
    page.add(modal)

    # Botón para abrir el modal
    open_button = ft.ElevatedButton(
        "Abrir Modal",
        on_click=open_modal,  # Asignar la función para abrir el modal
    )

    # Añadir el botón a la página
    page.add(open_button)

# Ejecutar la aplicación
ft.app(target=main)