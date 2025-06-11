#!/usr/bin/env python3

import asyncio
import json
import sys
import aiohttp
from typing import Any, Dict, List, Optional

# ESP32'nin IP adresi
ESP32_IP = "192.168.183.68"  # ESP32'nizin IP'si

# Not: Bu kodu çalıştırmadan önce 'aiohttp' kütüphanesini kurmanız gerekir.
# Terminal veya komut satırına şunu yazın: python3.11 -m pip install aiohttp

print("ESP32 MCP Server başlatılıyor...", file=sys.stderr)

class MCPServer:
    def __init__(self):
        """Sunucu başlatıldığında araçları tanımlar."""
        self.tools = [
            {
                "name": "control_servo",
                "description": "ESP32'ye bağlı servoyu belirtilen açıya ayarlar.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "angle": {
                            "type": "integer",
                            "minimum": 0,
                            "maximum": 180,
                            "description": "Servonun hareket edeceği açı (0-180 derece arası)."
                        }
                    },
                    "required": ["angle"]
                }
            }
        ]

    async def handle_request(self, request: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Gelen JSON-RPC isteklerini işler ve yanıtlar. Yanıt gerekmiyorsa None döner."""
        method = request.get("method")
        params = request.get("params", {})
        request_id = request.get("id")

        if method == "initialize":
            print("Initialize isteği işleniyor.", file=sys.stderr)
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "serverInfo": {
                        "name": "esp32-servo-controller",
                        "version": "0.1.2"
                    },
                    "capabilities": {
                        "tools": {
                             "version": "0.1.0",
                             "tools": self.tools
                        }
                    }
                }
            }

        elif method == "tools/list":
            print("Araç listesi isteği işleniyor.", file=sys.stderr)
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "tools": self.tools
                }
            }

        elif method == "tools/call":
            tool_name = params.get("name")
            arguments = params.get("arguments", {})
            print(f"Araç çağrısı isteği işleniyor: {tool_name}", file=sys.stderr)
            
            if tool_name == "control_servo":
                angle = arguments.get("angle")
                try:
                    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5)) as session:
                        async with session.post(
                            f"http://{ESP32_IP}/servo",
                            data={"angle": str(angle)}
                        ) as response:
                            if response.status == 200:
                                text_content = f"✅ Servo başarıyla {angle} derece açısına ayarlandı!"
                            else:
                                response_text = await response.text()
                                text_content = f"❌ Hata: ESP32'den {response.status} kodu döndü. Yanıt: {response_text}"
                    content = [{"type": "text", "text": text_content}]
                except Exception as e:
                    content = [{"type": "text", "text": f"❌ ESP32'ye bağlanılamadı veya bir hata oluştu: {str(e)}"}]

                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "content": content
                    }
                }

        # DÜZELTME: Bilinmeyen bir metot için hata yanıtı göndermeden önce isteğin bir bildirim olup olmadığını kontrol et.
        # Eğer 'id' yoksa (bu bir bildirimdir), protokol gereği yanıt gönderme.
        if request_id is None:
            print(f"Bilinmeyen metot '{method}' ile bir bildirim alındı. Yanıt gönderilmiyor.", file=sys.stderr)
            return None

        # Eğer isteğin bir 'id'si varsa, o zaman bir hata yanıtı gönder.
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": { "code": -32601, "message": f"Metot bulunamadı: {method}" }
        }

    async def run(self):
        """Sunucuyu başlatır ve standart girdiden gelen istekleri dinler."""
        print("MCP Server çalışıyor. İstemciden (client) gelen istekler bekleniyor...", file=sys.stderr)
        loop = asyncio.get_event_loop()
        
        while True:
            try:
                line = await loop.run_in_executor(None, sys.stdin.readline)
                if not line:
                    print("Girdi akışı kapandı. Sunucu durduruluyor.", file=sys.stderr)
                    break
                request = json.loads(line)
                response = await self.handle_request(request)
                
                # DÜZELTME: Sadece bir yanıt varsa (None değilse) gönder.
                if response:
                    print(json.dumps(response))
                    sys.stdout.flush()

            except EOFError:
                print("EOF alındı. Sunucu durduruluyor.", file=sys.stderr)
                break
            except Exception as e:
                print(f"Beklenmedik bir hata oluştu: {e}", file=sys.stderr)

async def main():
    server = MCPServer()
    await server.run()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nSunucu kullanıcı tarafından durduruldu.", file=sys.stderr)