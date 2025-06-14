#!/bin/bash

# Script para executar todos os componentes do bot

echo "🤖 Iniciando Bot do Telegram..."

# Função para verificar se um processo está rodando
check_process() {
    if pgrep -f "$1" > /dev/null; then
        echo "✅ $1 já está rodando"
        return 0
    else
        echo "❌ $1 não está rodando"
        return 1
    fi
}

# Função para iniciar um processo em background
start_process() {
    local script_name=$1
    local log_file=$2
    
    echo "🚀 Iniciando $script_name..."
    nohup python "$script_name" > "$log_file" 2>&1 &
    local pid=$!
    echo "📝 PID: $pid | Log: $log_file"
    sleep 2
    
    if kill -0 $pid 2>/dev/null; then
        echo "✅ $script_name iniciado com sucesso"
    else
        echo "❌ Erro ao iniciar $script_name"
        cat "$log_file"
    fi
}

# Criar diretório de logs se não existir
mkdir -p logs

echo "🔍 Verificando processos existentes..."

# Verificar se os processos já estão rodando
if check_process "telegram_bot.py" && check_process "notification_manager.py"; then
    echo "🎉 Todos os componentes já estão rodando!"
    echo ""
    echo "📊 Status dos processos:"
    ps aux | grep -E "(telegram_bot|notification_manager)" | grep -v grep
    exit 0
fi

echo ""
echo "🚀 Iniciando componentes do bot..."

# Iniciar o bot principal do Telegram
if ! check_process "telegram_bot.py"; then
    start_process "telegram_bot.py" "logs/telegram_bot.log"
fi

# Aguardar um pouco antes de iniciar o próximo
sleep 3

# Iniciar o gerenciador de notificações
if ! check_process "notification_manager.py"; then
    start_process "notification_manager.py" "logs/notification_manager.log"
fi

echo ""
echo "⏳ Aguardando inicialização completa..."
sleep 5

echo ""
echo "📊 Status final dos processos:"
ps aux | grep -E "(telegram_bot|notification_manager)" | grep -v grep

echo ""
echo "🎉 Bot iniciado com sucesso!"
echo ""
echo "📋 Componentes ativos:"
echo "  🤖 Bot do Telegram (telegram_bot.py)"
echo "  🔔 Gerenciador de Notificações (notification_manager.py)"
echo ""
echo "📁 Logs disponíveis em:"
echo "  📄 logs/telegram_bot.log"
echo "  📄 logs/notification_manager.log"
echo ""
echo "🛑 Para parar todos os processos, execute: ./stop_bot.sh"
echo ""
echo "🔍 Acompanhando logs ao vivo (Ctrl+C para parar):"
tail -f logs/telegram_bot.log



