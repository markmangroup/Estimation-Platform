## Steps to install and run Laurel Project

---

### 1.Create virtual environment

```
python3 -m venv venv
```

### 2.Activate virtual environment

```
source venv/bin/activate
```

### 3.Update pip to latest version

```
python3 -m pip install --upgrade pip setuptools wheel
```

### 4.Install requirements

```
pip3 install -r requirements.txt
```

### 5.Make migrations

```
python3 manage.py makemigrations
```

### 6.Migrate changes

```
python3 manage.py migrate
```

### 7. Start Server

```
python3 manage.py runserver
```

### 8. Start Celery
```
celery -A laurel worker -l info --beat --scheduler django
```