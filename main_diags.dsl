workspace {
    name "Лабораторная работа 1."
    
    model {
        # Описание компонент модели
        user = person "Покупатель"

        main_system = softwareSystem "Магазин" {
            app = container "Веб-приложение" {
                description "Сервис, с которым взаимодействует клиент"
                app_service = component "приложение" {
                    description " "
                }
                technology "Dash, Flask, Python"
            }
            user_cont = container "Клиенты" {
                description "Сервис работы с данными клиента"
                user_service = component "api клиентов" {
                    description "Предоставляет информацию о клиенте и том, какие с ним связаны корзины"
                }
                technology "FastAPI, Python"
            }
            bask_cont = container "Корзины" {
                description "Сервис работы с корзинами"
                bask_service = component "api корзин" {
                    description "Предоставляет информацию окорзинах и том, какие в них лежат товары"
                }
                technology "FastAPI, Python"
            }
            prod_cont = container "Товары" {
                description "Сервис работы со списком доступных товаров"
                prod_service = component "api продуктов" {
                    description "Предоставляет информацию о товарах, число на складе, цена и т.д."
                }
                technology "FastAPI, Python"
            }
            
            database = container "База данных" {
                description "Сервис работы с базой данных"
                database_ = component "База данных" {
                    description " " 
                }
                technology "PostgreSQL"
            }
        }
        order_proc = softwareSystem "Система обработки заказов" {
            description "Система обработки заказов"
        }
        warehouse_system = softwareSystem "Склад" {
            description "Систма склада товаров"
        }

        user -> main_system "Работает с системой, формирует корзину"
        warehouse_system -> main_system "Передает информацию о доступных продуктах"
        main_system -> order_proc "Передает информацию о собранной корзине для дальнейшей обработки"

        user -> app "Работа с приложением" "HTTPS"
        app -> user_cont "Регистрация пользователей" "JSON/HTTPS"
        app -> prod_cont "Просмотр списка товаров" "JSON/HTTPS"
        app -> bask_cont "Добавление товаров в корзину" "JSON/HTTPS"
        
        user_cont -> database "Запросы к бд" "SQL"
        prod_cont -> database "Запросы к бд" "SQL"
        bask_cont -> database "Запросы к бд" "SQL"

        warehouse_system -> prod_cont "Передает информацию о доступных на складе твоарах" "JSON/HTTPS"
        bask_cont -> order_proc "Передает информацию корзине покупателя в момент оформления заказа" "JSON/HTTPS"
        //---------------------------------
        
        user -> app_service "Работа с приложением" "HTTPS"
        app_service -> user_service "Регистрация пользователей" "JSON/HTTPS"
        app_service -> prod_service "Просмотр списка товаров" "JSON/HTTPS"
        app_service -> bask_service "Добавление товаров в корзину" "JSON/HTTPS"
        
        user_service -> database_ "Запросы к бд" "SQL"
        bask_service -> database_ "Запросы к бд" "SQL"
        prod_service -> database_ "Запросы к бд" "SQL"
    }
    views {
        themes default
        
        systemContext main_system "Context_diagram" {
            include *
            autoLayout
        }
        
        container main_system "Container_diagram" {
            include *
            autoLayout
        }
        //-----------------------------------------------
        component app "App_component_diagram" {
            include *
            autoLayout
        }
        
        component user_cont "User_component_diagram" {
            include *
            autoLayout
        }

        component bask_cont "Basket_component_diagram" {
            include *
            autoLayout
        }
        
        component prod_cont "Product_component_diagram" {
            include *
            autoLayout
        }
        
        component database "Database_component_diagram" {
            include *
            autoLayout
        }

        //---------------------------------------------

        dynamic main_system "UC01" "Добавление нового пользователя" {
            autoLayout
            user -> app "Создать нового пользователя"
            app -> user_cont "Сохранить данные о пользователе (POST user_api/save_new_user_data)" 
            user_cont -> database "Сохранить данные о пользователе (INSERT INTO users (...) VALUES (...) )"
        }
                        
        dynamic main_system "UC02" "Вход в систему" {
            autoLayout
            user -> app "Войти"
            app -> user_cont "Проверить пароль (POST user_api/log_in)" 
            user_cont -> database "Взять хэш пароля из бд (SELECT pw_hash FROM users where uname={?})"
        }

        dynamic main_system "UC03" "Просмотр списка товаров" {
            autoLayout
            user -> app "Посмотреть список товаров"
            app -> prod_cont "Передать список товаров (GET products_api/produce_products_list)" 
            prod_cont -> database "Взять список тваров из бд (SELECT * FROM products)"
        }

        dynamic main_system "UC04" "Добавление товара в корзину" {
            autoLayout
            // считаем, что когда пользователь нажимает "добавить в корзину, приложение знает, на какой товар он нажимает"
            user -> app "Добавить в корзину" 
            app -> user_cont "Узнать id активной корзины этого пользователя (GET user_api/get_user_basket_id)" 
            user_cont -> database "Взять данные о корзине пользователя из бд (SELECT b_id FROM users_to_baskets WHERE u_id={?} AND is_active=true)"
            app -> bask_cont "Добавить товар в корзину (POST baskets_api/add_product_to_basket)" 
            bask_cont -> database "Модифицировать корзину в бд (INSERT INTO baskets_to_products (b_id, p_id) VALUES (?, ?))"
        }
    }
}