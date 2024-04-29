
CREATE TABLE public.users
(
    id serial NOT NULL,
    username text NOT NULL,
    pword_hash text NOT NULL,
    pword_salt text NOT NULL,
    name_first text,
    name_last text,
    PRIMARY KEY (id)
);

ALTER TABLE IF EXISTS public.users
    OWNER to mxcitn;


CREATE TABLE public.products
(
    id serial NOT NULL,
    name text NOT NULL,
    price bigint NOT NULL,
    amount bigint NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE IF EXISTS public.products
    OWNER to mxcitn;

    
CREATE TABLE public.baskets
(
    id serial NOT NULL,
    owner_user_id bigint NOT NULL,
    time_opened timestamp NOT NULL,
    time_colsed timestamp,
    PRIMARY KEY (id),
    FOREIGN KEY (owner_user_id) REFERENCES public.users (id) ON DELETE CASCADE
);

ALTER TABLE IF EXISTS public.baskets
    OWNER to mxcitn;




CREATE TABLE public.basket_to_product
(
    id serial NOT NULL,
    basket_id bigint NOT NULL,
    product_id bigint NOT NULL,
    PRIMARY KEY (id),
    FOREIGN KEY (basket_id) REFERENCES public.baskets (id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES public.products (id) ON DELETE CASCADE
);

ALTER TABLE IF EXISTS public.basket_to_product
    OWNER to mxcitn;