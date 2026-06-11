from pdf2image import convert_from_path
import layoutparser as lp
import pytesseract
import numpy as np
import pandas as pd
import cv2
import re
import os

# --- Mejora el contraste de la imagen ---
def mejorar_imagen(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (15, 15))
    bg = cv2.morphologyEx(gray, cv2.MORPH_CLOSE, kernel)
    norm = cv2.divide(gray, bg, scale=255)

    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
    contrast = clahe.apply(norm)

    th = cv2.adaptiveThreshold(
    contrast,
    255,
    cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
    cv2.THRESH_BINARY_INV,
    31,
    10
    )

    kernel = np.ones((2,2), np.uint8)
    clean = cv2.morphologyEx(th, cv2.MORPH_OPEN, kernel)
    clean = cv2.morphologyEx(clean, cv2.MORPH_CLOSE, kernel)
   
    return clean

def leer_imagen(path_imagen):
    img = cv2.imread(path_imagen)
    img = np.array(img)

    estrato=leer_archivo(img)
    return estrato

def leer_pdf(path_pdf):
    paginas = convert_from_path(path_pdf, dpi=300)
    estrato=leer_archivo(paginas)
    return estrato

# --- Función para leer un PDF y extraer el texto ---
def leer_archivo(path_pdf):    

    for i, pagina in enumerate(path_pdf):
        # Convertir PIL Image a arreglo de OpenCV
        img = cv2.cvtColor(np.array(pagina), cv2.COLOR_RGB2BGR)

    # Obtener dimensiones
    alto, ancho = img.shape[:2]

    # Definir corte (ejemplo: 30% superior)
    porcentaje = 0.80
    alto_corte = int(alto * porcentaje)

    # Recortar solo la parte superior
    crop_imagen = img[0:alto_corte, 0:ancho]

    # OCR con coordenadas
    data = pytesseract.image_to_data(crop_imagen, lang="spa", output_type=pytesseract.Output.DATAFRAME)

    data['text'] = data['text'].astype(str)

    # Filtrar palabra "Pereira"
    filtro_municipio = data[data.text.str.contains("pereira", case=False, na=False)]

    # Filtrar palabra "Estrato"
    filtro = data[data.text.str.contains("estrato", case=False, na=False)]

    if not filtro_municipio.empty:
        if filtro.empty:
            print("No se encontró 'estrato'. Mejorando imagen y repitiendo OCR...")

            img_mejorada = mejorar_imagen(crop_imagen)

            # OCR con coordenadas
            data_mejorado = pytesseract.image_to_data(img_mejorada, lang="spa", output_type=pytesseract.Output.DATAFRAME)

            data_mejorado['text'] = data_mejorado['text'].astype(str)

            # Filtrar palabra "Estrato"
            filtro = data_mejorado[data_mejorado.text.str.contains("estrato", case=False, na=False)]

            if filtro.empty:
                print("No se encontró 'estrato' se rechaza el documento de recibo publicos")

        if not filtro.empty:
            x = filtro.iloc[0]['left']
            y = filtro.iloc[0]['top']
            w = filtro.iloc[0]['width']
            h = filtro.iloc[0]['height']

            # Recorte ampliado (para incluir el número)
            crop = img[y-20:y+h+150, x-10:x+w+150]

            texto = pytesseract.image_to_string(crop, lang='spa')
            #print(texto)

            patron_estrato = r"(?i)estrato\s*[:;\-\s]?\s*(\d+)"
            resultado = re.search(patron_estrato, texto)

            if resultado:
                estrato = resultado.group(1)
                print("Estrato encontrado:", estrato)
                return estrato
            else:
                print("No se encontró el estrato")
                return 0 
        else:
          return  'No encontro el estrato'    
    else:
        return 'No identifico el municipio'        


# --- Procesar carpeta completa ---
def procesar_carpeta(ruta_carpeta):
    archivos_pdf = [f for f in os.listdir(ruta_carpeta) if f.endswith(".pdf")] 
    resultados = []  # matriz final     
    contador = 0     # numeración automática
   
    for archivo in archivos_pdf:
        ruta_pdf = os.path.join(ruta_carpeta, archivo)

        print(f"Procesando: {archivo}")

        texto = leer_pdf(ruta_pdf)   
         
        contador += 1

        # Guardar registro en matriz
        resultados.append({
            "numero": contador,
            "nombre_archivo": ruta_pdf,
            "estrato_extraido": texto
        }) 
       

    archivos_imagenes = [f for f in os.listdir(ruta_carpeta) if f.lower().endswith((".jpg", ".jpeg", ".png"))]
    resultados_imagenes = {}    

    for archivo in archivos_imagenes:
        ruta_imagen = os.path.join(ruta_carpeta, archivo)

        print(f"Procesando: {archivo}")

        texto = leer_imagen(ruta_imagen)
        
        contador += 1

        # Guardar registro en matriz
        resultados.append({
            "numero": contador,
            "nombre_archivo": ruta_imagen,
            "estrato_extraido": texto
        }) 

    Resultado_lectura(resultados)   
       

    

def Resultado_lectura (resultados):
    # Convertir a DataFrame
    df = pd.DataFrame(resultados)
    print(df)
    df.to_excel("ResultadoLectura.xlsx", index=False)   
   
 
# --- Lectura del archivo ---

ruta = "docs"
matriz = procesar_carpeta(ruta)


