import random
import time

what_you_know = {
    "1": ["Я могу", "Я умею", "Я справляюсь с:"],
    "2": ["Отвечать по командам", "Говорить на русском"],
    "3": ["Помогать по рутине", "Помогать по работе"],
    "4": ["Но, как сырая модель", "Но,"],
    "5": ["Рассуждением"],
    "6": ["Или", "Или же", "Ну или"],
    "7": ["С кодом"],
    "8": ["Я не смогу помочь"]
}

greeting = {
    "1": ["Привет", "Приветики", "Здарова", "Приветствую", "Здравствуйте"],
    "2": ["Чем могу помочь?", "Что вы хотите знать?"]
}

g   = random.choice(greeting["1"])
g_2 = random.choice(greeting["2"])
w   = random.choice(what_you_know["1"])
h   = random.choice(what_you_know["2"])
a   = random.choice(what_you_know["3"])
t   = random.choice(what_you_know["4"])
y   = random.choice(what_you_know["5"])
o   = random.choice(what_you_know["6"])
u   = random.choice(what_you_know["7"])
k   = random.choice(what_you_know["8"])

print(g + ", " + g_2)
print(w + " " + h + ", " + a + ". " + t + " " + y + " " + o + " " + u + ". " + k)
