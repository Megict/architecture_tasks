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
                    description " "
                }
                technology "FastAPI, Python"
            }
            bask_cont = container "Корзины" {
                description "Сервис работы с корзинами"
                bask_service = component "api корзин" {
                    description " "
                }
                technology "FastAPI, Python"
            }
            prod_cont = container "Товары" {
                description "Сервис работы со списком доступных товаров"
                prod_service = component "api продуктов" {
                    description " "
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

        user -> app "Работа с приложением"
        app -> user_cont "Регистрация пользователей"
        app -> prod_cont "Просмотр списка товаров"
        app -> bask_cont "Добавление товаров в корзину"
        user_cont -> bask_cont "Связь пользователя с его корзинами"
        bask_cont -> prod_cont "Связь корзиты с товарами в ней"
        user_cont -> database "Запросы к бд"
        prod_cont -> database "Запросы к бд"
        bask_cont -> database "Запросы к бд"
        
        user -> app_service "Работа с приложением"
        app_service -> user_service "Регистрация пользователей"
        app_service -> prod_service "Просмотр списка товаров"
        app_service -> bask_service "Добавление товаров в корзину"
        user_service -> bask_service "Связь пользователя с его корзинами"
        bask_service -> prod_service "Связь корзиты с товарами в ней"
        user_service -> database_ "Запросы к бд"
        bask_service -> database_ "Запросы к бд"
        prod_service -> database_ "Запросы к бд"
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
    }
}