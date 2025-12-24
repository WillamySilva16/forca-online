from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import random

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

clientes = []
letras_usadas = set()
tentativas = 6

with open("animais.txt", encoding="utf-8") as f:
    palavras = [l.strip().upper() for l in f if l.strip()]

palavra = list(random.choice(palavras))
estado = ["_" for _ in palavra]


async def broadcast(msg):
    for c in clientes:
        try:
            await c.send_text(msg)
        except:
            pass


def render_estado():
    return (
        f"\nPalavra: {' '.join(estado)}"
        f"\nTentativas: {tentativas}"
        f"\nLetras usadas: {', '.join(sorted(letras_usadas))}"
    )


@app.get("/")
async def home():
    with open("static/index.html", encoding="utf-8") as f:
        return HTMLResponse(f.read())


@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    global tentativas
    await ws.accept()
    clientes.append(ws)

    await ws.send_text("🎮 Bem-vindo ao Forca Online!")
    await ws.send_text(render_estado())

    try:
        while True:
            letra = await ws.receive_text()
            letra = letra.strip().upper()

            if len(letra) != 1 or not letra.isalpha():
                await ws.send_text("Envie apenas 1 letra válida.")
                continue

            if letra in letras_usadas:
                await ws.send_text("Letra já usada.")
                continue

            letras_usadas.add(letra)

            if letra in palavra:
                for i, l in enumerate(palavra):
                    if l == letra:
                        estado[i] = letra
                await broadcast(f"✅ Letra correta: {letra}")
            else:
                tentativas -= 1
                await broadcast(f"❌ Letra errada: {letra}")

            await broadcast(render_estado())

            if "_" not in estado:
                await broadcast(f"🏆 Vitória! A palavra era: {''.join(palavra)}")
                break

            if tentativas == 0:
                await broadcast(f"💀 Game Over! A palavra era: {''.join(palavra)}")
                break

    except WebSocketDisconnect:
        clientes.remove(ws)
