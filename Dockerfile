# Dockerfile
FROM python:3.11.3-slim-buster
RUN pip install --upgrade pip

RUN useradd -m myuser
USER myuser
WORKDIR /home/myuser

COPY --chown=myuser:myuser requirements.txt requirements.txt
COPY --chown=myuser:myuser main.py main.py
RUN pip install --user -r requirements.txt

ENV PATH="/home/myuser/.local/bin:${PATH}"
ENV FLASK_APP=main
ENV FLASK_RUN_PORT=8080
ENV FLASK_RUN_HOST=0.0.0.0

CMD ["flask", "run"]
 
