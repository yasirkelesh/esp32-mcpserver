#!/usr/bin/env python3

import asyncio
import json
import sys
import aiohttp
from typing import Any, Dict, List, Optional

# raspi'nin IP adresi
RASPI_IP = "192.168.1.101:5000"  # raspi'nizin IP'si

print("raspi MCP Server başlatılıyor...", file=sys.stderr)

class MCPServer:
    def __init__(self):
        """Sunucu başlatıldığında araçları tanımlar."""
        self.tools = [
            {
                "name": "control_servo",
                "description": "Raspiye'ye bağlı servoyu belirtilen servoyu belirtilen açıya ayarlar.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "servo": {
                            "type": "integer",
                            "minimum": 0,
                            "maximum": 6,
                            "description": "Kontrol edilecek servo numarası (0-6 arası)."
                        },
                        "value": {
                            "type": "number",  # integer yerine number
                            "minimum": -1.0,
                            "maximum": 1.0,
                            "description": "Servonun hareket edeceği deger. -1.0 en düşük, 1.0 en yüksek değerdir."
                        }
                    },
                    "required": ["servo", "value"],
                }
            },
            {
                "name": "place_product",
                "description": "Ürünü alıp kutuya atar. Raspberry Pi'ye /hold endpoint'ine istek gönderir.",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                    "required": [],
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
                        "name": "raspi-servo-controller",
                        "version": "0.1.3"
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
                value = arguments.get("value")
                servo = arguments.get("servo")
                try:
                    # JSON veri gönder
                    payload = {"servo": servo, "value": value}
                    headers = {'Content-Type': 'application/json'}
                    
                    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5)) as session:
                        async with session.post(
                            f"http://{RASPI_IP}/servo",
                            json=payload,  # json parametresi kullan
                            headers=headers
                        ) as response:
                            if response.status == 200:
                                text_content = f"✅ {servo} nolu servo başarıyla {value} değerine ayarlandı!"
                            else:
                                response_text = await response.text()
                                text_content = f"❌ Hata: raspi'den {response.status} kodu döndü. Yanıt: {response_text}"
                    content = [{"type": "text", "text": text_content}]
                except Exception as e:
                    content = [{"type": "text", "text": f"❌ raspi'ye bağlanılamadı veya bir hata oluştu: {str(e)}"}]

                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "content": content
                    }
                }

            elif tool_name == "place_product":
                try:
                    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=60)) as session:
                        async with session.get(f"http://{RASPI_IP}/hold") as response:
                            if response.status == 200:
                                response_text = await response.text()
                                text_content = f"✅ Ürün başarıyla kutuya atıldı! Raspi yanıtı: {response_text}"
                            else:
                                response_text = await response.text()
                                text_content = f"❌ Hata: raspi'den {response.status} kodu döndü. Yanıt: {response_text}"
                    content = [{"type": "text", "text": text_content}]
                except Exception as e:
                    content = [{"type": "text", "text": f"❌ raspi'ye bağlanılamadı veya bir hata oluştu: {str(e)}"}]

                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "content": content
                    }
                }

        if request_id is None:
            print(f"Bilinmeyen metot '{method}' ile bir bildirim alındı. Yanıt gönderilmiyor.", file=sys.stderr)
            return None

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