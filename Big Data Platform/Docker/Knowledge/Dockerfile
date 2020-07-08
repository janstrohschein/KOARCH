FROM python:3.7-slim-buster

COPY ./configurations/requirements.txt /
RUN pip install -r requirements.txt

COPY ./knowledge.py /src/
COPY ./data/knowledge.yaml /src/
WORKDIR /src

CMD ["uvicorn", "knowledge:knowledgebase", "--host", "0.0.0.0"]
