"""Seed realistic data for the KoopAkıl demo.

Scenario: a regional agriculture cooperative ("Anadolu Üretici Kooperatifi")
selling 25+ SKUs to retail and small B2B accounts. The seed produces:
  * 5 users covering every role.
  * 25 products with realistic Turkish names + stock states (some critical).
  * 18 orders spanning the last 14 days.
  * 15 shipments — including 3 deliberately delayed ones for the AI demo.
  * 6 tasks (mix of open + in-progress).
  * 4 system alerts.
  * 3 knowledge-base documents (FAQ, shipping policy, returns) with chunks.

Idempotent: if the admin user already exists, the seeder returns early.
"""

from __future__ import annotations

import json
import logging
import random
from datetime import datetime, timedelta, timezone
from typing import List

from sqlalchemy import select

from app.ai.rag.chunker import chunk_text
from app.ai.services.gemini_service import gemini_service
from app.core.security import hash_password
from app.database import AsyncSessionLocal
from app.models.alert import Alert, AlertSeverity
from app.models.conversation import Conversation, Message, MessageRole
from app.models.document import Document, DocumentChunk
from app.models.order import Order, OrderItem, OrderStatus
from app.models.product import Product
from app.models.shipment import Shipment, ShipmentLog, ShipmentStatus
from app.models.task import Task, TaskPriority, TaskStatus
from app.models.user import User, UserRole

logger = logging.getLogger("koopakil.seed")
random.seed(7)


# ---------------------------------------------------------------------
# Static data
# ---------------------------------------------------------------------
_USERS = [
    ("admin@koopakil.tr", "admin1234", "Sistem Yöneticisi", UserRole.ADMIN, "+90 555 000 0001"),
    ("yonetici@koopakil.tr", "admin1234", "Aslı Demir", UserRole.MANAGER, "+90 555 000 0002"),
    ("depo@koopakil.tr", "admin1234", "Mehmet Yılmaz", UserRole.WAREHOUSE, "+90 555 000 0003"),
    ("kurye@koopakil.tr", "admin1234", "Ali Kara", UserRole.COURIER, "+90 555 000 0004"),
    ("destek@koopakil.tr", "admin1234", "Ezgi Şahin", UserRole.SUPPORT, "+90 555 000 0005"),
    # Müşteri demo hesabı — bu e-posta seed siparişlerindeki musteri1@example.com
    # yerine kullanılır ki müşteri panelinde gerçek siparişler görünsün.
    ("musteri@koopakil.tr", "admin1234", "Zeynep Aydın", UserRole.CUSTOMER, "+90 555 000 0006"),
]


