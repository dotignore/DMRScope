# 📋 DMRScope - Installation Guide

## 🌍 Language / Язык
- [English](#english)
- [Русский](#русский)

---

## English

### 📋 Requirements

- **Python 3.8 or higher**
- **pip3** (Python Package Manager)
- **Git** (optional, for cloning the repository)
- **Internet connection** (for downloading packages)
- **1GB free disk space** (for Python packages)

### 🖥️ Windows Installation

#### Step 1: Install Python

1. Visit [python.org](https://www.python.org/downloads/)
2. Download Python 3.11 or higher
3. Run the installer
4. **⚠️ IMPORTANT:** Check the box "Add Python to PATH"
5. Click "Install Now"
6. Wait for installation to complete

#### Step 2: Verify Python Installation

Open Command Prompt and type:
```bash
python --version
```

You should see something like: `Python 3.11.x`

#### Step 3: Run the Installation Script

1. Navigate to the DMRScope folder
2. Double-click on **`install_windows.bat`**
3. Wait for the installation to complete

The script will:
- ✅ Check if Python is installed
- ✅ Create a virtual environment
- ✅ Upgrade pip
- ✅ Install all required packages from `requirements.txt`

#### Step 4: Run the Application

Once installation is complete, simply:
- **Double-click on `run_windows.bat`**

Or from Command Prompt:
```bash
run_windows.bat
```

### 🐧 Linux Installation

#### Step 1: Update System Packages

```bash
sudo apt-get update && sudo apt-get upgrade -y
```

#### Step 2: Install Python and pip3

```bash
sudo apt-get install -y python3 python3-pip python3-venv
```

Verify installation:
```bash
python3 --version
pip3 --version
```

#### Step 3: Make Installation Script Executable

Navigate to the DMRScope folder:
```bash
chmod +x install_linux.sh
chmod +x run_linux.sh
```

#### Step 4: Run the Installation Script

```bash
./install_linux.sh
```

Or:
```bash
bash install_linux.sh
```

The script will:
- ✅ Check if Python 3 is installed
- ✅ Install Python 3 if needed (with sudo)
- ✅ Create a virtual environment
- ✅ Install all required packages
- ✅ Set proper file permissions

#### Step 5: Run the Application

Once installation is complete:
```bash
./run_linux.sh
```

Or:
```bash
bash run_linux.sh
```

### 📦 Installed Packages

The installation script will install the following packages:

```
torch                   # Deep learning framework
torch-geometric         # PyTorch extension for graphs
py2neo                  # Neo4j connector
networkx                # Network/graph analysis
matplotlib              # Data visualization
igraph                  # Graph analysis
tkcalendar              # Calendar widget for GUI
pillow                  # Image processing
reportlab               # PDF generation
openpyxl                # Excel file handling
svgwrite                # SVG file generation
svglib                  # SVG support for graphics
```

### 🆘 Troubleshooting

#### Problem: "Python is not installed or not in PATH"
**Solution:** 
- Reinstall Python from [python.org](https://www.python.org/)
- Make sure to check "Add Python to PATH" during installation

#### Problem: "pip is not installed"
**Solution:**
- **Windows:** `python -m ensurepip`
- **Linux:** `sudo apt-get install python3-pip`

#### Problem: "Virtual environment creation failed"
**Solution:**
- **Windows:** `python -m venv venv`
- **Linux:** `python3 -m venv venv`

#### Problem: "Permission denied" on Linux
**Solution:** 
```bash
chmod +x install_linux.sh
chmod +x run_linux.sh
```

#### Problem: "No module named 'torch'" or other packages
**Solution:** 
- Rerun the installation script
- Or manually: `pip install -r requirements.txt`

### ✅ Verification

After installation, verify everything is working:

**Windows:**
```bash
venv\Scripts\python -c "import torch; print('Torch version:', torch.__version__)"
```

**Linux:**
```bash
source venv/bin/activate
python3 -c "import torch; print('Torch version:', torch.__version__)"
```

---

## Русский

### 📋 Требования

- **Python 3.8 или выше**
- **pip3** (менеджер пакетов Python)
- **Git** (опционально, для клонирования репозитория)
- **Интернет соединение** (для скачивания пакетов)
- **1GB свободного места** (для пакетов Python)

### 🖥️ Установка на Windows

#### Шаг 1: Установка Python

1. Перейдите на [python.org](https://www.python.org/downloads/)
2. Скачайте Python 3.11 или выше
3. Запустите установщик
4. **⚠️ ВАЖНО:** Отметьте "Add Python to PATH"
5. Нажмите "Install Now"
6. Дождитесь завершения установки

#### Шаг 2: Проверка установки Python

Откройте Command Prompt и введите:
```bash
python --version
```

Вы должны увидеть что-то вроде: `Python 3.11.x`

#### Шаг 3: Запуск скрипта установки

1. Перейдите в папку DMRScope
2. Дважды кликните на **`install_windows.bat`**
3. Дождитесь завершения установки

Скрипт выполнит:
- ✅ Проверку наличия Python
- ✅ Создание виртуального окружения
- ✅ Обновление pip
- ✅ Установку всех пакетов из `requirements.txt`

#### Шаг 4: Запуск приложения

После завершения установки просто:
- **Дважды кликните на `run_windows.bat`**

Или из Command Prompt:
```bash
run_windows.bat
```

### 🐧 Установка на Linux

#### Шаг 1: Обновление системных пакетов

```bash
sudo apt-get update && sudo apt-get upgrade -y
```

#### Шаг 2: Установка Python и pip3

```bash
sudo apt-get install -y python3 python3-pip python3-venv
```

Проверьте установку:
```bash
python3 --version
pip3 --version
```

#### Шаг 3: Установка прав исполнения

Перейдите в папку DMRScope:
```bash
chmod +x install_linux.sh
chmod +x run_linux.sh
```

#### Шаг 4: Запуск скрипта установки

```bash
./install_linux.sh
```

Или:
```bash
bash install_linux.sh
```

Скрипт выполнит:
- ✅ Проверку наличия Python 3
- ✅ Установку Python 3 при необходимости (с sudo)
- ✅ Создание виртуального окружения
- ✅ Установку всех пакетов
- ✅ Установку правильных прав доступа

#### Шаг 5: Запуск приложения

После завершения установки:
```bash
./run_linux.sh
```

Или:
```bash
bash run_linux.sh
```

### 📦 Устанавливаемые пакеты

Скрипт установки установит следующие пакеты:

```
torch                   # Фреймворк глубокого обучения
torch-geometric         # Расширение PyTorch для графов
py2neo                  # Коннектор для Neo4j
networkx                # Анализ сетей/графов
matplotlib              # Визуализация данных
igraph                  # Анализ графов
tkcalendar              # Виджет календаря для GUI
pillow                  # Обработка изображений
reportlab               # Генерация PDF
openpyxl                # Работа с Excel файлами
svgwrite                # Генерация SVG файлов
svglib                  # Поддержка SVG для графики
```

### 🆘 Решение проблем

#### Проблема: "Python is not installed or not in PATH"
**Решение:** 
- Переустановите Python с [python.org](https://www.python.org/)
- Убедитесь, что отмечена опция "Add Python to PATH"

#### Проблема: "pip is not installed"
**Решение:**
- **Windows:** `python -m ensurepip`
- **Linux:** `sudo apt-get install python3-pip`

#### Проблема: "Не удалось создать виртуальное окружение"
**Решение:**
- **Windows:** `python -m venv venv`
- **Linux:** `python3 -m venv venv`

#### Проблема: "Permission denied" на Linux
**Решение:** 
```bash
chmod +x install_linux.sh
chmod +x run_linux.sh
```

#### Проблема: "No module named 'torch'" или другие пакеты
**Решение:** 
- Перезапустите скрипт установки
- Или вручную: `pip install -r requirements.txt`

### ✅ Проверка

После установки проверьте, что всё работает:

**Windows:**
```bash
venv\Scripts\python -c "import torch; print('Torch version:', torch.__version__)"
```

**Linux:**
```bash
source venv/bin/activate
python3 -c "import torch; print('Torch version:', torch.__version__)"
```

---

## 📁 Project Structure

```
examplaone_krakenSDR_web/
├── install_windows.bat          # Установщик для Windows
├── run_windows.bat              # Запуск на Windows
├── install_linux.sh             # Установщик для Linux
├── run_linux.sh                 # Запуск на Linux
├── requirements.txt             # Список пакетов
├── README_INSTALL.md            # Этот файл (инструкция по установке)
├── run.py                       # Главное приложение
├── _00_0_convert.py
├── _00_3_convert.py
├── _01_visualization.py
├── _02_graphics.py
├── _03_group_connections.py
├── _04_help.py
└── config.ini                   # Конфигурация
```

## ❓ FAQ

**Q: Can I use a different version of Python?**
A: Yes, Python 3.8+ should work, but Python 3.11+ is recommended.

**Q: Do I need to reinstall packages after each run?**
A: No, install once with the setup script, then just use `run_windows.bat` or `run_linux.sh`.

**Q: What if the installation is slow?**
A: This is normal. torch and other packages are large. The first installation may take 10-30 minutes.

**Q: Can I run this without an internet connection?**
A: No, the first installation requires internet to download packages. Subsequent runs don't need internet.

---

## 📞 Support

For issues or questions, please check:
1. The troubleshooting section above
2. Python version compatibility
3. That all required tools are installed
4. That you have sufficient disk space

---

**Last Updated:** 2025
**Version:** 1.0
