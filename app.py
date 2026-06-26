import os
from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3

# Configuración dinámica y absoluta de rutas para entorno Linux (Render)
DIR_ACTUAL = os.path.dirname(os.path.abspath(__file__))
RUTA_TEMPLATES = os.path.join(DIR_ACTUAL, "app", "templates")
RUTA_DB = os.path.join(DIR_ACTUAL, "database", "sistema_tech.db")

app = Flask(__name__, template_folder=RUTA_TEMPLATES)
app.secret_key = 'clave_secreta_sistema_tech'

def obtener_conexion_db():
    return sqlite3.connect(RUTA_DB)

# ==========================================
# RUTAS DE AUTENTICACIÓN Y REGISTRO (MÚLTIPLES ALIAS)
# ==========================================

@app.route('/')
def index():
    """Landing Page / Pantalla de Inicio (index.html)"""
    return render_template('index.html')

@app.route('/crear_usuario', methods=['GET', 'POST'])
@app.route('/crear_usuario.html', methods=['GET', 'POST'])
@app.route('/registro', methods=['GET', 'POST'])
def crear_usuario():
    """Controlador para el registro de nuevos pacientes"""
    if request.method == 'POST':
        dni = request.form.get('dni')
        nombre = request.form.get('nombre')
        correo = request.form.get('correo')
        password = request.form.get('password')
        
        try:
            conexion = obtener_conexion_db()
            cursor = conexion.cursor()
            cursor.execute(
                "INSERT INTO usuarios (dni, nombre, correo, password) VALUES (?, ?, ?, ?)",
                (dni, nombre, correo, password)
            )
            conexion.commit()
            conexion.close()
            return redirect(url_for('login'))
        except Exception as e:
            return f"Error en el registro de la cuenta: {str(e)}", 400
            
    return render_template('login.html')

@app.route('/login', methods=['GET', 'POST'])
@app.route('/login.html', methods=['GET', 'POST'])
def login():
    """Pantalla de Inicio de Sesión / Acceso (login.html)"""
    if request.method == 'POST':
        dni = request.form.get('dni')
        password = request.form.get('password')
        
        conexion = obtener_conexion_db()
        cursor = conexion.cursor()
        cursor.execute("SELECT dni, nombre, correo FROM usuarios WHERE dni = ? AND password = ?", (dni, password))
        usuario = cursor.fetchone()
        conexion.close()
        
        if usuario:
            session['usuario_dni'] = usuario[0]
            session['usuario_nombre'] = usuario[1]
            return redirect(url_for('dashboard'))
        else:
            return render_template('login.html', error="Credenciales incorrectas. Intente de nuevo.")
            
    return render_template('login.html')

@app.route('/dashboard')
@app.route('/dashboard.html')
def dashboard():
    """Panel de Control del Paciente Autenticado"""
    if 'usuario_dni' not in session:
        return redirect(url_for('login'))
        
    conexion = obtener_conexion_db()
    cursor = conexion.cursor()
    cursor.execute("SELECT id, especialidad, doctor, fecha, hora, estado FROM citas WHERE dni_paciente = ?", (session['usuario_dni'],))
    citas_paciente = cursor.fetchall()
    conexion.close()
    
    return render_template('dashboard.html', nombre=session['usuario_nombre'], citas=citas_paciente)

# ==========================================
# FLUJO 2: AGENDAMIENTO DE CITAS Médicas
# ==========================================

@app.route('/agendar', methods=['GET', 'POST'])
@app.route('/agendar.html', methods=['GET', 'POST'])
def agendar_cita():
    """Pantalla de Agendamiento - Filtros y Selección (agendar.html)"""
    if 'usuario_dni' not in session:
        return redirect(url_for('login'))
        
    if request.method == 'POST':
        especialidad = request.form.get('especialidad')
        doctor = request.form.get('doctor')
        fecha = request.form.get('fecha')
        hora = request.form.get('hora')
        dni_paciente = session['usuario_dni']
        
        conexion = obtener_conexion_db()
        cursor = conexion.cursor()
        cursor.execute(
            "INSERT INTO citas (dni_paciente, especialidad, doctor, fecha, hora, estado) VALUES (?, ?, ?, ?, ?, 'PENDIENTE')",
            (dni_paciente, especialidad, doctor, fecha, hora)
        )
        id_nueva_cita = cursor.lastrowid
        conexion.commit()
        conexion.close()
        
        return redirect(url_for('pantalla_pago', id_cita=id_nueva_cita))
        
    return render_template('agendar.html')

# ==========================================
# FLUJO 3: PASARELA Y PROCESAMIENTO DE PAGOS
# ==========================================

@app.route('/pago/<int:id_cita>')
def pantalla_pago(id_cita):
    """Muestra la interfaz para seleccionar el método de pago"""
    if 'usuario_dni' not in session:
        return redirect(url_for('login'))
        
    conexion = obtener_conexion_db()
    cursor = conexion.cursor()
    cursor.execute("SELECT id, especialidad, doctor, fecha, hora, estado FROM citas WHERE id = ?", (id_cita,))
    cita = cursor.fetchone()
    conexion.close()
    
    if not cita:
        return "Error: Cita no encontrada.", 404
        
    return render_template('buscar.html', cita=cita, monto=50.0)

@app.route('/procesar_pago', methods=['POST'])
def C_Pago():
    """Controlador central C_Pago: Registra la transacción física y lógica"""
    if 'usuario_dni' not in session:
        return redirect(url_for('login'))
        
    id_cita = request.form.get('id_cita')
    metodo_pago = request.form.get('metodo_pago') # Tarjeta / Yape / Plin
    monto_fijo = 50.0
    
    if not id_cita or not metodo_pago:
        return "Error: Datos de transacción incompletos.", 400
        
    from database.db_config import registrar_pago_completo
    
    try:
        registrar_pago_completo(int(id_cita), monto_fijo, metodo_pago)
        nombre_comprobante = f"COMPROBANTE_ELECTRONICO_CITA_{id_cita}.pdf"
        return render_template('exito.html', id_cita=id_cita, pdf=nombre_comprobante, metodo=metodo_pago)
        
    except Exception as e:
        return f"Error interno en la pasarela de pagos: {str(e)}", 500

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True, port=int(os.environ.get("PORT", 5000)))
    