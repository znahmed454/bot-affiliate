"""
Service untuk mengambil info produk dari link TikTok Shop / Shopee / Tokopedia
"""

import re
import httpx
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ProductInfo:
    name: str
    description: str = ""
    price: str = ""
    image_url: Optional[str] = None
    shop_name: str = ""
    platform: str = ""
    rating: str = ""
    tags: list = field(default_factory=list)
    affiliate_link: str = ""

    def to_prompt(self) -> str:
        """Ubah info produk menjadi prompt untuk AI"""
        parts = [f"Produk: {self.name}"]
        if self.description:
            parts.append(f"Deskripsi: {self.description[:200]}")
        if self.tags:
            parts.append(f"Kategori: {', '.join(self.tags[:5])}")
        return ". ".join(parts)

    def summary(self) -> str:
        """Ringkasan produk untuk ditampilkan ke user"""
        lines = [f"🏷️ *{self.name}*"]
        if self.price:
            lines.append(f"💰 Harga: {self.price}")
        if self.shop_name:
            lines.append(f"🏪 Toko: {self.shop_name}")
        if self.rating:
            lines.append(f"⭐ Rating: {self.rating}")
        if self.platform:
            lines.append(f"📱 Platform: {self.platform}")
        return "\n".join(lines)


class ProductScraper:
    """Scraper info produk dari berbagai platform"""

    HEADERS = {
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8",
    }

    def detect_platform(self, url: str) -> str:
        """Deteksi platform dari URL"""
        patterns = {
            "tiktok": r"tiktok\.com|vt\.tiktok\.com",
            "shopee": r"shopee\.co\.id",
            "tokopedia": r"tokopedia\.com|tokopedia\.link",
            "lazada": r"lazada\.co\.id",
        }
        for platform, pattern in patterns.items():
            if re.search(pattern, url, re.IGNORECASE):
                return platform
        return "unknown"

    async def scrape(self, url: str) -> ProductInfo:
        """Scrape info produk dari URL"""
        platform = self.detect_platform(url)

        scrapers = {
            "tiktok": self._scrape_tiktok,
            "shopee": self._scrape_shopee,
            "tokopedia": self._scrape_tokopedia,
        }

        scraper = scrapers.get(platform, self._scrape_generic)
        return await scraper(url)

    async def _scrape_generic(self, url: str) -> ProductInfo:
        """Scrape generik menggunakan Open Graph meta tags"""
        try:
            async with httpx.AsyncClient(headers=self.HEADERS, follow_redirects=True, timeout=15) as client:
                resp = await client.get(url)
                html = resp.text

            name = self._extract_og(html, "og:title") or self._extract_meta(html, "title") or "Produk"
            description = self._extract_og(html, "og:description") or ""
            image_url = self._extract_og(html, "og:image")

            return ProductInfo(
                name=name[:200],
                description=description[:500],
                image_url=image_url,
                platform="web",
                affiliate_link=url
            )
        except Exception as e:
            return ProductInfo(name="Produk dari link", affiliate_link=url)

    async def _scrape_tiktok(self, url: str) -> ProductInfo:
        """Scrape produk TikTok Shop"""
        try:
            async with httpx.AsyncClient(headers=self.HEADERS, follow_redirects=True, timeout=15) as client:
                resp = await client.get(url)
                html = resp.text

            name = self._extract_og(html, "og:title") or "Produk TikTok"
            description = self._extract_og(html, "og:description") or ""
            image_url = self._extract_og(html, "og:image")

            # Coba extract harga dari meta atau JSON-LD
            price = self._extract_price(html)
            shop = self._extract_between(html, '"sellerName":"', '"') or ""

            return ProductInfo(
                name=name,
                description=description,
                price=price,
                image_url=image_url,
                shop_name=shop,
                platform="TikTok Shop",
                affiliate_link=url
            )
        except Exception:
            return ProductInfo(name="Produk TikTok", platform="TikTok Shop", affiliate_link=url)

    async def _scrape_shopee(self, url: str) -> ProductInfo:
        """Scrape produk Shopee"""
        try:
            async with httpx.AsyncClient(headers=self.HEADERS, follow_redirects=True, timeout=15) as client:
                resp = await client.get(url)
                html = resp.text

            name = self._extract_og(html, "og:title") or "Produk Shopee"
            description = self._extract_og(html, "og:description") or ""
            image_url = self._extract_og(html, "og:image")
            price = self._extract_price(html)

            return ProductInfo(
                name=name,
                description=description,
                price=price,
                image_url=image_url,
                platform="Shopee",
                affiliate_link=url
            )
        except Exception:
            return ProductInfo(name="Produk Shopee", platform="Shopee", affiliate_link=url)

    async def _scrape_tokopedia(self, url: str) -> ProductInfo:
        """Scrape produk Tokopedia"""
        try:
            async with httpx.AsyncClient(headers=self.HEADERS, follow_redirects=True, timeout=15) as client:
                resp = await client.get(url)
                html = resp.text

            name = self._extract_og(html, "og:title") or "Produk Tokopedia"
            description = self._extract_og(html, "og:description") or ""
            image_url = self._extract_og(html, "og:image")

            return ProductInfo(
                name=name,
                description=description,
                image_url=image_url,
                platform="Tokopedia",
                affiliate_link=url
            )
        except Exception:
            return ProductInfo(name="Produk Tokopedia", platform="Tokopedia", affiliate_link=url)

    def _extract_og(self, html: str, property_: str) -> Optional[str]:
        match = re.search(
            rf'<meta[^>]+property=["\']?{re.escape(property_)}["\']?[^>]+content=["\']([^"\']+)',
            html, re.IGNORECASE
        )
        if not match:
            match = re.search(
                rf'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']?{re.escape(property_)}',
                html, re.IGNORECASE
            )
        return match.group(1).strip() if match else None

    def _extract_meta(self, html: str, name: str) -> Optional[str]:
        match = re.search(rf'<{name}[^>]*>([^<]+)</{name}>', html, re.IGNORECASE)
        return match.group(1).strip() if match else None

    def _extract_price(self, html: str) -> str:
        patterns = [
            r'"price":\s*"?([\d.,]+)"?',
            r'Rp\s*([\d.,]+)',
            r'"currentPrice":\s*(\d+)',
        ]
        for pattern in patterns:
            match = re.search(pattern, html)
            if match:
                price = match.group(1)
                if price.isdigit():
                    return f"Rp {int(price):,}".replace(",", ".")
                return f"Rp {price}"
        return ""

    def _extract_between(self, html: str, start: str, end: str) -> Optional[str]:
        try:
            idx = html.index(start) + len(start)
            end_idx = html.index(end, idx)
            return html[idx:end_idx]
        except ValueError:
            return None


scraper = ProductScraper()
