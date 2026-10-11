import random
import json
import os

SAVE_FILE = "save.json"

def load_save():
    if os.path.exists(SAVE_FILE):
        with open(SAVE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if "peak" not in data:
                data["peak"] = data["elo"]
            return data

    return {"elo": 1300, "win": 0, "lose": 0, "peak": 1300 }

def save_game(elo, win, lose, peak):
    with open(SAVE_FILE, "w", encoding="utf-8") as f:
        json.dump({"elo": elo, "win": win, "lose": lose, "peak": peak}, f)

numbers = [1, 2, 3]
game_2 = [1, 2] # легкий
game_3 = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10] # сложный

ranks = [
    (0, "Бронза"),
    (700, "Железо"),
    (1300, "Серебро"),
    (1500, "Золото"),
    (1800, "Платина"),
    (2000, "Алмаз"),
    (2500, "Бриллиант"),
    (3000, "Легенда"),
    
]
def get_rank(elo):
    rank = "Бронза"
    for update, name in ranks:
        if elo >= update:
            rank = name 
            
    return rank 
def progress(elo):
    current_update = 0
    next_update = None

    for update, name in ranks:
        if elo >= update:
            current_update = update
        elif next_update is None:
            next_update = update
            break

    if next_update is None:
        return "Максимальный ранг! "

    percent = (elo - current_update) / (next_update - current_update) * 100
    return f"{percent:.1f}%"
def win_rate(win, lose):
    total = win + lose
    if total == 0:
        return 0.0
    return win / total * 100

def profile(elo, win, lose, peak):
    print("=" * 50, "ВАШ ПРОФИЛЬ", "=" * 50)
    print(f"Ваше количество эло = {elo} ПТС")
    print(f"Ваше количество поражений = {lose} Поражений")
    print(f"Ваше количество побед = {win} Побед")
    print(f"Ваш ранг = {get_rank(elo)}")
    print(f"Ваш средний показатель побед = {win_rate(win, lose)} % ")
    print(f"Следующий ранг будет через {progress(elo)} %")
    print(f"Ваше пиковое ЭЛО: {peak} ЭЛО")
    print("=" * 100)
def mode():
    while True:
        print("Легкий(e)")
        print("Нормальный(Стандартный)(n)")
        print("Сложный(h)")
        mod = input(">")
        if mod.lower() == "e":
            easy()
            return
        elif mod.lower() == "n":
            play()
            return
        elif mod.lower() == "h":
            hard()
            return
def main():
    while True:
        data = load_save()
        elo, win, lose = data["elo"], data["win"], data["lose"]
        peak = data["peak"]

        print("=" * 50, "NUMBER---ELO", 50 * "=")
        print("Добро пожаловать")
        print("Играть(G)")
        print("Полка(S)")
        print("Выход(Q)")
        print("Профиль(P)")
        print("=" * 100)
        cho = input("|>")
        if cho.lower() == "g":
            mode()
        elif cho.lower() == "s":
            print("=" * 50, "Полка", 50 * "=")
            for update, name in ranks: # ранг высвечивает
                print(f"{name} — от {update} elo")      
                print("|", "Система Рангов")
            print("-" * 25, "Недавние обновления", 50 * "-")
            print("+Добавлены новые ранги")
            print("+Добавлены новые режимы")
            print("+Добавлен винрейт, главное меню ")
            print("+Добавлен штраф за выход из игры")
            continue
        elif cho.lower() == "q":
            print("Выходим...")
            quit()
        elif cho.lower() == "p":
            profile(elo, win, lose, peak)
        else:
            print("Неправильный ввод")
            

