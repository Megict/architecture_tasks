FROM python:3.8

WORKDIR /code

COPY ./requirements.txt /code/requirements.txt

RUN pip install --no-cache-dir --upgrade -r ./requirements.txt
RUN pip install fastapi uvicorn

COPY ./application_main_interface.py /code/application_main_interface.py

CMD ["uvicorn", "application_main_interface:app", "--reload", "--host", "0.0.0.0", "--port", "8000"]