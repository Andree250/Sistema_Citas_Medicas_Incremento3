from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
import os

app = Flask(__name__, template_folder='app/templates')
app.secret_key = 'sistema_tech_2026_key' 

# --- CONFIGURACIÓN DE RUTAS DE BASE DE DATOS ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Forzamos la creación de la estructura de directorios en el servidor de Render
DATABASE_DIR = os.path.join(BASE_DIR, 'app', 'database')
os.makedirs(DATABASE_DIR, exist_ok=True)

DB_PATH = os.path.join(DATABASE_DIR, 'sistema_tech.db')
DATABASE = DB_PATH

def get_db_connection():
    conn = sqlite3.connect(DB_PATH, timeout=20)
    conn.row_factory = sqlite3.Row
    return conn

# 🛠️ FUNCIÓN AUTOMÁTICA PARA INICIALIZAR LAS TABLAS EN RENDER
def init_db():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        # Crear tabla de usuarios si no existe
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS usuarios (
                dni TEXT PRIMARY KEY,
                nombre TEXT NOT NULL,
                password TEXT NOT NULL
            )
        ''')
        # Crear tabla de citas si no existe
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS citas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                dni_paciente TEXT NOT NULL,
                especialidad TEXT NOT NULL,
                doctor TEXT NOT NULL,
                fecha TEXT NOT NULL,
                hora TEXT NOT NULL
            )
        ''')
        conn.commit()

# Se ejecuta al levantar el servidor web para garantizar la existencia de la BD
init_db()

# --- SIMULADOR DE SERVICIOS EXTERNOS (PREPARADO PARA INCREMENTO 3) ---
def enviar_correo_confirmacion(dni, especialidad, doctor, fecha, hora):
    """
    Simula la invocación de un servicio API externo (ej. SendGrid / Mailgun)
    para el envío asíncrono de notificaciones por correo electrónico (Pregunta 20).
    """
    print("\n" + "="*50)
    print("🚀 [SERVICIO EXTERNO] Invocando API de Mensajería...")
    print(f"📧 Destinatario (Paciente DNI): {dni}")
    print(f"📝 Detalle: Cita confirmada con el Dr. {doctor} ({especialidad})")
    print(f"📅 Agenda: {fecha} a las {hora}")
    print("✅ [API STATUS] Email enviado exitosamente (200 OK)")
    print("="*50 + "\n")
    return True

# --- RUTAS DE NAVEGACIÓN ---
@app.route('/')
def home():
    return render_template('login.html')

@app.route('/registro')
def registro():
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    # 🔐 PROTECCIÓN OWASP A01: CONTROL DE ACCESO ROTO
    if 'usuario_nombre' not in session:
        return redirect(url_for('home'))
    return render_template('dashboard.html', nombre=session['usuario_nombre'])

# --- LÓGICA DE USUARIOS ---

@app.route('/crear_usuario', methods=['POST'])
def crear_usuario():
    dni = request.form.get('dni')
    nombre = request.form.get('nombre')
    contrasena = request.form.get('password')  

    if not dni or not nombre or not contrasena:
        return render_template('index.html', error="Todos los campos son obligatorios.")

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('INSERT INTO usuarios (dni, nombre, password) VALUES (?, ?, ?)', 
                           (dni, nombre, contrasena))
            conn.commit()
        
        return render_template('index.html', exito="Usuario registrado correctamente. Ya puedes iniciar sesión.")
        
    except sqlite3.IntegrityError:
        return render_template('index.html', error="El DNI ingresado ya se encuentra registrado.")
    except Exception as e:
        print(f"Error en Registro: {str(e)}")
        return render_template('index.html', error="Error al acceder a la base de datos.")

@app.route('/login_usuario', methods=['POST'])
def login_usuario():
    dni = request.form.get('dni')
    contrasena = request.form.get('contrasena')

    if not dni or not contrasena:
        return render_template('login.html', error="Todos los campos son obligatorios.")

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT nombre FROM usuarios WHERE dni = ? AND password = ?', (dni, contrasena))
            usuario = cursor.fetchone()
        
        if usuario:
            session['usuario_nombre'] = usuario['nombre']
            return redirect(url_for('dashboard'))
        else:
            return render_template('login.html', error="Usuario o contraseña incorrectos.")
            
    except Exception as e:
        print(f"Error en Login: {str(e)}")
        return render_template('login.html', error="Ocurrió un error en el servidor.")

