import psycopg2
from psycopg2 import sql
from psycopg2.extras import DictCursor
from datetime import datetime, date
import json
import os

def connect_db():
    try:
        conn = psycopg2.connect(
            dbname='movie_db',
            user='postgres',
            password='1111',
            host='localhost',
            port='5432'
        )
        print('База фильмов подключена')
        return conn
    except Exception as e:
        print(e)
        return None

def test_connection():
    conn = connect_db()
    if conn:
        print("База фильмов подключена, ok!")
        conn.close()
        return True
    else:
        print("База фильмов не подключена, not ok!")
        return False

def add_movie(title, watch_date, duration_min, rating, genre, review):
    conn = connect_db()
    if not conn:
        return None

    cursor = conn.cursor()

    try:
        if watch_date is None or watch_date == '':
            watch_date = date.today()

        query = """
            INSERT INTO movie_logs (title, watch_date, duration_min, rating, genre, review)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id;
            """

        cursor.execute(query, (title, watch_date, duration_min, rating, genre, review))
        movie_id = cursor.fetchone()[0]

        conn.commit()
        print(f"Фильм '{title}' успешно добавлен! (ID: {movie_id})")
        return movie_id

    except psycopg2.Error as e:
        print(f"Ошибка при добавлении фильма: {e}")
        conn.rollback()
        return None
    finally:
        cursor.close()
        conn.close()

def get_all_movies(sort_by='watch_date'):
    conn = connect_db()
    if not conn:
        return []

    cursor = conn.cursor(cursor_factory=DictCursor)

    valid_sort_fields = ['watch_date', 'title', 'duration_min', 'genre']

    if sort_by not in valid_sort_fields:
        sort_by = 'watch_date'

    try:
        query = f"""
        SELECT id, title, watch_date, duration_min, rating, genre, review
        FROM movie_logs 
        ORDER BY {sort_by} DESC;
        """

        cursor.execute(query)
        workouts = cursor.fetchall()
        return workouts

    except psycopg2.Error as e:
        print(f"Ошибка при получении списка фильмов(прости прости): {e}")
        return []
    finally:
        cursor.close()
        conn.close()

def search_by_title(movie_title):
    conn = connect_db()
    if not conn:
        return []

    cursor = conn.cursor(cursor_factory=DictCursor)

    search_pattern = f"%{movie_title}%"

    try:
        query = "SELECT * FROM movie_logs WHERE title ILIKE %s ORDER BY watch_date DESC;"
        cursor.execute(query, (search_pattern,))

        movies = cursor.fetchall()
        return movies

    except psycopg2.Error as e:
        print(f"Ошибка при поиске: {e}")
        return []
    finally:
        cursor.close()
        conn.close()

def filter_by_rating(min_rating):
    conn = connect_db()
    if not conn:
        return []

    cursor = conn.cursor(cursor_factory=DictCursor)

    try:
        query = """
            SELECT * FROM movie_logs 
            WHERE rating >= %s 
            ORDER BY rating DESC;
            """
        cursor.execute(query, (min_rating,))
        movies = cursor.fetchall()
        return movies

    except psycopg2.Error as e:
        print(f"Ошибка при фильтрации по рейтингу: {e}")
        return []
    finally:
        cursor.close()
        conn.close()

