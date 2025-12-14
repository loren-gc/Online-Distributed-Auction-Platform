# nossa imagem base
FROM python:3.9-slim

# diretorio de trabalho no container
WORKDIR /app

# copia requisitos e instala tudo para o ambiente
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# copia todo código da pasta app para o container
# A estrutura ficará /app/app/...
COPY . .

# expõe a porta do Flask
EXPOSE 5000

# variáveis de ambiente padrão (serão sobrescritas pelo K8s)
ENV FLASK_APP=app/main.py

# Comando para rodar
CMD ["python", "-m", "app.main"]