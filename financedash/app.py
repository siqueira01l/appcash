from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, date
import requests
import os
from dotenv import load_dotenv

load_dotenv()

from models import db, Usuario, Transacao


app = Flask(__name__)

app.secret_key = "chave-secreta-financedash"

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///finance.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False


# =========================================================
# BANCO DE DADOS
# =========================================================

db.init_app(app)

with app.app_context():
    db.create_all()

with app.app_context():

    db.create_all()

    colunas = db.session.execute(
        db.text("PRAGMA table_info(usuario)")
    ).fetchall()

    nomes_colunas = [coluna[1] for coluna in colunas]

    if "pluggy_item_id" not in nomes_colunas:

        db.session.execute(
            db.text(
                "ALTER TABLE usuario "
                "ADD COLUMN pluggy_item_id VARCHAR(100)"
            )
        )

        db.session.commit()

        print("Coluna pluggy_item_id adicionada.")

# =========================================================
# PLUGGY
# =========================================================

def obter_api_key_pluggy():

    resposta = requests.post(
        "https://api.pluggy.ai/auth",
        json={
            "clientId": os.getenv("PLUGGY_CLIENT_ID"),
            "clientSecret": os.getenv("PLUGGY_CLIENT_SECRET")
        }
    )

    if resposta.status_code != 200:

        print("Erro ao autenticar no Pluggy:")
        print(resposta.status_code)
        print(resposta.text)

        return None

    dados = resposta.json()

    return dados.get("apiKey")


# =========================================================
# SINCRONIZAR TRANSAÇÕES DO PLUGGY
# =========================================================

def sincronizar_transacoes_pluggy(usuario_id):

    usuario = Usuario.query.get(usuario_id)

    if not usuario:
        return 0

    item_id = usuario.pluggy_item_id

    if not item_id:
        print("Usuário ainda não possui conta Pluggy.")
        return 0

    api_key = obter_api_key_pluggy()

    if not api_key:
        return 0

    # ==========================================
    # BUSCA AS CONTAS DO ITEM REAL
    # ==========================================

    resposta_contas = requests.get(
        "https://api.pluggy.ai/accounts",
        headers={
            "X-API-KEY": api_key
        },
        params={
            "itemId": item_id
        }
    )

    if resposta_contas.status_code != 200:

        print("Erro ao buscar contas Pluggy:")
        print(resposta_contas.text)

        return 0

    dados_contas = resposta_contas.json()

    contas = dados_contas.get("results", [])

    if not contas:

        print("Nenhuma conta encontrada.")

        return 0

    adicionadas = 0

    # ==========================================
    # PROCESSA CADA CONTA
    # ==========================================

    for conta in contas:

        account_id = conta.get("id")

        if not account_id:
            continue

        print(
            "Sincronizando conta:",
            conta.get("name"),
            account_id
        )

        # ==========================================
        # BUSCA TRANSAÇÕES DA CONTA
        # ==========================================

        resposta = requests.get(
            "https://api.pluggy.ai/v2/transactions",
            headers={
                "X-API-KEY": api_key
            },
            params={
                "accountId": account_id
            }
        )

        if resposta.status_code != 200:

            print(
                "Erro ao buscar transações:",
                resposta.text
            )

            continue

        dados = resposta.json()

        transacoes_pluggy = dados.get(
            "results",
            []
        )

        # ==========================================
        # SALVA AS TRANSAÇÕES
        # ==========================================

        for transacao in transacoes_pluggy:

            pluggy_id = transacao.get("id")

            if not pluggy_id:
                continue

            # Evita duplicação
            existe = Transacao.query.filter_by(
                pluggy_id=pluggy_id
            ).first()

            if existe:
                continue

            descricao = transacao.get(
                "description",
                "Transação"
            )

            valor_original = float(
                transacao.get("amount", 0)
            )

            if transacao.get("type") == "CREDIT":
                tipo = "receita"
            else:
                tipo = "despesa"

            valor = abs(valor_original)

            categoria = transacao.get(
                "category",
                "Outros"
            )

            data_string = transacao.get("date")

            if not data_string:
                continue

            data = datetime.fromisoformat(
                data_string.replace("Z", "+00:00")
            ).date()

            nova_transacao = Transacao(
                usuario_id=usuario_id,
                pluggy_id=pluggy_id,
                descricao=descricao,
                valor=valor,
                tipo=tipo,
                categoria=categoria,
                data=data
            )

            db.session.add(nova_transacao)

            adicionadas += 1

    db.session.commit()

    print(
        f"{adicionadas} novas transações sincronizadas."
    )

    return adicionadas

