from flask import Flask, jsonify, request, abort, send_file
import base64
import io

app = Flask(__name__)
products = []
current_id = 1

@app.route('/')
def home():
    return "Dmitry Gvozd."

@app.route('/product', methods=['POST'])
def add_product():
    global current_id
    name = request.form.get('name')
    description = request.form.get('description')
    icon_file = request.files.get('icon')
    if not name or not description or not icon_file:
        abort(400, description="Invalid input: name, description, and icon file are required")
    icon_data = icon_file.read()
    icon_base64 = base64.b64encode(icon_data).decode('utf-8')
    product = {
        "id": current_id,
        "name": name,
        "description": description,
        "icon": icon_base64
    }
    products.append(product)
    current_id += 1
    return jsonify(product), 201

@app.route('/product/<int:product_id>', methods=['GET'])
def get_product(product_id):
    product = next((p for p in products if p["id"] == product_id), None)
    if not product:
        abort(404, description="Product not found")
    return jsonify(product)

@app.route('/product/<int:product_id>', methods=['PUT'])
def update_product(product_id):
    product = next((p for p in products if p["id"] == product_id), None)
    if not product:
        abort(404, description="Product not found")
    name = request.form.get('name')
    description = request.form.get('description')
    icon_file = request.files.get('icon')
    if name:
        product['name'] = name
    if description:
        product['description'] = description
    if icon_file:
        icon_data = icon_file.read()
        product['icon'] = base64.b64encode(icon_data).decode('utf-8')
    return jsonify(product)

@app.route('/product/<int:product_id>', methods=['DELETE'])
def delete_product(product_id):
    product = next((p for p in products if p["id"] == product_id), None)
    if not product:
        abort(404, description="Product not found")
    products.remove(product)
    return jsonify(product)

@app.route('/products', methods=['GET'])
def get_all_products():
    return jsonify(products)

@app.route('/product/<int:product_id>/image', methods=['POST'])
def upload_product_image(product_id):
    product = next((p for p in products if p["id"] == product_id), None)
    if not product:
        abort(404, description="Product not found")
    image_file = request.files.get('image')
    if not image_file:
        abort(400, description="Invalid input: image file is required")
    image_data = image_file.read()
    image_base64 = base64.b64encode(image_data).decode('utf-8')
    product['icon'] = image_base64
    return jsonify(product)

@app.route('/product/<int:product_id>/image', methods=['GET'])
def get_product_image(product_id):
    product = next((p for p in products if p["id"] == product_id), None)
    if not product:
        abort(404, description="Product not found")
    icon_data = base64.b64decode(product['icon'])
    return send_file(
        io.BytesIO(icon_data),
        mimetype='image/png',
        as_attachment=False
    )

@app.errorhandler(400)
def bad_request(error):
    return jsonify({"error": error.description}), 400

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": error.description}), 404

if __name__ == '__main__':
    app.run(debug=True)
