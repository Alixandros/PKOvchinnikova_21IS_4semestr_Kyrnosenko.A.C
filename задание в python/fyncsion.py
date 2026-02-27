import psycopg2
from psycopg2.extras import DictCursor
from datetime import datetime, date

def connect_db():
    try:
        conn = psycopg2.connect(
            dbname='shelters_db',
            user='postgres',
            password='1111',
            host='localhost',
            port='5432'
        )
        print('База подключена')
        return conn
    except Exception as e:
        print(e)
        return None

def test_connection():
    conn = connect_db()
    if conn:
        print("База питомцев подключена, ok!")
        conn.close()
        return True
    else:
        print("База питомцев не подключена, not ok!")
        return False

def add_animal(name, species, breed, age, weight, status, date):
    conn = connect_db()
    if not conn:
        return None
    cursor = conn.cursor()
    try:
        if date is None or date == '':
            date = date.today()
        query = """
                INSERT INTO shelter_logs (name, species, breed, age, weight, status, date)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id;
                """
        cursor.execute(query, (name, species, breed, age, weight, status, date))
        animal_id = cursor.fetchone()[0]
        conn.commit()
        print(f"Питомец '{name}' успешно добавлен! (ID: {animal_id})")
        return animal_id
    except psycopg2.Error as e:
        print(f"Ошибка при добавлении Питомец: {e}")
        conn.rollback()
        return None
    finally:
        cursor.close()
        conn.close()

def get_all_animals():
    conn = connect_db()
    if not conn:
        return []
    cursor = conn.cursor(cursor_factory=DictCursor)
    b = ['date', 'name', 'breed', 'status']
    if a not in b:
        a = 'date'
    try:
        query = f"""
        SELECT id, name, date, species, status, age, weight, status FROM shelter_logs ORDER BY {a} DESC;
        """
        cursor.execute(query)
        animals = cursor.fetchall()
        return animals
    except psycopg2.Error as e:
        print(f"Ошибка при получении списка фильмов: {e}")
        return []
    finally:
        cursor.close()
        conn.close()

def get_animal_by_id(animal_id):
    conn = connect_db()
    if not conn:
        return []
    cursor = conn.cursor(cursor_factory=DictCursor)
    try:
        query = "SELECT * FROM shelter_logs WHERE id = %s;"
        cursor.execute(query, (animal_id,))
        animal = cursor.fetchone()
        return animal
    except psycopg2.Error as e:
        print(f"Ошибка при поиске: {e}")
        return []
    finally:
        cursor.close()
        conn.close()

def search_by_name(name_part):
    conn = connect_db()
    if not conn:
        return []
    cursor = conn.cursor(cursor_factory=DictCursor)
    try:
        query = "SELECT * FROM shelter_logs WHERE name = %s;"
        cursor.execute(query, (name_part,))
        animal = cursor.fetchone()
        return animal
    except psycopg2.Error as e:
        print(f"Ошибка при поиске: {e}")
        return []
    finally:
        cursor.close()
        conn.close()

def update_status(animal_id, new_status):
    conn = connect_db()
    if not conn:
        return False
    cursor = conn.cursor()
    try:
        query = """
                UPDATE shelter_logs SET status = %s WHERE id = %s;
                """
        cursor.execute(query, (new_status, animal_id))
        if cursor.rowcount == 0:
            print(f"Питомец с ID {animal_id} не найден")
            return False
        conn.commit()
        print(f"Питомец ID {animal_id} обновлен")
        return True
    except (ValueError, psycopg2.Error) as e:
        print(f"Ошибка при редактировании: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()

def update_weight(animal_id, new_weight):
    conn = connect_db()
    if not conn:
        return False
    cursor = conn.cursor()
    try:
        query = """
                    UPDATE shelter_logs SET weight = %s WHERE id = %s;
                    """
        cursor.execute(query, (new_weight, animal_id))
        if cursor.rowcount == 0:
            print(f"Питомец с ID {animal_id} не найден")
            return False
        conn.commit()
        print(f"Питомец ID {animal_id} обновлен")
        return True
    except (ValueError, psycopg2.Error) as e:
        print(f"Ошибка при редактировании: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()

def delete_animal(animal_id):
    conn = connect_db()
    if not conn:
        return False
    cursor = conn.cursor()
    try:
        query = "DELETE FROM shelter_logs WHERE id = %s;"
        cursor.execute(query, (animal_id,))
        if cursor.rowcount == 0:
            print(f"Питомец с ID {animal_id} не найден")
            return False
        conn.commit()
        print(f"Питомец ID {animal_id} удален")
        return True
    except psycopg2.Error as e:
        print(f"Ошибка при удалении: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()

def get_youngest_animal():
    conn = connect_db()
    if not conn:
        return False
    cursor = conn.cursor(cursor_factory=DictCursor)
    try:
        query = "SELECT * FROM shelter_logs ORDER BY age ASC LIMIT 1;"
        cursor.execute(query)
        animal = cursor.fetchone()
        return animal
    except psycopg2.Error as e:
        print(f"Ошибка при поисках самолого молодога: {e}")
        return None
    finally:
        cursor.close()
        conn.close()

def get_heavy_animals(a=10):
    conn = connect_db()
    if not conn:
        return []
    cursor = conn.cursor(cursor_factory=DictCursor)
    try:
        query = "SELECT * FROM shelter_logs WHERE weight > %s ORDER BY weight DESC;"
        cursor.execute(query, (a,))
        animals = cursor.fetchall()
        return animals
    except psycopg2.Error as e:
        print(f"Ошибка при поиске крупного животного: {e}")
        return []
    finally:
        cursor.close()
        conn.close()