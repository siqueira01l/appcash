from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, date
import requests
import os
from dotenv import load_dotenv

load_dotenv()

BRAPI_TOKEN = os.getenv("BRAPI_TOKEN")
from models import db,Usuario, Transacao

app = Flask(__name__)

app.secret_key="chave-secreta-financedash"

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///finance.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False 

db.init_app(app)

with app.app_context():
    db.create_all()

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/cadastro", methods=["GET", "POST"])
def cadastro():
    
    if request.method == "POST":
        
        nome=request.form["nome"]
        email=request.form["email"]
        senha=request.form["senha"]
        
        senha_hash=generate_password_hash(senha)
        
        novo_usuario= Usuario(nome=nome,email=email,senha=senha_hash)
        
        db.session.add(novo_usuario)
        db.session.commit()
        
        return redirect(url_for("login"))
    
    return render_template("cadastro.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    
    if request.method == "POST":
        
        email = request.form["email"]
        senha = request.form["senha"]
        
        usuario = Usuario.query.filter_by(email=email).first()
        
        if usuario and check_password_hash(usuario.senha, senha):
            
            session["usuario_id"] = usuario.id
            session["usuario_nome"] = usuario.nome
            
            return redirect(url_for("dashboard"))
        
        return "Email ou senha incorretos"

    return render_template("login.html")

@app.route("/dashboard")
def dashboard():

    if "usuario_id" not in session:
        return redirect(url_for("login"))

    # =========================
    # TRANSAÇÕES
    # =========================

    transacoes = (
        Transacao.query
        .filter_by(usuario_id=session["usuario_id"])
        .order_by(Transacao.data.desc())
        .all()
    )


    # =========================
    # RECEITAS E DESPESAS
    # =========================

    receitas = 0
    despesas = 0

    for transacao in transacoes:

        if transacao.tipo == "receita":
            receitas += transacao.valor

        elif transacao.tipo == "despesa":
            despesas += transacao.valor


    saldo = receitas - despesas


    # =========================
    # GRÁFICO RECEITAS X DESPESAS
    # =========================

    meses = {}

    for transacao in transacoes:

        mes = transacao.data.strftime("%Y-%m")

        if mes not in meses:
            meses[mes] = {
                "receitas": 0,
                "despesas": 0
            }

        if transacao.tipo == "receita":

            meses[mes]["receitas"] += transacao.valor

        elif transacao.tipo == "despesa":

            meses[mes]["despesas"] += transacao.valor


    meses_ordenados = sorted(meses.keys())

    labels_meses = []
    valores_receitas = []
    valores_despesas = []


    for mes in meses_ordenados:

        ano, numero_mes = mes.split("-")

        labels_meses.append(
            f"{numero_mes}/{ano}"
        )

        valores_receitas.append(
            meses[mes]["receitas"]
        )

        valores_despesas.append(
            meses[mes]["despesas"]
        )


    # =========================
    # DESPESAS POR CATEGORIA
    # =========================

    categorias = {}

    for transacao in transacoes:

        if str(transacao.tipo).strip().lower() == "despesa":

            categoria = transacao.categoria

            if not categoria:
                categoria = "Outros"

            if categoria not in categorias:
                categorias[categoria] = 0

            categorias[categoria] += transacao.valor


    categorias_labels = list(categorias.keys())

    categorias_valores = list(categorias.values())


    # =========================
    # DASHBOARD
    # =========================

    return render_template(
        "dashboard.html",

        transacoes=transacoes,

        receitas=receitas,
        despesas=despesas,
        saldo=saldo,

        labels_meses=labels_meses,
        valores_receitas=valores_receitas,
        valores_despesas=valores_despesas,

        categorias_labels=categorias_labels,
        categorias_valores=categorias_valores
    )

@app.route("/logout")
def logout():
    
    session.clear()
    
    return redirect(url_for("login"))

@app.route("/nova_transacao", methods=["GET", "POST"])
def nova_transacao():
    
    if "usuario_id" not in session:
        return redirect(url_for("login"))
    
    if request.method == "POST":
        
        descricao = request.form["descricao"]
        valor = float(request.form["valor"])
        tipo = request.form["tipo"]
        categoria = request.form["categoria"]
        data = request.form.get("data")
        
        if data:
            data=datetime.strptime(data, "%Y-%m-%d").date()
        else:
            data = date.today()
    
    
        nova = Transacao(
            usuario_id=session["usuario_id"],
            descricao=descricao,
            valor=valor,
            tipo=tipo,
            categoria=categoria,
            data=data
        )
    
        db.session.add(nova)
        db.session.commit()
        
        return redirect(url_for("dashboard"))

    return render_template("nova_transacao.html")

@app.route("/excluir_transacao/<int:id>")
def excluir_transacao(id):
    
    if "usuario_id" not in session:
        return redirect(url_for(login))
    
    transacao = Transacao.query.get_or_404(id)
    
    if transacao.usuario_id != session["usuario_id"]:
        return "Acesso não autorizado", 403
    
    db.session.delete(transacao)
    db.session.commit()

    return redirect(url_for("dashboard"))

@app.route("/editar_transacao/<int:id>", methods=["GET", "POST"])
def editar_transacao(id):
    
    if "usuario_id" not in session:
        return redirect(url_for("login"))
    
    transacao = Transacao.query.get_or_404(id)
    
    if transacao.usuario_id != session["usuario_id"]:
        return "Acesso não autorizado", 403
    
    if request.method == "POST":
        
        transacao.descricao = request.form["descricao"]
        transacao.valor = float(request.form["valor"])
        transacao.tipo = request.form["tipo"]
        transacao.categoria = request.form["categoria"]
        
        data= request.form.get("data")
        
        if data:
            transacao.data=datetime.strptime(data, "%Y-%m-%d").date()
         
        db.session.commit()
        
        return redirect(url_for("dashboard"))
    
    return render_template(
        "editar_transacao.html",
        transacao=transacao
        )


@app.route("/investimentos")
def investimentos():
    if "usuario_id" not in session:
        return redirect(url_for("login"))
    
    return render_template("investimentos.html")

@app.route("/perfil-investidor", methods=["GET", "POST"])
def perfil_investidor():

    if "usuario_id" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":

        objetivo = request.form["objetivo"]
        prazo = request.form["prazo"]
        risco = request.form["risco"]
        oscilacao = request.form["oscilacao"]

        pontos = 0

        # Objetivo
        if objetivo == "reserva":
            pontos += 1
        elif objetivo == "patrimonio":
            pontos += 2
        elif objetivo == "crescimento":
            pontos += 3

        # Prazo
        if prazo == "curto":
            pontos += 1
        elif prazo == "medio":
            pontos += 2
        elif prazo == "longo":
            pontos += 3

        # Tolerância ao risco
        if risco == "vender":
            pontos += 1
        elif risco == "esperar":
            pontos += 2
        elif risco == "comprar":
            pontos += 3

        # Oscilação
        if oscilacao == "baixo":
            pontos += 1
        elif oscilacao == "medio":
            pontos += 2
        elif oscilacao == "alto":
            pontos += 3

        # Perfil
        if pontos <= 6:
            perfil = "Conservador"

            investimentos = [
                {
                    "nome": "Tesouro Selic",
                    "categoria": "Renda Fixa",
                    "descricao": "Título público com foco em segurança e liquidez."
                },
                {
                    "nome": "CDB",
                    "categoria": "Renda Fixa",
                    "descricao": "Título emitido por instituições financeiras."
                },
                {
                    "nome": "LCI",
                    "categoria": "Renda Fixa",
                    "descricao": "Título de renda fixa ligado ao setor imobiliário."
                },
                {
                    "nome": "LCA",
                    "categoria": "Renda Fixa",
                    "descricao": "Título de renda fixa ligado ao setor do agronegócio."
                }
            ]

        elif pontos <= 9:
            perfil = "Moderado"

            investimentos = [
                {
                    "nome": "Tesouro Direto",
                    "categoria": "Renda Fixa",
                    "descricao": "Títulos públicos com diferentes características de prazo e risco."
                },
                {
                    "nome": "ETFs",
                    "categoria": "Renda Variável",
                    "descricao": "Fundos negociados em bolsa que acompanham índices ou estratégias."
                },
                {
                    "nome": "FIIs",
                    "categoria": "Fundos Imobiliários",
                    "descricao": "Fundos relacionados ao mercado imobiliário e negociados em bolsa."
                },
                {
                    "nome": "Fundos Multimercado",
                    "categoria": "Fundos",
                    "descricao": "Fundos que podem investir em diferentes classes de ativos."
                }
            ]

        else:
            perfil = "Arrojado"

            investimentos = [
                {
                    "nome": "Ações",
                    "categoria": "Renda Variável",
                    "descricao": "Participação no capital de empresas negociadas em bolsa."
                },
                {
                    "nome": "ETFs",
                    "categoria": "Renda Variável",
                    "descricao": "Fundos negociados em bolsa que podem acompanhar índices de ações."
                },
                {
                    "nome": "FIIs",
                    "categoria": "Fundos Imobiliários",
                    "descricao": "Fundos imobiliários negociados em bolsa."
                },
                {
                    "nome": "Fundos de Ações",
                    "categoria": "Fundos",
                    "descricao": "Fundos com exposição ao mercado de ações."
                }
            ]

        return render_template(
            "perfil_resultado.html",
            perfil=perfil,
            pontos=pontos,
            investimentos=investimentos
        )

    return render_template("perfil_investidor.html")
    
@app.route("/radar")
def radar():
    if "usuario_id" not in session:
        return redirect(url_for("login"))

    url = "https://brapi.dev/api/v2/stocks/quote"

    params = {
        "symbols": "PETR4,VALE3,ITUB4"
    }

    resposta = requests.get(url, params=params)

    if resposta.status_code != 200:
        return "Erro ao consultar dados do mercado"

    dados = resposta.json()

    ativos = dados["results"]

    # Ordena os ativos pela maior variação percentual
    ranking = sorted(
        ativos,
        key=lambda ativo: ativo["data"]["regularMarketChangePercent"],
        reverse=True
    )

    return render_template(
        "radar.html",
        dados=ativos,
        ranking=ranking
    )
    
@app.route("/historico/<symbol>")
def historico(symbol):

    if "usuario_id" not in session:
        return redirect(url_for("login"))

    url = "https://brapi.dev/api/v2/stocks/historical"

    params = {
        "symbols": symbol,
        "range": "1mo",
        "interval": "1d"
    }

    headers = {
        "Authorization": f"Bearer {BRAPI_TOKEN}"
    }

    resposta = requests.get(
        url,
        params=params,
        headers=headers
    )

    if resposta.status_code != 200:
        return f"Erro ao consultar histórico: {resposta.text}"

    dados = resposta.json()

    historico = dados["results"][0]["data"]["historicalDataPrice"]

    return render_template(
        "historico.html",
        historico=historico,
        symbol=symbol
    )
                
        

if __name__ == "__main__":
    app.run(debug=True)