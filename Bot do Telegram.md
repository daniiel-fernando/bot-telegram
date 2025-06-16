# Bot do Telegram para Vendedora de Conteúdo +18

## Descrição

Bot completo para automação de vendas e agendamentos, desenvolvido especificamente para vendedoras de conteúdo +18. O sistema integra funcionalidades avançadas de agendamento, processamento de pagamentos via Mercado Pago, administração de grupos e envio de mensagens automáticas.

## Funcionalidades Principais

### 🤖 Bot Principal
- Menu interativo para clientes
- Sistema de agendamento inteligente
- Verificação automática de disponibilidade
- Calendário interativo para seleção de datas
- Processamento automático de pagamentos

### 💰 Sistema de Pagamentos
- Integração completa com Mercado Pago
- Suporte a todas as formas de pagamento (Pix, cartão, boleto)
- Processamento automático via webhooks
- Confirmação instantânea de pagamentos
- Relatórios financeiros detalhados

### 📅 Agendamento Inteligente
- Verificação automática de conflitos
- Bloqueio manual de horários
- Notificações automáticas para vendedora
- Lembretes para clientes
- Gestão completa da agenda

### 👥 Administração de Grupos
- Bot administrador automático
- Mensagens programadas diárias
- Múltiplos grupos simultâneos
- Conteúdo personalizado por grupo
- Análise de engajamento

### 🔔 Notificações Automáticas
- Confirmações de agendamento
- Alertas de pagamento
- Lembretes de atendimento
- Mensagens promocionais
- Relatórios periódicos

### 🛡️ Segurança e Privacidade
- Criptografia de dados
- Controle de acesso rigoroso
- Logs de auditoria
- Backup automático
- Conformidade com LGPD

## Preços dos Serviços

- **1 hora**: R$ 250,00
- **2 horas**: R$ 500,00
- **3 horas**: R$ 750,00
- **Pernoite**: R$ 2.000,00

## Arquivos do Projeto

### Código Principal
- `telegram_bot.py` - Bot principal do Telegram
- `webhook_server.py` - Servidor para webhooks do Mercado Pago
- `notification_manager.py` - Gerenciador de notificações
- `mercadopago_integration.py` - Integração com Mercado Pago

### Scripts de Controle
- `start_bot.sh` - Iniciar todos os componentes
- `stop_bot.sh` - Parar todos os componentes

### Documentação
- `manual_bot.md` - Manual completo do usuário
- `manual_bot.pdf` - Manual em PDF
- `documentacao_tecnica.md` - Documentação técnica
- `DEPLOY.md` - Instruções de instalação
- `README.md` - Este arquivo

### Configuração
- `requirements.txt` - Dependências Python
- `.env.example` - Exemplo de configuração
- `todo.md` - Lista de tarefas do projeto

## Instalação Rápida

### 1. Clonar/Baixar Arquivos
```bash
# Criar diretório do projeto
mkdir telegram_bot_vendas
cd telegram_bot_vendas

# Copiar todos os arquivos para este diretório
```

### 2. Instalar Dependências
```bash
# Criar ambiente virtual
python3 -m venv venv
source venv/bin/activate

# Instalar dependências
pip install -r requirements.txt
```

### 3. Configurar Variáveis
```bash
# Copiar exemplo de configuração
cp .env.example .env

# Editar com suas credenciais
nano .env
```

### 4. Executar
```bash
# Tornar scripts executáveis
chmod +x start_bot.sh stop_bot.sh

# Iniciar bot
./start_bot.sh
```

## Configuração Necessária

### Telegram Bot
1. Acesse @BotFather no Telegram
2. Crie um novo bot com `/newbot`
3. Copie o token fornecido
4. Configure no arquivo `.env`

### Mercado Pago
1. Acesse https://www.mercadopago.com.br/developers
2. Crie uma aplicação
3. Obtenha Access Token e Public Key
4. Configure no arquivo `.env`

### ID do Telegram
1. Envie mensagem para @userinfobot
2. Copie seu ID numérico
3. Configure como VENDEDORA_ID no `.env`

## Exemplo de Configuração (.env)

```bash
# Token do bot do Telegram
BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz

# ID do Telegram da vendedora
VENDEDORA_ID=123456789

# Credenciais do Mercado Pago
MERCADO_PAGO_ACCESS_TOKEN=APP_USR-123456789
MERCADO_PAGO_PUBLIC_KEY=APP_USR-123456789
MERCADO_PAGO_PRODUCTION=false

# URL do webhook (para produção)
WEBHOOK_URL=https://seudominio.com/mercadopago/webhook
```

## Como Usar

### Para Clientes
1. Iniciar conversa com o bot
2. Escolher "Agendar Atendimento"
3. Selecionar serviço desejado
4. Escolher data e horário
5. Realizar pagamento via Mercado Pago
6. Receber confirmação automática

### Para Vendedora
1. Usar `/admin` para acessar painel
2. Visualizar agendamentos
3. Programar mensagens automáticas
4. Gerenciar grupos
5. Bloquear horários quando necessário

## Estrutura de Logs

```
logs/
├── telegram_bot.log         # Interações do bot
├── webhook_server.log       # Processamento de pagamentos
└── notification_manager.log # Mensagens automáticas
```

## Banco de Dados

O sistema usa SQLite com as seguintes tabelas:
- `agendamentos` - Agendamentos dos clientes
- `pagamentos` - Histórico de pagamentos
- `mensagens_programadas` - Mensagens automáticas
- `grupos_gerenciados` - Grupos do Telegram
- `horarios_bloqueados` - Horários indisponíveis
- `configuracoes` - Configurações do sistema

## Comandos Úteis

```bash
# Verificar status dos processos
ps aux | grep -E "(telegram_bot|webhook_server|notification_manager)"

# Ver logs em tempo real
tail -f logs/telegram_bot.log

# Backup do banco de dados
cp bot_database.db backup_$(date +%Y%m%d).db

# Reiniciar bot
./stop_bot.sh && ./start_bot.sh
```

## Suporte e Manutenção

### Logs de Erro
Monitore regularmente os arquivos de log para identificar problemas:
- Erros de conectividade
- Falhas de pagamento
- Problemas de permissão

### Backup
Faça backup regular do arquivo `bot_database.db` que contém todos os dados importantes.

### Atualizações
Mantenha as dependências atualizadas:
```bash
pip install --upgrade -r requirements.txt
```

## Segurança

- ✅ Dados de pagamento processados pelo Mercado Pago
- ✅ Controle de acesso por ID do Telegram
- ✅ Logs de auditoria completos
- ✅ Criptografia de comunicações
- ✅ Backup automático de dados

## Licença

Este projeto foi desenvolvido especificamente para uso comercial da vendedora. Todos os direitos reservados.

## Contato

Para suporte técnico ou dúvidas sobre o sistema, consulte:
1. Manual do usuário (`manual_bot.pdf`)
2. Documentação técnica (`documentacao_tecnica.md`)
3. Instruções de deploy (`DEPLOY.md`)

---

**Desenvolvido por Manus AI**  
**Versão 1.0 - Dezembro 2025**

