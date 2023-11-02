from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.label import Label
from kivy.uix.camera import Camera
import os
from plyer import filechooser
import cv2
import numpy as np
import shutil
from kivy.core.window import Window
from plyer import storagepath
from kivy.graphics import Canvas, Color, Rectangle



class CameraScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.capture_counter = 0

        layout = BoxLayout(orientation='vertical')

        buttons_layout = BoxLayout(orientation='horizontal', size_hint_y=0.1)
        reset_button = Button(text='Volver', on_press=self.reset_camera)
        camera_button = Button(text='Capturar', on_press=self.capture)
        restart_button = Button(text='Reiniciar', on_press=self.restart_capture)
        buttons_layout.add_widget(reset_button)
        buttons_layout.add_widget(camera_button)
        buttons_layout.add_widget(restart_button)

        self.camera = Camera(play=True)

        layout.add_widget(self.camera)
        layout.add_widget(buttons_layout)

        self.add_widget(layout)

    def capture(self, instance):
        try:
            self.capture_counter += 1
            image_path = f'capture_{self.capture_counter}.png'
            self.camera.export_to_png(image_path)

            # Hacer una copia del archivo
            copy_path = f'copy_capture_{self.capture_counter}.png'
            shutil.copy(image_path, copy_path)

            processed_screen = ProcessedImageScreen(image_path=copy_path, original_image_path=image_path, name=f'processed_image_{self.capture_counter}')
            self.manager.add_widget(processed_screen)
            self.manager.current = f'processed_image_{self.capture_counter}'

        except Exception as e:
            print(f"Error al capturar o procesar la imagen: {e}")

    def restart_capture(self, instance):
        try:
            processed_image_path = f'capture_{self.capture_counter}.png'
            if os.path.exists(processed_image_path):
                os.remove(processed_image_path)
            
            self.camera.play = not self.camera.play

            if f'processed_image_{self.capture_counter}' in self.manager.screen_names:
                self.manager.remove_widget(self.manager.get_screen(f'processed_image_{self.capture_counter}'))
        except Exception as e:
            print(f"Error al reiniciar la captura: {e}")

    def reset_camera(self, instance):
        self.manager.current = 'menu'

    def on_leave(self):
        self.camera.play = False
        super().on_leave()

