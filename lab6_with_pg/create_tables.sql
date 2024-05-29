
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
