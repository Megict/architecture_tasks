from fastapi import FastAPI
from fastapi import Request

from datetime import datetime
from datetime import timedelta
import psycopg2
import bcrypt


conn = psycopg2.connect(dbname='shop_db', user='mxcitn', password='1234')
cursor = conn.cursor()

app = FastAPI()

@app.get("/main_api/ping")
def ping():
    return None

# методы работы с пользователями
#===============================
@app.post("/main_api/user_create", tags=["User object methods"])
# добавить пользователя
async def user_create(request : Request):
    request_details = await request.json()
    user_name = request_details["user_name"]
    user_password = request_details["user_password"]
    
    name_first = request_details["name_first"] if "name_first" in request_details else 'Null'
    name_last = request_details["name_last"] if "name_last" in request_details else 'Null'
    
    # проверка, не занято ли имя
    cursor.execute(f"SELECT id FROM users WHERE username= '{user_name}';")
    if len(cursor.fetchall()) != 0:
        return "user name unavailable"
    # запись

    salt = bcrypt.gensalt()
    password_hash = bcrypt.hashpw(user_password.encode('utf-8'), salt).decode('utf-8')

    cursor.execute(f"INSERT INTO users (username, pword_hash, pword_salt, name_first, name_last)\
                        VALUES {user_name, password_hash, salt.decode('utf-8'), name_first, name_last}\
                        ON CONFLICT (username) DO NOTHING;")
    conn.commit()
    return None

@app.post("/main_api/user_change", tags=["User object methods"])
async def user_change(request : Request):
    request_details = await request.json()
    # можно изменить что угодно, если данные не меняются, то надо передать старые
    old_user_name = request_details["old_user_name"]
    old_user_password = request_details["old_user_password"]

    user_name = request_details["user_name"]
    user_password = request_details["user_password"]
    
    name_first = request_details["name_first"] if "name_first" in request_details else 'Null'
    name_last = request_details["name_last"] if "name_last" in request_details else 'Null'

    # верификация по паролю
    cursor.execute(f"SELECT id, pword_hash, pword_salt FROM users WHERE username= '{old_user_name}';")
    user_id, user_password_hash, user_password_salt = cursor.fetchall()[0]
    if bcrypt.hashpw(old_user_password.encode('utf-8'), user_password_salt.encode('utf-8')).decode('utf-8') == user_password_hash:
        # проверка, не занято ли имя
        cursor.execute(f"SELECT id FROM users WHERE username= '{user_name}';")
        if len(cursor.fetchall()) != 0:
            return "user name unavailable"
        # запись
        salt = bcrypt.gensalt()
        password_hash = bcrypt.hashpw(user_password.encode('utf-8'), salt).decode('utf-8')
        cursor.execute(f"UPDATE users SET username = '{user_name}', pword_hash = '{password_hash}', pword_salt = '{salt.decode('utf-8')}', name_first = '{name_first}', name_last = '{name_last}'\
                         WHERE id = {user_id};")
        conn.commit()
        return "OK"
    else:
        # неверный пароль, ничего не делаем
        return "WRONG PASSWORD"

@app.post("/main_api/user_initiate_session", tags=["User object methods"])
async def user_initiate_session(request : Request):
    request_details = await request.json()
    user_name = request_details["user_name"]
    user_password = request_details["user_password"]

    cursor.execute(f"SELECT pword_hash, pword_salt FROM users WHERE username= '{user_name}';")
    user_password_hash, user_password_salt = cursor.fetchall()[0]
    if bcrypt.hashpw(user_password.encode('utf-8'), user_password_salt.encode('utf-8')).decode('utf-8') == user_password_hash:
        # тут надо какой-то токен сессии наверное возвращать, хз
        return "OK"
    else:
        return "WRONG PASSWORD"

@app.post("/main_api/find_user_data", tags=["User object methods", "Search"])
async def find_user_data(request : Request):
    request_details = await request.json()
    name_first_mask = request_details["name_first_mask"]
    name_last_mask = request_details["name_last_mask"]

    cursor.execute(f"SELECT * FROM users WHERE LOWER(name_first) LIKE '%{name_first_mask.lower()}%' AND LOWER(name_last) LIKE '%{name_last_mask.lower()}%';")

    return [{"user_name" : rec[1], "first_name" : rec[4], "last_name" : rec[5]} for rec in cursor.fetchall()]

# методы работы с корзинами
#===============================
@app.post("/main_api/basket_create", tags=["Basket object methods"])
async def basket_create(request : Request):
    return None

@app.post("/main_api/basket_add_item", tags=["Basket object methods"])
async def basket_add_item(request : Request):
    return None

@app.post("/main_api/basket_finalize", tags=["Basket object methods"])
async def basket_finalize(request : Request):
    return None


# методы работы с продуктами
#===============================
@app.get("/main_api/get_all_available_items_list", tags=["Product object methods"])
async def get_all_available_items_list(request : Request):
    return None