from dataclasses import dataclass

@dataclass
class QuoteResult:
    peso_cubado_kg: float
    peso_tarifavel_kg: float
    frete_base: float
    advalorem: float
    total: float

def calc_quote(*, peso_real_kg: float, volume_m3: float, valor_mercadoria: float,
               cubagem_kg_m3: float, min_ate_10kg: float, kg_excedente: float,
               adval_percent: float, adval_min: float) -> QuoteResult:
    # Peso cubado e tarifável
    peso_cubado = max(0.0, volume_m3) * cubagem_kg_m3
    peso_real = max(0.0, peso_real_kg)
    peso_tarifavel = max(peso_real, peso_cubado)

    # Frete base
    if peso_tarifavel <= 10.0:
        frete_base = min_ate_10kg
    else:
        frete_base = min_ate_10kg + (peso_tarifavel - 10.0) * kg_excedente

    # Ad valorem
    adval_calc = max(0.0, valor_mercadoria) * (adval_percent / 100.0)
    advalorem = max(adval_calc, adval_min)

    total = frete_base + advalorem

    # Arredondamentos simples (pode ajustar conforme sua regra)
    return QuoteResult(
        peso_cubado_kg=round(peso_cubado, 2),
        peso_tarifavel_kg=round(peso_tarifavel, 2),
        frete_base=round(frete_base, 2),
        advalorem=round(advalorem, 2),
        total=round(total, 2),
    )
