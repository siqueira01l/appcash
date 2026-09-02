from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, date

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
    
    usuario_id = session["usuario_id"]
    
    transacoes = Transacao.query.filter_by(
        usuario_id=usuario_id
    ).order_by(Transacao.data.desc()).all()
    
    receitas = sum(
        transacao.valor
        for transacao in transacoes
        if transacao.tipo == "receita"
    )
    
    despesas = sum(
        transacao.valor
        for transacao in transacoes
        if transacao.tipo == "despesa"
    )
    
    saldo = receitas - despesas
    
    return render_template(
        "dashboard.html",
        transacoes=transacoes,
        receitas=receitas,
        despesas=despesas,
        saldo=saldo
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
        

if __name__ == "__main__":
    app.run(debug=True)