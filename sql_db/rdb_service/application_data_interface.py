from fastapi import FastAPI
from fastapi import Request

app = FastAPI()

@app.get("/main_api/ping")
def ping():
    return None

# методы работы с пользователями
#===============================
@app.post("/main_api/user_create", tags=["User object methods"])
def user_create(request : Request):
    return None

@app.post("/main_api/user_change", tags=["User object methods"])
def user_create(request : Request):
    return None

@app.post("/main_api/user_initiate_session", tags=["User object methods"])
def user_initiate_session(request : Request):
    return None

@app.post("/main_api/find_user_data", tags=["User object methods", "Search"])
def find_user_data(request : Request):
    return None

# методы работы с корзинами
#===============================
@app.post("/main_api/basket_create", tags=["Basket object methods"])
def basket_create(request : Request):
    return None

@app.post("/main_api/basket_add_item", tags=["Basket object methods"])
def basket_add_item(request : Request):
    return None

@app.post("/main_api/basket_finalize", tags=["Basket object methods"])
def basket_finalize(request : Request):
    return None


# методы работы с продуктами
#===============================
@app.get("/main_api/get_all_available_items_list", tags=["Product object methods"])
def get_all_available_items_list(request : Request):
    return None