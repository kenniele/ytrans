FROM python:3.12-alpine AS builder

COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir --target=/deps -r /tmp/requirements.txt \
    && find /deps -name '*.pyc' -delete \
    && find /deps -name '__pycache__' -type d -exec rm -rf {} + 2>/dev/null; true

FROM alpine:3.21

RUN apk add --no-cache python3 \
    && rm -rf /usr/lib/python3.12/ensurepip \
              /usr/lib/python3.12/idlelib \
              /usr/lib/python3.12/tkinter \
              /usr/lib/python3.12/turtle* \
              /usr/lib/python3.12/turtledemo \
              /usr/lib/python3.12/pydoc_data \
              /usr/lib/python3.12/lib2to3 \
              /usr/lib/python3.12/unittest \
              /usr/lib/python3.12/distutils \
              /usr/lib/python3.12/test \
              /usr/lib/python3.12/multiprocessing \
              /usr/lib/python3.12/xmlrpc \
              /usr/lib/python3.12/ctypes \
              /usr/lib/python3.12/curses \
              /usr/lib/python3.12/dbm \
              /usr/lib/python3.12/sqlite3 \
              /usr/lib/python3.12/venv \
              /usr/lib/python3.12/wsgiref \
              /usr/lib/python3.12/asyncio \
              /usr/lib/python3.12/concurrent \
              /usr/lib/python3.12/tomllib \
              /usr/lib/python3.12/zipapp.py \
              /usr/lib/python3.12/doctest.py \
              /usr/lib/python3.12/pydoc.py \
              /usr/lib/python3.12/mailbox.py \
              /usr/lib/python3.12/imaplib.py \
              /usr/lib/python3.12/smtplib.py \
              /usr/lib/python3.12/poplib.py \
              /usr/lib/python3.12/ftplib.py \
              /usr/lib/python3.12/telnetlib.py \
              /usr/lib/python3.12/nntplib.py \
    && find /usr/lib/python3.12 -name '*.pyc' -delete \
    && find /usr/lib/python3.12 -name '__pycache__' -type d -exec rm -rf {} + 2>/dev/null; true \
    && adduser -D appuser \
    && mkdir /obsidian && chown appuser:appuser /obsidian

COPY --from=builder /deps /deps
COPY transcript.py /app/transcript.py

ENV PYTHONPATH=/deps
USER appuser

ENTRYPOINT ["python3", "/app/transcript.py"]
