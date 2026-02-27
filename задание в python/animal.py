import psycopg2
from fyncsion import *

def print_animals(animals):
    if not animals:
        print('Животные не найдены')
        return
    for a in animals:
        print(f"{a[1]} ({a[2]}) | {a[3]} | {a[4]} лет | {a[5]} кг | {a[6]}")

def main():
    while True:
        print('\n1. Добавить животное')
        print('2. Все животные')
        print('3. Найти по ID')
        print('4. Поиск по кличке')
        print('5. Обновить статус')
        print('6. Обновить вес')
        print('7. Удалить животное')
        print('8. Самое молодое')
        print('9. Крупные животные (>10кг)')
        print('10. Выход')
        choice = input('Выберите пункт: ')
        if choice == '1':
            name = input('Кличка: ')
            species = input('Вид (Кошка, Собака, Птица, Грызун, Другое): ')
            breed = input('Порода: ')
            age = int(input('Возраст (лет): '))
            weight = float(input('Вес (кг): '))
            status = input('Статус (Свободен, Усыновлен, На лечении): ')
            date = input('Дата (ГГГГ-ММ-ДД): ')
            add_animal(name, species, breed, age, weight, status, date)
        elif choice == '2':
            print_animals(get_all_animals())
        elif choice == '3':
            aid = int(input('ID: '))
            animal = get_animal_by_id(aid)
            if animal:
                print_animals([animal])
            else:
                print(f"Питомец с ID {aid} не был найден")
        elif choice == '4':
            name = input('Кличка: ')
            animal = search_by_name(name)
            if animal:
                print_animals([animal])
            else:
                print(f"Питомец с этой кличкой {name} не был найден")
        elif choice == '5':
            aid = int(input('ID: '))
            status = input('Новый статус: ')
            update_status(aid, status)
        elif choice == '6':
            aid = int(input('ID: '))
            weight = float(input('Новый вес: '))
            update_weight(aid, weight)
        elif choice == '7':
            aid = int(input('ID: '))
            delete_animal(aid)
        elif choice == '8':
            print_animals([get_youngest_animal()])
        elif choice == '9':
            print_animals(get_heavy_animals())
        elif choice == '10':
            break
        else:
            print('Неверный ввод')

if __name__ == '__main__':
    main()