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

    return {"elo": 1300, "win": 0, "lose": 0, "peak": 1300, }

def save_game(elo, win, lose, peak):
    with open(SAVE_FILE, "w", encoding="utf-8") as f:
        json.dump({"elo": elo, "win": win, "lose": lose, "peak": peak}, f)

numbers = [1, 2, 3]
game_2 = [1, 2] # легкий
game_3 = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10] # сложный
game_4 = [1, 2, 3]

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
    print("=" * 100)
def mode():
    while True:
        print("Игра против себя(m)")
        print("Игра против ботов(r)")
        mod = input(">")
        if mod.lower() == "m":
            print("Легкий(e)")
            print("Средний(n)")
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
            else:
                print("Неправильный ввод")
        elif mod.lower() == "r":
            print("Робоблиц(b)")
            print("Бот стратег(s)")
            mod = input(">")
            if mod.lower() == "b":
                robot()
                return
            elif mod.lower() == "s":
                smart_robot()
                return
            else:
                print("Неправильный ввод")
        else: 
            print("Неправильный ввод")

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
            print("11.10")
            print("+Добавлены новые ранги")
            print("+Добавлены новые режимы")
            print("+Добавлен винрейт, главное меню ")
            print("+Добавлен штраф за выход из игры")
            print("12.10")
            print("+Добавлен новый режим - Роботблиц и Бот-Стратег!")
            print("-Исправлены баги с вводом")
            
            continue
        elif cho.lower() == "q":
            print("Выходим...")
            quit()
        elif cho.lower() == "p":
            profile(elo, win, lose, peak)
        else:
            print("Неправильный ввод")
            




import random


def smart_robot():
    hint = None
    data = load_save()
    elo, win, lose = data["elo"], data["win"], data["lose"]
    peak = data["peak"]

    while True:
        print(
            f" Загадай число от 1 до 100, а бот попытается его угадать! (Твой рейтинг: {elo})"
        )

        while True:
            try:
                hint = int(input("Загадай число > "))
                if 1 <= hint <= 100:
                    break
                print("ОТ 1 ДО 100")
            except ValueError:
                print("Вводи только цифры!")

        low = 1
        high = 100
        att = 0
        bot = None

        while low <= high:
            att += 1

            
            bot_traits = ["Стандартный", "Агрессивный", "Недоумение"]
            current_trait = random.choice(bot_traits)

            if current_trait == "Стандартный":
                ideal = (low + high) // 2
                if random.random() < 0.4:  # 40% шанс на агрессивное смещение
                    bot = (
                        ideal + random.randint(1, 3)
                        if hint > ideal
                        else ideal - random.randint(1, 3)
                    )
                else:
                    bot = ideal
                bot = max(low, min(high, bot))

            elif current_trait == "Агрессивный":
                ideal = (low + high) // 2
                if hint > ideal:
                    bot = ideal + random.randint(
                        1, max(1, (high - ideal) // 2)
                    )  
                elif hint < ideal:
                    bot = ideal - random.randint(
                        1, max(1, (ideal - low) // 2)
                    ) 
                else:
                    bot = ideal
                bot = max(low, min(high, bot))

            elif current_trait == "Недоумение":
                if high - low > 2:
                        if random.choice([True, False]):
                            bot = random.randint(
                            low + 1, min(high - 1, low + (high - low) // 3)
                            )
                        else:
                                bot = random.randint(
                                max(low + 1, high - (high - low) // 3), high - 1
                                )
                else:
                    bot = (low + high) // 2
            if hint == bot:
                print(
                    f" Робот всё-таки угадал твой номер {hint} за {att} ходов!"
                )

                if att <= 6:
                    penalty = (8 - att) * 15
                    elo -= penalty
                    lose += 1
                    print(
                        f" Бот расколол тебя слишком быстро! Штраф: -{penalty} ЭЛО (Итого: {elo})"
                    )
                else:
                    reward = att * 10
                    elo += reward
                    win += 1
                    print(f" Награда: +{reward} ЭЛО (Итого: {elo})")

                save_game(elo, win, lose, peak)
                break

            elif hint < bot:
                high = bot - 1
            elif hint > bot:
                low = bot + 1

        ch = input("Играть еще раз? (y/n): ")
        if ch.lower() == "y":
            print("Возвращаем...")
            continue
        elif ch.lower() == "n":
            save_game(elo, win, lose, peak)
            print(f"Выходим. Итоговый рейтинг: {elo}")
            return
        else:
            print("Неправильный ввод")





def robot():
    data = load_save()
    elo, win, lose = data["elo"], data["win"], data["lose"]
    peak = data["peak"]
    while True:
        
        print(f"Напиши число от 1 до 3, Робот попытается угадать его (твой рейтинг: {elo})")
            
        raw = input('Выйти из игры - Q >')
        
        
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
                continue 
                
        try:
            choice = int(raw)
        except ValueError:
            print("Это не число.")
            continue
            
        if choice not in game_4:
            print("Это не совпадает..")
            continue
            
        print("Бот подбирает число..")
        robot_choice = random.choice(game_4)
        print("Собираем ответ..")
        
        
        if choice == robot_choice:
            print(f"Робот победил! его число {robot_choice}, Ваше {choice}")
            elo -= random.randint(20, 30)
            lose += 1
        if choice != robot_choice:
            print(f"Поздравляю! Робот промазал, его число {robot_choice}, Ваше {choice}")
            elo += random.randint(20, 30)
            win += 1

        ch = input("Играть еще раз? (y/n): ")
        if ch.lower() == "y":
            print("Возвращаем..")
            continue

        elif ch.lower() == "n":
            save_game(elo, win, lose, peak)
            print(f"Выходим. Итоговый рейтинг: {elo}")
            return
        else:
            print("Неправильный ввод")






        
def hard():
    data = load_save()
    elo, win, lose = data["elo"], data["win"], data["lose"]
    peak = data["peak"]
    while True:
        g_2 = random.choice(game_3)
        print(f"Угадай мое число! От 0 до 10! (твой рейтинг: {elo})")
        raw = input(" Выйти из игры - Q >")
        
       
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
            print(f"Победа! ")
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

        elif ch.lower() == "n":
            save_game(elo, win, lose, peak)
            print(f"Выходим. Итоговый рейтинг: {elo}")
            return
        else:
            print("Неправильный ввод")





def easy():
    data = load_save()
    elo, win, lose = data["elo"], data["win"], data["lose"]
    peak = data["peak"]
    while True:
        g_1 = random.choice(game_2)
        print(f"Угадай мое число! От 1 до 2! (твой рейтинг: {elo})")
        raw = input(" Выйти из игры - Q > ")
        
       
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

        elif ch.lower() == "n":
            save_game(elo, win, lose, peak)
            print(f"Выходим. Итоговый рейтинг: {elo}")
            return
        else:
            print("Неправильный ввод")




def play():
    data = load_save()
    elo, win, lose = data["elo"], data["win"], data["lose"] 
    peak = data["peak"]

    while True:
        num = random.choice(numbers)
        print(f"Угадай мое число! От 1 до 3! (твой рейтинг: {elo})")
        raw = input("  Выйти из игры - Q > ")


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

        elif ch.lower() == "n":
            save_game(elo, win, lose, peak)
            print(f"Выходим. Итоговый рейтинг: {elo}")
            return
        else:
            print("Неправильный ввод")


main()
