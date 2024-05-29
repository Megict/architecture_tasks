from pymongo import MongoClient
import psycopg2
import random
from random_word import RandomWords
import names
from datetime import datetime
from datetime import timedelta
import bcrypt
from tqdm import tqdm

rwg = RandomWords()

PROD_CNT = 100 # сколько товаров добавить
USER_CNT = 100 # сколько пользователей добавить

def create_random_product():
    name = rwg.get_random_word()
    price = abs(int(random.gauss(mu = 200, sigma = 50)))
    amount = abs(int(random.gauss(mu = 0, sigma = 10)))
    return {"name" : name, "price" : price, "amount" : amount}

def create_random_basket():
    opening_date = datetime.now() - timedelta(days = random.choice(range(1, 20)))
    closing_date = random.choice([None, datetime.now()])

    return {"time_opened" : opening_date, "time_closed" : closing_date}

def create_random_user():
    password = rwg.get_random_word()

    user_name = rwg.get_random_word()
    salt = bcrypt.gensalt()
    passwor_hash = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    name_first = names.get_first_name()
    name_last = names.get_last_name()

    baskets = []
    for _ in range(random.choice([1,1,1,1,2,2,3,4,5])):
        baskets.append(create_random_basket())

    return {"username" : user_name, "pword_hash" : passwor_hash, "pword_salt" : salt.decode('utf-8'), "name_first" : name_first, "name_last" : name_last}, baskets

try:
    # пытаемся подключиться к базе данных
    client = MongoClient("mongodb://root:1234@localhost:27020/?authSource=admin")
    db = client['ShopDB']
except:
    # в случае сбоя подключения будет выведено сообщение в STDOUT
    print('Can`t establish connection to database')
    db = None

try:
    # пытаемся подключиться к базе данных
    conn = psycopg2.connect(dbname='shop_db', user='mxcitn', password='1234', host='localhost') 
    cursor = conn.cursor()
except:
    # в случае сбоя подключения будет выведено сообщение в STDOUT
    print('Can`t establish connection to postgres')
    cursor = None

# инициализация бд случайно сгенерированными данными о клиентах, товарах и корзинах
if db is not None and cursor is not None:
    prod_coll = db.products
    random_user_data = create_random_user()
    # добавление продуктов
    for _ in tqdm(range(PROD_CNT)):
        prod_coll.insert_one(create_random_product())
        
    cur_ = prod_coll.find({})
    
    avail_products = [doc for doc in cur_]

    # users_coll = db.users
    basket_coll = db.baskets
    for _ in tqdm(range(USER_CNT)):
        random_user_data = create_random_user()
        cursor.execute(f"INSERT INTO users (username, pword_hash, pword_salt, name_first, name_last)\
                            VALUES {random_user_data[0]['username'], random_user_data[0]['pword_hash'], random_user_data[0]['pword_salt'], random_user_data[0]['name_first'], random_user_data[0]['name_last']};")
        cursor.execute("SELECT id FROM users ORDER BY id desc limit 1")
        user_id = cursor.fetchall()[0][0]
        # добавляем корзины для этого пользователя
        for basket in random_user_data[1]:
            # наполняем корзину товарами
            basket_contents = []
            for _ in range(random.choice(range(10))):
                basket_contents += [{"product_id" : random.choice(avail_products)['_id'], "amount" : random.choice(range(10))}]
            if basket['time_closed'] is None:
                basket_id = basket_coll.insert_one({"owner_user_id" : user_id, "basket_contents" : basket_contents, "time_opened" : basket["time_opened"]}).inserted_id
            else:
                basket_id = basket_coll.insert_one({"owner_user_id" : user_id, "basket_contents" : basket_contents, "time_opened" : basket["time_opened"], "time_closed" : basket["time_closed"]}).inserted_id


    conn.commit()
    cursor.close()
    conn.close()
