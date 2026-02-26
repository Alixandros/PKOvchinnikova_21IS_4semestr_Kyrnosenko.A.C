import psycopg2
from psycopg2 import sql
from psycopg2.extras import DictCursor
from datetime import datetime, date
import json
import os

def connect_db():
    try:
        connection = psycopg2.connect(
            host="localhost",
            database="workout_db",
            user="postgres",
            password="1111",
            port="5432"
        )
        return connection

    except psycopg2.Error as e:
        print(f"Failed to connect to PostgreSQL: {e}")
        return None

def test_connection():
    conn = connect_db()
    if conn:
        print("Connected to PostgreSQL, ok!")
        conn.close()
        return True
    else:
        print("Failed to connect to PostgreSQL, not ok!")
        return False

def add_workout(exercise_name, sets, reps, weight_kg, difficulty, notes=None, traning_data=None):
    conn = connect_db()
    if not conn:
        return None

    cursor = conn.cursor()

    try:
        if traning_data is None:
            traning_data = date.today()

        query = """
        INSERT INTO traning_logs (exercise_name, traning_data, sets, reps, weight_kg, difficulty, notes)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        RETURNING id;
        """

        cursor.execute(query, (exercise_name, traning_data, sets, reps, weight_kg, difficulty, notes))
        workout_id = cursor.fetchone()[0]

        conn.commit()
        print(f"Тренировка '{exercise_name}' успешно добавлена! (ID: {workout_id})")
        return workout_id

    except psycopg2.Error as e:
        print(f"Ошибка при добавлении тренировки(Не возможно): {e}")
        conn.rollback()
        return None
    finally:
        cursor.close()
        conn.close()

def get_all_workouts(sort_by='traning_data'):
    conn = connect_db()
    if not conn:
        return []

    cursor = conn.cursor(cursor_factory=DictCursor)

    valid_sort_fields = ['traning_data', 'exercise_name', 'weight_kg', 'difficulty']

    if sort_by not in valid_sort_fields:
        sort_by = 'traning_data'

    try:
        query = f"""
        SELECT id, exercise_name, traning_data, sets, reps, weight_kg, difficulty, notes
        FROM traning_logs 
        ORDER BY {sort_by} DESC;
        """

        cursor.execute(query)
        workouts = cursor.fetchall()
        return workouts

    except psycopg2.Error as e:
        print(f"Ошибка при получении списка тренировок: {e}")
        return []
    finally:
        cursor.close()
        conn.close()

def search_workouts(search_term, search_field='all'):
    conn = connect_db()
    if not conn:
        return []

    cursor = conn.cursor(cursor_factory=DictCursor)

    search_pattern = f"%{search_term}%"

    try:
        if search_field == 'exercise':
            query = "SELECT * FROM traning_logs WHERE exercise_name ILIKE %s ORDER BY traning_data DESC;"
            cursor.execute(query, (search_pattern,))
        elif search_field == 'difficulty':
            query = "SELECT * FROM traning_logs WHERE difficulty ILIKE %s ORDER BY traning_data DESC;"
            cursor.execute(query, (search_pattern,))
        elif search_field == 'notes':
            query = "SELECT * FROM traning_logs WHERE notes ILIKE %s ORDER BY traning_data DESC;"
            cursor.execute(query, (search_pattern,))
        else:
            query = """
            SELECT * FROM traning_logs 
            WHERE exercise_name ILIKE %s 
               OR difficulty ILIKE %s 
               OR notes ILIKE %s
               OR CAST(weight_kg AS TEXT) ILIKE %s
            ORDER BY traning_data DESC;
            """
            cursor.execute(query, (search_pattern, search_pattern, search_pattern, search_pattern))

        workouts = cursor.fetchall()
        return workouts

    except psycopg2.Error as e:
        print(f"Ошибка при поиске: {e}")
        return []
    finally:
        cursor.close()
        conn.close()

def filter_by_date_range(start_date, end_date):
    conn = connect_db()
    if not conn:
        return []

    cursor = conn.cursor(cursor_factory=DictCursor)

    try:
        query = """
        SELECT * FROM traning_logs 
        WHERE traning_data BETWEEN %s AND %s 
        ORDER BY traning_data DESC;
        """
        cursor.execute(query, (start_date, end_date))
        workouts = cursor.fetchall()
        return workouts

    except psycopg2.Error as e:
        print(f"Ошибка при фильтрации по дате: {e}")
        return []
    finally:
        cursor.close()
        conn.close()