# =========================================================
# HOME
# =========================================================

@app.route("/")
def home():

    return render_template("index.html")


# =========================================================
# CADASTRO
# =========================================================

@app.route("/cadastro", methods=["GET", "POST"])
def cadastro():

    if request.method == "POST":

        nome = request.form["nome"]
        email = request.form["email"]
        senha = request.form["senha"]

        senha_hash = generate_password_hash(senha)

        novo_usuario = Usuario(
            nome=nome,
            email=email,
            senha=senha_hash
        )

        db.session.add(novo_usuario)
        db.session.commit()

        return redirect(url_for("login"))

    return render_template("cadastro.html")


# =========================================================
# LOGIN
# =========================================================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        senha = request.form["senha"]

        usuario = Usuario.query.filter_by(
            email=email
        ).first()

        if usuario and check_password_hash(
            usuario.senha,
            senha
        ):

            session["usuario_id"] = usuario.id
            session["usuario_nome"] = usuario.nome

            return redirect(url_for("dashboard"))

        return "Email ou senha incorretos"

    return render_template("login.html")


# =========================================================
# DASHBOARD
# =========================================================
def obter_saldo_pluggy(usuario_id):

    usuario = Usuario.query.get(usuario_id)

    if not usuario:
        return 0

    item_id = usuario.pluggy_item_id

    if not item_id:
        print("Usuário não possui conta Pluggy conectada.")
        return 0

    api_key = obter_api_key_pluggy()

    if not api_key:
        return 0

    # Busca as contas pertencentes ao Item conectado
    resposta = requests.get(
        "https://api.pluggy.ai/accounts",
        headers={
            "X-API-KEY": api_key
        },
        params={
            "itemId": item_id,
            "type": "BANK"
        }
    )

    if resposta.status_code != 200:

        print("Erro ao buscar contas para obter saldo:")
        print(resposta.status_code)
        print(resposta.text)

        return 0

    dados = resposta.json()

    contas = dados.get("results", [])

    saldo_total = 0

    for conta in contas:

        account_id = conta.get("id")

        if not account_id:
            continue

        # Busca o saldo em tempo real
        resposta_saldo = requests.get(
            f"https://api.pluggy.ai/accounts/{account_id}/balance",
            headers={
                "X-API-KEY": api_key
            }
        )

        if resposta_saldo.status_code == 200:

            dados_saldo = resposta_saldo.json()

            saldo = dados_saldo.get("balance", 0)

            saldo_total += float(saldo)

            print(
                f"Conta: {conta.get('name')} | "
                f"Saldo: R$ {saldo:.2f}"
            )

        else:

            # Se o saldo em tempo real não estiver disponível,
            # utiliza o saldo retornado pela conta.
            saldo = conta.get("balance", 0)

            saldo_total += float(saldo)

            print(
                f"Usando saldo armazenado: "
                f"{conta.get('name')} | "
                f"R$ {saldo:.2f}"
            )

    print(
        f"SALDO TOTAL PLUGGY: R$ {saldo_total:.2f}"
    )

    return saldo_total


# =========================================================
# DASHBOARD
# =========================================================

