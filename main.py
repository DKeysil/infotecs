from fastapi import FastAPI, HTTPException
import pendulum

app = FastAPI()


def city_dict_serializer(city_params: list) -> dict:
    """
    Сериализация списка параметров в словарь.
    :param city_params: список значений у города
    :return:
    """
    city_dict = {'geonameid': int(city_params[0]),
                 'name': city_params[1],
                 'asciiname': city_params[2],
                 'alternatenames': city_params[3],
                 'latitude': float(city_params[4]),
                 'longtitude': float(city_params[5]),
                 'feature_class': city_params[6],
                 'feature_code': city_params[7],
                 'county_code': city_params[8],
                 'cc2': city_params[9],
                 'admin1_code': city_params[10],
                 'admin2_code': city_params[11],
                 'admin3_code': city_params[12],
                 'admin4_code': city_params[13],
                 'population': int(city_params[14]),
                 'elevation': city_params[15],
                 'dem': city_params[16],
                 'timezone': city_params[17],
                 'modification_date': city_params[18][:-1]}
    return city_dict


with open('RU.txt', 'r', encoding='utf-8') as file:
    # Обрабатывает все строчки и добавляет их в список
    cities_list = []
    for line in file:
        serialized_city = city_dict_serializer(line.split('\t'))
        cities_list.append(serialized_city)


def find_city_by_id(geoname_id: int):
    """
    Ищет город по айди через бинарных поиск
    :param geoname_id: айди geoname объекта
    :return: dict объект города или None
    """
    first = 0
    last = len(cities_list)

    while first <= last:
        mid = (first + last) // 2

        if geoname_id < cities_list[mid].get('geonameid'):
            last = mid - 1
        elif geoname_id > cities_list[mid].get('geonameid'):
            first = mid + 1
        else:
            city_dict = cities_list[mid]
            return city_dict


def find_city_by_name(city_name: str):
    """
    Ищет город в списке по названию
    :param city_name: Название города на русском
    :return: dict объект города или None
    """
    cities_by_name = []

    for city in cities_list:
        alter_names = city.get('alternatenames').split(',')
        if city_name in alter_names:
            cities_by_name.append(city)

    cities_by_name.sort(key=lambda c: c.get('population'))
    if not cities_by_name:
        return None
    result_city = cities_by_name[-1]
    return result_city


@app.get("/city_info")
async def city_info(geoname_id: int):
    """
    Возвращает город по айди
    :param geoname_id:
    :return:
    """
    city_dict = find_city_by_id(geoname_id)
    if not city_dict:
        raise HTTPException(
            status_code=404,
            detail="City not found"
        )
    return city_dict


@app.get("/cities_page")
async def cities_page(page: int, page_size: int):
    """
    Возвращает список городов при заданных параметрах
    :param page: номер страницы
    :param page_size: размер страницы
    :return:
    """
    page_from = (page - 1) * page_size
    page_to = page * page_size

    cities_page_list = cities_list[page_from:page_to]
    return cities_page_list


@app.get("/compare_cities")
async def compare_cities(city_1: str, city_2: str):
    """
    Сравнивает два города по названиям
    :param city_1: название первого города
    :param city_2: название второго города
    :return: {
              "city_1": {json объект города},
              "city_2": {json объект города},
              "northern": "city_name",
              "same_timezone": false,
              "time_difference": 1
            }
    """
    city_1 = find_city_by_name(city_1)
    city_2 = find_city_by_name(city_2)
    if not city_1 or not city_2:
        raise HTTPException(
            status_code=404,
            detail="City not found"
        )

    result = {
        'city_1': city_1,
        'city_2': city_2
    }

    # Сравнивает широту, чтобы определить какой из двух городов севернее
    if city_1.get('latitude') > city_2.get('latitude'):
        result.update({'northern': city_1.get('name')})
    else:
        result.update({'northern': city_2.get('name')})

    if city_1.get('timezone') == city_2.get('timezone'):
        # Таймзона совпала
        result.update({'same_timezone': True, 'time_difference': 0})
    else:
        # Таймзона не совпала. Через библиотеку pendulum получаем время в первой и второй таймзоны, получаем разницу
        city_1_time = pendulum.now(city_1.get('timezone'))
        city_2_time = city_1_time.in_timezone(city_2.get('timezone'))
        difference = abs(city_1_time.hour - city_2_time.hour)
        result.update({'same_timezone': False, 'time_difference': difference})

    return result
