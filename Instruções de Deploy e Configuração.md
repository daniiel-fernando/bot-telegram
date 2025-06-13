# Instruções de Deploy e Configuração

## Pré-requisitos

### Sistema Operacional
- Ubuntu 20.04+ ou similar
- Python 3.8+
- Acesso à internet
- Permissões de administrador (sudo)

### Contas Necessárias
1. **Telegram Bot**: Criar bot via @BotFather
2. **Mercado Pago**: Conta de desenvolvedor ativa
3. **Servidor**: VPS ou servidor dedicado (opcional para produção)

## Instalação Passo a Passo

### 1. Preparação do Ambiente

```bash
# Atualizar sistema
sudo apt update && sudo apt upgrade -y

# Instalar Python e pip
sudo apt install python3 python3-pip python3-venv -y

# Criar diretório do projeto
mkdir telegram_bot_vendas
cd telegram_bot_vendas
```

### 2. Configuração do Ambiente Virtual

```bash
# Criar ambiente virtual
python3 -m venv venv

# Ativar ambiente virtual
source venv/bin/activate

# Instalar dependências
pip install aiogram mercadopago flask
```

### 3. Configuração do Bot no Telegram

1. Acesse @BotFather no Telegram
2. Envie `/newbot`
3. Escolha um nome para o bot
4. Escolha um username (deve terminar com 'bot')
5. Copie o token fornecido

### 4. Configuração do Mercado Pago

1. Acesse https://www.mercadopago.com.br/developers
2. Crie uma aplicação
3. Obtenha o Access Token e Public Key
4. Configure webhook URL (se usando servidor público)

### 5. Configuração das Variáveis de Ambiente

Crie o arquivo `.env`:

```bash
# Informações do Bot
BOT_TOKEN=SEU_TOKEN_DO_BOT_AQUI
VENDEDORA_ID=SEU_ID_DO_TELEGRAM

# Mercado Pago
MERCADO_PAGO_ACCESS_TOKEN=SEU_ACCESS_TOKEN
MERCADO_PAGO_PUBLIC_KEY=SUA_PUBLIC_KEY
MERCADO_PAGO_PRODUCTION=false

# Configurações opcionais
WEBHOOK_URL=https://seudominio.com/mercadopago/webhook
```

### 6. Deploy dos Arquivos

Copie todos os arquivos Python para o diretório do projeto:
- telegram_bot.py
- webhook_server.py
- notification_manager.py
- mercadopago_integration.py
- start_bot.sh
- stop_bot.sh

### 7. Configuração de Permissões

```bash
# Tornar scripts executáveis
chmod +x start_bot.sh stop_bot.sh

# Criar diretório de logs
mkdir logs
```

### 8. Teste Local

```bash
# Iniciar o bot
./start_bot.sh

# Verificar se está funcionando
ps aux | grep -E "(telegram_bot|webhook_server|notification_manager)"

# Testar bot no Telegram
# Envie /start para o bot
```

## Configuração para Produção

### 1. Servidor VPS

Para produção, recomenda-se usar um VPS com:
- 1GB RAM mínimo
- 10GB espaço em disco
- IP fixo
- Ubuntu 20.04+

### 2. Configuração de Domínio

```bash
# Instalar nginx
sudo apt install nginx -y

# Configurar proxy reverso para webhook
sudo nano /etc/nginx/sites-available/telegram_bot
```

Configuração nginx:
```nginx
server {
    listen 80;
    server_name seudominio.com;

    location /mercadopago/webhook {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### 3. SSL/HTTPS

```bash
# Instalar certbot
sudo apt install certbot python3-certbot-nginx -y

# Obter certificado SSL
sudo certbot --nginx -d seudominio.com
```

### 4. Configuração de Webhook no Mercado Pago

```bash
# Configurar webhook URL no Mercado Pago
curl -X POST \
  'https://api.mercadopago.com/v1/webhooks' \
  -H 'Authorization: Bearer SEU_ACCESS_TOKEN' \
  -H 'Content-Type: application/json' \
  -d '{
    "url": "https://seudominio.com/mercadopago/webhook",
    "events": ["payment"]
  }'
```

### 5. Serviço Systemd (Opcional)

Criar serviço para inicialização automática:

```bash
sudo nano /etc/systemd/system/telegram-bot.service
```

Conteúdo do serviço:
```ini
[Unit]
Description=Telegram Bot Vendas
After=network.target

[Service]
Type=forking
User=ubuntu
WorkingDirectory=/home/ubuntu/telegram_bot_vendas
ExecStart=/home/ubuntu/telegram_bot_vendas/start_bot.sh
ExecStop=/home/ubuntu/telegram_bot_vendas/stop_bot.sh
Restart=always

[Install]
WantedBy=multi-user.target
```

Ativar serviço:
```bash
sudo systemctl enable telegram-bot
sudo systemctl start telegram-bot
```

## Configuração Inicial do Bot

### 1. Obter ID do Telegram

Para obter seu ID do Telegram:
1. Envie uma mensagem para @userinfobot
2. Copie o ID numérico retornado
3. Use este ID na variável VENDEDORA_ID

### 2. Configurar Grupos

1. Adicione o bot ao grupo de prévias
2. Promova o bot a administrador
3. Execute `/start` no grupo
4. Confirme que o bot foi configurado corretamente

### 3. Testar Funcionalidades

1. **Agendamento**: Teste o fluxo completo de agendamento
2. **Pagamento**: Faça um pagamento teste (use modo sandbox)
3. **Mensagens**: Configure uma mensagem automática de teste
4. **Admin**: Acesse o painel administrativo com `/admin`

## Monitoramento e Manutenção

### 1. Logs

Monitore os logs regularmente:
```bash
# Ver logs em tempo real
tail -f logs/telegram_bot.log
tail -f logs/webhook_server.log
tail -f logs/notification_manager.log
```

### 2. Backup

Configure backup automático:
```bash
# Criar script de backup
nano backup.sh
```

Script de backup:
```bash
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
cp bot_database.db backups/backup_$DATE.db
find backups/ -name "backup_*.db" -mtime +7 -delete
```

### 3. Atualizações

```bash
# Atualizar dependências
pip install --upgrade aiogram mercadopago flask

# Reiniciar bot após atualizações
./stop_bot.sh
./start_bot.sh
```

## Solução de Problemas

### Bot não responde
1. Verificar se os processos estão rodando
2. Verificar logs de erro
3. Validar token do bot
4. Verificar conectividade

### Pagamentos não funcionam
1. Verificar credenciais Mercado Pago
2. Verificar webhook URL
3. Testar em modo sandbox primeiro
4. Verificar logs do webhook server

### Mensagens automáticas não enviadas
1. Verificar permissões do bot nos grupos
2. Verificar configuração de horários
3. Verificar se notification_manager está rodando

## Suporte

Para suporte técnico:
1. Verificar logs de erro
2. Consultar documentação técnica
3. Verificar issues conhecidos
4. Contatar desenvolvedor se necessário

---

**Instruções de Deploy v1.0**  
**Dezembro 2025**

