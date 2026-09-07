FROM python:3.14

RUN groupadd --gid 10001 product-service && \
    useradd --uid 10001 \
            --gid 10001 \
            --create-home \
            --home-dir /home/produser \
            produser

WORKDIR /product-service

COPY --chown=produser:product-service pyproject.toml poetry.lock ./

RUN pip install poetry && \
    poetry config virtualenvs.create false && \
    poetry install --without test --no-root

COPY --chown=produser:product-service . .

ENV PYTHONPATH=/product-service

RUN chmod +x /product-service/entrypoint.sh

USER produser

EXPOSE 8000

ENTRYPOINT ["/product-service/entrypoint.sh"]