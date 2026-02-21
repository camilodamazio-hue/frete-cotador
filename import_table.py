import argparse
import re
import pandas as pd

from db import engine, SessionLocal, Base
from models import Lane

def parse_cubagem(value) -> float:
    # Ex.: "300 kg/m³" -> 300
    if value is None:
        return 300.0
    s = str(value)
    m = re.search(r"(\d+(?:[\.,]\d+)?)", s)
    if not m:
        return 300.0
    return float(m.group(1).replace(",", "."))

def main(excel_path: str):
    Base.metadata.create_all(bind=engine)

    df = pd.read_excel(excel_path)
    required = ["Origem","Destino","Região","Mínimo até 10kg (R$)","Kg excedente (R$/kg)","Ad val (%)","Ad val mín (R$)","Cubagem","ICMS","Observação"]
    for c in required:
        if c not in df.columns:
            raise SystemExit(f"Coluna ausente no Excel: {c}")

    # Limpeza básica
    df = df.fillna("")
    db = SessionLocal()

    # Upsert simples por origem+destino
    count = 0
    for _, row in df.iterrows():
        origem = str(row["Origem"]).strip()
        destino = str(row["Destino"]).strip()

        lane = db.query(Lane).filter(Lane.origem == origem, Lane.destino == destino).one_or_none()
        if lane is None:
            lane = Lane(origem=origem, destino=destino)
            db.add(lane)

        lane.regiao = str(row["Região"]).strip()
        lane.min_ate_10kg = float(str(row["Mínimo até 10kg (R$)"]).replace(",", "."))
        lane.kg_excedente = float(str(row["Kg excedente (R$/kg)"]).replace(",", "."))
        lane.adval_percent = float(str(row["Ad val (%)"]).replace(",", "."))
        lane.adval_min = float(str(row["Ad val mín (R$)"]).replace(",", "."))
        lane.cubagem_kg_m3 = parse_cubagem(row["Cubagem"])
        lane.icms = str(row["ICMS"]).strip()
        lane.observacao = str(row["Observação"]).strip()

        count += 1

    db.commit()
    db.close()
    print(f"Importação concluída. Registros processados: {count}")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--excel", required=True, help="Caminho para o Excel da tabela")
    args = ap.parse_args()
    main(args.excel)