_PRODUCTS = [
    # (sku, name, category, unit, price, cost, stock, threshold, reorder, supplier)
    ("DMS-001", "Organik Domates Salçası 700g", "gıda", "adet", 79.90, 42.00, 6, 20, 80, "Anadolu Tarım"),
    ("ZEY-001", "Erken Hasat Zeytinyağı 1L", "gıda", "adet", 219.00, 138.00, 4, 15, 60, "Ege Bağcılık"),
    ("BAL-001", "Çiçek Balı 850g", "gıda", "adet", 189.00, 110.00, 22, 10, 40, "Karadeniz Arıcılık"),
    ("BAL-002", "Kestane Balı 450g", "gıda", "adet", 159.00, 92.00, 18, 8, 30, "Karadeniz Arıcılık"),
    ("PEY-001", "Ezine İnek Peyniri 750g", "gıda", "adet", 269.00, 165.00, 12, 10, 40, "Ezine Süt"),
    ("PEY-002", "Köy Tulum Peyniri 500g", "gıda", "adet", 229.00, 145.00, 9, 10, 40, "Erzincan Mandıra"),
    ("KAH-001", "Türk Kahvesi 250g", "gıda", "adet", 89.00, 48.00, 56, 25, 80, "İstanbul Kahveci"),
    ("CAY-001", "Siyah Çay 1kg", "gıda", "adet", 129.00, 75.00, 38, 20, 80, "Rize Çay Kooperatifi"),
    ("KOY-001", "Köy Yumurtası 30'lu", "gıda", "adet", 99.00, 60.00, 14, 12, 60, "Anadolu Çiftliği"),
    ("UNN-001", "Tam Buğday Unu 5kg", "gıda", "adet", 119.00, 70.00, 26, 10, 40, "Anadolu Değirmen"),
    ("BUL-001", "Köftelik Bulgur 1kg", "gıda", "adet", 65.00, 38.00, 84, 30, 100, "Gaziantep Hububat"),
    ("MER-001", "Yeşil Mercimek 1kg", "gıda", "adet", 79.00, 45.00, 7, 15, 60, "Çukurova Tahıl"),
    ("KUR-001", "Kuru Fasulye 1kg", "gıda", "adet", 89.00, 52.00, 32, 15, 60, "Çukurova Tahıl"),
    ("FIN-001", "Çiğ Fındık 500g", "gıda", "adet", 199.00, 125.00, 11, 10, 40, "Giresun Fındık"),
    ("CEV-001", "Ceviz İçi 500g", "gıda", "adet", 249.00, 160.00, 5, 8, 30, "Bitlis Kuruyemiş"),
    ("BAD-001", "Çiğ Badem 500g", "gıda", "adet", 229.00, 148.00, 13, 8, 30, "Datça Bademleri"),
    ("REC-001", "Vişne Reçeli 380g", "gıda", "adet", 79.00, 42.00, 41, 15, 50, "Anadolu Tarım"),
    ("REC-002", "Çilek Reçeli 380g", "gıda", "adet", 75.00, 40.00, 35, 15, 50, "Anadolu Tarım"),
    ("SEK-001", "Ev Yapımı Şekerleme 200g", "gıda", "adet", 119.00, 70.00, 20, 10, 40, "Konya Şekerleme"),
    ("SAB-001", "Defne Sabunu 4'lü", "el sanatları", "paket", 149.00, 80.00, 9, 8, 30, "Antakya Kooperatifi"),
    ("SAB-002", "Zeytinyağlı Sabun 4'lü", "el sanatları", "paket", 139.00, 75.00, 16, 8, 30, "Ayvalık Kooperatifi"),
    ("TEK-001", "El Dokuması Yastık", "el sanatları", "adet", 449.00, 270.00, 6, 4, 12, "Denizli Dokuma"),
    ("TEK-002", "Pamuklu Sofra Bezi", "el sanatları", "adet", 299.00, 175.00, 11, 6, 20, "Buldan Dokumacıları"),
    ("CAM-001", "El Yapımı Cam Kupa", "el sanatları", "adet", 159.00, 95.00, 24, 10, 40, "Kütahya Sanatçıları"),
    ("BAH-001", "Doğal Bahar Çayı Karışımı 250g", "gıda", "adet", 169.00, 100.00, 8, 10, 40, "Toros Bitkileri"),
]


