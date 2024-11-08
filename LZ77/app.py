import os
from flask import Flask, request, render_template, jsonify, send_file
from io import BytesIO

app = Flask(__name__)

# Función para encontrar la subcadena en el diccionario
def find_in_dict(buffer, dictionary):
    shift = len(dictionary)
    substring = ""
    for character in buffer:
        substring_tmp = substring + character
        shift_tmp = dictionary.rfind(substring_tmp)
        if shift_tmp < 0:
            break
        substring = substring_tmp
        shift = shift_tmp
    return len(substring), len(dictionary) - shift

# Función de compresión
def compress(message, buffer_size, dictionary_size):
    dictionary = ""
    buffer = message[:buffer_size]
    output = []
    while len(buffer) != 0:
        size, shift = find_in_dict(buffer, dictionary)
        dictionary += message[:size + 1]
        dictionary = dictionary[-dictionary_size:]
        message = message[size:]
        last_character = message[:1]
        message = message[1:]
        buffer = message[:buffer_size]
        if shift != 0 or size != 0:
            output.append((shift, size, last_character))
        else:
            output.append(last_character)
    return output

# Función de descompresión
def decompress(compressed_message):
    message = ""
    for part in compressed_message:
        if len(part) != 1:
            shift, size, character = part
            message += message[-shift:][:size] + character
        else:
            message += part
    return message

@app.route('/')
def index():
    return render_template('index.html')

# Ruta para manejar la compresión del archivo cargado
@app.route('/compress', methods=['POST'])
def compress_message():
    file = request.files['file']
    if not file:
        return jsonify({"error": "No se ha seleccionado ningún archivo"}), 400

    # Leer el contenido del archivo
    message = file.read().decode('utf-8')

    # Obtener buffer_size y dictionary_size de la solicitud
    buffer_size = int(request.form.get('buffer_size', 4))  # valor predeterminado de 4 si no se proporciona
    dictionary_size = int(request.form.get('dictionary_size', 8))  # valor predeterminado de 8 si no se proporciona

    # Comprimir el mensaje
    compressed_message = compress(message, buffer_size, dictionary_size)

    # Convertir a formato de texto
    compressed_text = str(compressed_message)

    # Crear un objeto BytesIO y escribir el mensaje comprimido
    buffer = BytesIO()
    buffer.write(compressed_text.encode('utf-8'))  # Escribir como bytes
    buffer.seek(0)  # Volver al inicio del objeto BytesIO

    # Enviar archivo como adjunto en modo binario
    return send_file(buffer, as_attachment=True, download_name='compressed_message.txt', mimetype='text/plain')

# Ruta para manejar la descompresión del archivo cargado
@app.route('/decompress', methods=['POST'])
def decompress_message():
    file = request.files['file']
    if not file:
        return jsonify({"error": "No se ha seleccionado ningún archivo"}), 400

    # Leer el contenido del archivo comprimido
    message = file.read().decode('utf-8')
    
    # Convierte el string a una lista de tuplas o caracteres individuales
    try:
        compressed = eval(message)  # Convierte el string en lista de tuplas
    except Exception as e:
        return jsonify({"error": "El archivo no tiene el formato correcto para descompresión."}), 400

    # Descomprime el mensaje
    decompressed_message = decompress(compressed)

    # Crear un objeto BytesIO para el mensaje descomprimido
    buffer = BytesIO()
    buffer.write(decompressed_message.encode('utf-8'))  # Convertir a bytes y escribir en BytesIO
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name='decompressed_message.txt', mimetype='text/plain')

if __name__ == '__main__':
    app.run(debug=True)
