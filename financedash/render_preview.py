"""
Renderiza os templates Jinja com dados fictícios para gerar um preview
estático navegável (usado apenas para visualizar o design fora do Flask).

Uso: python3 flask/render_preview.py public/preview
"""

import json
import os
import sys
from datetime import date, timedelta

from jinja2 import Environment, FileSystemLoader

BASE = os.path.dirname(os.path.abspath(__file__))
OUT = sys.argv[1] if len(sys.argv) > 1 else "public/preview"

PAGES = {
    "home": "index.html",
    "login": "login.html",
    "cadastro": "cadastro.html",
    "dashboard": "dashboard.html",
    "nova_transacao": "nova_transacao.html",
    "editar_transacao": "editar_transacao.html",
    "excluir_transacao": "dashboard.html",
    "investimentos": "investimentos.html",
    "perfil_investidor": "perfil_investidor.html",
    "perfil_resultado": "perfil_resultado.html",
    "radar": "radar.html",
    "historico": "historico.html",
    "logout": "index.html",
}


def url_for(endpoint, **kwargs):
    if endpoint == "static":
        return "static/" + kwargs["filename"]
    return PAGES.get(endpoint, "index.html")


class T:
    def __init__(self, i, descricao, valor, tipo, categoria, dias):
        self.id = i
        self.descricao = descricao
        self.valor = valor
        self.tipo = tipo
        self.categoria = categoria
        self.data = date.today() - timedelta(days=dias)


TRANSACOES = [
    T(1, "Salário", 7200.00, "receita", "Salário", 2),
    T(2, "Aluguel", 1850.00, "despesa", "Moradia", 4),
    T(3, "Mercado do mês", 940.35, "despesa", "Alimentação", 7),
    T(4, "Freelance de design", 1500.00, "receita", "Investimentos", 12),
    T(5, "Uber e transporte", 260.90, "despesa", "Transporte", 18),
    T(6, "Academia", 129.90, "despesa", "Saúde", 24),
    T(7, "Cinema e streaming", 187.40, "despesa", "Lazer", 33),
    T(8, "Salário", 7200.00, "receita", "Salário", 34),
    T(9, "Curso de Python", 399.00, "despesa", "Educação", 45),
    T(10, "Salário", 7000.00, "receita", "Salário", 64),
]


def dashboard_ctx():
    receitas = sum(t.valor for t in TRANSACOES if t.tipo == "receita")
    despesas = sum(t.valor for t in TRANSACOES if t.tipo == "despesa")

    meses = {}
    for t in TRANSACOES:
        m = t.data.strftime("%Y-%m")
        meses.setdefault(m, {"receitas": 0, "despesas": 0})
        meses[m][t.tipo + "s"] += t.valor

    ordenados = sorted(meses)
    cats = {}
    for t in TRANSACOES:
        if t.tipo == "despesa":
            cats[t.categoria] = cats.get(t.categoria, 0) + t.valor

    return dict(
        transacoes=TRANSACOES,
        receitas=receitas,
        despesas=despesas,
        saldo=receitas - despesas,
        labels_meses=["{}/{}".format(m.split("-")[1], m.split("-")[0]) for m in ordenados],
        valores_receitas=[meses[m]["receitas"] for m in ordenados],
        valores_despesas=[meses[m]["despesas"] for m in ordenados],
        categorias_labels=list(cats),
        categorias_valores=list(cats.values()),
    )


ATIVOS = [
    {"symbol": "PETR4", "data": {"longName": "Petróleo Brasileiro S.A.", "regularMarketPrice": 38.72,
                                 "regularMarketChangePercent": 2.41, "regularMarketDayHigh": 39.10,
                                 "regularMarketDayLow": 37.88, "regularMarketVolume": 48213900}},
    {"symbol": "VALE3", "data": {"longName": "Vale S.A.", "regularMarketPrice": 61.05,
                                 "regularMarketChangePercent": -1.12, "regularMarketDayHigh": 62.40,
                                 "regularMarketDayLow": 60.75, "regularMarketVolume": 31980400}},
    {"symbol": "ITUB4", "data": {"longName": "Itaú Unibanco Holding S.A.", "regularMarketPrice": 34.18,
                                 "regularMarketChangePercent": 0.86, "regularMarketDayHigh": 34.55,
                                 "regularMarketDayLow": 33.70, "regularMarketVolume": 22540100}},
]

HIST = []
preco = 35.0
import math

for i in range(30):
    preco += math.sin(i / 3) * 0.6 + 0.08
    HIST.append({
        "date": int((date.today() - timedelta(days=29 - i)).strftime("%s") if os.name != "nt" else 0),
        "open": round(preco - 0.3, 2),
        "high": round(preco + 0.45, 2),
        "low": round(preco - 0.55, 2),
        "close": round(preco, 2),
    })

INVEST = [
    {"nome": "Tesouro Direto", "categoria": "Renda Fixa",
     "descricao": "Títulos públicos com diferentes características de prazo e risco."},
    {"nome": "ETFs", "categoria": "Renda Variável",
     "descricao": "Fundos negociados em bolsa que acompanham índices ou estratégias."},
    {"nome": "FIIs", "categoria": "Fundos Imobiliários",
     "descricao": "Fundos relacionados ao mercado imobiliário e negociados em bolsa."},
    {"nome": "Fundos Multimercado", "categoria": "Fundos",
     "descricao": "Fundos que podem investir em diferentes classes de ativos."},
]

CONTEXTS = {
    "index.html": {},
    "login.html": {},
    "cadastro.html": {},
    "dashboard.html": dashboard_ctx(),
    "nova_transacao.html": {},
    "editar_transacao.html": {"transacao": TRANSACOES[1]},
    "investimentos.html": {},
    "perfil_investidor.html": {},
    "perfil_resultado.html": {"perfil": "Moderado", "pontos": 8, "investimentos": INVEST},
    "radar.html": {"dados": ATIVOS, "ranking": sorted(
        ATIVOS, key=lambda a: a["data"]["regularMarketChangePercent"], reverse=True)},
    "historico.html": {"historico": HIST, "symbol": "PETR4"},
}


def main():
    env = Environment(loader=FileSystemLoader(os.path.join(BASE, "templates")))
    env.globals["url_for"] = url_for
    env.globals["session"] = {"usuario_nome": "Arthur"}
    env.filters["tojson"] = lambda v, **kw: json.dumps(v)

    os.makedirs(OUT, exist_ok=True)
    for name, ctx in CONTEXTS.items():
        html = env.get_template(name).render(**ctx)
        with open(os.path.join(OUT, name), "w", encoding="utf-8") as f:
            f.write(html)
        print("ok:", name)


if __name__ == "__main__":
    main()
