from fastapi import FastAPI
from fastapi import Request

from datetime import datetime
from datetime import timedelta
import psycopg2
import bcrypt


conn = psycopg2.connect(dbname='shop_db', user='mxcitn', password='1234')
cursor = conn.cursor()

app = FastAPI()

def verify_user(user_name, presented_password):
    try:
        cursor.execute(f"SELECT id, pword_hash, pword_salt FROM users WHERE username= '{user_name}';")
        user_id, user_password_hash, user_password_salt = cursor.fetchall()[0]
        if bcrypt.hashpw(presented_password.encode('utf-8'), user_password_salt.encode('utf-8')).decode('utf-8') == user_password_hash:
            return "OK", user_id
        else:
            return "WRONG PASSWORD"
    except IndexError:
        return "USER DOES NOT EXIST"


@app.get("/main_api/ping")
def ping():
    return None

# методы работы с пользователями
#===============================
@app.post("/main_api/user_create", tags=["User object methods"])
# добавить пользователя
async def user_create(request : Request):
    conn.rollback()
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
                        VALUES {user_name, password_hash, salt.decode('utf-8'), name_first, name_last};")
    conn.commit()
    return None

@app.post("/main_api/user_change", tags=["User object methods"])
async def user_change(request : Request):
    conn.rollback()
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

# возвращаем данные по пользователю, пароль и имя которого предоставлено
@app.post("/main_api/produce_user_data", tags=["User object methods"])
async def produce_user_data(request : Request):
    conn.rollback()
    request_details = await request.json()
    user_name = request_details["user_name"]
    user_password = request_details["user_password"]

    verify = verify_user(user_name, user_password)
    if verify[0] != "OK":
        return verify
    
    cursor.execute(f"SELECT id, username, name_first, name_last FROM users WHERE username= '{user_name}';")
    u_data = cursor.fetchall()[0]
    return {"id" : u_data[0], "username" : u_data[1], "name_first" : u_data[2], "name_last" : u_data[3]} 

# возвращаем список всех корзин пользователя
@app.post("/main_api/produce_user_baskets", tags=["User object methods"])
async def produce_user_baskets(request : Request):
    conn.rollback()
    request_details = await request.json()
    user_name = request_details["user_name"]
    user_password = request_details["user_password"]

    verify = verify_user(user_name, user_password)
    if verify[0] != "OK":
        return verify
    
    cursor.execute(f"SELECT * FROM baskets WHERE owner_user_id = {verify[1]}")
    return [{"basket_id" : bask[0], "basket_owned" : bask[1], "basket_opened" : bask[2], "basket_closed" : bask[3], "basket_contents" : get_products_in_basket(bask[0], request)}  for bask in cursor.fetchall()]

# поиск по маске имени и фамилии
@app.post("/main_api/find_user_data", tags=["User object methods", "Search"])
async def find_user_data(request : Request):
    conn.rollback()
    request_details = await request.json()
    name_first_mask = request_details["name_first_mask"]
    name_last_mask = request_details["name_last_mask"]

    cursor.execute(f"SELECT * FROM users WHERE LOWER(name_first) LIKE '%{name_first_mask.lower()}%' AND LOWER(name_last) LIKE '%{name_last_mask.lower()}%';")

    return [{"user_name" : rec[1], "first_name" : rec[4], "last_name" : rec[5]} for rec in cursor.fetchall()]

# методы работы с корзинами
#===============================
@app.post("/main_api/basket_create", tags=["Basket object methods"])
async def basket_create(request : Request):
    conn.rollback()
    request_details = await request.json()
    user_name = request_details["user_name"]
    user_password = request_details["user_password"]
    
    verify = verify_user(user_name, user_password)
    if verify[0] != "OK":
        return verify
    
    cursor.execute(f"INSERT INTO baskets (owner_user_id, time_opened)\
                        VALUES {verify[1], str(datetime.now())};")
    # смотрим id последней записи 
    cursor.execute("SELECT id FROM baskets ORDER BY id desc limit 1")
    basket_id = cursor.fetchall()[0][0]
    conn.commit()

    return basket_id

# общие данные о корзине
@app.get("/main_api/get_basket_data", tags=["Basket object methods"])
def get_basket_data(basket_id, request : Request): 
    conn.rollback()
    cursor.execute(f"SELECT * FROM baskets WHERE id = {basket_id}")
    bask = cursor.fetchall()[0]
    return {"basket_owned" : bask[1], "basket_opened" : bask[2], "basket_closed" : bask[3]}

