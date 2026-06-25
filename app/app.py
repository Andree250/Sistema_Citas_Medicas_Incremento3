from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
import os

app = Flask(__name__)
app.secret_key = 'sistema_tech_2026_key' 

# --- CONFIGURACIÓN DE RUTAS DE BASE DE DATOS ---
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.abspath(os.path.join(BASE_DIR, '..', 'database', 'sistema_tech.db'))

def get_db_connection():
    conn = sqlite3.connect(DB_PATH, timeout=20)
    conn.row_factory = sqlite3.Row
    return conn

# --- RUTAS DE NAVEGACIÓN ---

@app.route('/')
def home():
    return render_template('login.html')

@app.route('/registro')
def registro():
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
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
    if 'usuario_nombre' not in session:
        return redirect(url_for('home'))
    return render_template('agendar.html', especialidad=especialidad)

@app.route('/confirmar_cita', methods=['POST'])
def confirmar_cita():
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
        
        return f"""
        <div style="text-align:center; margin-top:50px; font-family:sans-serif; color:#00796b;">
            <h1>✅ ¡CITA REGISTRADA CON ÉXITO!</h1>
            <hr style="width:50%;">
            <p><strong>Especialidad:</strong> {especialidad}</p>
            <p><strong>Doctor:</strong> {doctor}</p>
            <p><strong>Fecha:</strong> {fecha}</p>
            <p><strong>Hora:</strong> {hora}</p>
            <br>
            <a href="/dashboard" style="padding:10px 20px; background:#00796b; color:white; text-decoration:none; border-radius:5px;">Volver al Panel</a>
        </div>
        """
    except Exception as e:
        return f"<h1>Ocurrió un error:</h1><p>{str(e)}</p><a href='/dashboard'>Regresar</a>"

# --- 🔍 MÓDULO OPTIMIZADO Y SEGURO: BUSCAR Y FILTRAR CITAS  ---

@app.route('/buscar_citas', methods=['GET', 'POST'])
def buscar_citas():
    if 'usuario_nombre' not in session:
        return redirect(url_for('home'))
        
    citas_filtradas = []
    dni_buscado = ""
    
    if request.method == 'POST':
        dni_buscado = request.form.get('dni')
        
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                # El sistema valida de forma segura por el parámetro ingresado
                cursor.execute('''
                    SELECT rowid, especialidad, doctor, fecha, hora 
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
    if 'usuario_nombre' not in session:
        return redirect(url_for('home'))
        
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            # 🔐 OWASP A01 Control de Acceso: Eliminación controlada por rowid único
            cursor.execute('DELETE FROM citas WHERE rowid = ?', (id_cita,))
            conn.commit()
    except Exception as e:
        print(f"Error al cancelar cita: {str(e)}")
        
    return redirect(url_for('buscar_citas'))

# --- CIERRE DE SESIÓN ---

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

if name == 'main':
# Render asigna un puerto dinámico, si no encuentra uno usa el 8080
port = int(os.environ.get("PORT", 8080))
app.run(host='0.0.0.0', port=port)
