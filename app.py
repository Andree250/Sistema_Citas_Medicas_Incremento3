import os
from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3

app = Flask(__name__)
app.secret_key = 'clave_secreta_sistema_tech'

# Configuración de la ruta de la base de datos
DIR_ACTUAL = os.path.dirname(os.path.abspath(__file__))
RUTA_DB = os.path.join(DIR_ACTUAL, "database", "sistema_tech.db")

def obtener_conexion_db():
    return sqlite3.connect(RUTA_DB)

# ==========================================
# RUTAS DE AUTENTICACIÓN Y NAVEGACIÓN
# ==========================================

@app.route('/')
def index():
    """Landing Page / Pantalla de Inicio (index.html)"""
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
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
            return render_template('login.html', error="Credenciales incorrectas. Intente nuevamente.")
            
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    """Panel de Control / Dashboard del Paciente (dashboard.html)"""
    if 'usuario_dni' not in session:
        return redirect(url_for('login'))
        
    conexion = obtener_conexion_db()
    cursor = conexion.cursor()
    # Listar las citas del paciente incluyendo su estado de pago
    cursor.execute("SELECT id, especialidad, doctor, fecha, hora, estado FROM citas WHERE dni_paciente = ?", (session['usuario_dni'],))
    citas_paciente = cursor.fetchall()
    conexion.close()
    
    return render_template('dashboard.html', nombre=session['usuario_nombre'], citas=citas_paciente)

# ==========================================
# FLUJO 2: AGENDAMIENTO DE CITAS
# ==========================================

@app.route('/agendar', methods=['GET', 'POST'])
def agendar_cita():
    """Pantalla de Agendamiento - Filtros y Selección (agendar.html / buscar.html)"""
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
        # Se inserta la cita con el estado por defecto 'PENDIENTE'
        cursor.execute(
            "INSERT INTO citas (dni_paciente, especialidad, doctor, fecha, hora, estado) VALUES (?, ?, ?, ?, ?, 'PENDIENTE')",
            (dni_paciente, especialidad, doctor, fecha, hora)
        )
        id_nueva_cita = cursor.lastrowid
        conexion.commit()
        conexion.close()
        
        # Redirigir directamente al flujo de pago pasando el ID de la cita recién creada
        return redirect(url_for('pantalla_pago', id_cita=id_nueva_cita))
        
    return render_template('agendar.html')

# ==========================================
# FLUJO 3: CONTROLADOR Y PASARELA DE PAGOS
# ==========================================

@app.route('/pago/<int:id_cita>')
def pantalla_pago(id_cita):
    """Muestra la interfaz para que el usuario seleccione el método de pago"""
    if 'usuario_dni' not in session:
        return redirect(url_for('login'))
        
    conexion = obtener_conexion_db()
    cursor = conexion.cursor()
    cursor.execute("SELECT id, especialidad, doctor, fecha, hora, estado FROM citas WHERE id = ?", (id_cita,))
    cita = cursor.fetchone()
    conexion.close()
    
    if not cita:
        return "Error: Cita no encontrada", 404
        
    return render_template('buscar.html', cita=cita, monto=50.0) # Reutiliza o renderiza la vista de pago

@app.route('/procesar_pago', methods=['POST'])
def C_Pago():
    """Controlador C_Pago: Procesa la transacción y actualiza las estructuras lógicas"""
    if 'usuario_dni' not in session:
        return redirect(url_for('login'))
        
    id_cita = request.form.get('id_cita')
    metodo_pago = request.form.get('metodo_pago') # Tarjeta / Yape / Plin
    monto_fijo = 50.0 # Costo base de la consulta médica general
    
    if not id_cita or not metodo_pago:
        return "Error: Parámetros de transacción incompletos.", 400
        
    # Importar funciones de persistencia del módulo de datos
    from database.db_config import registrar_pago_completo
    
    try:
        # Registrar transacción completa y ejecutar SP_M_Cita_Estado interno
        registrar_pago_completo(int(id_cita), monto_fijo, metodo_pago)
        
        # Simulación de generación del comprobante PDF descargable según documentación
        nombre_comprobante = f"COMPROBANTE_ELECTRONICO_CITA_{id_cita}.pdf"
        
        return render_template('exito.html', id_cita=id_cita, pdf=nombre_comprobante, metodo=metodo_pago)
        
    except Exception as e:
        return f"Error crítico en el procesamiento de la transacción: {str(e)}", 500

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    # Inicialización en modo seguro para despliegue local o Render
    app.run(debug=True, port=int(os.environ.get("PORT", 5000)))

    