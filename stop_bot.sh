#!/bin/bash

# Script para parar todos os componentes do bot

echo "🛑 Parando Bot do Telegram..."

# Função para parar um processo
stop_process() {
    local process_name=$1
    local pids=$(pgrep -f "$process_name")
    
    if [ -n "$pids" ]; then
        echo "🔄 Parando $process_name (PIDs: $pids)..."
        kill $pids
        sleep 2
        
        # Verificar se ainda está rodando
        local remaining_pids=$(pgrep -f "$process_name")
        if [ -n "$remaining_pids" ]; then
            echo "⚠️  Forçando parada de $process_name (PIDs: $remaining_pids)..."
            kill -9 $remaining_pids
        fi
        
        echo "✅ $process_name parado"
    else
        echo "ℹ️  $process_name não estava rodando"
    fi
}

# Parar todos os componentes
stop_process "telegram_bot.py"
stop_process "webhook_server.py"
stop_process "notification_manager.py"

echo ""
echo "🔍 Verificando processos restantes..."
remaining=$(ps aux | grep -E "(telegram_bot|webhook_server|notification_manager)" | grep -v grep)

if [ -n "$remaining" ]; then
    echo "⚠️  Alguns processos ainda estão rodando:"
    echo "$remaining"
else
    echo "✅ Todos os componentes foram parados com sucesso!"
fi

echo ""
echo "🎉 Bot parado!"

