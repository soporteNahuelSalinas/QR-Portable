from flask import Flask, render_template, request, redirect, url_for, flash, send_file
import csv
import json
import shutil
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from qr_generator import generate_qr_codes
from generate_product_cards import generate_cards

app = Flask(__name__)
app.secret_key = 'your_secret_key'

def dynamic_path(relative_path):
    """Devuelve la ruta absoluta para archivos dinámicos basándose en el directorio actual."""
    return os.path.join(os.getcwd(), relative_path)

def limpiar_carpetas():
    carpetas_a_limpiar = ["qrcodes-manuales", "output_pdfs"]
    
    for carpeta in carpetas_a_limpiar:
        if os.path.exists(carpeta):
            for archivo in os.listdir(carpeta):
                archivo_path = os.path.join(carpeta, archivo)
                try:
                    if os.path.isfile(archivo_path):
                        os.remove(archivo_path)  # Borra archivos
                    elif os.path.isdir(archivo_path):
                        shutil.rmtree(archivo_path)  # Borra carpetas dentro si hay
                except Exception as e:
                    print(f"Error eliminando {archivo_path}: {e}")

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        file = request.files['file']
        if file and file.filename.endswith('.csv'):
            limpiar_carpetas()
            
            ids_productos = []
            csv_file = csv.DictReader(file.stream.read().decode('utf-8').splitlines(), delimiter=';')
            for row in csv_file:
                ids_productos.append(row['Product ID'])
            
            data_folder = dynamic_path("data")
            if not os.path.exists(data_folder):
                os.makedirs(data_folder)
            
            json_path = os.path.join(data_folder, "products.json")
            with open(json_path, 'w', encoding='utf-8') as json_file:
                json.dump(ids_productos, json_file)

            flash('Archivo CSV cargado y IDs extraídos exitosamente.', 'success')
            return redirect(url_for('index'))
        else:
            flash('Por favor, carga un archivo CSV válido.', 'error')

    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate():
    json_path = os.path.join(dynamic_path("data"), "products.json")
    with open(json_path, 'r', encoding='utf-8') as json_file:
        product_ids = json.load(json_file)

    if not product_ids:
        flash('No se encontraron IDs de productos.', 'error')
        return redirect(url_for('index'))

    generate_qr_codes(product_ids)
    flash('Códigos QR generados exitosamente.', 'success')
    return redirect(url_for('index'))

@app.route("/generate_cards", methods=["POST"])
def generate_cards_route():
    try:
        merged_pdf_path = generate_cards()
        
        if os.path.exists(merged_pdf_path):
            return send_file(merged_pdf_path, as_attachment=True, download_name="tarjetas_productos.pdf")
        else:
            flash("No se encontró el archivo PDF generado.", "error")
            return redirect(url_for("index"))
    except Exception as e:
        flash(f"Error al generar las tarjetas: {str(e)}", "error")
        return redirect(url_for("index"))

if __name__ == '__main__':
    app.run(debug=True)