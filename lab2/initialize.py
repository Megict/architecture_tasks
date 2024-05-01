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
    return name, price, amount

def create_random_basket():
    opening_date = datetime.now() - timedelta(days = random.choice(range(1, 20)))
    closing_date = random.choice([None, datetime.now()])

    return opening_date, closing_date

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

    return user_name, passwor_hash, salt.decode('utf-8'), name_first, name_last, baskets

try:
    # пытаемся подключиться к базе данных
    conn = psycopg2.connect(dbname='shop_db', user='mxcitn', password='1234')
except:
    # в случае сбоя подключения будет выведено сообщение в STDOUT
    print('Can`t establish connection to database')
    conn = None

# инициализация бд случайно сгенерированными данными о клиентах, товарах и корзинах
if conn is not None:
    cursor = conn.cursor()
    random_user_data = create_random_user()
    
    for _ in tqdm(range(PROD_CNT)):
        cursor.execute(f"INSERT INTO products (name, price, amount)\
                            VALUES {create_random_product()};")
        
    cursor.execute("SELECT id FROM products")
    avail_products = cursor.fetchall()

    for _ in tqdm(range(USER_CNT)):
        random_user_data = create_random_user()
        cursor.execute(f"INSERT INTO users (username, pword_hash, pword_salt, name_first, name_last)\
                            VALUES {random_user_data[0:5]};")
        cursor.execute("SELECT id FROM users ORDER BY id desc limit 1")
        # добавляем корзины для этого пользователя
        user_id = cursor.fetchall()[0][0]
        for basket in random_user_data[5]:
            if basket[1] is None:
                cursor.execute(f"INSERT INTO baskets (owner_user_id, time_opened)\
                                    VALUES {user_id, str(basket[0])};")
            else:
                cursor.execute(f"INSERT INTO baskets (owner_user_id, time_opened, time_colsed)\
                                    VALUES {user_id, str(basket[0]), str(basket[1])};")
            cursor.execute("SELECT id FROM baskets ORDER BY id desc limit 1")
            # наполняем корзину товарами
            basket_id = cursor.fetchall()[0][0]
            for _ in range(random.choice(range(10))):
                cursor.execute(f"INSERT INTO basket_to_product (basket_id, product_id)\
                                    VALUES {basket_id, random.choice(avail_products)[0]};")
                

    conn.commit()
    cursor.close()
    conn.close()