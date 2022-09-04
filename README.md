# Проект «Yatube»
Yatube — это социальная сеть для блогеров с возможностью публикации личных дневников с системами комментирования и подписок.
## Приложение имеет следующий функционал:
* публикация поста с возможностью прикрепить к нему изображение;
* комментирование постов;
* подписки на авторов; 
* группировка постов;
* пагинация и кеширование. 
Код проекта покрыт unit-тестами.

## Технологии
* Python 3.7
* Django 2.2

## Установка и запуск

Клонировать репозиторий и перейти в него в командной строке:

```bash
git clone https://github.com/shakdv/hw05_final.git
```

```bash
cd hw05_final
```

Создать и активировать виртуальное окружение:
```bash
python -m venv env
```

```bash
source env/bin/activate
```

Обновить pip
```bash
python -m pip install --upgrade pip
```

Установить зависимости из файла requirements.txt:
```bash
pip install -r requirements.txt
```
Перейти в каталол проекта:
```bash
cd yatube
```

Выполнить миграции:
```bash
python manage.py migrate
```

Создаем суперпользователя:
```bash
python manage.py createsuperuser
```

Запустить проект:
```bash
python manage.py runserver
```
