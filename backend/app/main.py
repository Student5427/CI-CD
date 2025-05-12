import sentry_sdk
from fastapi import FastAPI, Request
from fastapi.routing import APIRoute
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from prometheus_fastapi_instrumentator import Instrumentator
from starlette.middleware.cors import CORSMiddleware
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor


from app.api.main import api_router
from app.core.config import settings
import logging
from logger_config import logger  # ваш кастомный логгер


def custom_generate_unique_id(route: APIRoute) -> str:
    if route.tags:
        return f"{route.tags[0]}-{route.name}"
    else:
        return f"no-tag-{route.name}"  # Или другое значение по умолчанию


if settings.SENTRY_DSN and settings.ENVIRONMENT != "local":
    sentry_sdk.init(dsn=str(settings.SENTRY_DSN), enable_tracing=True)


# Переопределяем корневой логгер
def override_root_logger():
    # 1. Отключаем все существующие обработчики
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)
    
    # 2. Копируем настройки из вашего логгера
    logging.root.handlers = logger.handlers
    logging.root.setLevel(logging.DEBUG)
    logging.root.propagate = False  # отключаем распространение

# Вызываем в начале работы приложения
override_root_logger()

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    generate_unique_id_function=custom_generate_unique_id,
)

# Улучшенная инициализация трейсинга
def setup_tracing():
    resource = Resource.create(attributes={
    "service.name": "backend-service",  # Должно быть точно так
    "service.version": "1.0.0",
    "deployment.environment": "production"
})
    
    provider = TracerProvider(resource=resource)
    trace.set_tracer_provider(provider)

    # Для gRPC (основной)
    #otlp_exporter = OTLPSpanExporter(
    #    endpoint="tempo:4317",  # Без http:// для gRPC
    #    insecure=True
    #)

     # Используем HTTP экспортер вместо gRPC
    otlp_exporter = OTLPSpanExporter(
    endpoint="http://jaeger:4317",  # Для Docker
    # endpoint="http://localhost:4317",  # Если запускаете вне Docker
    insecure=True
)
    
    provider.add_span_processor(
        BatchSpanProcessor(otlp_exporter)
    )

    # ИЛИ для HTTP (альтернатива)
    # otlp_exporter = OTLPSpanExporter(
    #     endpoint="http://tempo:4318/v1/traces",
    # )

    print(f"Tracing initialized. Service name: 'backend-service', Exporting to: http://jaeger:4317")
    
    FastAPIInstrumentor.instrument_app(app)
    RequestsInstrumentor().instrument()
    SQLAlchemyInstrumentor().instrument()

setup_tracing()

# Set all CORS enabled origins
# allow_origins=settings.all_cors_origins
if settings.all_cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(api_router, prefix=settings.API_V1_STR)
