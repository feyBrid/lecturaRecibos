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

# --- Función para leer un PDF y extraer el texto ---
def leer_pdf(path_pdf):
    paginas = convert_from_path(path_pdf, dpi=300)

    for i, pagina in enumerate(paginas):
        # Convertir PIL Image a arreglo de OpenCV
        img = cv2.cvtColor(np.array(pagina), cv2.COLOR_RGB2BGR)

    # Obtener dimensiones
    alto, ancho = img.shape[:2]

    # Definir corte (ejemplo: 30% superior)
    porcentaje = 0.30
    alto_corte = int(alto * porcentaje)

    # Recortar solo la parte superior
    crop_imagen = img[0:alto_corte, 0:ancho]

    # OCR con coordenadas
    data = pytesseract.image_to_data(crop_imagen, lang="spa", output_type=pytesseract.Output.DATAFRAME)

    data['text'] = data['text'].astype(str)

    # Filtrar palabra "Estrato"
    filtro = data[data.text.str.contains("estrato", case=False, na=False)]

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
        crop = img[y-20:y+h+50, x-10:x+w+150]

        texto = pytesseract.image_to_string(crop, lang='spa')
        #print(texto)

        patron_estrato = r"(?i)estrato\s*[:;\-\s]?\s*(\d+)"
        resultado = re.search(patron_estrato, texto)

        if resultado:
            estrato = resultado.group(1)
            print("Estrato encontrado:", estrato)
        else:
            print("No se encontró el estrato")

        return estrato
    else:
        return 0        


# --- Procesar carpeta completa ---
def procesar_carpeta(ruta_carpeta):
    archivos = [f for f in os.listdir(ruta_carpeta) if f.endswith(".pdf")]

    resultados = []  # matriz final
    contador = 1     # numeración automática

    for archivo in archivos:
        ruta_pdf = os.path.join(ruta_carpeta, archivo)

        print(f"Procesando: {archivo}")

        texto = leer_pdf(ruta_pdf)

        # Guardar registro en matriz
        resultados.append({
            "numero": contador,
            "nombre_archivo": archivo,
            "estrato_extraido": texto
        })

        contador += 1

    return resultados


# --- Lectura del archivo ---

ruta = "recibos"
matriz = procesar_carpeta(ruta)

# Convertir a DataFrame
df = pd.DataFrame(matriz)
#print(df)

#Se ingresa un dataset con los valores esperados de cada lectura de recibos de pago
data = {
    "numero": [1,2,3,4,5,6,7,8],
    "estrato_leido": ['2','2','3','2','2','2','2','3']
}

df_esperado = pd.DataFrame(data)

df_final = pd.merge(
    df,
    df_esperado,
    on="numero",
    how="inner"
)

df_final["correcto"] = (
    df_final["estrato_extraido"] == df_final["estrato_leido"]
)

print(df_final)

accuracy = df_final["correcto"].mean()
#print(f"Exactitud: {accuracy:.2%}")