def update_workout(workout_id, field, new_value):
    conn = connect_db()
    if not conn:
        return False

    cursor = conn.cursor()

    valid_fields = ['exercise_name', 'sets', 'reps', 'weight_kg', 'difficulty', 'notes', 'traning_data']
    if field not in valid_fields:
        print(f"Ошибка: поле '{field}' не существует")
        return False

    try:
        if field in ['sets', 'reps']:
            if new_value:
                new_value = int(new_value)
            else:
                new_value = None
        elif field == 'weight_kg':
            if new_value:
                new_value = float(new_value)
            else:
                new_value = None
        elif field == 'traning_data':
            if new_value:
                new_value = datetime.strptime(new_value, '%Y-%m-%d').date()
            else:
                new_value = None

        query = sql.SQL("UPDATE traning_logs SET {} = %s WHERE id = %s;").format(sql.Identifier(field))
        cursor.execute(query, (new_value, workout_id))

        conn.commit()
        print(f"Поле '{field}' тренировки ID {workout_id} обновлено")
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
        query = "DELETE FROM traning_logs WHERE id = %s;"
        cursor.execute(query, (workout_id,))

        if cursor.rowcount == 0:
            print(f"Тренировка с ID {workout_id} не найдена")
            return False

        conn.commit()
        print(f"Тренировка ID {workout_id} удалена")
        return True

    except psycopg2.Error as e:
        print(f"Ошибка при удалении: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()

def get_statistics():
    conn = connect_db()
    if not conn:
        return {}

    cursor = conn.cursor()

    try:
        stats = {}

        cursor.execute("SELECT COUNT(*) FROM traning_logs;")
        stats['total'] = cursor.fetchone()[0]

        if stats['total'] > 0:
            cursor.execute("SELECT MAX(weight_kg) FROM traning_logs;")
            stats['max_weight'] = cursor.fetchone()[0]

            cursor.execute("SELECT AVG(sets) FROM traning_logs;")
            stats['avg_sets'] = round(cursor.fetchone()[0], 1)

            cursor.execute("SELECT AVG(reps) FROM traning_logs;")
            stats['avg_reps'] = round(cursor.fetchone()[0], 1)

            cursor.execute("""
                SELECT exercise_name, COUNT(*) as count 
                FROM traning_logs 
                GROUP BY exercise_name 
                ORDER BY count DESC 
                LIMIT 1;
            """)
            popular = cursor.fetchone()
            stats['popular_exercise'] = popular[0] if popular else 'нет данных'

            cursor.execute("""
                SELECT difficulty, COUNT(*) as count 
                FROM traning_logs 
                GROUP BY difficulty;
            """)
            stats['difficulty_stats'] = {row[0]: row[1] for row in cursor.fetchall()}

            cursor.execute("""
                SELECT EXTRACT(DOW FROM traning_data) as day, COUNT(*) as count
                FROM traning_logs
                GROUP BY day
                ORDER BY day;
            """)
            days = ['Воскресенье', 'Понедельник', 'Вторник', 'Среда',
                    'Четверг', 'Пятница', 'Суббота']
            stats['day_stats'] = {days[int(row[0])]: row[1] for row in cursor.fetchall()}

            cursor.execute("""
                SELECT traning_data, weight_kg, exercise_name
                FROM traning_logs
                ORDER BY traning_data DESC
                LIMIT 5;
            """)
            stats['recent'] = cursor.fetchall()

        return stats

    except psycopg2.Error as e:
        print(f"Ошибка при получении статистики: {e}")
        return {}
    finally:
        cursor.close()
        conn.close()

def get_personal_records():
    conn = connect_db()
    if not conn:
        return []

    cursor = conn.cursor(cursor_factory=DictCursor)

    try:
        query = """
        SELECT DISTINCT ON (exercise_name) 
            exercise_name,
            weight_kg as max_weight,
            sets,
            reps,
            traning_data,
            difficulty
        FROM traning_logs
        WHERE weight_kg > 0
        ORDER BY exercise_name, weight_kg DESC, traning_data DESC;
        """
        cursor.execute(query)
        records = cursor.fetchall()
        return records

    except psycopg2.Error as e:
        print(f"Ошибка при получении рекордов: {e}")
        return []
    finally:
        cursor.close()
        conn.close()

def get_weekly_stats():
    conn = connect_db()
    if not conn:
        return {}

    cursor = conn.cursor(cursor_factory=DictCursor)

    try:
        stats = {}

        query = """
        SELECT 
            COUNT(*) as total_workouts,
            COUNT(DISTINCT exercise_name) as unique_exercises,
            SUM(weight_kg * sets * reps) as total_volume,
            AVG(weight_kg) as avg_weight,
            MAX(weight_kg) as max_weight,
            COUNT(DISTINCT traning_data) as days_trained
        FROM traning_logs
        WHERE traning_data >= CURRENT_DATE - INTERVAL '7 days';
        """
        cursor.execute(query)
        result = cursor.fetchone()

        stats['total_workouts'] = result['total_workouts'] or 0
        stats['unique_exercises'] = result['unique_exercises'] or 0
        stats['total_volume'] = round(result['total_volume'] or 0, 2)
        stats['avg_weight'] = round(result['avg_weight'] or 0, 2)
        stats['max_weight'] = result['max_weight'] or 0
        stats['days_trained'] = result['days_trained'] or 0

        query = """
        SELECT 
            traning_data,
            COUNT(*) as workouts_count,
            SUM(weight_kg * sets * reps) as daily_volume
        FROM traning_logs
        WHERE traning_data >= CURRENT_DATE - INTERVAL '7 days'
        GROUP BY traning_data
        ORDER BY traning_data;
        """
        cursor.execute(query)
        stats['daily'] = cursor.fetchall()

        return stats

    except psycopg2.Error as e:
        print(f"Ошибка при получении недельной статистики: {e}")
        return {}
    finally:
        cursor.close()
        conn.close()

def get_workout_reminder():
    conn = connect_db()
    if not conn:
        return ""

    cursor = conn.cursor()

    try:
        query = """
        SELECT COUNT(*) as count
        FROM traning_logs
        WHERE traning_data >= CURRENT_DATE - INTERVAL '1 day';
        """
        cursor.execute(query)
        recent_workouts = cursor.fetchone()[0]

        if recent_workouts == 0:
            return "Напоминание: Вы не тренировались сегодня и вчера!"
        elif recent_workouts == 1:
            return "Хорошая работа! У вас была тренировка вчера или сегодня."
        else:
            return "Отлично! У вас регулярные тренировки!"

    except psycopg2.Error as e:
        print(f"Ошибка при проверке напоминаний: {e}")
        return ""
    finally:
        cursor.close()
        conn.close()

def get_exercise_history(exercise_name):
    conn = connect_db()
    if not conn:
        return []

    cursor = conn.cursor(cursor_factory=DictCursor)

    try:
        query = """
        SELECT 
            traning_data,
            weight_kg,
            sets,
            reps,
            difficulty,
            notes
        FROM traning_logs
        WHERE exercise_name ILIKE %s
        ORDER BY traning_data;
        """
        cursor.execute(query, (f'%{exercise_name}%',))
        history = cursor.fetchall()
        return history

    except psycopg2.Error as e:
        print(f"Ошибка при получении истории: {e}")
        return []
    finally:
        cursor.close()
        conn.close()

def export_to_json(filename='workouts.json'):
    workouts = get_all_workouts()

    if not workouts:
        print("Нет тренировок для экспорта")
        return False

    try:
        export_data = []
        for w in workouts:
            w_dict = dict(w)
            w_dict['traning_data'] = str(w_dict['traning_data'])
            export_data.append(w_dict)

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)

        print(f"Экспорт завершен! Файл сохранен как(козел) '{filename}'")
        print(f"Экспортировано записей: {len(workouts)}")
        return True

    except Exception as e:
        print(f"Ошибка при экспорте: {e}")
        return False

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def print_header(title):
    print(f" {title:^58}")

