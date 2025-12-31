"""
Documents Router
API для генерации и скачивания PDF документов
"""

from fastapi import APIRouter, HTTPException, Request, Query
from fastapi.responses import Response
from typing import Optional
from datetime import datetime, timedelta
import logging

from app.services.pdf_generator import pdf_generator

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/documents/ride/{ride_id}/receipt")
async def get_ride_receipt(
    request: Request,
    ride_id: int,
    download: bool = Query(False, description="Скачать файл вместо отображения")
):
    # TODO:
    try:
        pdf_bytes = await pdf_generator.generate_ride_receipt(
            ride_id=ride_id,
            client_name="Иван Иванов",  # TODO: 
            driver_name="Пётр Петров",  # TODO: 
            pickup_address="Москва, ул. Ленина 1",  # TODO: 
            dropoff_address="Москва, ул. Пушкина 10",  # TODO: 
            fare=500.00,  # TODO: 
            distance_km=12.5,
            duration_min=25,
            payment_method="Наличные"
        )
    except Exception as e:
        logger.error(f"Failed to generate receipt PDF: {e}")
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {str(e)}")
    
    headers = {}
    if download:
        headers["Content-Disposition"] = f"attachment; filename=receipt_{ride_id}.pdf"
    else:
        headers["Content-Disposition"] = f"inline; filename=receipt_{ride_id}.pdf"
    
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers=headers
    )


@router.get("/documents/driver/{driver_id}/report")
async def get_driver_report(
    request: Request,
    driver_id: int,
    period_days: int = Query(30, ge=1, le=365, description="Период отчёта в днях"),
    download: bool = Query(False)
):

    period_end = datetime.utcnow()
    period_start = period_end - timedelta(days=period_days)
    
    test_rides = [
        {"id": 101, "date": "15.12.2025", "route": "Ленина → Пушкина", "fare": 350.00},
        {"id": 102, "date": "16.12.2025", "route": "Гагарина → Мира", "fare": 520.00},
        {"id": 103, "date": "17.12.2025", "route": "Центр → Аэропорт", "fare": 1200.00},
    ]
    
    try:
        pdf_bytes = await pdf_generator.generate_driver_report(
            driver_name="Пётр Петров",  # TODO: из БД
            period_start=period_start,
            period_end=period_end,
            rides=test_rides,
            total_earnings=2070.00,
            total_commission=310.50
        )
    except Exception as e:
        logger.error(f"Failed to generate driver report PDF: {e}")
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {str(e)}")
    
    headers = {}
    filename = f"driver_report_{driver_id}_{period_start.strftime('%Y%m%d')}_{period_end.strftime('%Y%m%d')}.pdf"
    if download:
        headers["Content-Disposition"] = f"attachment; filename={filename}"
    else:
        headers["Content-Disposition"] = f"inline; filename={filename}"
    
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers=headers
    )


@router.get("/documents/user/{user_id}/balance")
async def get_balance_statement(
    request: Request,
    user_id: int,
    download: bool = Query(False)
):

    test_transactions = [
        {"id": 1, "date": "10.12.2025", "is_withdraw": False, "amount": 1000.00},
        {"id": 2, "date": "12.12.2025", "is_withdraw": True, "amount": 350.00},
        {"id": 3, "date": "15.12.2025", "is_withdraw": False, "amount": 500.00},
        {"id": 4, "date": "17.12.2025", "is_withdraw": True, "amount": 520.00},
    ]
    
    try:
        pdf_bytes = await pdf_generator.generate_balance_statement(
            user_name="Иван Иванов", 
            current_balance=630.00, 
            transactions=test_transactions
        )
    except Exception as e:
        logger.error(f"Failed to generate balance statement PDF: {e}")
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {str(e)}")
    
    headers = {}
    filename = f"balance_{user_id}_{datetime.utcnow().strftime('%Y%m%d')}.pdf"
    if download:
        headers["Content-Disposition"] = f"attachment; filename={filename}"
    else:
        headers["Content-Disposition"] = f"inline; filename={filename}"
    
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers=headers
    )


@router.get("/documents/health")
async def documents_health():
    return {
        "status": "ok",
        "weasyprint_available": pdf_generator.weasyprint_available,
        "reportlab_available": pdf_generator.reportlab_available
    }


documents_router = router
