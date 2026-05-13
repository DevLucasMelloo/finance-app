FROM python:3.11-slim

WORKDIR /app

# Instala dependências do projeto principal + bot
COPY requirements.txt ./requirements_main.txt
COPY bot/requirements.txt ./requirements_bot.txt
RUN pip install --no-cache-dir -r requirements_main.txt -r requirements_bot.txt

# Copia todo o projeto
COPY . .

EXPOSE 8000

CMD ["uvicorn", "bot.main:app", "--host", "0.0.0.0", "--port", "8000"]
