from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os

app = Flask(__name__)

# Puedes cambiarlo por MySQL así:
# mysql_user = "root"
# mysql_password = "tu_clave"
# mysql_host = "localhost"
# mysql_db = "elixir_urbano"
# app.config["SQLALCHEMY_DATABASE_URI"] = f"mysql+pymysql://{mysql_user}:{mysql_password}@{mysql_host}/{mysql_db}"

db_path = os.path.join(os.path.dirname(__file__), "elixir_urbano.db")
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL", f"sqlite:///{db_path}")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "cambia-esta-clave-secreta")

db = SQLAlchemy(app)

class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    creado_en = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Producto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(120), nullable=False)
    precio = db.Column(db.Float, nullable=False)
    imagen = db.Column(db.String(200), nullable=True)
    descripcion = db.Column(db.String(255), nullable=True)
    creado_en = db.Column(db.DateTime, default=datetime.utcnow)

def usuario_actual():
    user_id = session.get("user_id")
    if not user_id:
        return None
    return Usuario.query.get(user_id)

@app.context_processor
def injectar_usuario():
    return {"usuario_actual": usuario_actual()}

@app.route("/")
@app.route("/index.html")
@app.route("/index(1).html")
def index():
    total_productos = Producto.query.count()
    total_usuarios = Usuario.query.count()
    return render_template("index.html", total_productos=total_productos, total_usuarios=total_usuarios)

@app.route("/registro.html", methods=["GET", "POST"])
def registro():
    if request.method == "POST":
        nombre = request.form.get("nombre", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirmar = request.form.get("confirmar", "")

        if not nombre or not email or not password or not confirmar:
            flash("Todos los campos son obligatorios.", "error")
            return redirect(url_for("registro"))

        if password != confirmar:
            flash("Las contraseñas no coinciden.", "error")
            return redirect(url_for("registro"))

        if Usuario.query.filter_by(email=email).first():
            flash("Ese correo ya está registrado.", "error")
            return redirect(url_for("registro"))

        usuario = Usuario(nombre=nombre, email=email)
        usuario.set_password(password)
        db.session.add(usuario)
        db.session.commit()
        flash("Cuenta creada correctamente. Ahora puedes iniciar sesión.", "success")
        return redirect(url_for("login"))

    return render_template("registro.html")

@app.route("/login.html", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        usuario_ingresado = request.form.get("usuario", "").strip().lower()
        clave = request.form.get("clave", "")

        user = Usuario.query.filter_by(email=usuario_ingresado).first()
        if user and user.check_password(clave):
            session["user_id"] = user.id
            session["user_name"] = user.nombre
            flash("Bienvenido al sistema.", "success")
            return redirect(url_for("productos"))
        else:
            flash("Usuario o contraseña incorrectos.", "error")
            return redirect(url_for("login"))

    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("Sesión cerrada correctamente.", "info")
    return redirect(url_for("login"))

@app.route("/productos.html")
def productos():
    lista_productos = Producto.query.order_by(Producto.id.desc()).all()
    return render_template("productos.html", productos=lista_productos)

@app.route("/proyectofinal.html")
def proyectofinal():
    lista_productos = Producto.query.order_by(Producto.nombre.asc()).all()
    return render_template("proyectofinal.html", productos=lista_productos)

@app.route("/proyectoelixirurbano.html")
def proyectoelixirurbano():
    lista_productos = Producto.query.order_by(Producto.nombre.asc()).all()
    return render_template("proyectoelixirurbano.html", productos=lista_productos)

@app.route("/productos/crear", methods=["POST"])
def crear_producto():
    if not usuario_actual():
        flash("Debes iniciar sesión para crear productos.", "error")
        return redirect(url_for("login"))

    nombre = request.form.get("nombre", "").strip()
    precio = request.form.get("precio", "").strip()
    imagen = request.form.get("imagen", "").strip()
    descripcion = request.form.get("descripcion", "").strip()

    if not nombre or not precio:
        flash("Nombre y precio son obligatorios.", "error")
        return redirect(url_for("productos"))

    try:
        precio = float(precio)
    except ValueError:
        flash("El precio debe ser numérico.", "error")
        return redirect(url_for("productos"))

    producto = Producto(nombre=nombre, precio=precio, imagen=imagen or None, descripcion=descripcion or None)
    db.session.add(producto)
    db.session.commit()
    flash("Producto creado correctamente.", "success")
    return redirect(url_for("productos"))

@app.route("/productos/editar/<int:producto_id>", methods=["GET", "POST"])
def editar_producto(producto_id):
    if not usuario_actual():
        flash("Debes iniciar sesión para editar productos.", "error")
        return redirect(url_for("login"))

    producto = Producto.query.get_or_404(producto_id)

    if request.method == "POST":
        nombre = request.form.get("nombre", "").strip()
        precio = request.form.get("precio", "").strip()
        imagen = request.form.get("imagen", "").strip()
        descripcion = request.form.get("descripcion", "").strip()

        if not nombre or not precio:
            flash("Nombre y precio son obligatorios.", "error")
            return redirect(url_for("editar_producto", producto_id=producto_id))

        try:
            precio = float(precio)
        except ValueError:
            flash("El precio debe ser numérico.", "error")
            return redirect(url_for("editar_producto", producto_id=producto_id))

        producto.nombre = nombre
        producto.precio = precio
        producto.imagen = imagen or None
        producto.descripcion = descripcion or None
        db.session.commit()
        flash("Producto actualizado correctamente.", "success")
        return redirect(url_for("productos"))

    return render_template("editar_producto.html", producto=producto)

@app.route("/productos/eliminar/<int:producto_id>", methods=["POST"])
def eliminar_producto(producto_id):
    if not usuario_actual():
        flash("Debes iniciar sesión para eliminar productos.", "error")
        return redirect(url_for("login"))

    producto = Producto.query.get_or_404(producto_id)
    db.session.delete(producto)
    db.session.commit()
    flash("Producto eliminado correctamente.", "info")
    return redirect(url_for("productos"))

def sembrar_productos():
    if Producto.query.count() == 0:
        productos_iniciales = [
            {"nombre": "Paracetamol 500mg", "precio": 5000, "imagen": "https://via.placeholder.com/300x180?text=Paracetamol", "descripcion": "Analgésico y antipirético."},
            {"nombre": "Ibuprofeno 400mg", "precio": 7000, "imagen": "https://via.placeholder.com/300x180?text=Ibuprofeno", "descripcion": "Antiinflamatorio."},
            {"nombre": "Alcohol Antiséptico 70%", "precio": 4500, "imagen": "https://via.placeholder.com/300x180?text=Alcohol+70", "descripcion": "Uso externo."},
            {"nombre": "Aspirina 100mg", "precio": 6000, "imagen": "https://via.placeholder.com/300x180?text=Aspirina", "descripcion": "Analgésico."},
            {"nombre": "Acetaminofén", "precio": 2000, "imagen": "https://via.placeholder.com/300x180?text=Acetaminofen", "descripcion": "Medicamento de alta rotación."},
        ]
        for p in productos_iniciales:
            db.session.add(Producto(**p))
        db.session.commit()

with app.app_context():
    db.create_all()
    sembrar_productos()

if __name__ == "__main__":
    app.run(debug=True)
