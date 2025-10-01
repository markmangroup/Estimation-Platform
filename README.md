# Estimation Platform

Irrigation system estimation and proposal generation platform for contractors.

## Overview

This platform handles the complete proposal workflow including:
- Task code selection and CAD file uploads
- Material list generation and task mapping
- Labor cost calculation with location-based pricing
- Automated margin, tax, and profit calculations
- Proposal creation with grouping and customization
- Invoice generation with deposit/payment tracking

## Installation & Setup

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