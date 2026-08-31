FROM python:3.14

WORKDIR /product-service

COPY pyproject.toml poetry.lock ./

RUN pip install poetry && \
    poetry config virtualenvs.create false && \
    poetry install --without test --no-root

COPY . .

ENV PYTHONPATH=/product-service

EXPOSE 8000

RUN chmod +x /product-service/entrypoint.sh

ENTRYPOINT ["/product-service/entrypoint.sh"]