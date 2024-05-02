FROM python:3.8

WORKDIR /code

COPY ./plantuml-1.2024.4.jar /code/plantuml-1.2024.4.jar

RUN apt-get update && \
    apt-get install -y openjdk-17-jre-headless && \
    apt-get install -y graphviz && \
    apt-get clean;

CMD ["java", "-jar", "plantuml-1.2024.4.jar", "-charset", "UTF-8", "/data/*.puml"]