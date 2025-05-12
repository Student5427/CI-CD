import logging
from pythonjsonlogger import jsonlogger
import sys

def setup_logging():
    # 1. Полностью сбрасываем все логгеры
    logging.root.handlers = []
    
    # 2. Создаём логгер приложения
    logger = logging.getLogger("backend")
    logger.setLevel(logging.DEBUG)
    logger.propagate = False  # Отключаем распространение
    
    # 3. Форматтер для JSON
    formatter = jsonlogger.JsonFormatter(
        '%(asctime)s %(name)s %(levelname)s %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 4. Обработчик для stdout (обязательно!)
    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setFormatter(formatter)
    logger.addHandler(stdout_handler)
    
    # 5. Обработчик для файла (если нужно)
    try:
        file_handler = logging.FileHandler("/var/log/backend/app.log")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except Exception as e:
        logger.error(f"Failed to create file handler: {e}")
    
    # 6. Отключаем логи Uvicorn и FastAPI
    for name in ["uvicorn", "uvicorn.error", "uvicorn.access", "fastapi"]:
        logging.getLogger(name).handlers = []
        logging.getLogger(name).propagate = False
    
    return logger

logger = setup_logging()