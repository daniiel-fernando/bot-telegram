# Documentação Técnica do Bot do Telegram

## Arquitetura do Sistema

### Visão Geral

O bot é composto por três componentes principais que trabalham em conjunto:

1. **telegram_bot.py** - Bot principal que gerencia interações com usuários
2. **webhook_server.py** - Servidor Flask para processar webhooks do Mercado Pago
3. **notification_manager.py** - Gerenciador de notificações e mensagens automáticas

### Dependências

```python
aiogram==3.20.0.post0
mercadopago==2.3.0
flask==2.3.3
sqlite3 (built-in)
asyncio (built-in)
```

### Estrutura de Arquivos

```
/
├── telegram_bot.py              # Bot principal
├── webhook_server.py            # Servidor webhook
├── notification_manager.py      # Gerenciador de notificações
├── mercadopago_integration.py   # Integração Mercado Pago
├── start_bot.sh                 # Script de inicialização
├── stop_bot.sh                  # Script para parar o bot
├── bot_database.db              # Banco de dados SQLite
├── logs/                        # Diretório de logs
│   ├── telegram_bot.log
│   ├── webhook_server.log
│   └── notification_manager.log
└── .env                         # Variáveis de ambiente
```

## Banco de Dados

### Schema das Tabelas

#### agendamentos
```sql
CREATE TABLE agendamentos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    username TEXT,
    servico TEXT NOT NULL,
    preco REAL NOT NULL,
    data TEXT NOT NULL,
    horario TEXT NOT NULL,
    status TEXT DEFAULT 'pendente',
    payment_id TEXT,
    preference_id TEXT,
    external_reference TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### mensagens_programadas
```sql
CREATE TABLE mensagens_programadas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    mensagem TEXT NOT NULL,
    horario TEXT NOT NULL,
    dias_semana TEXT,
    ativo BOOLEAN DEFAULT 1,
    grupo_id TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### grupos_gerenciados