def print_workout_info(workout, detailed=False):
    if detailed:
        print(f"\nID: {workout['id']}")
        print(f"Дата: {workout['traning_data']}")
        print(f"Упражнение: {workout['exercise_name']}")
        print(f"Подходы: {workout['sets']} x {workout['reps']} повторений")
        print(f"Вес: {workout['weight_kg']} кг")
        print(f"Сложность: {workout['difficulty']}")
        if workout['notes']:
            print(f"Заметки: {workout['notes']}")
    else:
        print(f"ID: {workout['id']:3} | "
              f"{workout['traning_data']} | "
              f"{workout['exercise_name'][:20]:20} | "
              f"{workout['sets']}x{workout['reps']} | "
              f"{workout['weight_kg']:5.1f} кг | "
              f"{workout['difficulty']}")


def show_menu():
    print_header("ДНЕВНИК ТРЕНИРОВОК")
    print(" 1. Добавить тренировку")
    print(" 2. Показать все тренировки")
    print(" 3. Поиск тренировок")
    print(" 4. Фильтр по дате")
    print(" 5. Редактировать тренировку")
    print(" 6. Удалить тренировку")
    print(" 7. Статистика")
    print(" 8. Личные рекорды")
    print(" 9. Статистика за неделю")
    print("10. Экспорт в JSON")
    print(" 0. Выход")

