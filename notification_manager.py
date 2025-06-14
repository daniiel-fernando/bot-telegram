import asyncio
import logging
from datetime import datetime, timedelta
import sqlite3
from telegram_bot import bot, obter_grupos_gerenciados, obter_mensagens_programadas, enviar_mensagem_grupo, get_all_rifa_subscribers, get_rifa_config

# Configurar logging
logging.basicConfig(level=logging.INFO)

class NotificationManager:
    def __init__(self):
        self.running = False
    
    async def start(self):
        """Inicia o gerenciador de notificações"""
        self.running = True
        logging.info("Gerenciador de notificações iniciado")
        
        # Executar tarefas em paralelo
        await asyncio.gather(
            self.processar_mensagens_programadas(),
            self.verificar_agendamentos_pendentes(),
            self.limpar_agendamentos_expirados(),
            self.verificar_lembretes_agendamento(),
            self.enviar_notificacao_rifa_inscritos(), # Nova função para rifa
            self.publicar_rifa_no_grupo() # Nova função para publicar rifa no grupo
        )
    
    async def stop(self):
        """Para o gerenciador de notificações"""
        self.running = False
        logging.info("Gerenciador de notificações parado")
    
    async def processar_mensagens_programadas(self):
        """Processa e envia mensagens programadas"""
        while self.running:
            try:
                agora = datetime.now()
                hora_atual = agora.strftime("%H:%M")
                dia_semana = agora.weekday()  # 0 = segunda, 6 = domingo
                
                mensagens = obter_mensagens_programadas()
                
                for msg in mensagens:
                    msg_id, mensagem, horario, dias_semana, ativo, grupo_id, tipo, media_file_id, created_at = msg
                    
                    # Verificar se é a hora certa
                    if horario == hora_atual:
                        # Verificar se é o dia da semana correto (se especificado)
                        if dias_semana:
                            dias_permitidos = [int(d) for d in dias_semana.split(",")]
                            if dia_semana not in dias_permitidos:
                                continue
                        
                        # Enviar mensagem
                        if grupo_id:
                            await enviar_mensagem_grupo(grupo_id, mensagem, tipo, media_file_id)
                            logging.info(f"Mensagem programada {msg_id} enviada para grupo {grupo_id}")
                        else:
                            # Se não tem grupo específico, enviar para todos os grupos
                            grupos = obter_grupos_gerenciados()
                            for grupo in grupos:
                                await enviar_mensagem_grupo(grupo[1], mensagem, tipo, media_file_id)  # grupo[1] é o grupo_id
                                logging.info(f"Mensagem programada {msg_id} enviada para grupo {grupo[1]}")
                
                # Aguardar 60 segundos antes da próxima verificação
                await asyncio.sleep(60)
                
            except Exception as e:
                logging.error(f"Erro no processamento de mensagens programadas: {e}")
                await asyncio.sleep(60)
    
    async def enviar_notificacao_rifa_inscritos(self):
        """Envia notificações da rifa para usuários inscritos"""
        while self.running:
            try:
                # Intervalo de 12 ou 24 horas, configurável
                intervalo_horas = int(get_rifa_config("intervalo_notificacao_inscritos") or 12)
                await asyncio.sleep(intervalo_horas * 3600) # Converter horas para segundos

                mensagem_rifa = get_rifa_config("mensagem_rifa_texto")
                tipo_mensagem = get_rifa_config("mensagem_rifa_tipo")
                media_id = get_rifa_config("mensagem_rifa_media_id")
                link_rifa = get_rifa_config("link_rifa")

                if not mensagem_rifa or not link_rifa:
                    logging.warning("Mensagem ou link da rifa não configurados. Pulando notificação para inscritos.")
                    continue

                subscribers = get_all_rifa_subscribers()
                if not subscribers:
                    logging.info("Nenhum inscrito na rifa para enviar notificação.")
                    continue

                full_message = f"{mensagem_rifa}\n\nParticipe aqui: {link_rifa}"

                for user_id in subscribers:
                    try:
                        if tipo_mensagem == 'photo' and media_id:
                            await bot.send_photo(chat_id=user_id, photo=media_id, caption=full_message, parse_mode="Markdown")
                        elif tipo_mensagem == 'video' and media_id:
                            await bot.send_video(chat_id=user_id, video=media_id, caption=full_message, parse_mode="Markdown")
                        else:
                            await bot.send_message(user_id, full_message, parse_mode="Markdown")
                        logging.info(f"Notificação da rifa enviada para o inscrito: {user_id}")
                        await asyncio.sleep(1) # Pequeno delay para evitar flood
                    except Exception as e:
                        logging.error(f"Erro ao enviar notificação da rifa para {user_id}: {e}")

            except Exception as e:
                logging.error(f"Erro no processamento de notificações da rifa para inscritos: {e}")
                await asyncio.sleep(60) # Espera um minuto antes de tentar novamente em caso de erro

    async def publicar_rifa_no_grupo(self):
        """Publica a mensagem da rifa nos grupos gerenciados"""
        while self.running:
            try:
                # Intervalo de 24 horas, configurável
                intervalo_horas = int(get_rifa_config("intervalo_publicacao_grupo") or 24)
                await asyncio.sleep(intervalo_horas * 3600) # Converter horas para segundos

                mensagem_rifa = get_rifa_config("mensagem_rifa_texto")
                tipo_mensagem = get_rifa_config("mensagem_rifa_tipo")
                media_id = get_rifa_config("mensagem_rifa_media_id")
                link_rifa = get_rifa_config("link_rifa")

                if not mensagem_rifa or not link_rifa:
                    logging.warning("Mensagem ou link da rifa não configurados. Pulando publicação no grupo.")
                    continue

                grupos = obter_grupos_gerenciados()
                if not grupos:
                    logging.info("Nenhum grupo gerenciado para publicar a rifa.")
                    continue
                
                full_message = f"{mensagem_rifa}\n\nParticipe aqui: {link_rifa}"

                for grupo in grupos:
                    grupo_id = grupo[1] # grupo[1] é o grupo_id
                    try:
                        if tipo_mensagem == 'photo' and media_id:
                            await bot.send_photo(chat_id=grupo_id, photo=media_id, caption=full_message, parse_mode="Markdown")
                        elif tipo_mensagem == 'video' and media_id:
                            await bot.send_video(chat_id=grupo_id, video=media_id, caption=full_message, parse_mode="Markdown")
                        else:
                            await bot.send_message(grupo_id, full_message, parse_mode="Markdown")
                        logging.info(f"Publicação da rifa enviada para o grupo: {grupo_id}")
                        await asyncio.sleep(1) # Pequeno delay para evitar flood
                    except Exception as e:
                        logging.error(f"Erro ao publicar rifa no grupo {grupo_id}: {e}")

            except Exception as e:
                logging.error(f"Erro no processamento de publicação da rifa nos grupos: {e}")
                await asyncio.sleep(60) # Espera um minuto antes de tentar novamente em caso de erro

    async def verificar_agendamentos_pendentes(self):
        """Verifica agendamentos com pagamento pendente há muito tempo"""
        while self.running:
            try:
                # Verificar a cada 30 minutos
                await asyncio.sleep(1800)  # 30 minutos
                
                # Buscar agendamentos pendentes há mais de 30 minutos
                conn = sqlite3.connect("bot_database.db")
                cursor = conn.cursor()
                
                limite_tempo = datetime.now() - timedelta(minutes=30)
                
                cursor.execute("""
                    SELECT * FROM agendamentos 
                    WHERE status = 'aguardando_pagamento' 
                    AND created_at < ?
                """, (limite_tempo.strftime("%Y-%m-%d %H:%M:%S"),))
                
                agendamentos_expirados = cursor.fetchall()
                
                for ag in agendamentos_expirados:
                    agendamento_id = ag[0]
                    user_id = ag[1]
                    username = ag[2]
                    
                    # Atualizar status para expirado
                    cursor.execute("""
                        UPDATE agendamentos 
                        SET status = 'expirado' 
                        WHERE id = ?
                    """, (agendamento_id,))
                    
                    # Notificar cliente sobre expiração
                    try:
                        mensagem_expiracao = f"""
⏰ **AGENDAMENTO EXPIRADO**

Olá @{username or 'Cliente'}!

Seu agendamento #{agendamento_id} expirou por falta de pagamento.

Para fazer um novo agendamento, use /start

💡 **Dica**: Complete o pagamento em até 30 minutos após criar o agendamento.
"""
                        await bot.send_message(user_id, mensagem_expiracao, parse_mode="Markdown")
                        logging.info(f"Notificação de expiração enviada para usuário {user_id}")
                        
                    except Exception as e:
                        logging.error(f"Erro ao notificar usuário {user_id} sobre expiração: {e}")
                
                conn.commit()
                conn.close()
                
                if agendamentos_expirados:
                    logging.info(f"{len(agendamentos_expirados)} agendamentos expirados processados")
                
            except Exception as e:
                logging.error(f"Erro na verificação de agendamentos pendentes: {e}")
    
    async def limpar_agendamentos_expirados(self):
        """Remove agendamentos muito antigos do banco de dados"""
        while self.running:
            try:
                # Executar limpeza a cada 24 horas
                await asyncio.sleep(86400)  # 24 horas
                
                conn = sqlite3.connect("bot_database.db")
                cursor = conn.cursor()
                
                # Remover agendamentos expirados há mais de 7 dias
                limite_limpeza = datetime.now() - timedelta(days=7)
                
                cursor.execute("""
                    DELETE FROM agendamentos 
                    WHERE status IN ('expirado', 'cancelado') 
                    AND created_at < ?
                """, (limite_limpeza.strftime("%Y-%m-%d %H:%M:%S"),))
                
                removidos = cursor.rowcount
                
                # Remover pagamentos órfãos
                cursor.execute("""
                    DELETE FROM pagamentos 
                    WHERE agendamento_id NOT IN (SELECT id FROM agendamentos)
                """
                )
                
                pagamentos_removidos = cursor.rowcount
                
                conn.commit()
                conn.close()
                
                if removidos > 0 or pagamentos_removidos > 0:
                    logging.info(f"Limpeza concluída: {removidos} agendamentos e {pagamentos_removidos} pagamentos removidos")
                
            except Exception as e:
                logging.error(f"Erro na limpeza de agendamentos: {e}")
    
    async def enviar_lembrete_agendamento(self, agendamento_id, user_id, username, servico, data, horario):
        """Envia lembrete de agendamento próximo"""
        try:
            mensagem_lembrete = f"""
🔔 **LEMBRETE DE AGENDAMENTO**

Olá @{username or 'Cliente'}!

Você tem um agendamento hoje:

🕐 Serviço: {servico}
📅 Data: {data}
⏰ Horário: {horario}
🆔 ID: {agendamento_id}

Nos vemos em breve! 💕

Para reagendar ou cancelar, entre em contato.
"""
            await bot.send_message(user_id, mensagem_lembrete, parse_mode="Markdown")
            logging.info(f"Lembrete enviado para usuário {user_id} - agendamento {agendamento_id}")
            
        except Exception as e:
            logging.error(f"Erro ao enviar lembrete para usuário {user_id}: {e}")
    
    async def verificar_lembretes_agendamento(self):
        """Verifica e envia lembretes de agendamentos do dia seguinte"""
        while self.running:
            try:
                # Verificar a cada hora
                await asyncio.sleep(3600)  # 1 hora
                
                # Verificar se é 20:00 (hora de enviar lembretes)
                agora = datetime.now()
                if agora.hour == 20:  # 8 PM
                    amanha = (agora + timedelta(days=1)).strftime("%Y-%m-%d")
                    
                    conn = sqlite3.connect("bot_database.db")
                    cursor = conn.cursor()
                    
                    # Buscar agendamentos para amanhã
                    cursor.execute("""
                        SELECT * FROM agendamentos 
                        WHERE data = ? AND status = 'pago'
                        ORDER BY horario
                    """, (amanha,))
                    
                    agendamentos_amanha = cursor.fetchall()
                    conn.close()
                    
                    for ag in agendamentos_amanha:
                        agendamento_id = ag[0]
                        user_id = ag[1]
                        username = ag[2]
                        servico = ag[3]
                        data = ag[5]
                        horario = ag[6]
                        
                        # Enviar lembrete
                        await self.enviar_lembrete_agendamento(
                            agendamento_id, user_id, username, servico, data, horario
                        )
                        
                        # Aguardar um pouco entre envios para não sobrecarregar
                        await asyncio.sleep(2)
                    
                    if agendamentos_amanha:
                        logging.info(f"{len(agendamentos_amanha)} lembretes enviados para agendamentos de amanhã")
                
            except Exception as e:
                logging.error(f"Erro na verificação de lembretes: {e}")

# Função para executar o gerenciador de notificações
async def main():
    notification_manager = NotificationManager()
    
    try:
        await notification_manager.start()
    except KeyboardInterrupt:
        logging.info("Interrompido pelo usuário")
    finally:
        await notification_manager.stop()

if __name__ == '__main__':
    asyncio.run(main())


