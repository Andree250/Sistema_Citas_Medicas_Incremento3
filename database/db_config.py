import sqlite3
import os

def inicializar_db():
    dir_actual = os.path.dirname(__file__)
    ruta_db = os.path.join(dir_actual, "sistema_tech.db")
    
    # Nos aseguramos de cerrar cualquier conexión previa
    conexion = sqlite3.connect(ruta_db)
    cursor = conexion.cursor()

    # Limpiamos tablas antiguas para evitar errores de estructura
    cursor.execute('DROP TABLE IF EXISTS transaccion')
    cursor.execute('DROP TABLE IF EXISTS pago')
    cursor.execute('DROP TABLE IF EXISTS citas')
    cursor.execute('DROP TABLE IF EXISTS usuarios')

    # Tabla de Usuarios
    cursor.execute('''
        CREATE TABLE usuarios (
            dni TEXT PRIMARY KEY,
            nombre TEXT NOT NULL,
            correo TEXT NOT NULL,
            password TEXT NOT NULL
        )
    ''')

    # Tabla de Citas (CON COLUMNA ESTADO ADICIONAL PARA PAGOS)
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
    
    # ==========================================
    # FLUJO 3: ESTRUCTURAS DE GESTIÓN DE PAGOS
    # ==========================================
    
    # Tabla PAGO
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pago (
            id_pago INTEGER PRIMARY KEY AUTOINCREMENT,
            id_cita INTEGER NOT NULL,
            monto REAL NOT NULL,
            estado TEXT NOT NULL,
            FOREIGN KEY(id_cita) REFERENCES citas(id)
        )
    ''')
    
    # Tabla TRANSACCION
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transaccion (
            id_transaccion INTEGER PRIMARY KEY AUTOINCREMENT,
            id_pago INTEGER NOT NULL,
            metodo TEXT NOT NULL, -- Tarjeta / Yape / Plin
            fecha_transaccion TEXT NOT NULL,
            FOREIGN KEY(id_pago) REFERENCES pago(id_pago)
        )
    ''')
    
    conexion.commit()
    conexion.close()
    print("Base de datos SQLite reseteada y lista con estructuras de Pago (Flujo 3).")

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
    
    # 1. Insertar en tabla pago
    cursor.execute("INSERT INTO pago (id_cita, monto, estado) VALUES (?, ?, 'PAGADO')", (id_cita, monto))
    id_pago = cursor.lastrowid
    
    # 2. Insertar en tabla transaccion
    import datetime
    fecha_actual = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("INSERT INTO transaccion (id_pago, metodo, fecha_transaccion) VALUES (?, ?, ?)", (id_pago, metodo, fecha_actual))
    
    conexion.commit()
    conexion.close()
    
    # 3. Cambiar estado en tabla citas utilizando el SP correspondiente
    SP_M_Cita_Estado(id_cita, 'PAGADO')

if __name__ == '__main__':
    inicializar_db()

    