import random
import json
import os

SAVE_FILE = "save.json"

def load_save():
    if os.path.exists(SAVE_FILE):
        with open(SAVE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"elo": 1300, "win": 0, "lose": 0}

def save_game(elo, win, lose):
    with open(SAVE_FILE, "w", encoding="utf-8") as f:
        json.dump({"elo": elo, "win": win, "lose": lose}, f)

numbers = [1, 2, 3]


def profile(elo, win, lose):
    print("=" * 50, "ВАШ ПРОФИЛЬ", "=" * 50)
    print(f"Ваше количество эло = {elo}")
    print(f"Ваше количество поражений = {lose}")
    print(f"Ваше количество побед = {win}")


def play():
    data = load_save()
    elo, win, lose = data["elo"], data["win"], data["lose"]    

    while True:
        num = random.choice(numbers)
        print(f"Угадай мое число! От 1 до 3! (твой рейтинг: {elo})")
        raw = input("Твой вариант (показать профиль - P, выйти из игры - Q): ")

        if raw.lower() == "p":
            profile(elo, win, lose)
            continue

        if raw.lower() == "q":
            save_game(elo, win, lose)
            print(f"Выходим. Итоговый рейтинг: {elo}")
            break
                    
  
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
                save_game(elo, win, lose)
                print(f"Выходим. Итоговый рейтинг: {elo}")
                break


play()
