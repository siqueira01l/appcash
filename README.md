# 💰 FinanceDash

Um dashboard financeiro desenvolvido em **Python e Flask** para ajudar usuários a controlar suas finanças pessoais de forma simples e organizada.

O projeto permite registrar receitas e despesas, acompanhar o saldo e visualizar informações financeiras através de um dashboard.

## 🚀 Funcionalidades

* 👤 Cadastro e autenticação de usuários
* 🔐 Sistema de login e logout
* 💵 Cadastro de receitas
* 💸 Cadastro de despesas
* 📊 Dashboard financeiro
* 💰 Cálculo automático de receitas, despesas e saldo
* 📋 Visualização das transações
* 🔒 Dados separados por usuário
* 🗄️ Persistência de dados utilizando SQLite
* 🔑 Senhas armazenadas de forma segura

## 🛠️ Tecnologias utilizadas

* **Python**
* **Flask**
* **SQLAlchemy**
* **SQLite**
* **HTML5**
* **CSS3**
* **Jinja2**

## 📂 Estrutura do projeto

```text
FinanceDash/
│
├── app.py
├── models.py
├── requirements.txt
├── instance/
│   └── database.db
│
├── templates/
│   ├── login.html
│   ├── cadastro.html
│   ├── dashboard.html
│   └── ...
│
├── static/
│   ├── css/
│   │   └── style.css
│   └── ...
│
└── README.md
```

> A estrutura pode variar de acordo com a organização atual do projeto.

## ⚙️ Como executar o projeto

### 1. Clone o repositório

```bash
git clone https://github.com/SEU-USUARIO/FinanceDash.git
```

Entre na pasta:

```bash
cd FinanceDash
```

### 2. Crie um ambiente virtual

No Windows:

```bash
python -m venv venv
```

Ative o ambiente virtual:

```bash
venv\Scripts\activate
```

### 3. Instale as dependências

```bash
pip install -r requirements.txt
```

### 4. Execute o projeto

```bash
python app.py
```

Depois, acesse no navegador:

```text
http://127.0.0.1:5000
```

## 📊 Dashboard

O dashboard apresenta informações financeiras do usuário, permitindo acompanhar:

* Total de receitas
* Total de despesas
* Saldo atual
* Histórico de transações

## 🗄️ Banco de dados

O projeto utiliza **SQLite** para armazenamento dos dados e **SQLAlchemy** para comunicação com o banco.

Cada usuário possui suas próprias transações, garantindo que os dados financeiros sejam associados corretamente à sua conta.

## 🔐 Segurança

O sistema utiliza recursos do Flask para gerenciamento de sessões e autenticação.

As senhas dos usuários são armazenadas utilizando **hash**, evitando que sejam salvas diretamente em texto puro.

> ⚠️ Nunca publique senhas, chaves de API, tokens ou outras credenciais no repositório.

## 🎯 Objetivo do projeto

O FinanceDash foi desenvolvido como um projeto prático para aplicar conhecimentos de:

* Desenvolvimento web com Python
* Backend com Flask
* Bancos de dados relacionais
* ORM com SQLAlchemy
* Autenticação de usuários
* Desenvolvimento de interfaces web
* Integração entre frontend e backend

## 🔮 Próximas melhorias

Algumas funcionalidades que podem ser adicionadas futuramente:

* [ ] Gráficos de receitas e despesas
* [ ] Filtros por período
* [ ] Categorias de gastos
* [ ] Exportação de dados
* [ ] Relatórios financeiros
* [ ] Modo escuro
* [ ] Melhorias de responsividade
* [ ] API REST
* [ ] Deploy em produção

## 👨‍💻 Autor

**Arthur Siqueira**

Estudante de Ciência da Computação e desenvolvedor interessado em **desenvolvimento de software, backend e cibersegurança**.

---

⭐ Se você gostou do projeto, considere deixar uma estrela no repositório!