def update_movie(log_id, new_rating, new_review):
    conn = connect_db()
    if not conn:
        return False

    cursor = conn.cursor()

    try:
        query = """
            UPDATE movie_logs 
            SET rating = %s, review = %s 
            WHERE id = %s;
            """
        cursor.execute(query, (new_rating, new_review, log_id))

        if cursor.rowcount == 0:
            print(f"Фильм с ID {log_id} не найден")
            return False

        conn.commit()
        print(f"Фильм ID {log_id} обновлен")
        return True

    except (ValueError, psycopg2.Error) as e:
        print(f"Ошибка при редактировании: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()

def delete_workout(workout_id):
    conn = connect_db()
    if not conn:
        return False

    cursor = conn.cursor()

    try:
        query = "DELETE FROM movie_logs WHERE id = %s;"
        cursor.execute(query, (workout_id,))

        if cursor.rowcount == 0:
            print(f"Фильм с ID {workout_id} не найдена")
            return False

        conn.commit()
        print(f"Фильм ID {workout_id} удалена")
        return True

    except psycopg2.Error as e:
        print(f"Ошибка при удалении: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()

def get_cinema_stats():
    conn = connect_db()
    if not conn:
        return {}

    cursor = conn.cursor()

    try:
        stats = {}

        cursor.execute("SELECT COUNT(*) FROM movie_logs;")
        stats['total_movies'] = cursor.fetchone()[0]  # ИСПРАВЛЕНО: total_movies

        if stats['total_movies'] > 0:
            cursor.execute("SELECT AVG(rating) FROM movie_logs;")
            avg = cursor.fetchone()[0]
            stats['average_rating'] = round(avg, 2) if avg else 0  # ИСПРАВЛЕНО: average_rating

            cursor.execute("SELECT SUM(duration_min) FROM movie_logs;")
            total_minutes = cursor.fetchone()[0]
            stats['total_hours'] = round(total_minutes / 60, 2) if total_minutes else 0  # ИСПРАВЛЕНО: total_hours

            cursor.execute("""
                SELECT genre, COUNT(*) FROM movie_logs
                GROUP BY genre ORDER BY COUNT(*) DESC LIMIT 1;
            """)
            popular = cursor.fetchone()
            stats['popular_genre'] = popular[0] if popular else 'Нет данных'  # ИСПРАВЛЕНО: popular_genre
        else:
            stats['average_rating'] = 0
            stats['total_hours'] = 0
            stats['popular_genre'] = 'Нет данных'

        return stats

    except psycopg2.Error as e:
        print(f"Ошибка при получении статистики: {e}")
        return {}
    finally:
        cursor.close()
        conn.close()

def main():
    while True:
        print('\n1. Добавить фильм')
        print('2. Показать все фильмы')
        print('3. Поиск по названию')
        print('4. Фильтр по рейтингу')
        print('5. Обновить фильм')
        print('6. Удалить фильм')
        print('7. Статистика')
        print('8. Выход')
        choice = input('Выберите пункт: ')

        if choice == '1':
            title = input('Название: ')
            watch_date = input('Дата (ГГГГ-ММ-ДД): ')
            duration = int(input('Длительность (мин): '))
            rating = int(input('Оценка (1-10): '))
            genre = input('Жанр (Боевик, Комедия, Драма, Фантастика, Другое): ')
            review = input('Отзыв: ')
            add_movie(title, watch_date, duration, rating, genre, review)
            print('Фильм добавлен')
        elif choice == '2':
            movies = get_all_movies()
            print_movies(movies)
        elif choice == '3':
            title = input('Название для поиска: ')
            movies = search_by_title(title)
            print_movies(movies)
        elif choice == '4':
            min_r = int(input('Минимальный рейтинг: '))
            movies = filter_by_rating(min_r)
            print_movies(movies)
        elif choice == '5':
            log_id = int(input('ID фильма: '))
            new_r = int(input('Новая оценка: '))
            new_rev = input('Новый отзыв: ')
            update_movie(log_id, new_r, new_rev)
            print('Обновлено')
        elif choice == '6':
            log_id = int(input('ID фильма для удаления: '))
            delete_movie(log_id)
            print('Удалено')
        elif choice == '7':
            stats = get_cinema_stats()
            print(f"Всего фильмов: {stats.get('count', 0)}")
            print(f"Средняя оценка: {stats.get('avg_rating', 0)}")
            print(f"Время в часах: {stats.get('total_hours', 0)}")
            print(f"Популярный жанр: {stats.get('popular_genre', 'Нет данных')}")
        elif choice == '8':
            break
        else:
            print('Неверный ввод')

if __name__ == '__main__':
    main()
"C:\Program Files\Python313\python.exe" C:\Users\Student\Desktop\PythonProject32\movie-tracker1.py 

1. Добавить фильм
2. Показать все фильмы
3. Поиск по названию
4. Фильтр по рейтингу
5. Обновить фильм
6. Удалить фильм
7. Статистика
8. Выход
Выберите пункт: 7
База фильмов подключена
Всего фильмов: 0
Средняя оценка: 0
Время в часах: 10.82
Популярный жанр: Другое

1. Добавить фильм
2. Показать все фильмы
3. Поиск по названию
4. Фильтр по рейтингу
5. Обновить фильм
6. Удалить фильм
7. Статистика
8. Выход
Выберите пункт: 2
База фильмов подключена
Traceback (most recent call last):
  File "C:\Users\Student\Desktop\PythonProject32\movie-tracker1.py", line 296, in <module>
    main()
    ~~~~^^
  File "C:\Users\Student\Desktop\PythonProject32\movie-tracker1.py", line 265, in main
    print_movies(movies)
    ^^^^^^^^^^^^
NameError: name 'print_movies' is not defined

Process finished with exit code 1
