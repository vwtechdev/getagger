# getagger

Gerador de etiquetas de devolucao de pecas para tecnicos de atendimento.

## Funcionalidades

- Cadastro de atendimentos (chamado, peca, defeito)
- Importacao de Nota Fiscal em PDF com extracao automatica de itens
- Associacao visual por drag & drop entre pecas da NF e atendimentos
- Geracao de etiquetas de pecas (1 por peca) em PDF
- Geracao de etiquetas de romaneio (1 por volume) em PDF separado
- Reimpressao de etiquetas
- Isolamento de dados por tecnico
- Tema escuro exclusivo com layout responsivo

## Stack

- Python 3.9 / Django 4.2
- PostgreSQL 16
- Bootstrap 5.3, HTMX, Alpine.js, SortableJS
- pdfplumber (extracao de PDF), ReportLab (geracao de PDF)

## Desenvolvimento

```bash
# Iniciar banco
docker compose up -d db

# Ativar ambiente
source venv/bin/activate

# Migracoes
python manage.py migrate
python manage.py makemigrations

# Servidor
python manage.py runserver

# Testes
python manage.py test
```

Login por e-mail. Superuser padrao: `tecnico@example.com` / `getagger123`.

---

Desenvolvido por VWTech Dev.
