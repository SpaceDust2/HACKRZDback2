import pyowm
import telebot
from telebot import types
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.neural_network import MLPRegressor
import requests
from sklearn.preprocessing import LabelEncoder

bot = telebot.TeleBot("6380614700:AAHX_n4gvpEinKXxzH8hi_tmZQOIcPn3QdM")

current_step = 0

variables = ['Тип/Кл.обсл.', 'Кол-во прод. Мест', 'Сумма по бил.', 'Сумма по плац.', 'Сумма серв.усл.', 'Расстояние']


# Function to retrieve weather data based on coordinates
def get_weather(lat, lon, api_key):
    url = f"http://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_key}"
    response = requests.get(url)
    data = response.json()
    weather = data['weather'][0]['main']
    return weather


def preprocess_data(data):
    data = data.drop(['Поезд/Нитка', 'Месяц операции', 'Станция отп.', 'Станция назн.'], axis=1)
    data = data.fillna(0)

    data = pd.get_dummies(data, columns=['Тип/Кл.обсл.'])

    return data


def train_model(X, y):
    # Split the data into training and test sets
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.1, random_state=42)
    # Initialize and train the model
    model = MLPRegressor(hidden_layer_sizes=(100, 100), max_iter=500)
    model.fit(X_train, y_train)
    return model, X_test, y_test


def make_prediction(model, new_data, api_key):
    # Retrieve weather information
    owm = pyowm.OWM(api_key)
    weather_mgr = owm.weather_manager()
    city = 'Krasnodar'
    observation = weather_mgr.weather_at_place(city)
    weather = observation.weather
    current_temperature = weather.temperature('celsius')['temp']
    precipitation = weather.rain if weather.rain else 0

    new_data['Температура'] = current_temperature
    new_data['Осадки'] = precipitation

    # Reorder the columns to match the order of the training data
    new_data = new_data[X.columns]

    new_prediction = model.predict(new_data)
    return new_prediction[0]




data1 = pd.read_excel('d2.xlsx')
data2 = pd.read_excel('d3.xlsx')

data = pd.concat([data1, data2], ignore_index=True)
data = preprocess_data(data)

X = data.drop(['Итого сумма билета'], axis=1)
y = data['Итого сумма билета']

model, X_test, y_test = train_model(X, y)

user_data = {}


def handle_value_input(message):
    global current_step

    chat_id = message.chat.id
    value = message.text

    # Save the value to the corresponding variable
    variable = variables[current_step]
    if variable == 'Тип/Кл.обсл.':
        le_transform = LabelEncoder().fit_transform
        user_data[chat_id][variable] = le_transform([value])[0]
    else:
        user_data[chat_id][variable] = float(value)

    current_step += 1

    if current_step < len(variables):
        # Request the next value
        bot.send_message(chat_id, f"Введите значение для {variables[current_step]}",
                         reply_markup=types.ReplyKeyboardRemove())
    else:
        # All values entered, make a prediction
        current_step = 0  # Reset the current step

        input_data = pd.DataFrame(user_data[chat_id], index=[0])
        input_data = input_data.reindex(columns=X.columns, fill_value=0)  # Reorder columns to match X

        new_prediction = make_prediction(model, input_data,
                                         'f07f0ddca23a8348dff8538dc77252d1')  # Replace with your weather API key

        formatted_price = f'{new_prediction:.1f} ₽'
        bot.send_message(chat_id, formatted_price, reply_markup=types.ReplyKeyboardMarkup(resize_keyboard=True))


@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton("Тип/Кл.обсл.")
    btn2 = types.KeyboardButton("Кол-во прод. Мест")
    btn3 = types.KeyboardButton("Сумма по бил.")
    btn4 = types.KeyboardButton("Сумма по плац.")
    btn5 = types.KeyboardButton("Сумма серв.усл.")
    btn6 = types.KeyboardButton("Расстояние")
    markup.add(btn1, btn2, btn3, btn4, btn5, btn6)
    bot.send_message(message.chat.id,
                     text="Привет, {0.first_name}🤗! Введите значения для каждой переменной по очереди.".format(
                         message.from_user), reply_markup=markup)


# Handler for the first variable input
@bot.message_handler(func=lambda message: message.text in variables)
def variable_input(message):
    chat_id = message.chat.id
    variable = message.text
    user_data[chat_id] = {'variable': variable}
    bot.send_message(chat_id, f"Введите значение для {variable}", reply_markup=types.ReplyKeyboardRemove())


# Handler for value input
@bot.message_handler(func=lambda message: 'variable' in user_data.get(message.chat.id, {}))
def value_input(message):
    handle_value_input(message)


# Send a notification about the bot launch
@bot.message_handler(func=lambda message: True, content_types=['new_chat_members'])
def send_notification(message):
    bot.send_message(message.chat.id, "Бот успешно запущен! Добро пожаловать!")


print("Бот успешно запущен! Добро пожаловать!")
bot.polling(none_stop=True)