def add_workout_interactive():
    print_header("ДОБАВЛЕНИЕ НОВОЙ ТРЕНИРОВКИ(я вернулся из небытия)")

    exercise = input("Название упражнения: ").strip()
    if not exercise:
        print("Название упражнения обязательно!")
        return

    try:
        sets = int(input("Количество подходов: "))
        if sets <= 0:
            print("Количество подходов должно быть больше 0!")
            return

        reps = int(input("Количество повторений: "))
        if reps <= 0:
            print("Количество повторений должно быть больше 0!")
            return

        weight = float(input("Вес (кг): "))
        if weight < 0:
            print("Вес не может быть отрицательным!")
            return

        print("Уровень сложности:")
        print("   1 - Легко")
        print("   2 - Нормально")
        print("   3 - Тяжело")
        diff_choice = input("Выберите (1-3): ").strip()

        difficulty_map = {'1': 'легко', '2': 'нормально', '3': 'тяжело'}
        difficulty = difficulty_map.get(diff_choice)
        if not difficulty:
            print("Неверный выбор сложности!")
            return

        notes = input("Заметки (Enter если нет): ").strip()
        if not notes:
            notes = None

        date_input = input("Дата (ГГГГ-ММ-ДД, Enter - сегодня): ").strip()
        if date_input:
            traning_data = datetime.strptime(date_input, '%Y-%m-%d').date()
        else:
            traning_data = date.today()

        add_workout(exercise, sets, reps, weight, difficulty, notes, traning_data)

    except ValueError as e:
        print(f"Ошибка ввода: {e}")

def show_all_workouts_interactive():
    print_header("ВСЕ ТРЕНИРОВКИ")

    print("Сортировать по:")
    print("1 - Дате (новые сначала)")
    print("2 - Названию упражнения")
    print("3 - Весу")
    print("4 - Сложности")
    print("Enter - без сортировки")

    choice = input("Ваш выбор: ").strip()

    sort_map = {
        '1': 'traning_data',
        '2': 'exercise_name',
        '3': 'weight_kg',
        '4': 'difficulty'
    }

    sort_by = sort_map.get(choice, 'traning_data')
    workouts = get_all_workouts(sort_by)

    if not workouts:
        print("\nВ дневнике пока нет тренировок.")
        return

    print(f"\nНайдено тренировок: {len(workouts)}")

    for workout in workouts:
        print_workout_info(workout)

    view_id = input("\nВведите ID для детального просмотра (Enter для продолжения): ").strip()
    if view_id:
        try:
            workout_id = int(view_id)
            for workout in workouts:
                if workout['id'] == workout_id:
                    print_workout_info(workout, detailed=True)
                    break
        except ValueError:
            pass

def search_workouts_interactive():
    print_header("ПОИСК ТРЕНИРОВОК")

    print("Искать по:")
    print("1 - Названию упражнения")
    print("2 - Сложности")
    print("3 - Заметкам")
    print("4 - Всем полям")

    choice = input("Ваш выбор: ").strip()

    field_map = {
        '1': 'exercise',
        '2': 'difficulty',
        '3': 'notes',
        '4': 'all'
    }

    search_field = field_map.get(choice, 'all')
    search_term = input("Введите текст для поиска: ").strip()

    if not search_term:
        print("Введите текст для поиска")
        return

    workouts = search_workouts(search_term, search_field)

    if not workouts:
        print(f"\nТренировки по запросу '{search_term}' не найдены")
        return

    print(f"\nНайдено тренировок: {len(workouts)}")
    print("-" * 80)

    for workout in workouts:
        print_workout_info(workout)

