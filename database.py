import psycopg2
import os

# Función para conectar a la base de datos
def get_db_connection():
    database_url = os.getenv('SCHEMATOGO_URL')  # URL de la base de datos
    conn = psycopg2.connect(database_url)
    return conn

# Función para crear la tabla "personas"
def crear_tabla():
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Crear tabla "personas"
    cur.execute('''
        CREATE TABLE IF NOT EXISTS personas (
            id SERIAL PRIMARY KEY,
            nombre VARCHAR(100),
            apellido VARCHAR(100),
            dia DATE
        )
    ''')
    
    conn.commit()
    cur.close()
    conn.close()

# Función para insertar datos
def insertar_persona(nombre, apellido, dia):
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute('''
        INSERT INTO personas (nombre, apellido, dia)
        VALUES (%s, %s, %s)
    ''', (nombre, apellido, dia))
    
    conn.commit()
    cur.close()
    conn.close()