# что лежит в коризне
@app.get("/main_api/get_basket_contents", tags=["Basket object methods"])
def get_products_in_basket(basket_id, request : Request): 
    conn.rollback()
    cursor.execute(f"SELECT product_id, name, price, product_amount FROM basket_to_product JOIN products ON product_id= products.id WHERE basket_id = {basket_id}")
    return [{"id" : elm[0], "name" : elm[1], "price" : elm[2], "amount" : elm[3]} for elm in cursor.fetchall()]

# добавить товар в корзину
@app.post("/main_api/basket_add_item", tags=["Basket object methods"])
async def basket_add_item(request : Request):
    conn.rollback()
    request_details = await request.json()
    user_name = request_details["user_name"]
    user_password = request_details["user_password"]
    
    basket_id = request_details["basket_id"]
    product_id = request_details["product_id"]

    amount = request_details["amount"]
    # добавить проверку, что добавляемое количество меньше максимально доступного
    # вообще это должно в интерфейсе отрабатываться, где предлагается выбрать чисто от 1 до доступного кол-ва
    # доступное количество передается методом, который дает инфу по товарам
    # здесь будет только проверка при закрытии корзины

    verify = verify_user(user_name, user_password)
    if verify[0] != "OK":
        return verify
    # доавить проверку принадлежности корзины
    # проверка принадлежности корзины
    # ---------------------------------------
    cursor.execute(f"SELECT owner_user_id FROM baskets WHERE id = {basket_id}")
    basket_owner_data = cursor.fetchall()
    if len(basket_owner_data) == 0:
        return "BASKET NOT FOUND"
    if int(basket_owner_data[0][0]) != int(verify[1]):
        return "NOT YOUR BASKET"
    # ---------------------------------------
    # проверка, не закрыта ли корзина
    # ---------------------------------------
    cursor.execute(f"SELECT baskets.time_colsed FROM baskets WHERE id = {basket_id}")
    basket_closed_data = cursor.fetchall()
    if basket_closed_data[0][0] is not None:
        return "CLOSED BASKET"
    # ---------------------------------------
    # проверка количества товара
    # ---------------------------------------
    cursor.execute(f"SELECT amount FROM products WHERE id = {product_id}")
    avail_amount = cursor.fetchall()
    if int(amount) > int(avail_amount[0][0]):
        return "ADDING MORE THEN AVAILABLE", int(product_id)
    # ---------------------------------------    

    # если товар уже есть в корине по идее интерфейс должен не давать случиться такой ситуации
    cursor.execute(f"INSERT INTO basket_to_product (basket_id, product_id, product_amount)\
                        VALUES {basket_id, product_id, amount};")
    conn.commit()

    return "OK"

# поменять количество товара в корзине
@app.post("/main_api/basket_mod_item", tags=["Basket object methods"])
async def basket_mod_item(request : Request):
    conn.rollback()
    request_details = await request.json()
    user_name = request_details["user_name"]
    user_password = request_details["user_password"]
    
    basket_id = request_details["basket_id"]
    product_id = request_details["product_id"]

    amount = request_details["amount"]
    # добавить проверку, что добавляемое количество меньше максимально доступного

    verify = verify_user(user_name, user_password)
    if verify[0] != "OK":
        return verify
    # проверка принадлежности корзины
    # ---------------------------------------
    cursor.execute(f"SELECT owner_user_id FROM baskets WHERE id = {basket_id}")
    basket_owner_data = cursor.fetchall()
    if len(basket_owner_data) == 0:
        return "BASKET NOT FOUND"
    if int(basket_owner_data[0][0]) != int(verify[1]):
        return "NOT YOUR BASKET"
    # ---------------------------------------
    # проверка, не закрыта ли корзина
    # ---------------------------------------
    cursor.execute(f"SELECT baskets.time_colsed FROM baskets WHERE id = {basket_id}")
    basket_closed_data = cursor.fetchall()
    if basket_closed_data[0][0] is not None:
        return "CLOSED BASKET"
    # ---------------------------------------
    # проверка количества товара
    # ---------------------------------------
    cursor.execute(f"SELECT amount FROM products WHERE id = {product_id}")
    avail_amount = cursor.fetchall()
    if int(amount) > int(avail_amount[0][0]):
        return "ADDING MORE THEN AVAILABLE", int(product_id)
    # ---------------------------------------

    cursor.execute(f"UPDATE basket_to_product SET product_amount = {amount}\
                        WHERE basket_id= {basket_id} AND product_id= {product_id};")
    conn.commit()

    return "OK"

