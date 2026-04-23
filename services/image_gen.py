"""
Service generate gambar produk menggunakan Replicate AI atau DALL-E
"""

import os
import httpx
import replicate
from pathlib import Path
from config import config


class ImageGenerator:
    """Generate gambar produk berkualitas tinggi untuk konten TikTok"""

    IMAGE_SYSTEM_PROMPT = """
    Kamu adalah AI yang ahli membuat prompt gambar untuk produk affiliate TikTok.
    Buat prompt gambar dalam bahasa Inggris yang:
    1. Menampilkan produk dengan pencahayaan profesional
    2. Background clean, minimalis, atau lifestyle yang menarik
    3. Cocok untuk konten TikTok/sosmed
    4. Tambahkan detail: sudut pengambilan, pencahayaan, suasana
    Format: hanya prompt saja, tanpa penjelasan lain
    """

    async def generate_prompt(self, product_info: str) -> str:
        """Generate prompt gambar dari info produk menggunakan AI"""
        if config.ANTHROPIC_API_KEY:
            return await self._generate_prompt_claude(product_info)
        elif config.OPENAI_API_KEY:
            return await self._generate_prompt_openai(product_info)
        else:
            return self._default_prompt(product_info)

    async def _generate_prompt_claude(self, product_info: str) -> str:
        """Generate prompt menggunakan Claude"""
        import anthropic
        client = anthropic.AsyncAnthropic(api_key=config.ANTHROPIC_API_KEY)
        msg = await client.messages.create(
            model="claude-opus-4-5",
            max_tokens=300,
            system=self.IMAGE_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": f"Buat prompt gambar untuk produk ini:\n{product_info}"}]
        )
        return msg.content[0].text.strip()

    async def _generate_prompt_openai(self, product_info: str) -> str:
        """Generate prompt menggunakan OpenAI"""
        import openai
        client = openai.AsyncOpenAI(api_key=config.OPENAI_API_KEY)
        resp = await client.chat.completions.create(
            model="gpt-4o-mini",
            max_tokens=300,
            messages=[
                {"role": "system", "content": self.IMAGE_SYSTEM_PROMPT},
                {"role": "user", "content": f"Buat prompt gambar untuk produk ini:\n{product_info}"}
            ]
        )
        return resp.choices[0].message.content.strip()

    def _default_prompt(self, product_info: str) -> str:
        """Prompt default jika tidak ada API AI"""
        return (
            f"Professional product photography, {product_info}, "
            "clean white background, studio lighting, high quality, "
            "commercial photography, 4K resolution, sharp focus"
        )

    async def generate_with_replicate(self, prompt: str, save_path: str) -> str:
        """Generate gambar menggunakan Replicate AI"""
        if not config.REPLICATE_API_TOKEN:
            raise ValueError("REPLICATE_API_TOKEN tidak ditemukan")

        os.environ["REPLICATE_API_TOKEN"] = config.REPLICATE_API_TOKEN

        # Enhance prompt untuk kualitas lebih baik
        enhanced_prompt = (
            f"{prompt}, product photography, commercial quality, "
            f"highly detailed, professional, 8k resolution, "
            f"trending on artstation, photorealistic"
        )

        output = await replicate.async_run(
            config.REPLICATE_IMAGE_MODEL,
            input={
                "prompt": enhanced_prompt,
                "negative_prompt": "blurry, bad quality, watermark, text, logo, distorted, ugly",
                "width": config.IMAGE_WIDTH,
                "height": config.IMAGE_HEIGHT,
                "num_outputs": 1,
                "scheduler": "K_EULER",
                "num_inference_steps": 30,
                "guidance_scale": 7.5,
            }
        )

        image_url = str(output[0]) if isinstance(output, list) else str(output)

        # Download dan simpan gambar
        await self._download_file(image_url, save_path)
        return save_path

    async def generate_with_dalle(self, prompt: str, save_path: str) -> str:
        """Generate gambar menggunakan DALL-E 3"""
        if not config.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY tidak ditemukan")

        import openai
        client = openai.AsyncOpenAI(api_key=config.OPENAI_API_KEY)

        response = await client.images.generate(
            model="dall-e-3",
            prompt=f"Professional product photography for TikTok: {prompt}",
            size="1024x1024",
            quality="hd",
            n=1,
        )

        image_url = response.data[0].url
        await self._download_file(image_url, save_path)
        return save_path

    async def generate(self, prompt: str, save_path: str) -> str:
        """Generate gambar dengan API yang tersedia"""
        Path(save_path).parent.mkdir(parents=True, exist_ok=True)

        if config.REPLICATE_API_TOKEN:
            return await self.generate_with_replicate(prompt, save_path)
        elif config.OPENAI_API_KEY:
            return await self.generate_with_dalle(prompt, save_path)
        else:
            raise ValueError("Tidak ada API gambar yang dikonfigurasi")

    async def _download_file(self, url: str, save_path: str):
        """Download file dari URL"""
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            with open(save_path, "wb") as f:
                f.write(resp.content)


image_generator = ImageGenerator()