_DOCUMENTS = [
    (
        "Sıkça Sorulan Sorular",
        "faq.txt",
        "Müşterilerimizin en sık sorduğu soruların yanıtlarını bu rehberde bir araya getirdik.\n\n"
        "Çalışma saatleri: Müşteri hizmetleri hafta içi 09:00 - 18:00 arasında hizmet vermektedir. "
        "Cumartesi günleri 10:00 - 14:00 arasında acil destek hattımız aktiftir. Pazar günü kapalıdır.\n\n"
        "Ödeme yöntemleri: Tüm büyük kredi kartları, banka havalesi ve kapıda ödeme seçenekleri "
        "sunulmaktadır. Kapıda ödeme yalnızca 1000 TL altındaki siparişler için geçerlidir.\n\n"
        "Sipariş takibi: Her sipariş için bir takip kodu üretilir. Kullanıcı panelinden anlık "
        "kargo durumunu görüntüleyebilirsiniz. KoopAkıl AI asistanı 7/24 anlık sipariş ve "
        "kargo sorgulaması yapabilir.\n\n"
        "Stok bilgisi: Ürün sayfasındaki stok durumu canlıdır. 'Stokta' yazan ürünler en geç "
        "1 iş günü içinde kargoya verilir.",
    ),
    (
        "Kargo Politikası",
        "kargo-politikasi.txt",
        "Tüm yurt içi siparişler Yurtiçi Kargo, Aras Kargo ve MNG Kargo aracılığıyla "
        "gönderilmektedir. İstanbul içi siparişler genelde 1 iş günü, yurt içi diğer iller "
        "2-4 iş günü içinde teslim edilir.\n\n"
        "Kargo ücreti: 750 TL ve üzeri siparişlerde kargo ücretsizdir. Altındaki siparişlerde "
        "39 TL kargo bedeli uygulanır.\n\n"
        "Gecikme: Kargo firması kaynaklı gecikmelerde KoopAkıl AI sistemi 48 saati aşan "
        "duraksamaları otomatik olarak tespit eder. Müşteri talep etmeden önce hem müşteriye "
        "hem işletme yöneticisine bildirim gönderilir.\n\n"
        "Kayıp veya hasar: Teslimat sırasında hasarlı veya eksik ürün olması durumunda 48 saat "
        "içinde müşteri hizmetlerine başvurunuz; tüm masraflar tarafımızdan karşılanır.",
    ),
    (
        "İade ve Değişim",
        "iade-degisim.txt",
        "Tüketicinin Korunması Hakkında Kanun gereğince teslim tarihinden itibaren 14 gün "
        "içinde herhangi bir gerekçe göstermeden iade hakkınız vardır.\n\n"
        "İade adımları: (1) Üye panelinizden ilgili siparişe gidip 'İade talebi oluştur' butonuna "
        "tıklayın. (2) Sistem otomatik olarak kargo etiketi e-postalar. (3) Ürünü orijinal "
        "ambalajıyla anlaşmalı kargoya teslim edin. (4) Ürün depomuza ulaştıktan sonra 3 iş "
        "günü içinde kontrol edilir ve ödeme iadesi başlatılır.\n\n"
        "Değişim: Bedeni veya rengi farklı ürünle değişim talep ediyorsanız iade sürecini "
        "tamamladıktan sonra yeni siparişinizi oluşturmanız yeterlidir. Karma sipariş yapan "
        "müşterilerimize manuel destek sunulmaktadır.\n\n"
        "Hijyen ürünleri (kişisel bakım, kozmetik) açılmış ise iade kabul edilmez.",
    ),
]