def filter_by_date_interactive():
    print_header("ФИЛЬТР ПО ДАТЕ(какой год)")

    try:
        start_str = input("Начальная дата (ГГГГ-ММ-ДД): ").strip()
        end_str = input("Конечная дата (ГГГГ-ММ-ДД): ").strip()

        start_date = datetime.strptime(start_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_str, '%Y-%m-%d').date()

        workouts = filter_by_date_range(start_date, end_date)

        if not workouts:
            print(f"\nТренировки с {start_date} по {end_date} не найдены")
            return

        print(f"\nНайдено тренировок: {len(workouts)}")
        print("-" * 80)

        for workout in workouts:
            print_workout_info(workout)

    except ValueError:
        print("Неверный формат даты. Используйте ГГГГ-ММ-ДД(ты че в 23344433444 веке после перед нашей эры живешь?")


def edit_workout_interactive():
    print_header("РЕДАКТИРОВАНИЕ ТРЕНИРОВКИ")

    try:
        workout_id = int(input("Введите ID тренировки для редактирования: "))

        workouts = get_all_workouts()
        workout = next((w for w in workouts if w['id'] == workout_id), None)

        if not workout:
            print(f"Тренировка с ID {workout_id} не найдена")
            return

        print("\nТекущая информация:")
        print_workout_info(workout, detailed=True)

        print("\nЧто редактировать?")
        print("1 - Название упражнения")
        print("2 - Количество подходов")
        print("3 - Количество повторений")
        print("4 - Вес")
        print("5 - Сложность")
        print("6 - Заметки")
        print("7 - Дату")

        field_map = {
            '1': 'exercise_name',
            '2': 'sets',
            '3': 'reps',
            '4': 'weight_kg',
            '5': 'difficulty',
            '6': 'notes',
            '7': 'traning_data'
        }

        choice = input("Ваш выбор(Спать): ").strip()

        if choice not in field_map:
            print("Неверный выбор")
            return

        field = field_map[choice]
        current_value = workout[field]

        print(f"Текущее значение: {current_value or 'не указано'}")
        new_value = input("Новое значение (Enter для отмены): ").strip()

        if new_value:
            update_workout(workout_id, field, new_value)

    except ValueError:
        print("Ошибка ввода. Введите число.")


def delete_workout_interactive():
    print_header("УДАЛЕНИЕ ТРЕНИРОВКИ(Что за че..........)")

    try:
        workout_id = int(input("Введите ID тренировки для удаления(Ам вы бек): "))

        workouts = get_all_workouts()
        workout = next((w for w in workouts if w['id'] == workout_id), None)

        if not workout:
            print(f"Тренировка с ID {workout_id} не найдена")
            return

        print("\nТренировка для удаления(Математика):")
        print_workout_info(workout, detailed=True)

        confirm = input("\nВы уверены? (да/нет): ").strip().lower()

        if confirm == "да":
            delete_workout(workout_id)
        else:
            print("Удаление отменено(НЕтт)")

    except ValueError:
        print("Ошибка ввода. Введите число(А букву).")


def show_statistics_interactive():
    print_header("СТАТИСТИКА ТРЕНИРОВОК(27647474 фрагов только за минуту)")

    stats = get_statistics()

    if not stats or stats.get('total', 0) == 0:
        print("Пока нет данных для статистики(Меня нету у статистики(Че сказал сам понял?))")
        return

    print(f"\nОБЩАЯ СТАТИСТИКА:")
    print(f"Всего тренировок: {stats['total']}")
    print(f"Максимальный вес: {stats['max_weight']} кг")
    print(f"Среднее количество подходов: {stats['avg_sets']}")
    print(f"Среднее количество повторений: {stats['avg_reps']}")
    print(f"Самое частое упражнение: {stats['popular_exercise']}")

    print(f"\nРАСПРЕДЕЛЕНИЕ ПО СЛОЖНОСТИ:")
    for diff, count in stats['difficulty_stats'].items():
        percent = (count / stats['total']) * 100
        bar = '#' * int(percent / 5)
        print(f"{diff}: {bar} {count} ({percent:.1f}%)")

    print(f"\nТРЕНИРОВКИ ПО ДНЯМ НЕДЕЛИ:")
    for day, count in stats['day_stats'].items():
        print(f"{day}: {count}")

    print(f"\nПОСЛЕДНИЕ ТРЕНИРОВКИ(Что такое тренировки):")
    for workout in stats['recent'][:5]:
        print(f"{workout[0]}: {workout[2]} - {workout[1]} кг")


