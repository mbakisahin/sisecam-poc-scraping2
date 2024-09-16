FROM python:3.9-slim

RUN apt-get update && apt-get install -y \
    libx11-xcb1 \
    libxcomposite1 \
    libxrandr2 \
    libxcursor1 \
    libxdamage1 \
    libxfixes3 \
    libxi6 \
    libxtst6 \
    libnss3 \
    libgconf-2-4 \
    libxss1 \
    libatk1.0-0 \
    libgtk-3-0 \
    libasound2 \
    fonts-liberation \
    libappindicator1 \
    libdbusmenu-glib4 \
    libdbusmenu-gtk3-4 \
    libnspr4 \
    lsb-release \
    xdg-utils \
    wget \
    ca-certificates \
    fonts-liberation \
    libgbm1 \
    && apt-get clean && rm -rf /var/lib/apt/lists/*



WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["python", "main.py"]