# ---------------------------------------------------------------------
# Seed runner
# ---------------------------------------------------------------------
async def seed_database() -> None:
    async with AsyncSessionLocal() as db:
        # Idempotent guard.
        existing = await db.execute(select(User).where(User.email == _USERS[0][0]))
        if existing.scalar_one_or_none():
            logger.debug("Seed: admin user already exists, skipping.")
            return

        # ----- Users --------------------------------------------------
        users: List[User] = []
        for email, password, full_name, role, phone in _USERS:
            user = User(
                email=email,
                hashed_password=hash_password(password),
                full_name=full_name,
                role=role,
                phone=phone,
            )
            db.add(user)
            users.append(user)
        await db.flush()

        # ----- Products ----------------------------------------------
        products: List[Product] = []
        for (
            sku,
            name,
            category,
            unit,
            price,
            cost,
            stock,
            threshold,
            reorder,
            supplier,
        ) in _PRODUCTS:
            product = Product(
                sku=sku,
                name=name,
                category=category,
                unit=unit,
                price=price,
                cost=cost,
                stock_qty=stock,
                reorder_threshold=threshold,
                reorder_quantity=reorder,
                supplier_name=supplier,
                supplier_email=f"satis@{supplier.lower().replace(' ', '')}.tr",
                description=f"{name} — yerel üretici garantili.",
            )
            db.add(product)
            products.append(product)
        await db.flush()

        # ----- Orders + items + shipments ----------------------------
        cities = [
            ("İstanbul", "Kadıköy"),
            ("İstanbul", "Beşiktaş"),
            ("Ankara", "Çankaya"),
            ("İzmir", "Karşıyaka"),
            ("Bursa", "Nilüfer"),
            ("Antalya", "Muratpaşa"),
            ("Konya", "Selçuklu"),
            ("Eskişehir", "Tepebaşı"),
        ]
        carriers = ["Yurtiçi Kargo", "Aras Kargo", "MNG Kargo"]
        statuses = [
            OrderStatus.PENDING,
            OrderStatus.PREPARING,
            OrderStatus.READY,
            OrderStatus.SHIPPED,
            OrderStatus.SHIPPED,
            OrderStatus.DELIVERED,
            OrderStatus.DELIVERED,
            OrderStatus.DELIVERED,
        ]
        now = datetime.now(timezone.utc)
        orders: List[Order] = []

        for i in range(18):
            order_age_days = random.randint(0, 13)
            city, district = random.choice(cities)
            status = random.choice(statuses)
            # İlk 5 siparişi demo müşterimize ata — müşteri panelinde dolu
            # bir geçmiş görünmesini sağlar.
            is_demo_customer = i < 5
            customer_email = (
                "musteri@koopakil.tr" if is_demo_customer else f"musteri{i+1}@example.com"
            )
            customer_name = (
                "Zeynep Aydın"
                if is_demo_customer
                else random.choice(
                    [
                        "Selin Yıldız",
                        "Mert Aksoy",
                        "Burcu Polat",
                        "Cem Aydın",
                        "Deniz Kara",
                        "Ece Erdem",
                        "Onur Aksu",
                        "Tuğçe Şen",
                    ]
                )
            )
            order = Order(
                order_code=f"KOP-{(1000 + i):05d}",
                customer_name=customer_name,
                customer_email=customer_email,
                customer_phone=f"+90 5{random.randint(30, 59)} {random.randint(100, 999)} {random.randint(1000, 9999)}",
                shipping_address=f"{district} mah. No:{random.randint(1, 250)}",
                shipping_city=city,
                status=status,
                total_amount=0.0,
                created_at=now - timedelta(days=order_age_days, hours=random.randint(0, 12)),
            )
            db.add(order)
            await db.flush()

            line_items = random.sample(products, k=random.randint(1, 4))
            total = 0.0
            for p in line_items:
                qty = random.choice([1, 1, 2, 2, 3])
                db.add(
                    OrderItem(
                        order_id=order.id,
                        product_id=p.id,
                        quantity=qty,
                        unit_price=p.price,
                    )
                )
                total += qty * p.price
            order.total_amount = round(total, 2)
            orders.append(order)

            # Make a shipment for non-pending orders.
            if status in (OrderStatus.SHIPPED, OrderStatus.DELIVERED, OrderStatus.READY):
                await _make_shipment(db, order, status, carriers, now)

        await db.flush()

        # ----- Extra deliberately-delayed shipments for the demo -----
        for i in range(3):
            tracking = f"KOP-RISK-{i:03d}"
            shipment = Shipment(
                tracking_code=tracking,
                order_id=None,
                carrier=random.choice(carriers),
                origin_city="İstanbul",
                destination_city=random.choice([c[0] for c in cities]),
                current_location="Transfer Merkezi - Ankara",
                status=ShipmentStatus.DELAYED,
                risk_score=0.78,
                ai_summary="Kargo 52 saattir aynı transfer merkezinde bekliyor.",
                estimated_delivery=now + timedelta(days=2),
                created_at=now - timedelta(days=5),
                updated_at=now - timedelta(hours=52),
            )
            db.add(shipment)
            await db.flush()
            db.add_all(
                [
                    ShipmentLog(
                        shipment_id=shipment.id,
                        event="Kargo oluşturuldu",
                        location="İstanbul Depo",
                        created_at=now - timedelta(days=5),
                    ),
                    ShipmentLog(
                        shipment_id=shipment.id,
                        event="Transfere alındı",
                        location="Transfer Merkezi - Ankara",
                        created_at=now - timedelta(days=3),
                    ),
                    ShipmentLog(
                        shipment_id=shipment.id,
                        event="Beklemede",
                        location="Transfer Merkezi - Ankara",
                        note="52+ saat hareket yok",
                        created_at=now - timedelta(hours=52),
                    ),
                ]
            )

        # ----- Tasks -------------------------------------------------
        tasks_data = [
            (
                "Sabah operasyon brifingini incele",
                "Yönetici özet raporunu kontrol et ve kritik aksiyonları onayla.",
                TaskPriority.HIGH,
                "manager",
            ),
            (
                "KOP-RISK-000 kargosu için müşteri bilgilendirmesi",
                "Gecikme riski yüksek; müşteriye proaktif SMS gönder.",
                TaskPriority.CRITICAL,
                "support",
            ),
            (
                "Domates Salçası tedarikçi siparişi",
                "DMS-001 SKU'sunda stok kritik eşik altına düştü.",
                TaskPriority.HIGH,
                "warehouse",
            ),
            (
                "Bugünkü 8 paketi hazırla",
                "Öncelikli siparişler önce; KAH-001 ve BAL-001 ürünleri yer alıyor.",
                TaskPriority.MEDIUM,
                "warehouse",
            ),
            (
                "Kadıköy-Üsküdar-Beşiktaş rota teslimatı",
                "AI tarafından optimize edilmiş 6 paketlik rota.",
                TaskPriority.MEDIUM,
                "courier",
            ),
            (
                "Haftalık satış raporunu yöneticilere ilet",
                "Salı saat 10:00'a kadar PDF olarak gönder.",
                TaskPriority.LOW,
                "support",
            ),
        ]
        for title, desc, prio, role in tasks_data:
            db.add(
                Task(
                    title=title,
                    description=desc,
                    status=TaskStatus.OPEN,
                    priority=prio,
                    assignee_role=role,
                    ai_generated=True,
                    due_date=now + timedelta(days=1),
                )
            )

        # ----- Alerts ------------------------------------------------
        db.add_all(
            [
                Alert(
                    title="Kritik stok: Domates Salçası",
                    message="DMS-001 mevcut 6 adet — yeniden sipariş eşiği 20.",
                    category="inventory",
                    severity=AlertSeverity.HIGH,
                    source="ai",
                ),
                Alert(
                    title="Kargo gecikmesi: KOP-RISK-000",
                    message="52 saattir aynı transfer merkezinde — proaktif aksiyon önerilir.",
                    category="logistics",
                    severity=AlertSeverity.CRITICAL,
                    source="ai",
                ),
                Alert(
                    title="Yeni AI içgörü hazır",
                    message="Önümüzdeki hafta için satış tahminleri güncellendi.",
                    category="analytics",
                    severity=AlertSeverity.INFO,
                    source="ai",
                ),
                Alert(
                    title="Tedarikçi yanıtı bekleniyor",
                    message="Anadolu Tarım'a gönderilen siparişe henüz dönüş alınamadı.",
                    category="procurement",
                    severity=AlertSeverity.WARNING,
                    source="system",
                ),
            ]
        )

        # ----- Sample conversation ----------------------------------
        convo = Conversation(
            session_id="sess_demo_main",
            title="Müşteri Destek — Sipariş Sorgusu",
            channel="web",
        )
        db.add(convo)
        await db.flush()
        db.add_all(
            [
                Message(
                    conversation_id=convo.id,
                    role=MessageRole.USER,
                    content="Merhaba, 128 numaralı siparişim ne zaman gelir?",
                ),
                Message(
                    conversation_id=convo.id,
                    role=MessageRole.ASSISTANT,
                    content=(
                        "Siparişinizi sistemde sorguladım. Şu anda kargo işlemleri devam "
                        "ediyor ve tahmini teslim süresi 1-2 iş günüdür. Kargo takip "
                        "kodunuzu hesabınızdaki 'Kargolarım' bölümünden takip edebilirsiniz."
                    ),
                    confidence=0.9,
                    sources_json=json.dumps(
                        [
                            {
                                "type": "document",
                                "label": "Kargo Politikası",
                                "reference": "doc:2#0",
                            }
                        ],
                        ensure_ascii=False,
                    ),
                    latency_ms=320,
                ),
            ]
        )

        # ----- Knowledge-base documents ------------------------------
        for title, filename, content in _DOCUMENTS:
            doc = Document(
                title=title,
                filename=filename,
                mime_type="text/plain",
                category="kurumsal",
                size_bytes=len(content.encode("utf-8")),
                chunk_count=0,
                content_preview=content[:500],
            )
            db.add(doc)
            await db.flush()
            chunks = chunk_text(content)
            embeddings = await gemini_service.embed([c.content for c in chunks])
            for chunk, emb in zip(chunks, embeddings):
                db.add(
                    DocumentChunk(
                        document_id=doc.id,
                        chunk_index=chunk.index,
                        content=chunk.content,
                        embedding_json=json.dumps(emb),
                        token_count=chunk.token_estimate,
                    )
                )
            doc.chunk_count = len(chunks)

        await db.commit()
        logger.info("Seed complete: %d users / %d products / %d orders", len(users), len(products), len(orders))


