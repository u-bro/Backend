from typing import Optional, Dict, Any
from datetime import datetime, timezone
from io import BytesIO
import logging

logger = logging.getLogger(__name__)

try:
    from weasyprint import HTML, CSS
    WEASYPRINT_AVAILABLE = True
except ImportError:
    WEASYPRINT_AVAILABLE = False
    logger.warning("WeasyPrint not installed. PDF generation will use fallback method.")

try:
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    logger.warning("ReportLab not installed. PDF generation may be limited.")


class PDFGenerator:
    DEFAULT_CSS = """
        @page {
            size: A4;
            margin: 20mm;
        }
        body {
            font-family: Arial, sans-serif;
            font-size: 12pt;
            line-height: 1.5;
            color: #333;
        }
        h1 {
            color: #2c3e50;
            border-bottom: 2px solid #3498db;
            padding-bottom: 10px;
        }
        h2 {
            color: #34495e;
        }
        .header {
            text-align: center;
            margin-bottom: 30px;
        }
        .logo {
            font-size: 24pt;
            font-weight: bold;
            color: #3498db;
        }
        .receipt-info {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 5px;
            margin: 20px 0;
        }
        .receipt-info p {
            margin: 5px 0;
        }
        .amount {
            font-size: 18pt;
            font-weight: bold;
            color: #27ae60;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }
        th, td {
            border: 1px solid #ddd;
            padding: 10px;
            text-align: left;
        }
        th {
            background: #3498db;
            color: white;
        }
        tr:nth-child(even) {
            background: #f2f2f2;
        }
        .footer {
            margin-top: 50px;
            text-align: center;
            font-size: 10pt;
            color: #666;
        }
    """
    
    def __init__(self):
        self.weasyprint_available = WEASYPRINT_AVAILABLE
        self.reportlab_available = REPORTLAB_AVAILABLE
    
    async def generate_ride_receipt(
        self,
        ride_id: int,
        client_name: str,
        driver_name: str,
        pickup_address: str,
        dropoff_address: str,
        fare: float,
        distance_km: Optional[float] = None,
        duration_min: Optional[int] = None,
        payment_method: str = "Наличные",
        created_at: Optional[datetime] = None
    ) -> bytes:
        
        if created_at is None:
            created_at = datetime.now(timezone.utc)
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Квитанция #{ride_id}</title>
        </head>
        <body>
            <div class="header">
                <div class="logo">🚗 U-BRO TAXI</div>
                <p>Квитанция об оплате поездки</p>
            </div>
            
            <h1>Квитанция #{ride_id}</h1>
            
            <div class="receipt-info">
                <p><strong>Дата:</strong> {created_at.strftime('%d.%m.%Y %H:%M')}</p>
                <p><strong>Клиент:</strong> {client_name}</p>
                <p><strong>Водитель:</strong> {driver_name}</p>
            </div>
            
            <h2>Детали поездки</h2>
            <table>
                <tr>
                    <th>Параметр</th>
                    <th>Значение</th>
                </tr>
                <tr>
                    <td>Адрес подачи</td>
                    <td>{pickup_address}</td>
                </tr>
                <tr>
                    <td>Адрес назначения</td>
                    <td>{dropoff_address}</td>
                </tr>
                {f'<tr><td>Расстояние</td><td>{distance_km:.1f} км</td></tr>' if distance_km else ''}
                {f'<tr><td>Время в пути</td><td>{duration_min} мин</td></tr>' if duration_min else ''}
                <tr>
                    <td>Способ оплаты</td>
                    <td>{payment_method}</td>
                </tr>
            </table>
            
            <div class="receipt-info">
                <p><strong>Итого к оплате:</strong></p>
                <p class="amount">{fare:.2f} ₽</p>
            </div>
            
            <div class="footer">
                <p>Спасибо за использование U-BRO TAXI!</p>
                <p>Служба поддержки: support@u-bro.ru</p>
            </div>
        </body>
        </html>
        """
        
        return await self._generate_pdf_from_html(html)

    async def generate_commission_receipt(
        self,
        ride_id: int,
        client_name: str,
        amount: float,
        purpose: str,
        operation_id: Optional[str] = None,
        created_at: Optional[datetime] = None,
    ) -> bytes:

        if created_at is None:
            created_at = datetime.now(timezone.utc)

        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset=\"UTF-8\">
            <title>Квитанция комиссии #{ride_id}</title>
        </head>
        <body>
            <div class=\"header\">
                <div class=\"logo\">U-BRO TAXI</div>
                <p>Квитанция об оплате комиссии</p>
            </div>

            <h1>Комиссия за поездку #{ride_id}</h1>

            <div class=\"receipt-info\">
                <p><strong>Дата:</strong> {created_at.strftime('%d.%m.%Y %H:%M')}</p>
                <p><strong>Клиент:</strong> {client_name}</p>
                <p><strong>Назначение:</strong> {purpose}</p>
                {f'<p><strong>Operation ID:</strong> {operation_id}</p>' if operation_id else ''}
            </div>

            <div class=\"receipt-info\">
                <p><strong>Сумма комиссии:</strong></p>
                <p class=\"amount\">{amount:.2f} ₽</p>
            </div>

            <div class=\"footer\">
                <p>Спасибо за использование U-BRO TAXI!</p>
                <p>Служба поддержки: support@u-bro.ru</p>
            </div>
        </body>
        </html>
        """

        return await self._generate_pdf_from_html(html)
    
    async def _generate_pdf_from_html(self, html: str) -> bytes:
        
        if self.weasyprint_available:
            return self._generate_with_weasyprint(html)
        elif self.reportlab_available:
            return self._generate_fallback(html)
        else:
            raise RuntimeError("No PDF generation library available. Install weasyprint or reportlab.")
    
    def _generate_with_weasyprint(self, html: str) -> bytes:
        html_doc = HTML(string=html)
        pdf = html_doc.write_pdf()
        return pdf
    
    def _generate_fallback(self, html: str) -> bytes:
        buffer = BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4 
        c.setFont("Helvetica-Bold", 16)
        c.drawString(50, height - 50, "U-BRO TAXI")
        c.setFont("Helvetica", 12)
        c.drawString(50, height - 80, "PDF документ")
        c.drawString(50, height - 110, f"Сгенерирован: {datetime.now(timezone.utc).strftime('%d.%m.%Y %H:%M')}")
        c.drawString(50, height - 150, "Для полноценной генерации установите WeasyPrint")
        
        c.save()
        buffer.seek(0)
        return buffer.read()
                                        
pdf_generator = PDFGenerator()
