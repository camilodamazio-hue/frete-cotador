from fastapi import FastAPI, Request, Form, UploadFile, File
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import select
import json
import os
import tempfile
import shutil

from db import SessionLocal, engine, Base
from models import User, Lane, Quote
from security import hash_password, verify_password, set_session, clear_session, get_session_user_id
from pricing import calc_quote

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Frete Cotador Web")
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

def get_db() -> Session:
    db = SessionLocal()
    try:
        return db
    finally:
        pass

def current_user(request: Request, db: Session):
    uid = get_session_user_id(request)
    if not uid:
        return None
    return db.get(User, uid)

def require_user(request: Request, db: Session):
    user = current_user(request, db)
    if not user:
        return None, RedirectResponse("/login", status_code=302)
    return user, None

def require_admin(request: Request, db: Session):
    user = current_user(request, db)
    if not user or not user.is_admin:
        return None, RedirectResponse("/", status_code=302)
    return user, None

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    db = get_db()
    user = current_user(request, db)
    return templates.TemplateResponse("home.html", {"request": request, "user": user})

@app.get("/register", response_class=HTMLResponse)
def register_get(request: Request):
    return templates.TemplateResponse("register.html", {"request": request, "error": None})

@app.post("/register", response_class=HTMLResponse)
def register_post(
    request: Request,
    name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
):
    db = get_db()
    email = email.strip().lower()
    if db.execute(select(User).where(User.email == email)).scalar_one_or_none():
        return templates.TemplateResponse("register.html", {"request": request, "error": "E-mail já cadastrado."})

    u = User(name=name.strip(), email=email, password_hash=hash_password(password))
    db.add(u)
    db.commit()

    resp = RedirectResponse("/", status_code=302)
    set_session(resp, u.id)
    return resp

@app.get("/login", response_class=HTMLResponse)
def login_get(request: Request):
    return templates.TemplateResponse("login.html", {"request": request, "error": None})

@app.post("/login", response_class=HTMLResponse)
def login_post(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
):
    db = get_db()
    email = email.strip().lower()
    u = db.execute(select(User).where(User.email == email)).scalar_one_or_none()
    if not u or not verify_password(password, u.password_hash):
        return templates.TemplateResponse("login.html", {"request": request, "error": "Login inválido."})

    resp = RedirectResponse("/", status_code=302)
    set_session(resp, u.id)
    return resp

@app.post("/logout")
def logout():
    resp = RedirectResponse("/", status_code=302)
    clear_session(resp)
    return resp

@app.get("/cotacao", response_class=HTMLResponse)
def quote_get(request: Request):
    db = get_db()
    user, redirect = require_user(request, db)
    if redirect:
        return redirect

    # Listas para datalist (origem/destino)
    origens = [r[0] for r in db.execute(select(Lane.origem).distinct().order_by(Lane.origem)).all()]
    destinos = [r[0] for r in db.execute(select(Lane.destino).distinct().order_by(Lane.destino)).all()]

    return templates.TemplateResponse("quote.html", {
        "request": request,
        "user": user,
        "origens": origens,
        "destinos": destinos,
        "result": None,
        "error": None,
    })