async def _make_shipment(db, order: Order, status: OrderStatus, carriers, now) -> None:
    """Create a shipment + a few logs for an order."""
    delivered = status == OrderStatus.DELIVERED
    ship_status = (
        ShipmentStatus.DELIVERED
        if delivered
        else random.choice(
            [
                ShipmentStatus.IN_TRANSIT,
                ShipmentStatus.AT_HUB,
                ShipmentStatus.OUT_FOR_DELIVERY,
            ]
        )
    )
    days_ago = max(0, (now - order.created_at).days)
    shipment = Shipment(
        tracking_code=f"KOP{order.order_code.replace('-', '')}",
        order_id=order.id,
        carrier=random.choice(carriers),
        origin_city="İstanbul",
        destination_city=order.shipping_city,
        current_location=order.shipping_city if delivered else "Dağıtım Merkezi",
        status=ship_status,
        risk_score=0.1 if delivered else round(random.uniform(0.1, 0.4), 2),
        estimated_delivery=now + timedelta(days=2),
        delivered_at=order.created_at + timedelta(days=2) if delivered else None,
        created_at=order.created_at,
        updated_at=now - timedelta(hours=random.randint(1, 24)),
    )
    db.add(shipment)
    
    # Kargo ID'sinin oluşması için veritabanını bekle
    await db.flush()
    
    # Add minimal log trail.
    db.add(
        ShipmentLog(
            shipment_id=shipment.id,
            event="Kargo oluşturuldu",
            location="İstanbul Depo",
            created_at=order.created_at,
        )
    )
    if not delivered:
        db.add(
            ShipmentLog(
                shipment_id=shipment.id,
                event="Yolda",
                location="Dağıtım Merkezi",
                created_at=order.created_at + timedelta(days=1),
            )
        )
    else:
        db.add(
            ShipmentLog(
                shipment_id=shipment.id,
                event="Teslim edildi",
                location=order.shipping_city,
                created_at=order.created_at + timedelta(days=2),
            )
        )


if __name__ == "__main__":  # pragma: no cover
    import asyncio

    asyncio.run(seed_database())