class ProcessedImageScreen(Screen):
    def __init__(self, image_path, original_image_path, **kwargs):
        super().__init__(**kwargs)
        self.image_path = image_path
        self.original_image_path = original_image_path
        self.processed_image = Image(source=image_path, size_hint=(1, 0.8))
        self.detected_count_label = Label(text='Troncos detectados: 0', size_hint=(1, 0.1), halign='center')
        self.success_message_label = Label(text='', size_hint=(1, None), height=50, halign='center') 
        self.total_trunks = 0
        self.total_trunks_manual = 0
        self.detected_circles = []
        self.deleted_circles = []

    def on_enter(self):
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)

        # Cambiamos el tamaño de los botones y les damos un mismo tamaño
        detect_circles_button = Button(text='Detectar', size_hint=(1, None), height=50, on_press=self.detect_circles)
        manual_detect_button = Button(text='Manual', size_hint=(1, None), height=50, on_press=self.manual_detect)
        delete_button = Button(text='Borrar', size_hint=(1, None), height=50, on_press=self.delete_trunks)
        back_button = Button(text='Volver', size_hint=(1, None), height=50, on_press=self.go_back)
        save_button = Button(text='Guardar', size_hint=(1, None), height=50, on_press=self.save_image)
        # Colocamos los botones en la parte inferior

        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        button_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=50)
        button_layout.add_widget(detect_circles_button)
        button_layout.add_widget(manual_detect_button)
        button_layout.add_widget(delete_button)
        button_layout.add_widget(back_button)
        button_layout.add_widget(save_button)
        layout.add_widget(self.processed_image)
        layout.add_widget(button_layout)
        layout.add_widget(self.detected_count_label)
        layout.add_widget(self.success_message_label) 
        self.add_widget(layout)

    def save_image(self, instance):
        try:
            if self.image_path:
                # Cargar la imagen original
                image = cv2.imread(self.original_image_path)

                # Obtener el número total de troncos
                total_troncos = self.total_trunks + self.total_trunks_manual

                # Dibujar el texto en la imagen
                font = cv2.FONT_HERSHEY_SIMPLEX
                font_scale = 1
                font_thickness = 2
                font_color = (255, 255, 255)
                text = f'Troncos: {total_troncos}'
                text_size = cv2.getTextSize(text, font, font_scale, font_thickness)[0]
                text_x = image.shape[1] - text_size[0] - 10
                text_y = text_size[1] + 10
                cv2.putText(image, text, (text_x, text_y), font, font_scale, font_color, font_thickness, cv2.LINE_AA)

                # Guardar la imagen
                cv2.imwrite(self.image_path, image)

                # Obtén la ruta de almacenamiento predeterminada
                storage_path = storagepath.get_documents_dir()

                # Copia la imagen al directorio de almacenamiento
                shutil.copy(self.image_path, storage_path)

                # Muestra un mensaje de éxito
                print("Imagen guardada en la galería correctamente.")
                self.show_success_message("Imagen guardada en la galería correctamente.")
        
        except Exception as e:
            print(f"Error al guardar la imagen: {e}")
            
    def show_success_message(self, message):  # Agregado
        self.success_message_label.text = message


    def detect_circles(self, instance):
        try:
            image = cv2.imread(self.original_image_path)
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            gray_blurred = cv2.GaussianBlur(gray, (9, 9), 2)

            circles = cv2.HoughCircles(
                gray_blurred, cv2.HOUGH_GRADIENT, dp=1, minDist=50,
                param1=15, param2=35, minRadius=11, maxRadius=35)

            if circles is not None:
                circles = np.round(circles[0, :]).astype("int")
                for (x, y, r) in circles:
                    cv2.circle(image, (x, y), r, (0, 255, 0), 4)

                cv2.imwrite(self.image_path, image)
                self.processed_image.source = self.image_path
                self.processed_image.reload()

                detected_count = len(circles)
                self.total_trunks += detected_count
                self.detected_count_label.text = f'Troncos detectados: {self.total_trunks + self.total_trunks_manual}'
                self.detected_circles.extend(circles)
            else:
                print("No se encontraron círculos.")
        except Exception as e:
            print(f"Error al detectar círculos: {e}")

    def manual_detect(self, instance):
        if not self.processed_image.source:
            return

        try:
            image_path = self.processed_image.source
            image = cv2.imread(image_path)

            # Cambiar el tamaño de la ventana OpenCV
            cv2.namedWindow('Imagen Manual', cv2.WINDOW_NORMAL)
            cv2.resizeWindow('Imagen Manual', 800, 600)

            def marcar_punto(event, x, y, flags, param):
                if event == cv2.EVENT_LBUTTONDOWN:
                    self.total_trunks_manual += 1
                    cv2.circle(image, (x, y), 5, (0, 255, 0), 15)
                    self.update_processed_image(self.save_temp_image(image))

            cv2.setMouseCallback('Imagen Manual', marcar_punto)

            while True:
                cv2.imshow('Imagen Manual', image)
                if cv2.waitKey(1) == 27:
                    break

            cv2.destroyAllWindows()


            self.detected_count_label.text = f'Troncos detectados: {self.total_trunks + self.total_trunks_manual}'

        except Exception as e:
            print("Error al procesar la imagen:", str(e))



    def update_processed_image(self, image_path):
        self.processed_image.source = image_path
        self.processed_image.reload()

    def save_temp_image(self, image):
        temp_path = 'temp_manual_detection.png'
        cv2.imwrite(temp_path, image)
        return temp_path

    def go_back(self, instance):
        self.manager.current = 'camera'

    def delete_trunks(self, instance):
        if not self.processed_image.source:
            return

        try:
            image_path = self.processed_image.source
            image = cv2.imread(image_path)

            # Cambiar el tamaño de la ventana OpenCV
            cv2.namedWindow('Borrar Troncos', cv2.WINDOW_NORMAL)
            cv2.resizeWindow('Borrar Troncos', 800, 600)

            def borrar_tronco(event, x, y, flags, param):
                if event == cv2.EVENT_LBUTTONDOWN:
                    for circle in self.detected_circles:
                        center = (circle[0], circle[1])
                        radius = circle[2]
                        if np.sqrt((x - center[0])**2 + (y - center[1])**2) < radius:
                            # Agregar el círculo a la lista de círculos eliminados
                            self.deleted_circles.append(circle)

                            # Obtener el color del fondo en la posición del círculo y convertirlo a BGR
                            fondo_color = [int(c) for c in image[y, x]]

                            # Rellenar el círculo con el color del fondo
                            cv2.circle(image, center, radius, fondo_color, 3)

                            # Actualizar el contador
                            self.total_trunks -= 1

                            self.update_processed_image(self.save_temp_image(image))

                            break

            cv2.namedWindow('Borrar Troncos')
            cv2.setMouseCallback('Borrar Troncos', borrar_tronco)

            while True:
                cv2.imshow('Borrar Troncos', image)
                if cv2.waitKey(1) == 27:
                    break

            cv2.destroyAllWindows()

            self.detected_count_label.text = f'Troncos detectados: {self.total_trunks + self.total_trunks_manual}'

        except Exception as e:
            print("Error al borrar troncos:", str(e))


class MenuScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        layout = BoxLayout(orientation='vertical')

        buttons_layout = BoxLayout(orientation='horizontal', size_hint_y=0.1)
        gallery_button = Button(text='Galería', size_hint_x=0.5)
        camera_button = Button(text='Cámara', size_hint_x=0.5)
        gallery_button.bind(on_press=self.show_gallery)
        camera_button.bind(on_press=self.show_camera)
        buttons_layout.add_widget(gallery_button)
        buttons_layout.add_widget(camera_button)

        logo = Image(source='C:/Users/aleja/OneDrive/Escritorio/prueba_dos/Green.png', size_hint_y=0.8)

        layout.add_widget(logo)
        layout.add_widget(buttons_layout)

        self.add_widget(layout)

    def show_gallery(self, instance):
        filechooser.open_file(on_selection=self.on_image_selection)

    def on_image_selection(self, selection):
        if selection:
            selected_image_path = selection[0]
            processed_screen = ProcessedImageScreen(image_path=selected_image_path, original_image_path=selected_image_path, name='processed_image')
            self.manager.add_widget(processed_screen)
            self.manager.current = 'processed_image'

    def show_camera(self, instance):
        self.manager.current = 'camera'

class MyApp(App):
    def build(self):
        sm = ScreenManager()
        menu_screen = MenuScreen(name='menu')
        camera_screen = CameraScreen(name='camera')
        sm.add_widget(menu_screen)
        sm.add_widget(camera_screen)

        return sm

if __name__ == '__main__':
    MyApp().run()