# удалить товар из корзины
@app.post("/main_api/basket_remove_item", tags=["Basket object methods"])
async def basket_remove_item(request : Request):
    conn.rollback()
    request_details = await request.json()
    user_name = request_details["user_name"]
    user_password = request_details["user_password"]
    
    basket_id = request_details["basket_id"]
    product_id = request_details["product_id"]

    verify = verify_user(user_name, user_password)
    if verify[0] != "OK":
        return verify
    # доавить проверку принадлежности корзины
    # проверка принадлежности корзины
    # ---------------------------------------
    cursor.execute(f"SELECT owner_user_id FROM baskets WHERE id = {basket_id}")
    basket_owner_data = cursor.fetchall()
    if len(basket_owner_data) == 0:
        return "BASKET NOT FOUND"
    if int(basket_owner_data[0][0]) != int(verify[1]):
        return "NOT YOUR BASKET"
    # ---------------------------------------
    # проверка, не закрыта ли корзина
    # ---------------------------------------
    cursor.execute(f"SELECT baskets.time_colsed FROM baskets WHERE id = {basket_id}")
    basket_closed_data = cursor.fetchall()
    if basket_closed_data[0][0] is not None:
        return "CLOSED BASKET"
    # ---------------------------------------

    cursor.execute(f"DELETE FROM basket_to_product\
                        WHERE basket_id= {basket_id} and product_id= {product_id};")
    conn.commit()

    return "OK"

# закрыть коризину (тут в теории информация должна передаваться в сервис оплаты и доставки)
@app.post("/main_api/basket_finalize", tags=["Basket object methods"])
async def basket_finalize(request : Request):
    conn.rollback()
    # указываем дату закрытия корзины и возвращаем спиок всех товаров
    request_details = await request.json()
    user_name = request_details["user_name"]
    user_password = request_details["user_password"]
    
    basket_id = request_details["basket_id"]
    
    verify = verify_user(user_name, user_password)
    if verify[0] != "OK":
        return verify
    # проверка принадлежности корзины
    # ---------------------------------------
    cursor.execute(f"SELECT owner_user_id FROM baskets WHERE id = {basket_id}")
    basket_owner_data = cursor.fetchall()
    if len(basket_owner_data) == 0:
        return "BASKET NOT FOUND"
    if int(basket_owner_data[0][0]) != int(verify[1]):
        return "NOT YOUR BASKET"
    # ---------------------------------------
    # проверка, не закрыта ли корзина
    # ---------------------------------------
    cursor.execute(f"SELECT baskets.time_colsed FROM baskets WHERE id = {basket_id}")
    basket_closed_data = cursor.fetchall()
    if basket_closed_data[0][0] is not None:
        return "CLOSED BASKET" 
    # ---------------------------------------
    # проверка наличия достаточного количества товаров
    cursor.execute(f"SELECT product_amount, amount, product_id FROM basket_to_product JOIN products ON product_id= products.id WHERE basket_id = {basket_id}")
    
    for elm in cursor.fetchall():
        if int(elm[0]) > int(elm[1]):
            conn.rollback()
            return "REQUESTED MORE THEN AVAILABLE", int(elm[2])
        cursor.execute(f"UPDATE products SET amount = '{int(elm[1]) - int(elm[0])}'\
                         WHERE id = {int(elm[2])};")
        
    cursor.execute(f"UPDATE baskets SET time_colsed = '{str(datetime.now())}'\
                        WHERE id = {basket_id};")
    conn.commit()

    # сделать проверку, чтобы нельзя было закрыть одну и ту же корзину много раз +
    # еще надо сделать так, чтобы при закрытии корзины число товаров в ней вычиталось из amount в товарах +
    # и добавить проверку, чтобы amount не мог стать отрициательным +
    
    # вообще получется если 2 чела набрали максимум одного и того же товара, то у того, кто попробует купить вторым не пройдет
    cursor.execute(f"SELECT product_id, name, price, product_amount FROM basket_to_product JOIN products ON product_id= products.id WHERE basket_id = {basket_id}")
    return [{"id" : elm[0], "name" : elm[1], "price" : elm[2], "amount" : elm[3]} for elm in cursor.fetchall()]


# методы работы с продуктами
#===============================
@app.get("/main_api/get_all_available_items_list", tags=["Product object methods"])
async def get_all_available_items_list(request : Request):
    conn.rollback()
    cursor.execute(f"SELECT * FROM products")
    return [{"id" : elm[0], "name" : elm[1], "price" : elm[2], "amount" : elm[3]} for elm in cursor.fetchall()]

@app.get("/main_api/get_product_data", tags=["Product object methods"])
async def get_product_data(product_id, request : Request):
    conn.rollback()
    cursor.execute(f"SELECT * FROM products WHERE id= {product_id}")
    elm = cursor.fetchall()
    if len(elm) == 0:
        return "NO SUCH PRODUCT"
    else:
        elm = elm[0]
    return {"id" : elm[0], "name" : elm[1], "price" : elm[2], "amount" : elm[3]}