def hard():
    data = load_save()
    elo, win, lose = data["elo"], data["win"], data["lose"]
    peak = data["peak"]
    while True:
        g_2 = random.choice(game_3)
        print(f"Угадай мое число! От 0 до 10! (твой рейтинг: {elo})")
        raw = input(" выйти из игры - Q:")
        
       
        if raw.lower() == "q":
            ser = input("Ты уверен? незавершенная игра - минус рейтинг(y/n)")
            if ser.lower() == "y":
                elo -= random.randint(45, 50)
                print(f"Выходим. Штраф за незавершенный выход. Итоговый рейтинг: {elo}")
                save_game(elo, win, lose, peak)
                return
            elif ser.lower() == "n":
                continue
            else: 
                print("Неправильный ввод")
        try:
            choice = int(raw)
        except ValueError:
            print("Это не число. Введи 1, 2, 3, P или Q.")
            continue

        if choice == g_2:
            print("Победа!")
            elo += random.randint(75, 100)
            win += 1
            if elo > peak:
                print(f"У тебя новое пиковое ЭЛО: {peak}!")
        else:
            print(f"Поражение! Было число {g_2}")
            elo -= random.randint(10, 35)
            lose += 1


        ch = input("Играть еще раз? (y/n): ")
        if ch.lower() == "y":
            print("Возвращаем..")
            continue

        else:
            save_game(elo, win, lose, peak)
            print(f"Выходим. Итоговый рейтинг: {elo}")
            return



def easy():
    data = load_save()
    elo, win, lose = data["elo"], data["win"], data["lose"]
    peak = data["peak"]
    while True:
        g_1 = random.choice(game_2)
        print(f"Угадай мое число! От 1 до 2! (твой рейтинг: {elo})")
        raw = input(" выйти из игры - Q:")
        
       
        if raw.lower() == "q":
            ser = input("Ты уверен? незавершенная игра - минус рейтинг(y/n)")
            if ser.lower() == "y":
                elo -= random.randint(45, 50)
                print(f"Выходим. Штраф за незавершенный выход. Итоговый рейтинг: {elo}")
                save_game(elo, win, lose, peak)
                return
            elif ser.lower() == "n":
                continue
            else: 
                print("Неправильный ввод")
        try:
            choice = int(raw)
        except ValueError:
            print("Это не число. Введи 1, 2, 3, P или Q.")
            continue

        if choice == g_1:
            print("Победа!")
            elo += random.randint(5, 15)
            win += 1
        else:
            print(f"Поражение! Было число {g_1}")
            elo -= random.randint(5, 15)
            lose += 1


        ch = input("Играть еще раз? (y/n): ")
        if ch.lower() == "y":
            print("Возвращаем..")
            continue

        else:
            save_game(elo, win, lose, peak)
            print(f"Выходим. Итоговый рейтинг: {elo}")
            return


def play():
    data = load_save()
    elo, win, lose = data["elo"], data["win"], data["lose"] 
    peak = data["peak"]

    while True:
        num = random.choice(numbers)
        print(f"Угадай мое число! От 1 до 3! (твой рейтинг: {elo})")
        raw = input("  выйти из игры - Q: ")


        if raw.lower() == "q":
            ser = input("Ты уверен? незавершенная игра - минус рейтинг(y/n)")
            if ser.lower() == "y":
                elo -= random.randint(45, 50)
                print(f"Выходим. Штраф за незавершенный выход. Итоговый рейтинг: {elo}")
                save_game(elo, win, lose, peak)
                return
            elif ser.lower() == "n":
                continue
            else: 
                print("Неправильный ввод")
  
        try:
            choice = int(raw)
        except ValueError:
            print("Это не число. Введи 1, 2, 3, P или Q.")
            continue

        if choice == num:
            print("Победа!")
            elo += random.randint(20, 30)
            win += 1
        else:
            print(f"Поражение! Было число {num}")
            elo -= random.randint(20, 30)
            lose += 1


        ch = input("Играть еще раз? (y/n): ")
        if ch.lower() == "y":
            print("Возвращаем..")
            continue

        else:
            save_game(elo, win, lose, peak)
            print(f"Выходим. Итоговый рейтинг: {elo}")
            return

main()