@app.post("/cotacao", response_class=HTMLResponse)
def quote_post(
    request: Request,
    origem: str = Form(...),
    destino: str = Form(...),
    peso_real_kg: float = Form(...),
    volume_m3: float = Form(...),
    valor_mercadoria: float = Form(...),
):
    db = get_db()
    user, redirect = require_user(request, db)
    if redirect:
        return redirect

    origem = origem.strip()
    destino = destino.strip()

    lane = db.execute(select(Lane).where(Lane.origem == origem, Lane.destino == destino)).scalar_one_or_none()
    if not lane:
        # tenta achar pelo destino apenas (caso origem fixa) - opcional
        return templates.TemplateResponse("quote.html", {
            "request": request,
            "user": user,
            "origens": [r[0] for r in db.execute(select(Lane.origem).distinct().order_by(Lane.origem)).all()],
            "destinos": [r[0] for r in db.execute(select(Lane.destino).distinct().order_by(Lane.destino)).all()],
            "result": None,
            "error": "Rota (origem/destino) não encontrada na tabela.",
        })

    res = calc_quote(
        peso_real_kg=peso_real_kg,
        volume_m3=volume_m3,
        valor_mercadoria=valor_mercadoria,
        cubagem_kg_m3=lane.cubagem_kg_m3,
        min_ate_10kg=lane.min_ate_10kg,
        kg_excedente=lane.kg_excedente,
        adval_percent=lane.adval_percent,
        adval_min=lane.adval_min,
    )

    q = Quote(
        user_id=user.id,
        origem=origem,
        destino=destino,
        peso_real_kg=peso_real_kg,
        volume_m3=volume_m3,
        valor_mercadoria=valor_mercadoria,
        cubagem_kg_m3=lane.cubagem_kg_m3,
        peso_cubado_kg=res.peso_cubado_kg,
        peso_tarifavel_kg=res.peso_tarifavel_kg,
        frete_base=res.frete_base,
        advalorem=res.advalorem,
        total=res.total,
        detalhes_json=json.dumps({
            "regiao": lane.regiao,
            "icms": lane.icms,
            "observacao": lane.observacao,
            "min_ate_10kg": lane.min_ate_10kg,
            "kg_excedente": lane.kg_excedente,
            "adval_percent": lane.adval_percent,
            "adval_min": lane.adval_min,
        }, ensure_ascii=False),
    )
    db.add(q)
    db.commit()

    origens = [r[0] for r in db.execute(select(Lane.origem).distinct().order_by(Lane.origem)).all()]
    destinos = [r[0] for r in db.execute(select(Lane.destino).distinct().order_by(Lane.destino)).all()]

    return templates.TemplateResponse("quote.html", {
        "request": request,
        "user": user,
        "origens": origens,
        "destinos": destinos,
        "result": {
            "origem": origem,
            "destino": destino,
            "regiao": lane.regiao,
            "cubagem_kg_m3": lane.cubagem_kg_m3,
            "peso_cubado_kg": res.peso_cubado_kg,
            "peso_tarifavel_kg": res.peso_tarifavel_kg,
            "frete_base": res.frete_base,
            "advalorem": res.advalorem,
            "total": res.total,
            "icms": lane.icms,
            "observacao": lane.observacao,
        },
        "error": None,
    })

@app.get("/historico", response_class=HTMLResponse)
def history(request: Request):
    db = get_db()
    user, redirect = require_user(request, db)
    if redirect:
        return redirect

    quotes = db.execute(select(Quote).where(Quote.user_id == user.id).order_by(Quote.created_at.desc()).limit(200)).scalars().all()
    return templates.TemplateResponse("history.html", {"request": request, "user": user, "quotes": quotes})

@app.get("/admin", response_class=HTMLResponse)
def admin(request: Request):
    db = get_db()
    user, redirect = require_admin(request, db)
    if redirect:
        return redirect

    lanes_count = db.execute(select(Lane.id)).all()
    return templates.TemplateResponse("admin.html", {"request": request, "user": user, "lanes_count": len(lanes_count), "msg": None, "error": None})

@app.post("/admin/import", response_class=HTMLResponse)
def admin_import(request: Request, excel: UploadFile = File(...)):
    db = get_db()
    user, redirect = require_admin(request, db)
    if redirect:
        return redirect

    # salva temporário e chama import_table.py via função inline para evitar subprocesso
    import pandas as pd
    import re

    def parse_cubagem(v) -> float:
        if v is None:
            return 300.0
        s = str(v)
        m = re.search(r"(\d+(?:[\.,]\d+)?)", s)
        if not m:
            return 300.0
        return float(m.group(1).replace(",", "."))

    with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
        shutil.copyfileobj(excel.file, tmp)
        tmp_path = tmp.name

    try:
        df = pd.read_excel(tmp_path).fillna("")
        # Limpa tabela e recria (mais simples). Se quiser, troque por UPSERT.
        db.query(Lane).delete()
        db.commit()

        for _, row in df.iterrows():
            lane = Lane(
                origem=str(row["Origem"]).strip(),
                destino=str(row["Destino"]).strip(),
                regiao=str(row.get("Região","")).strip(),
                min_ate_10kg=float(str(row["Mínimo até 10kg (R$)"]).replace(",", ".")),
                kg_excedente=float(str(row["Kg excedente (R$/kg)"]).replace(",", ".")),
                adval_percent=float(str(row["Ad val (%)"]).replace(",", ".")),
                adval_min=float(str(row["Ad val mín (R$)"]).replace(",", ".")),
                cubagem_kg_m3=parse_cubagem(row.get("Cubagem","300")),
                icms=str(row.get("ICMS","")).strip(),
                observacao=str(row.get("Observação","")).strip(),
            )
            db.add(lane)

        db.commit()
        lanes_count = db.execute(select(Lane.id)).all()
        return templates.TemplateResponse("admin.html", {"request": request, "user": user, "lanes_count": len(lanes_count), "msg": "Tabela importada com sucesso.", "error": None})
    except Exception as e:
        return templates.TemplateResponse("admin.html", {"request": request, "user": user, "lanes_count": 0, "msg": None, "error": f"Erro ao importar: {e}"})
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
