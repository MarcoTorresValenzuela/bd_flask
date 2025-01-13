import psycopg2
import os

# Función para conectar a la base de datos
def get_db_connection():
    database_url = os.getenv('SCHEMATOGO_URL')  # URL de la base de datos
    return psycopg2.connect(database_url)

# Función para crear la tabla "personas"
def crear_tabla():
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # Crea la tabla si no existe
        cur.execute('''
            CREATE TABLE IF NOT EXISTS personas (
                id SERIAL PRIMARY KEY,
                nombre VARCHAR(100),
                apellido VARCHAR(100),  -- Nuevo campo
                dia DATE,              -- Nuevo campo
                correo VARCHAR(100) UNIQUE,
                telefono VARCHAR(20)
            )
        ''')
        conn.commit()
    except Exception as e:
        print(f"Error al crear la tabla: {e}")
    finally:
        cur.close()
        conn.close()

# Función para insertar datos
def insertar_persona(nombre, apellido, dia):
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute('''
            INSERT INTO personas (nombre, apellido, dia)
            VALUES (%s, %s, %s)
        ''', (nombre, apellido, dia))
        
        conn.commit()
    except Exception as e:
        print(f"Error al insertar persona: {e}")
    finally:
        cur.close()
        conn.close()

# Ejemplo de uso
if __name__ == '__main__':
    crear_tabla()
    insertar_persona("Marco", "Torres", "2025-01-13")
