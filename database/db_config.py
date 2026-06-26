import sqlite3
import os

def inicializar_db():
    dir_actual = os.path.dirname(__file__)
    ruta_db = os.path.join(dir_actual, "sistema_tech.db")
    
    conexion = sqlite3.connect(ruta_db)
    cursor = conexion.cursor()

    # Limpiamos tablas para reestructurar correctamente sin conflictos de columnas
    cursor.execute('DROP TABLE IF EXISTS transaccion')
    cursor.execute('DROP TABLE IF EXISTS pago')
    cursor.execute('DROP TABLE IF EXISTS citas')
    cursor.execute('DROP TABLE IF EXISTS usuarios')

    # 1. Tabla de Usuarios (Capa de autenticación)
    cursor.execute('''
        CREATE TABLE usuarios (
            dni TEXT PRIMARY KEY,
            nombre TEXT NOT NULL,
            correo TEXT NOT NULL,
            password TEXT NOT NULL
        )
    ''')

    # 2. Tabla de Citas (Incluye columna de estado para el control de pagos)
    cursor.execute('''
        CREATE TABLE citas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            dni_paciente TEXT NOT NULL,
            especialidad TEXT NOT NULL,
            doctor TEXT NOT NULL,
            fecha TEXT NOT NULL,
            hora TEXT NOT NULL,
            estado TEXT DEFAULT 'PENDIENTE',
            FOREIGN KEY (dni_paciente) REFERENCES usuarios (dni)
        )
    ''')
    
    # 3. Tabla de Pagos (Estructura requerida Flujo 3)
    cursor.execute('''
        CREATE TABLE pago (
            id_pago INTEGER PRIMARY KEY AUTOINCREMENT,
            id_cita INTEGER NOT NULL,
            monto REAL NOT NULL,
            estado TEXT NOT NULL,
            FOREIGN KEY(id_cita) REFERENCES citas(id)
        )
    ''')
    
    # 4. Tabla de Transacciones (Estructura requerida Flujo 3)
    cursor.execute('''
        CREATE TABLE transaccion (
            id_transaccion INTEGER PRIMARY KEY AUTOINCREMENT,
            id_pago INTEGER NOT NULL,
            metodo TEXT NOT NULL, -- Tarjeta / Yape / Plin
            fecha_transaccion TEXT NOT NULL,
            FOREIGN KEY(id_pago) REFERENCES pago(id_pago)
        )
    ''')
    
    # INSERTAR PACIENTE DE PRUEBA POR DEFECTO PARA LOGUEARSE DE INMEDIATO
    try:
        cursor.execute("""
            INSERT INTO usuarios (dni, nombre, correo, password) 
            VALUES ('12345678', 'César César', 'cesar@mail.com', '123456')
        """)
    except sqlite3.IntegrityError:
        pass
    
    conexion.commit()
    conexion.close()
    print("Base de datos reseteada e inicializada correctamente con usuario de prueba.")

# ==========================================
# FUNCIONES LÓGICAS DEL FLUJO 3 (BACKEND)
# ==========================================

def SP_M_Cita_Estado(id_cita, nuevo_estado):
    """Procedimiento simulado para modificar el estado de la cita"""
    dir_actual = os.path.dirname(__file__)
    ruta_db = os.path.join(dir_actual, "sistema_tech.db")
    
    conexion = sqlite3.connect(ruta_db)
    cursor = conexion.cursor()
    cursor.execute("UPDATE citas SET estado = ? WHERE id = ?", (nuevo_estado, id_cita))
    conexion.commit()
    conexion.close()

def registrar_pago_completo(id_cita, monto, metodo):
    """Inserta registros en PAGO y TRANSACCION, y actualiza la Cita"""
    dir_actual = os.path.dirname(__file__)
    ruta_db = os.path.join(dir_actual, "sistema_tech.db")
    
    conexion = sqlite3.connect(ruta_db)
    cursor = conexion.cursor()
    
    # Insertar en tabla pago
    cursor.execute("INSERT INTO pago (id_cita, monto, estado) VALUES (?, ?, 'PAGADO')", (id_cita, monto))
    id_pago = cursor.lastrowid
    
    # Insertar en tabla transaccion
    import datetime
    fecha_actual = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("INSERT INTO transaccion (id_pago, metodo, fecha_transaccion) VALUES (?, ?, ?)", (id_pago, metodo, fecha_actual))
    
    conexion.commit()
    conexion.close()
    
    # Actualizar estado de la cita
    SP_M_Cita_Estado(id_cita, 'PAGADO')

if __name__ == '__main__':
    inicializar_db()
    