```sql
CREATE TABLE grupos_gerenciados (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    grupo_id TEXT NOT NULL,
    nome_grupo TEXT,
    tipo TEXT DEFAULT 'previas',
    ativo BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### pagamentos
```sql
CREATE TABLE pagamentos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    agendamento_id INTEGER,
    payment_id TEXT,
    preference_id TEXT,
    external_reference TEXT,
    status TEXT,
    amount REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (agendamento_id) REFERENCES agendamentos (id)
);
```

#### horarios_bloqueados
```sql
CREATE TABLE horarios_bloqueados (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    data TEXT NOT NULL,
    horario_inicio TEXT NOT NULL,
    horario_fim TEXT NOT NULL,
    motivo TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### configuracoes
```sql
CREATE TABLE configuracoes (
    chave TEXT PRIMARY KEY,
    valor TEXT NOT NULL
);
```

## APIs e Integrações

### Telegram Bot API

O bot utiliza a biblioteca `aiogram` para interagir com a API do Telegram. Principais funcionalidades:

- Processamento de comandos e callbacks
- Envio de mensagens formatadas
- Gerenciamento de estados (FSM)
- Administração de grupos

### Mercado Pago API

Integração completa com a API do Mercado Pago para processamento de pagamentos:

#### Endpoints Utilizados

- `POST /checkout/preferences` - Criar preferência de pagamento
- `GET /v1/payments/{id}` - Consultar status de pagamento
- Webhook notifications - Receber notificações de mudança de status

#### Fluxo de Pagamento

1. Cliente confirma agendamento
2. Sistema cria preferência no Mercado Pago
3. Cliente é redirecionado para checkout
4. Mercado Pago processa pagamento
5. Webhook notifica mudança de status
6. Sistema atualiza agendamento automaticamente

## Funcionalidades Principais

### Sistema de Estados (FSM)

```python
class AgendamentoStates(StatesGroup):
    escolhendo_servico = State()
    escolhendo_data = State()
    escolhendo_horario = State()
    confirmando_agendamento = State()
    aguardando_pagamento = State()

class AdminStates(StatesGroup):
    programando_mensagem = State()
    configurando_grupo = State()
    bloqueando_horario = State()
```

### Verificação de Disponibilidade

```python
def verificar_disponibilidade(data, horario_inicio, duracao_horas):
    # Verifica conflitos com agendamentos existentes
    # Verifica horários bloqueados manualmente
    # Retorna True se horário está disponível
```

### Processamento de Webhooks

```python
@app.route('/mercadopago/webhook', methods=['POST'])
def mercadopago_webhook():
    # Processa notificações do Mercado Pago
    # Atualiza status dos agendamentos
    # Envia notificações para vendedora
```

## Configuração e Deploy

### Variáveis de Ambiente Obrigatórias

```bash
BOT_TOKEN=                    # Token do @BotFather
VENDEDORA_ID=                 # ID do Telegram da vendedora
MERCADO_PAGO_ACCESS_TOKEN=    # Access token do Mercado Pago
MERCADO_PAGO_PUBLIC_KEY=      # Public key do Mercado Pago
MERCADO_PAGO_PRODUCTION=      # true/false para produção/teste
```

### Comandos de Execução

```bash
# Iniciar todos os componentes
./start_bot.sh

# Parar todos os componentes
./stop_bot.sh

# Verificar status dos processos
ps aux | grep -E "(telegram_bot|webhook_server|notification_manager)"
```

### Logs e Monitoramento

Logs são gerados automaticamente em:
- `logs/telegram_bot.log` - Interações do bot
- `logs/webhook_server.log` - Processamento de webhooks
- `logs/notification_manager.log` - Mensagens automáticas

## Segurança

### Medidas Implementadas

1. **Autenticação por ID**: Apenas a vendedora tem acesso administrativo
2. **Validação de Webhooks**: Verificação de integridade das notificações
3. **Criptografia**: Todas as comunicações usam HTTPS/TLS
4. **Isolamento de Dados**: Informações de pagamento não são armazenadas localmente
5. **Logs de Auditoria**: Registro completo de todas as operações

### Boas Práticas

- Manter credenciais em variáveis de ambiente
- Backup regular do banco de dados
- Monitoramento contínuo dos logs
- Atualizações regulares das dependências
- Teste de recuperação de desastres

## Manutenção

### Rotinas Recomendadas

#### Diária
- Verificar logs de erro
- Confirmar funcionamento dos componentes
- Monitorar métricas de performance

#### Semanal
- Backup do banco de dados
- Análise de métricas de negócio
- Verificação de atualizações de segurança

#### Mensal
- Limpeza de dados antigos
- Otimização do banco de dados
- Revisão de configurações

### Comandos Úteis

```bash
# Backup do banco de dados
cp bot_database.db backup_$(date +%Y%m%d).db

# Verificar espaço em disco
df -h

# Monitorar uso de recursos
top -p $(pgrep -f telegram_bot)

# Verificar conectividade com APIs
curl -s https://api.telegram.org/bot$BOT_TOKEN/getMe
curl -s https://api.mercadopago.com/v1/payment_methods
```

## Troubleshooting

### Problemas Comuns

#### Bot não responde
1. Verificar se o processo está rodando
2. Verificar conectividade com internet
3. Validar token do bot
4. Verificar logs de erro

#### Pagamentos não processados
1. Verificar webhook server
2. Validar credenciais Mercado Pago
3. Verificar URL do webhook
4. Analisar logs do webhook

#### Mensagens automáticas não enviadas
1. Verificar notification_manager
2. Validar permissões do bot nos grupos
3. Verificar configuração de horários
4. Analisar logs de notificação

### Códigos de Erro Comuns

- `401 Unauthorized` - Token inválido
- `403 Forbidden` - Permissões insuficientes
- `429 Too Many Requests` - Rate limit excedido
- `500 Internal Server Error` - Erro interno da API

## Extensões Futuras

### Funcionalidades Planejadas

1. **Dashboard Web**: Interface web para administração
2. **Relatórios Avançados**: Analytics detalhados
3. **Integração WhatsApp**: Suporte a múltiplas plataformas
4. **Sistema de Cupons**: Promoções e descontos
5. **API REST**: Integração com outros sistemas

### Arquitetura Escalável

O sistema foi projetado para suportar:
- Múltiplos bots simultâneos
- Distribuição de carga
- Banco de dados externo (PostgreSQL)
- Cache distribuído (Redis)
- Monitoramento avançado (Prometheus/Grafana)

---

**Documentação Técnica v1.0**  
**Última atualização: Dezembro 2025**