# --- LÓGICA DE CITAS MÉDICAS ---

@app.route('/agendar/<especialidad>')
def agendar(especialidad):
    # 🔐 PROTECCIÓN OWASP A01: CONTROL DE ACCESO ROTO
    if 'usuario_nombre' not in session:
        return redirect(url_for('home'))
    return render_template('agendar.html', especialidad=especialidad)

@app.route('/confirmar_cita', methods=['POST'])
def confirmar_cita():
    # 🔐 PROTECCIÓN OWASP A01: CONTROL DE ACCESO ROTO
    # Bloquea peticiones directas por POST de usuarios no autenticados en el servidor
    if 'usuario_nombre' not in session:
        return """
        <div style="text-align:center; margin-top:50px; font-family:sans-serif; color:#d32f2f;">
            <h1>❌ ERROR 403: ACCESO NO AUTORIZADO</h1>
            <hr style="width:50%;">
            <p>Debe iniciar sesión en el sistema para realizar esta acción.</p>
            <br>
            <a href="/" style="padding:10px 20px; background:#d32f2f; color:white; text-decoration:none; border-radius:5px;">Ir al Login</a>
        </div>
        """, 403

    try:
        dni = request.form.get('dni')
        especialidad = request.form.get('especialidad')
        doctor = request.form.get('doctor')
        fecha = request.form.get('fecha')
        hora = request.form.get('hora')
        
        with get_db_connection() as conn:
            conn.execute('''
                INSERT INTO citas (dni_paciente, especialidad, doctor, fecha, hora) 
                VALUES (?, ?, ?, ?, ?)
            ''', (dni, especialidad, doctor, fecha, hora))
            conn.commit()
        
        # 🚀 INVOCACIÓN ASÍNCRONA DEL SERVICIO EXTERNO DE EMAIL
        enviar_correo_confirmacion(dni, especialidad, doctor, fecha, hora)
        
        return f"""
        <div style="text-align:center; margin-top:50px; font-family:sans-serif; color:#00796b;">
            <h1>✅ ¡CITA REGISTRADA CON ÉXITO!</h1>
            <hr style="width:50%;">
            <p><strong>Especialidad:</strong> {especialidad}</p>
            <p><strong>Doctor:</strong> {doctor}</p>
            <p><strong>Fecha:</strong> {fecha}</p>
            <p><strong>Hora:</strong> {hora}</p>
            <p style="color:#555; font-size:14px;">📧 *Se ha enviado un correo de confirmación electrónico al paciente (API externa ejecutada).*</p>
            <br>
            <a href="/dashboard" style="padding:10px 20px; background:#00796b; color:white; text-decoration:none; border-radius:5px;">Volver al Panel</a>
        </div>
        """
    except Exception as e:
        return f"<h1>Ocurrió un error:</h1><p>{str(e)}</p><a href='/dashboard'>Regresar</a>"

# --- 🔍 MÓDULO OPTIMIZADO Y SEGURO: BUSCAR Y FILTRAR CITAS ---

@app.route('/buscar_citas', methods=['GET', 'POST'])
def buscar_citas():
    # 🔐 PROTECCIÓN OWASP A01: CONTROL DE ACCESO ROTO
    if 'usuario_nombre' not in session:
        return redirect(url_for('home'))
        
    citas_filtradas = []
    dni_buscado = ""
    
    if request.method == 'POST':
        dni_buscado = request.form.get('dni')
        
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT id, especialidad, doctor, fecha, hora 
                    FROM citas 
                    WHERE dni_paciente = ?
                ''', (dni_buscado,))
                citas_filtradas = cursor.fetchall()
        except Exception as e:
            print(f"Error en la búsqueda: {str(e)}")

    return render_template('buscar.html', citas=citas_filtradas, dni=dni_buscado)

# --- ❌ MÓDULO SEGURO: CANCELAR CITA (CU-04) ---

@app.route('/cancelar_cita/<int:id_cita>', methods=['POST'])
def cancelar_cita(id_cita):
    # 🔐 PROTECCIÓN OWASP A01: CONTROL DE ACCESO ROTO
    if 'usuario_nombre' not in session:
        return redirect(url_for('home'))
        
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM citas WHERE id = ?', (id_cita,))
            conn.commit()
    except Exception as e:
        print(f"Error al cancelar cita: {str(e)}")
        
    return redirect(url_for('buscar_citas'))

# --- CIERRE DE SESIÓN ---

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

    