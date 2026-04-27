
# Ozon-scraper

<img width="1920" height="1080" alt="image" src="https://github.com/user-attachments/assets/df6e8b0a-4098-4809-b9aa-5d2145c4ef2d" />


Приложение собирает данные по ссылкам и обрабатывает страницы параллельно, что ускоряет получение результатов.

---

## ⚙️ Возможности

- Парсинг товаров с Ozon по ссылкам
- Параллельная обработка страниц (ускоренный сбор данных)
- Получение:
  - цены
  - старой цены
  - скидки
  - рейтинга
  - количества отзывов
- Выгрузка данных в:
  - JSON
  - CSV
  - XLSX

---

## Установка

Установите Python 3.10+  
https://www.python.org/downloads/

Скачайте проект:

```bash
git clone https://github.com/BlackRaisons/Ozon-scraper.git
cd Ozon-scraper
```

Установите зависимости:

```bash
pip install -r requirements.txt
```

## Запуск

1. Запуск API сервера
   ```bash
   uvicorn Api.api:app --host 127.0.0.1 --port 8000 --reload
   ```

2.   Запуск интерфейса
   ```bash
  streamlit run Gui/gui.py
  ```

После запуска интерфейс будет доступен:

http://localhost:8501

## Вывод

данные можно будет экспортировать в разных форматов






cd Ozon-scraper

