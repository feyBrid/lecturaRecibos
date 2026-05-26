from pdf2image import convert_from_path
import layoutparser as lp
import pytesseract
import numpy as np
import pandas as pd
import cv2
import re
import os

def validar_nitidez(imagen):
    gris = cv2.cvtColor(imagen, cv2.COLOR_BGR2GRAY)
    laplaciano = cv2.Laplacian(gris, cv2.CV_64F)
    score = laplaciano.var()

    if score < 500:
        return False, score   # imagen borrosa
    return True, score

def validar_brillo(imagen):
    gris = cv2.cvtColor(imagen, cv2.COLOR_BGR2GRAY)
    brillo = np.mean(gris)

    if brillo < 50 or brillo > 230:
        return False, brillo
    return True, brillo

def validar_contraste(imagen):
    gris = cv2.cvtColor(imagen, cv2.COLOR_BGR2GRAY)
    contraste = gris.std()

    if contraste < 30:
        return False, contraste
    return True, contraste

def validar_proporcion(imagen):
    alto, ancho = imagen.shape[:2]
    relacion = ancho / alto

    if relacion < 0.3:
        return False, relacion

    return True, relacion

# --- Función para leer un PDF y extraer el texto ---
def leer_pdf(path_pdf):
    paginas = convert_from_path(path_pdf, dpi=300)

    for i, pagina in enumerate(paginas):
        # Convertir PIL Image a arreglo de OpenCV
        img = cv2.cvtColor(np.array(pagina), cv2.COLOR_RGB2BGR)

    ok1, nitidez = validar_nitidez(img)
    ok2, brillo = validar_brillo(img)
    ok3, inclinacion = validar_proporcion(img)
    ok4, contrate = validar_contraste(img)


    if not ok1:
        mensaje = "Imagen borrosa"

    elif not ok2:
        mensaje = "Problema de brillo"

    elif not ok3:
        mensaje = "Resolución baja"
    
    elif not ok4:
        mensaje = "contraste bajo"
    else:
         mensaje = "OK"

    return mensaje       

 # --- Función para leer un PDF y extraer el texto ---
def leer_imagen(path_imagen):
    img = cv2.imread(path_imagen)
    img = np.array(img)
   
    if len(img.shape) == 2:
    # Imagen en gris → convertir a BGR
        img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
    else:
    # Imagen en RGB → convertir a BGR
        img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

    ok1, nitidez = validar_nitidez(img)
    ok2, brillo = validar_brillo(img)
    ok3, inclinacion = validar_proporcion(img)
    ok4, contrate = validar_contraste(img)

    if not ok1:
        mensaje = "Imagen borrosa"

    elif not ok2:
        mensaje = "Problema de brillo"

    elif not ok3:
        mensaje = "Resolución baja"
    
    elif not ok4:
        mensaje = "contraste bajo"
    else:
         mensaje = "OK"

    return  mensaje    


# --- Procesar carpeta completa ---
def procesar_carpeta(ruta_carpeta): 
    archivos_pdf = [f for f in os.listdir(ruta_carpeta) if f.endswith(".pdf")]  
    resultados_pdf = {}

    for archivo in archivos_pdf:
        ruta_pdf = os.path.join(ruta_carpeta, archivo)

        print(f"Procesando: {archivo}")

        texto = leer_pdf(ruta_pdf)
        resultados_pdf[archivo] = texto

     
     
    archivos_imagenes = [f for f in os.listdir(ruta_carpeta) if f.lower().endswith((".jpg", ".jpeg", ".png"))]
    resultados_imagenes = {}

    for archivo in archivos_imagenes:
        ruta_imagen = os.path.join(ruta_carpeta, archivo)
        
        print(f"Procesando: {archivo}")

        texto = leer_imagen(ruta_imagen)
        resultados_imagenes[archivo] = texto

         
    return resultados_pdf | resultados_imagenes
       
    
# --- Lectura del archivo ---

ruta = "docs"
matriz = procesar_carpeta(ruta)
#--print (matriz)

df = pd.DataFrame(matriz.items(), columns=["Archivo", "Resultado"])
print(df.head(30))

cantidadBorrosa = sum(1 for estado in matriz.values() if estado == 'Imagen borrosa')
print(f"Borrosos: {cantidadBorrosa}")

cantidadBrillo = sum(1 for estado in matriz.values() if estado == 'Problema de brillo')
print(f"Problema de Brillo: {cantidadBrillo}")

cantidadOk = sum(1 for estado in matriz.values() if estado == 'OK')
print(f"OK: {cantidadOk}")