def show_personal_records_interactive():
    print_header("ЛИЧНЫЕ РЕКОРДЫ")

    records = get_personal_records()

    if not records:
        print("Пока нет личных рекордов")
        return

    print(f"\nМАКСИМАЛЬНЫЙ ВЕС ПО УПРАЖНЕНИЯМ:")

    for record in records:
        print(f"\n{record['exercise_name']}")
        print(f"Максимальный вес: {record['max_weight']} кг")
        print(f"Достижение: {record['sets']} x {record['reps']} повторений")
        print(f"Дата: {record['traning_data']}")
        print(f"Сложность: {record['difficulty']}")


def show_weekly_stats_interactive():
    print_header("СТАТИСТИКА ЗА НЕДЕЛЮ")

    stats = get_weekly_stats()

    if stats['total_workouts'] == 0:
        print("Нет тренировок за последнюю неделю(а за день?)")
        return

    print(f"\nВсего тренировок: {stats['total_workouts']}")
    print(f"Разных упражнений: {stats['unique_exercises']}")
    print(f"Общий объем: {stats['total_volume']} кг")
    print(f"Средний вес: {stats['avg_weight']} кг")
    print(f"Максимальный вес: {stats['max_weight']} кг")
    print(f"Дней с тренировками: {stats['days_trained']} из 7")

    progress = (stats['days_trained'] / 7) * 100
    bar_length = 20
    filled = int(bar_length * progress / 100)
    bar = '#' * filled + '-' * (bar_length - filled)
    print(f"\nПрогресс недели: [{bar}] {progress:.1f}%")

    if stats['daily']:
        print(f"\nТРЕНИРОВКИ ПО ДНЯМ(Их вроде 3):")
        for day in stats['daily']:
            print(f"{day['traning_data']}: {day['workouts_count']} тренировок, объем {day['daily_volume']} кг")

def export_json_interactive():
    print_header("ЭКСПОРТ В JSON")

    filename = input("Имя файла (Enter - workouts.json)(Не матересь): ").strip()
    if not filename:
        filename = "workouts.json"
    if not filename.endswith('.json'):
        filename += '.json'

    export_to_json(filename)

def main():
    if not test_connection():
        print("\nНе удалось подключиться к базе данных(Как)!")
        print("Проверьте(Что вы не мужчина):")
        print("1. Запущен ли PostgreSQL(А это что)")
        print("2. Правильный ли пароль в функции connect_db()(Да нет наверное)")
        print("3. Создана ли база данных workout_db(Сомниваетесь?)")
        input("\nНажмите Enter для выхода(Пока)...")
        return

    while True:
        clear_screen()
        show_menu()
        choice = input("\nВаш выбор(Синяя или Красная, ой не то кино): ").strip()

        if choice == "1":
            add_workout_interactive()
        elif choice == "2":
            show_all_workouts_interactive()
        elif choice == "3":
            search_workouts_interactive()
        elif choice == "4":
            filter_by_date_interactive()
        elif choice == "5":
            edit_workout_interactive()
        elif choice == "6":
            delete_workout_interactive()
        elif choice == "7":
            show_statistics_interactive()
        elif choice == "8":
            show_personal_records_interactive()
        elif choice == "9":
            show_weekly_stats_interactive()
        elif choice == "10":
            export_json_interactive()
        elif choice == "0":
            print_header("ДО СВИДАНИЯ(Спасибо, счастливо оставаться и идите в жопу) !")
            print("Хороших тренировок(НЕТТТТТ)!")
            break
        else:
            print("Неверный выбор. Попробуйте снова(ПЛАКИПЛАКИ).")

        input("\nНажмите Enter, чтобы продолжить(Жми)...")


if __name__ == "__main__":
    main()