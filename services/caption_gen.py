"""
Service generate caption TikTok yang viral dan engaging
"""

from config import config


CAPTION_PROMPT = """
Kamu adalah copywriter TikTok affiliate Indonesia yang ahli membuat caption viral.
Tugas: buat caption TikTok untuk produk affiliate berdasarkan info produk yang diberikan.

Aturan caption:
1. Mulai dengan hook yang menarik perhatian (pertanyaan, fakta mengejutkan, atau pernyataan bold)
2. Jelaskan manfaat utama produk (bukan fitur)
3. Tambahkan social proof atau urgensi
4. Akhiri dengan CTA (Call To Action) yang jelas
5. Sertakan 5-8 hashtag relevan (mix trending + niche)
6. Gunakan emoji secukupnya agar terasa natural
7. Panjang total: 150-300 karakter untuk caption utama + hashtag terpisah
8. Bahasa: santai, relatable, seperti teman merekomendasikan produk

Format output WAJIB:
HOOK: [kalimat pembuka]
CAPTION: [caption lengkap]
CTA: [call to action]
HASHTAG: [hashtag]
"""

CAPTION_PROMPT_EN = """
You are a viral TikTok affiliate copywriter. Create an engaging caption for the product.

Rules:
1. Start with a strong hook (question, shocking fact, bold statement)
2. Focus on benefits, not features
3. Add social proof or urgency
4. Clear CTA at the end
5. 5-8 relevant hashtags
6. Natural emoji usage
7. 150-300 chars for main caption + separate hashtags
8. Conversational tone like a friend recommending

Output format:
HOOK: [opening line]
CAPTION: [full caption]
CTA: [call to action]
HASHTAG: [hashtags]
"""


class CaptionGenerator:
    """Generate caption TikTok viral untuk produk affiliate"""

    def _get_system_prompt(self) -> str:
        return CAPTION_PROMPT if config.CAPTION_LANGUAGE == "indonesia" else CAPTION_PROMPT_EN

    async def generate(self, product_info: str, style: str = "engaging") -> dict:
        """
        Generate caption dari info produk
        Returns dict dengan keys: hook, caption, cta, hashtag, full_caption
        """
        if config.ANTHROPIC_API_KEY:
            raw = await self._generate_claude(product_info, style)
        elif config.OPENAI_API_KEY:
            raw = await self._generate_openai(product_info, style)
        else:
            raise ValueError("Tidak ada API caption yang dikonfigurasi")

        return self._parse_caption(raw)

    async def _generate_claude(self, product_info: str, style: str) -> str:
        import anthropic
        client = anthropic.AsyncAnthropic(api_key=config.ANTHROPIC_API_KEY)

        style_note = {
            "engaging": "Buat caption yang engaging dan relatable",
            "viral": "Buat caption yang berpotensi viral, gunakan trend terkini",
            "review": "Buat caption gaya review jujur dan autentik",
            "promo": "Buat caption promo dengan urgensi tinggi",
        }.get(style, "Buat caption yang engaging")

        msg = await client.messages.create(
            model="claude-opus-4-5",
            max_tokens=600,
            system=self._get_system_prompt(),
            messages=[{
                "role": "user",
                "content": f"{style_note}\n\nInfo produk:\n{product_info}"
            }]
        )
        return msg.content[0].text

    async def _generate_openai(self, product_info: str, style: str) -> str:
        import openai
        client = openai.AsyncOpenAI(api_key=config.OPENAI_API_KEY)

        resp = await client.chat.completions.create(
            model="gpt-4o-mini",
            max_tokens=600,
            messages=[
                {"role": "system", "content": self._get_system_prompt()},
                {"role": "user", "content": f"Info produk:\n{product_info}"}
            ]
        )
        return resp.choices[0].message.content

    def _parse_caption(self, raw: str) -> dict:
        """Parse output AI menjadi komponen caption"""
        result = {"hook": "", "caption": "", "cta": "", "hashtag": "", "full_caption": raw}

        for key, label in [("hook", "HOOK:"), ("caption", "CAPTION:"), ("cta", "CTA:"), ("hashtag", "HASHTAG:")]:
            if label in raw:
                start = raw.index(label) + len(label)
                # Cari label berikutnya atau akhir string
                next_labels = [raw.index(l) for l in ["HOOK:", "CAPTION:", "CTA:", "HASHTAG:"] if l in raw and raw.index(l) > start]
                end = min(next_labels) if next_labels else len(raw)
                result[key] = raw[start:end].strip()

        # Buat full caption yang siap copy-paste
        if result["caption"] and result["hashtag"]:
            result["full_caption"] = f"{result['caption']}\n\n{result['hashtag']}"
        elif result["caption"]:
            result["full_caption"] = result["caption"]

        return result

    def format_for_telegram(self, caption_data: dict, product_name: str = "") -> str:
        """Format caption untuk ditampilkan di Telegram"""
        lines = []

        if product_name:
            lines.append(f"✨ *Caption untuk: {product_name}*\n")

        if caption_data.get("hook"):
            lines.append(f"🪝 *Hook:*\n`{caption_data['hook']}`\n")

        if caption_data.get("caption"):
            lines.append(f"📝 *Caption:*\n{caption_data['caption']}\n")

        if caption_data.get("cta"):
            lines.append(f"📢 *CTA:*\n`{caption_data['cta']}`\n")

        if caption_data.get("hashtag"):
            lines.append(f"#️⃣ *Hashtag:*\n`{caption_data['hashtag']}`\n")

        lines.append("─────────────────")
        lines.append("💡 Ketuk teks di atas untuk copy langsung!")

        return "\n".join(lines)


caption_generator = CaptionGenerator()
