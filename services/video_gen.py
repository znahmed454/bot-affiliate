"""
Service generate video dari gambar menggunakan Kling AI atau RunwayML
"""

import os
import time
import base64
import httpx
import jwt
from pathlib import Path
from config import config


class VideoGenerator:
    """Generate video TikTok dari gambar produk"""

    KLING_BASE_URL = "https://api.klingai.com"

    def _generate_kling_token(self) -> str:
        """Generate JWT token untuk Kling AI"""
        payload = {
            "iss": config.KLING_ACCESS_KEY,
            "exp": int(time.time()) + 1800,
            "nbf": int(time.time()) - 5,
        }
        return jwt.encode(payload, config.KLING_API_KEY, algorithm="HS256")

    async def generate_with_kling(self, image_path: str, prompt: str, save_path: str) -> str:
        """
        Generate video dari gambar menggunakan Kling AI
        Menggunakan fitur image-to-video
        """
        if not config.KLING_API_KEY or not config.KLING_ACCESS_KEY:
            raise ValueError("KLING_API_KEY dan KLING_ACCESS_KEY diperlukan")

        token = self._generate_kling_token()
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        # Encode gambar ke base64
        with open(image_path, "rb") as f:
            image_b64 = base64.b64encode(f.read()).decode()

        # Buat task video
        async with httpx.AsyncClient(timeout=30) as client:
            create_resp = await client.post(
                f"{self.KLING_BASE_URL}/v1/videos/image2video",
                headers=headers,
                json={
                    "model_name": "kling-v1",
                    "image": image_b64,
                    "prompt": prompt,
                    "negative_prompt": "blurry, distorted, bad quality, watermark",
                    "cfg_scale": 0.5,
                    "mode": "std",
                    "duration": str(config.VIDEO_DURATION),
                }
            )
            create_resp.raise_for_status()
            task_id = create_resp.json()["data"]["task_id"]

        # Polling sampai video selesai
        video_url = await self._poll_kling_task(task_id, headers)
        await self._download_file(video_url, save_path)
        return save_path

    async def _poll_kling_task(self, task_id: str, headers: dict,
                                max_wait: int = 300, interval: int = 5) -> str:
        """Poll status task Kling AI hingga selesai"""
        elapsed = 0
        async with httpx.AsyncClient(timeout=15) as client:
            while elapsed < max_wait:
                resp = await client.get(
                    f"{self.KLING_BASE_URL}/v1/videos/image2video/{task_id}",
                    headers=headers
                )
                resp.raise_for_status()
                data = resp.json()["data"]
                status = data.get("task_status")

                if status == "succeed":
                    works = data.get("task_result", {}).get("videos", [])
                    if works:
                        return works[0]["url"]
                    raise ValueError("Video tidak tersedia di hasil task")
                elif status == "failed":
                    raise ValueError(f"Task Kling gagal: {data.get('task_status_msg', 'Unknown error')}")

                time.sleep(interval)
                elapsed += interval

        raise TimeoutError(f"Timeout setelah {max_wait} detik menunggu video")

    async def generate_with_runway(self, image_path: str, prompt: str, save_path: str) -> str:
        """
        Generate video menggunakan RunwayML Gen-3 Alpha
        """
        if not config.RUNWAY_API_SECRET:
            raise ValueError("RUNWAY_API_SECRET tidak ditemukan")

        # Encode gambar
        with open(image_path, "rb") as f:
            image_b64 = base64.b64encode(f.read()).decode()

        ext = Path(image_path).suffix.lstrip(".")
        media_type = f"image/{ext}" if ext in ["jpg", "jpeg", "png", "webp"] else "image/jpeg"
        image_data_url = f"data:{media_type};base64,{image_b64}"

        headers = {
            "Authorization": f"Bearer {config.RUNWAY_API_SECRET}",
            "Content-Type": "application/json",
            "X-Runway-Version": "2024-11-06",
        }

        async with httpx.AsyncClient(timeout=30) as client:
            # Buat task
            create_resp = await client.post(
                "https://api.dev.runwayml.com/v1/image_to_video",
                headers=headers,
                json={
                    "promptImage": image_data_url,
                    "model": "gen3a_turbo",
                    "promptText": prompt,
                    "duration": config.VIDEO_DURATION,
                    "ratio": "9:16",  # Portrait untuk TikTok
                }
            )
            create_resp.raise_for_status()
            task_id = create_resp.json()["id"]

        # Polling
        video_url = await self._poll_runway_task(task_id, headers)
        await self._download_file(video_url, save_path)
        return save_path

    async def _poll_runway_task(self, task_id: str, headers: dict,
                                 max_wait: int = 300, interval: int = 5) -> str:
        """Poll status task RunwayML"""
        elapsed = 0
        async with httpx.AsyncClient(timeout=15) as client:
            while elapsed < max_wait:
                resp = await client.get(
                    f"https://api.dev.runwayml.com/v1/tasks/{task_id}",
                    headers=headers
                )
                resp.raise_for_status()
                data = resp.json()
                status = data.get("status")

                if status == "SUCCEEDED":
                    outputs = data.get("output", [])
                    if outputs:
                        return outputs[0]
                    raise ValueError("Output video tidak ditemukan")
                elif status == "FAILED":
                    raise ValueError(f"Task RunwayML gagal: {data.get('failure', 'Unknown')}")

                time.sleep(interval)
                elapsed += interval

        raise TimeoutError(f"Timeout setelah {max_wait} detik")

    async def generate(self, image_path: str, prompt: str, save_path: str) -> str:
        """Generate video dengan API yang tersedia"""
        Path(save_path).parent.mkdir(parents=True, exist_ok=True)

        if config.KLING_API_KEY and config.KLING_ACCESS_KEY:
            return await self.generate_with_kling(image_path, prompt, save_path)
        elif config.RUNWAY_API_SECRET:
            return await self.generate_with_runway(image_path, prompt, save_path)
        else:
            raise ValueError(
                "Tidak ada API video yang dikonfigurasi.\n"
                "Daftarkan KLING_API_KEY + KLING_ACCESS_KEY atau RUNWAY_API_SECRET di .env"
            )

    async def _download_file(self, url: str, save_path: str):
        """Download file dari URL"""
        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            with open(save_path, "wb") as f:
                f.write(resp.content)


video_generator = VideoGenerator()