@app.route("/dashboard")
def dashboard():

    if "usuario_id" not in session:
        return redirect(url_for("login"))

    usuario_id = session["usuario_id"]

    # ==========================================
    # SINCRONIZA PLUGGY
    # ==========================================

    sincronizar_transacoes_pluggy(usuario_id)

    # ==========================================
    # BUSCA TODAS AS TRANSAÇÕES DO USUÁRIO
    # ==========================================

    transacoes = (
        Transacao.query
        .filter_by(usuario_id=usuario_id)
        .order_by(Transacao.data.desc())
        .all()
    )

    # ==========================================
    # MÊS ATUAL
    # ==========================================

    hoje = date.today()

    mes_atual = hoje.month
    ano_atual = hoje.year

    # ==========================================
    # RECEITAS E DESPESAS DO MÊS ATUAL
    # ==========================================

    receitas = 0
    despesas = 0

    for transacao in transacoes:

        if (
            transacao.data.month == mes_atual
            and transacao.data.year == ano_atual
        ):

            if transacao.tipo == "receita":
                receitas += transacao.valor

            elif transacao.tipo == "despesa":
                despesas += transacao.valor

    # ==========================================
    # SALDO REAL DA CONTA PLUGGY
    # ==========================================

    saldo = obter_saldo_pluggy(usuario_id)

    # ==========================================
    # GRÁFICO DE RECEITAS X DESPESAS
    # ==========================================

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

    # ==========================================
    # DESPESAS POR CATEGORIA
    # ==========================================

    categorias = {}

    for transacao in transacoes:

        if str(transacao.tipo).strip().lower() == "despesa":

            categoria = transacao.categoria or "Outros"

            if categoria not in categorias:
                categorias[categoria] = 0

            categorias[categoria] += transacao.valor

    categorias_labels = list(categorias.keys())
    categorias_valores = list(categorias.values())

   

    return render_template(
        "dashboard.html",

        transacoes=transacoes,

        # Valores do mês atual
        receitas=receitas,
        despesas=despesas,

        # Saldo real da conta
        saldo=saldo,

        # Gráfico
        labels_meses=labels_meses,
        valores_receitas=valores_receitas,
        valores_despesas=valores_despesas,

        # Categorias
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

        valor = float(
            request.form["valor"]
        )

        tipo = request.form["tipo"]

        categoria = request.form["categoria"]

        data = request.form.get("data")

        if data:

            data = datetime.strptime(
                data,
                "%Y-%m-%d"
            ).date()

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
        return redirect(url_for("login"))

    transacao = Transacao.query.get_or_404(id)

    if transacao.usuario_id != session["usuario_id"]:

        return "Acesso não autorizado", 403

    db.session.delete(transacao)

    db.session.commit()

    return redirect(url_for("dashboard"))


# =========================================================
# EDITAR TRANSAÇÃO
# =========================================================

@app.route("/editar_transacao/<int:id>", methods=["GET", "POST"])
def editar_transacao(id):

    if "usuario_id" not in session:
        return redirect(url_for("login"))

    transacao = Transacao.query.get_or_404(id)

    if transacao.usuario_id != session["usuario_id"]:

        return "Acesso não autorizado", 403

    if request.method == "POST":

        transacao.descricao = request.form["descricao"]

        transacao.valor = float(
            request.form["valor"]
        )

        transacao.tipo = request.form["tipo"]

        transacao.categoria = request.form["categoria"]

        data = request.form.get("data")

        if data:

            transacao.data = datetime.strptime(
                data,
                "%Y-%m-%d"
            ).date()

        db.session.commit()

        return redirect(url_for("dashboard"))

    return render_template(
        "editar_transacao.html",
        transacao=transacao
    )


# =========================================================
# INVESTIMENTOS
# =========================================================

@app.route("/investimentos")
def investimentos():

    if "usuario_id" not in session:
        return redirect(url_for("login"))

    return render_template("investimentos.html")


# =========================================================
# PERFIL DO INVESTIDOR
# =========================================================

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

        # =================================================
        # OBJETIVO
        # =================================================

        if objetivo == "reserva":

            pontos += 1

        elif objetivo == "patrimonio":

            pontos += 2

        elif objetivo == "crescimento":

            pontos += 3

        # =================================================
        # PRAZO
        # =================================================

        if prazo == "curto":

            pontos += 1

        elif prazo == "medio":

            pontos += 2

        elif prazo == "longo":

            pontos += 3

        # =================================================
        # TOLERÂNCIA AO RISCO
        # =================================================

        if risco == "vender":

            pontos += 1

        elif risco == "esperar":

            pontos += 2

        elif risco == "comprar":

            pontos += 3

        # =================================================
        # OSCILAÇÃO
        # =================================================

        if oscilacao == "baixo":

            pontos += 1

        elif oscilacao == "medio":

            pontos += 2

        elif oscilacao == "alto":

            pontos += 3

        # =================================================
        # PERFIL CONSERVADOR
        # =================================================

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

        # =================================================
        # PERFIL MODERADO
        # =================================================

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

        # =================================================
        # PERFIL ARROJADO
        # =================================================

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


# =========================================================
# RADAR
# =========================================================

@app.route("/radar")
def radar():

    if "usuario_id" not in session:
        return redirect(url_for("login"))

    url = "https://brapi.dev/api/v2/stocks/quote"

    params = {
        "symbols": "PETR4,VALE3,ITUB4"
    }

    resposta = requests.get(
        url,
        params=params
    )

    if resposta.status_code != 200:

        return "Erro ao consultar dados do mercado"

    dados = resposta.json()

    ativos = dados["results"]

    # =====================================================
    # ORDENA PELO MAIOR MOVIMENTO
    # =====================================================

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


# =========================================================
# HISTÓRICO DE UMA AÇÃO
# =========================================================

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
        "Authorization": f"Bearer {os.getenv('BRAPI_TOKEN')}"
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


# =========================================================
# CRIAR CONNECT TOKEN DO PLUGGY
# =========================================================

def criar_connect_token():

    api_key = obter_api_key_pluggy()

    if not api_key:
        return None

    resposta = requests.post(
        "https://api.pluggy.ai/connect_token",
        headers={
            "X-API-KEY": api_key
        },
        json={
            "options": {
                "clientUserId": str(session["usuario_id"])
            }
        }
    )

    if resposta.status_code != 200:

        print("Erro ao criar Connect Token:")
        print(resposta.status_code)
        print(resposta.text)

        return None

    dados = resposta.json()

    return dados.get("accessToken")


# =========================================================
# CONECTAR BANCO
# =========================================================
@app.route("/salvar-item-pluggy", methods=["POST"])
def salvar_item_pluggy():

    if "usuario_id" not in session:
        return {
            "success": False,
            "error": "Usuário não autenticado"
        }, 401

    dados = request.get_json()

    item_id = dados.get("item_id")

    if not item_id:
        return {
            "success": False,
            "error": "Item ID não informado"
        }, 400

    usuario = Usuario.query.get(session["usuario_id"])

    if not usuario:
        return {
            "success": False,
            "error": "Usuário não encontrado"
        }, 404

    usuario.pluggy_item_id = item_id

    db.session.commit()

    print(
        f"Pluggy Item {item_id} associado ao usuário {usuario.id}"
    )

    return {
        "success": True
    }


@app.route("/conectar-banco")
def conectar_banco():

    if "usuario_id" not in session:
        return redirect(url_for("login"))

    connect_token = criar_connect_token()

    if not connect_token:

        return "Erro ao criar conexão com o banco", 500

    return render_template(
        "conectar_banco.html",
        connect_token=connect_token
    )


# =========================================================
# SINCRONIZAR TRANSAÇÕES MANUALMENTE
# =========================================================

@app.route("/sincronizar-transacoes")
def sincronizar_transacoes():

    if "usuario_id" not in session:
        return redirect(url_for("login"))

    usuario_id = session["usuario_id"]

    sincronizar_transacoes_pluggy(usuario_id)

    return redirect(url_for("dashboard"))


# =========================================================
# EXECUTAR APLICAÇÃO
# =========================================================

if __name__ == "__main__":

    app.run(debug=True)