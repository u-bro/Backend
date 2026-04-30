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

    async def generate_commission_receipt(
        self,
        client_name: str,
        amount: float,
        payment_id: Optional[str] = None,
        card_mask: Optional[str] = None,
        email: Optional[str] = None,
        created_at: Optional[datetime] = None,
    ) -> bytes:

        if created_at is None:
            created_at = datetime.now(timezone.utc)

        receipt_order_id = payment_id or "???"
        created_at_local = created_at.astimezone(timezone.utc)
        date_str = created_at_local.strftime("%d.%m.%Y")
        time_str = created_at_local.strftime("%H:%M")

        email_block = (
            f"<p>Чек направлен на электронную почту: {email}</p>" if email else (
                "<p>Чек не был направлен на электронную почту, так как адрес не указан.</p>"
                "<p>Вы можете запросить чек:<br>"
                "по телефону: +7 926 044-44-42<br>"
                "по email: ubrowork@mail.ru</p>"
            )
        )

        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset=\"UTF-8\">
            <title>Квитанция об оплате комиссии</title>
            <style>
                {self.DEFAULT_CSS}
                .section-title {{ font-weight: bold; margin-top: 16px; }}
                .divider {{ margin: 16px 0; }}
                .divider span {{ display: inline-block; letter-spacing: 1px; }}
                .mono {{ font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, \"Liberation Mono\", \"Courier New\", monospace; }}
            </style>
        </head>
        <body>
            <div class=\"header\">
                <h1>🧾 КВИТАНЦИЯ ОБ ОПЛАТЕ КОМИССИИ</h1>
                <p>Сервис: У-бро</p>
            </div>

            <div class=\"divider\"><span>⸻</span></div>

            <p><strong>Дата:</strong> {date_str}</p>
            <p><strong>Время:</strong> {time_str}</p>
            <p><strong>Номер операции:</strong> <span class=\"mono\">{receipt_order_id}</span></p>

            <div class=\"divider\"><span>⸻</span></div>

            <div class=\"section-title\">Плательщик</div>
            <p>{client_name}</p>

            <div class=\"divider\"><span>⸻</span></div>

            <div class=\"section-title\">Детали платежа</div>
            <p><strong>Назначение платежа:</strong><br>
               Комиссия сервиса «У-бро» за использование платформы</p>
            <p><strong>Сумма:</strong> {amount:.2f} ₽</p>
            <p><strong>Способ оплаты:</strong> Банковская карта</p>
            <p><strong>Маска карты:</strong> {card_mask or "—"}</p>
            <p><strong>Статус:</strong> Оплачено</p>

            <div class=\"divider\"><span>⸻</span></div>

            <div class=\"section-title\">Информация о чеке</div>
            <p>Фискальный чек сформирован с использованием онлайн-кассы.</p>
            {email_block}

            <div class=\"divider\"><span>⸻</span></div>

            <div class=\"section-title\">Оператор сервиса</div>
            <p>Общество с ограниченной ответственностью «ИНТЕГРАЦИЯ»</p>
            <p>ИНН: 7708421320<br>
               КПП: 770801001<br>
               ОГРН: 1237700454815</p>
            <p><strong>Юридический адрес:</strong><br>
               107140, Россия, г. Москва,<br>
               вн.тер.г. муниципальный округ Красносельский,<br>
               ул. Краснопрудная, д. 12/1, стр. 1, помещ. 1/6</p>

            <div class=\"divider\"><span>⸻</span></div>

            <div class=\"section-title\">Банковские реквизиты</div>
            <p>Банк: АО «ТБанк»<br>
               БИК: 044525974<br>
               р/с: 40702810910002090599<br>
               к/с: 30101810145250000974</p>

            <div class=\"divider\"><span>⸻</span></div>

            <div class=\"section-title\">Дополнительная информация</div>
            <p>Оплата стоимости поездки осуществляется пользователем напрямую водителю.</p>
            <p>Сервис «У-бро» не является исполнителем услуги перевозки.</p>
            <p>Настоящий документ не является кассовым чеком.</p>
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