# Getagger

Getagger é uma aplicação web desenvolvida em Django para automatizar o processo dos técnicos da Wyntech Serviços em Tecnologia da Informação, com objetivo principal de gerar etiquetas para devolução de peças com defeito para o estoque conforme padrões do estoque da empresa.

## Funcionalidades

- Cadastro de Peças com defeito (chamado, peça, defeito)
- Importacao de Nota Fiscal em PDF com extracao automatica de itens
- Associacao visual por drag & drop entre peças da NF e peças com defeitos
- Geracao de etiquetas de peças (1 por peça) em PDF
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
