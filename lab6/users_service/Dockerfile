FROM python:3.8

WORKDIR /code

COPY ./requirements.txt /code/requirements.txt

RUN pip install --no-cache-dir --upgrade -r ./requirements.txt
RUN pip install fastapi uvicorn

COPY ./users_service_interface.py /code/users_service_interface.py

CMD ["uvicorn", "users_service_interface:app", "--reload", "--host", "0.0.0.0", "--port", "8000"]