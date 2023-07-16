import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.neural_network import MLPRegressor
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import mean_squared_error, r2_score
import locale
import seaborn as sns
from rest_framework.decorators import api_view
from rest_framework.response import Response
import pyowm
import matplotlib.pyplot as plt
import base64

owm = pyowm.OWM('f07f0ddca23a8348dff8538dc77252d1')
weather_mgr = owm.weather_manager()

data1 = pd.read_excel(r"C:\pythonProject2023\d2.xlsx")
data2 = pd.read_excel(r"C:\pythonProject2023\d3.xlsx")

data = pd.concat([data1, data2], ignore_index=True)

# Предварительная обработка данных
data = data.drop(['Поезд/Нитка', 'Месяц операции', 'Станция отп.', 'Станция назн.'], axis=1)
# Заполнение пропущенных значений, если есть
data = data.fillna(0)

le = LabelEncoder()
data['Тип/Кл.обсл.'] = data['Тип/Кл.обсл.'].astype(str)
data['Тип/Кл.обсл.'] = le.fit_transform(data['Тип/Кл.обсл.'])

X = data.drop(['Итого сумма билета'], axis=1)
y = data['Итого сумма билета']

# Разделение данных на обучающую и тестовую выборки с меньшим test_size
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.1, random_state=42)

X_train['Температура'] = [0] * len(X_train)
X_train['Осадки'] = [0] * len(X_train)
X_train = X_train[
    ['Тип/Кл.обсл.', 'Кол-во прод. Мест', 'Сумма по бил.', 'Сумма по плац.', 'Сумма серв.усл.', 'Расстояние',
     'Температура', 'Осадки']]

model = MLPRegressor(hidden_layer_sizes=(100, 100), max_iter=500)
model.fit(X_train, y_train)

# Предсказание на тестовой выборке
X_test['Температура'] = [0] * len(X_test)
X_test['Осадки'] = [0] * len(X_test)
X_test = X_test[
    ['Тип/Кл.обсл.', 'Кол-во прод. Мест', 'Сумма по бил.', 'Сумма по плац.', 'Сумма серв.усл.', 'Расстояние',
     'Температура', 'Осадки']]
y_pred = model.predict(X_test)

mse = mean_squared_error(y_test, y_pred)
r_squared = r2_score(y_test, y_pred)

errors = y_pred - y_test

# Путь к файлу для сохранения графика
output_path = r"C:\pythonProject2023\error_histogram.png"

# Построение гистограммы ошибок
fig, ax = plt.subplots(figsize=(10, 6))
sns.histplot(errors, bins=50, kde=True, palette='pastel', ax=ax)
plt.xlabel('Ошибка')
plt.ylabel('Частота')
plt.title('Распределение ошибок')
plt.grid(True)
plt.tight_layout()

# Добавление линии динамики
mean_error = errors.mean()
plt.axvline(mean_error, color='red', linestyle='--', label='Средняя ошибка')
plt.legend()

# Сохранение графика в формате PNG
plt.savefig(output_path, format='png')
plt.close()


@api_view(['POST'])
def predict_price(request):
    if request.method == 'POST':
        body = request.data

        input_data = {
            'Тип/Кл.обсл.': [le.transform([body['Тип/Кл.обсл.']])],
            'Кол-во прод. Мест': [body['Кол-во прод. Мест']],
            'Сумма по бил.': [body['Сумма по бил.']],
            'Сумма по плац.': [body['Сумма по плац.']],
            'Сумма серв.усл.': [body['Сумма серв.усл.']],
            'Расстояние': [body['Расстояние']],
            'Температура': [0],
            'Осадки': [0]
        }

        city = 'Krasnodar'
        observation = weather_mgr.weather_at_place(city)
        weather = observation.weather
        current_temperature = weather.temperature('celsius')['temp']
        precipitation = weather.rain if weather.rain else 0

        input_data['Температура'] = [current_temperature]
        input_data['Осадки'] = [precipitation]

        new_data = pd.DataFrame(input_data)

        new_prediction = model.predict(new_data)

        if current_temperature < 10 and precipitation > 5:
            new_prediction *= 1.15
        elif current_temperature < 30 and precipitation < 0.5:
            new_prediction *= 1.2
        elif precipitation > 10:
            new_prediction *= 1.3
        elif current_temperature < 0:
            new_prediction *= 1.1

        # Устанавливаем русскую локаль
        locale.setlocale(locale.LC_ALL, 'ru_RU.UTF-8')

        print('Request Body:', body)
        print('New Prediction:', new_prediction)

        # Преобразование изображения в base64
        with open(output_path, "rb") as image_file:
            image_data = image_file.read()
            image_base64 = base64.b64encode(image_data).decode("utf-8")

        formatted_price = f'{new_prediction[0]:.1f}'
        formatted_mse = f'{mse:.1f}'
        formatted_r_squared = f'{r_squared:.1f}'

        response_data = {
            'predicted_price': f'{formatted_price} ₽',
            'mean_squared_error': f'{formatted_mse}',
            'r_squared': f'{formatted_r_squared}',
            'current_temperature': f'{current_temperature}°C',
            'precipitation': f'{precipitation} mm',
            'error_histogram': image_base64
        }

        return Response(response_data)

    return Response({'error': 'Invalid request method'})
