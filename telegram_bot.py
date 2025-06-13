import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ChatMemberAdministrator,
    ChatMemberOwner,
)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
import sqlite3
from datetime import datetime, timedelta
import os
import calendar
import schedule
import time
import threading

WHATSAPP_NUMBER = "5579991196359"

from dotenv import load_dotenv

load_dotenv()

# Configuração de logging
logging.basicConfig(level=logging.INFO)

# Token do bot (deve ser configurado via variável de ambiente)
BOT_TOKEN = os.getenv("BOT_TOKEN", "SEU_TOKEN_AQUI")

# Inicialização do bot e dispatcher
bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# Estados para o FSM (Finite State Machine)


class SelecaoHorarioStates(StatesGroup):
    escolhendo_data = State()
    escolhendo_horario = State()
    servico_selecionado = State()


class AdminStates(StatesGroup):
    programando_mensagem = State()
    configurando_grupo = State()
    programando_mensagem_horario = State()
    selecionando_grupos_para_mensagem = State()
    programando_mensagem_horario_grupos_especificos = State()


# Configuração do banco de dados
def init_db():
    conn = sqlite3.connect("bot_database.db")
    cursor = conn.cursor()

    # Tabela de mensagens programadas
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS mensagens_programadas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            mensagem TEXT NOT NULL,
            horario TEXT NOT NULL,
            dias_semana TEXT,
            ativo BOOLEAN DEFAULT 1,
            grupo_id TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """
    )

    # Tabela de configurações
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS configuracoes (
            chave TEXT PRIMARY KEY,
            valor TEXT NOT NULL
        )
    """
    )

    # Tabela de pagamentos
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS pagamentos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            payment_id TEXT,
            preference_id TEXT,
            external_reference TEXT,
            status TEXT,
            amount REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """
    )

    # Tabela de grupos gerenciados
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS grupos_gerenciados (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            grupo_id TEXT NOT NULL,
            nome_grupo TEXT,
            tipo TEXT DEFAULT 'previas',
            ativo BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """
    )

    conn.commit()
    conn.close()


# Preços dos serviços
PRECOS = {"1h": 250.00, "2h": 500.00, "3h": 750.00, "pernoite": 2000.00}

# Duração dos serviços em horas
DURACOES = {
    "1h": 1,
    "2h": 2,
    "3h": 3,
    "pernoite": 12,  # Considerando pernoite como 12 horas
}

# Horários disponíveis (24h)
HORARIOS_DISPONIVEIS = [
    "08:00",
    "09:00",
    "10:00",
    "11:00",
    "12:00",
    "13:00",
    "14:00",
    "15:00",
    "16:00",
    "17:00",
    "18:00",
    "19:00",
    "20:00",
    "21:00",
    "22:00",
    "23:00",
]

# ID da vendedora (deve ser configurado)
VENDEDORA_ID = os.getenv("VENDEDORA_ID", "123456789")  # Substitua pelo ID real


# Função para verificar se o bot é admin de um grupo
async def verificar_admin_grupo(grupo_id):
    try:
        bot_member = await bot.get_chat_member(grupo_id, bot.id)
        return isinstance(bot_member, (ChatMemberAdministrator, ChatMemberOwner))
    except Exception as e:
        logging.error(f"Erro ao verificar admin do grupo {grupo_id}: {e}")
        return False


# Função para salvar grupo gerenciado
def salvar_grupo_gerenciado(grupo_id, nome_grupo, tipo="previas"):
    conn = sqlite3.connect("bot_database.db")
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT OR REPLACE INTO grupos_gerenciados (grupo_id, nome_grupo, tipo, ativo)
        VALUES (?, ?, ?, 1)
    """,
        (grupo_id, nome_grupo, tipo),
    )

    conn.commit()
    conn.close()


# Função para obter grupos gerenciados
def obter_grupos_gerenciados():
    conn = sqlite3.connect("bot_database.db")
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM grupos_gerenciados WHERE ativo = 1")
    grupos = cursor.fetchall()

    conn.close()
    return grupos


# Função para salvar mensagem programada
def salvar_mensagem_programada(mensagem, horario, dias_semana=None, grupo_id=None):
    conn = sqlite3.connect("bot_database.db")
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO mensagens_programadas (mensagem, horario, dias_semana, grupo_id, ativo)
        VALUES (?, ?, ?, ?, 1)
    """,
        (mensagem, horario, dias_semana, grupo_id),
    )

    mensagem_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return mensagem_id


# Função para obter mensagens programadas ativas
def obter_mensagens_programadas():
    conn = sqlite3.connect("bot_database.db")
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM mensagens_programadas WHERE ativo = 1")
    mensagens = cursor.fetchall()

    conn.close()
    return mensagens


# Função para enviar mensagem para grupo
async def enviar_mensagem_grupo(grupo_id, mensagem):
    try:
        await bot.send_message(grupo_id, mensagem, parse_mode="Markdown")
        logging.info(f"Mensagem enviada para grupo {grupo_id}")
        return True
    except Exception as e:
        logging.error(f"Erro ao enviar mensagem para grupo {grupo_id}: {e}")
        return False


# Função para processar mensagens programadas
async def processar_mensagens_programadas():
    """Função que roda em background para enviar mensagens programadas"""
    while True:
        try:
            agora = datetime.now()
            hora_atual = agora.strftime("%H:%M")
            dia_semana = agora.weekday()  # 0 = segunda, 6 = domingo

            mensagens = obter_mensagens_programadas()

            for msg in mensagens:
                (
                    msg_id,
                    mensagem,
                    horario,
                    dias_semana_str,
                    ativo,
                    grupo_id,
                    created_at,
                ) = msg

                # Verificar se é a hora certa
                if horario == hora_atual:
                    # Verificar se é o dia da semana correto (se especificado)
                    if dias_semana_str:
                        dias_permitidos = [int(d) for d in dias_semana_str.split(",")]
                        if dia_semana not in dias_permitidos:
                            continue

                    # Enviar mensagem
                    if grupo_id:
                        await enviar_mensagem_grupo(grupo_id, mensagem)
                    else:
                        # Se não tem grupo específico, enviar para todos os grupos
                        grupos = obter_grupos_gerenciados()
                        for grupo in grupos:
                            await enviar_mensagem_grupo(
                                grupo[1], mensagem
                            )  # grupo[1] é o grupo_id

            # Aguardar 60 segundos antes da próxima verificação
            await asyncio.sleep(60)

        except Exception as e:
            logging.error(f"Erro no processamento de mensagens programadas: {e}")
            await asyncio.sleep(60)


# Função para criar o menu principal
def get_main_menu():
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="💰 Ver Preços", callback_data="ver_precos")],
            [
                InlineKeyboardButton(
                    text="👥 Grupo de Prévias", callback_data="grupo_previas"
                )
            ],
            [InlineKeyboardButton(text="� Contato", callback_data="contato")],
        ]
    )
    return keyboard


# Função para criar o menu de preços
def get_precos_menu():
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="1 hora - R$ 250/Meu-Local", callback_data="selecionar_data_1h"
                )
            ],
            [
                InlineKeyboardButton(
                    text="Casal - R$ 400/Meu-Local", callback_data="selecionar_data_2h"
                )
            ],
            [
                InlineKeyboardButton(
                    text="Casal - R$ 500/Hotel-Motel",
                    callback_data="selecionar_data_3h",
                )
            ],
            [
                InlineKeyboardButton(
                    text="Inversão - R$ 300", callback_data="selecionar_data_pernoite"
                )
            ],
            [InlineKeyboardButton(text="🔙 Voltar", callback_data="voltar_menu")],
        ]
    )
    return keyboard


# Função para criar o menu de agendamento


# Função para criar calendário de datas
def get_calendar_keyboard(year=None, month=None):
    if year is None:
        year = datetime.now().year
    if month is None:
        month = datetime.now().month

    # Criar calendário
    cal = calendar.monthcalendar(year, month)
    month_name = calendar.month_name[month]

    keyboard = []

    # Cabeçalho com mês e ano
    keyboard.append(
        [InlineKeyboardButton(text=f"{month_name} {year}", callback_data="ignore")]
    )

    # Dias da semana
    keyboard.append(
        [
            InlineKeyboardButton(text="S", callback_data="ignore"),
            InlineKeyboardButton(text="T", callback_data="ignore"),
            InlineKeyboardButton(text="Q", callback_data="ignore"),
            InlineKeyboardButton(text="Q", callback_data="ignore"),
            InlineKeyboardButton(text="S", callback_data="ignore"),
            InlineKeyboardButton(text="S", callback_data="ignore"),
            InlineKeyboardButton(text="D", callback_data="ignore"),
        ]
    )

    # Dias do mês
    today = datetime.now().date()
    for week in cal:
        row = []
        for day in week:
            if day == 0:
                row.append(InlineKeyboardButton(text=" ", callback_data="ignore"))
            else:
                date_obj = datetime(year, month, day).date()
                if date_obj < today:
                    # Data passada - não clicável
                    row.append(
                        InlineKeyboardButton(text=str(day), callback_data="ignore")
                    )
                else:
                    # Data futura - clicável
                    date_str = f"{year}-{month:02d}-{day:02d}"
                    row.append(
                        InlineKeyboardButton(
                            text=str(day), callback_data=f"data_{date_str}"
                        )
                    )
        keyboard.append(row)

    # Navegação entre meses
    prev_month = month - 1 if month > 1 else 12
    prev_year = year if month > 1 else year - 1
    next_month = month + 1 if month < 12 else 1
    next_year = year if month < 12 else year + 1

    keyboard.append(
        [
            InlineKeyboardButton(
                text="◀️", callback_data=f"cal_{prev_year}_{prev_month}"
            ),
            InlineKeyboardButton(text="🔙 Voltar", callback_data="ver_precos"),
            InlineKeyboardButton(
                text="▶️", callback_data=f"cal_{next_year}_{next_month}"
            ),
        ]
    )

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


# Função para criar menu de horários
def get_horarios_keyboard(data, servico):
    keyboard = []

    # Agrupar horários em linhas de 3
    for i in range(0, len(HORARIOS_DISPONIVEIS), 3):
        row = []
        for j in range(i, min(i + 3, len(HORARIOS_DISPONIVEIS))):
            horario = HORARIOS_DISPONIVEIS[j]
            row.append(
                InlineKeyboardButton(
                    text=horario, callback_data=f"confirmar_{data}_{horario}_{servico}"
                )
            )
        keyboard.append(row)

    keyboard.append(
        [
            InlineKeyboardButton(
                text="🔙 Escolher outra data",
                callback_data=f"selecionar_data_{servico}",
            )
        ]
    )

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


# Função para notificar a vendedora
async def notificar_vendedora(mensagem):
    try:
        await bot.send_message(VENDEDORA_ID, mensagem, parse_mode="Markdown")
    except Exception as e:
        logging.error(f"Erro ao notificar vendedora: {e}")


# Comando /start
@dp.message(Command("start"))
async def send_welcome(message: types.Message, state: FSMContext):
    await state.clear()  # Limpar qualquer estado anterior

    # Verificar se o comando foi enviado em um grupo
    if message.chat.type in ["group", "supergroup"]:
        if str(message.from_user.id) == VENDEDORA_ID:
            if await verificar_admin_grupo(message.chat.id):
                salvar_grupo_gerenciado(str(message.chat.id), message.chat.title)
                await message.reply(
                    "Olá! Este grupo foi configurado para receber mensagens programadas. Use /admin no chat privado para gerenciar."
                )
            else:
                await message.reply(
                    "Olá! Para configurar este grupo, preciso ser administrador."
                )
        else:
            await message.reply(
                "Olá! Para interagir comigo, por favor, me chame no chat privado."
            )
        return

    # Mensagem de boas-vindas no chat privado
    welcome_message = (
        "Olá! Seja bem-vindo(a) ao meu sistema de agendamento. ✨\n\n"
        "Aqui você pode:\n"
        "💰 **Ver Preços:** Consulte os valores dos meus atendimentos.\n"
        "👥 **Grupo de Prévias:** Acesse meu grupo exclusivo com conteúdos especiais.\n"
        "📞 **Contato:** Fale diretamente comigo.\n\n"
        "Selecione uma opção abaixo para começar:\n"
    )

    await message.reply(welcome_message, reply_markup=get_main_menu())


# Comando /admin (apenas para vendedora)
@dp.message(Command("admin"))
async def admin_panel(message: types.Message, state: FSMContext):
    if str(message.from_user.id) != VENDEDORA_ID:
        await message.reply("❌ Você não tem permissão para acessar este comando.")
        return

    if message.chat.type != "private":
        await message.reply("Por favor, use este comando no chat privado comigo.")
        return

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📝 Programar Mensagem", callback_data="admin_programar_msg"
                )
            ],
            [
                InlineKeyboardButton(
                    text="⚙️ Configurações", callback_data="admin_config"
                )
            ],  # Futuro
        ]
    )
    await message.reply("Painel Administrativo:", reply_markup=keyboard)


# Processamento de callbacks (botões)
@dp.callback_query()
async def process_callback(query: types.CallbackQuery, state: FSMContext):
    query_data = query.data
    user_id = query.from_user.id
    username = query.from_user.username or query.from_user.first_name

    await query.answer()  # Importante para remover o "loading" do botão

    if query_data == "ver_precos":
        await query.message.edit_text(
            "Confira meus valores:", reply_markup=get_precos_menu()
        )

    elif query_data.startswith("selecionar_data_"):
        servico = query_data.split("_")[1]
        await state.update_data(servico_selecionado=servico)
        await query.message.edit_text(
            "Selecione a data desejada:", reply_markup=get_calendar_keyboard()
        )
        await state.set_state(SelecaoHorarioStates.escolhendo_data)

    elif query_data.startswith("cal_"):
        _, year, month = query_data.split("_")
        await query.message.edit_reply_markup(
            reply_markup=get_calendar_keyboard(int(year), int(month))
        )

    elif query_data.startswith("data_"):
        data_selecionada_str = query_data.split("_")[1]
        # CORREÇÃO APLICADA AQUI:
        await state.update_data(data_selecionada=data_selecionada_str)
        user_data = await state.get_data()
        servico = user_data.get("servico_selecionado")

        if not servico:
            await query.message.edit_text(
                "❌ Ocorreu um erro. Por favor, comece o agendamento novamente.",
                reply_markup=get_main_menu(),
            )
            await state.clear()
            return

        await query.message.edit_text(
            f"📅 Você selecionou a data: {data_selecionada_str}\nEscolha um horário disponível para o serviço de {servico.replace('h', ' hora').replace('pernoite', 'Pernoite')}:",
            reply_markup=get_horarios_keyboard(data_selecionada_str, servico),
        )
        await state.set_state(SelecaoHorarioStates.escolhendo_horario)

    elif query_data.startswith("confirmar_"):
        _, data, horario, servico = query_data.split("_")

        user_data = await state.get_data()

        # Construir a mensagem para o WhatsApp
        mensagem_whatsapp = f"Olá! Gostaria de agendar um atendimento de {servico.replace('h', ' hora').replace('pernoite', 'Pernoite')} para o dia {data} às {horario}."

        # Link do WhatsApp
        whatsapp_link = f"https://wa.me/{WHATSAPP_NUMBER}?text={mensagem_whatsapp}"

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="✅ Confirmar e Pagar", url=whatsapp_link)],
                [
                    InlineKeyboardButton(
                        text="🔙 Voltar ao Menu Principal", callback_data="voltar_menu"
                    )
                ],
            ]
        )

        await query.message.edit_text(
            f"🎉 Agendamento quase concluído!\n\n"
            f"Serviço: {servico.replace('h', ' hora').replace('pernoite', 'Pernoite')}\n"
            f"Data: {data}\n"
            f"Horário: {horario}\n\n"
            f'Clique em "Confirmar e Pagar" para finalizar o agendamento e ser redirecionado(a) para o WhatsApp para combinar o pagamento.',
            reply_markup=keyboard,
        )
        await state.clear()  # Limpar o estado após a confirmação

    elif query_data == "grupo_previas":
        # Aqui você pode adicionar o link para o grupo de prévias
        await query.message.edit_text(
            "Acesse nosso grupo de prévias exclusivo para conteúdos especiais! [Link do Grupo](https://t.me/+FgJVW0A6p0wzMGU5)",
            parse_mode="Markdown",
            reply_markup=get_main_menu(),
        )

    elif query_data == "contato":
        # Aqui você pode adicionar as informações de contato
        await query.message.edit_text(
            f"Para falar diretamente comigo, entre em contato via WhatsApp: [Clique aqui](https://wa.me/{+5579991196359})",
            parse_mode="Markdown",
            reply_markup=get_main_menu(),
        )

    elif query_data == "voltar_menu":
        await query.message.edit_text(
            "Selecione uma opção abaixo para começar:", reply_markup=get_main_menu()
        )

    elif query_data == "admin_programar_msg":
        await query.message.edit_text(
            "Envie a mensagem que deseja programar:",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="🔙 Voltar", callback_data="admin_panel"
                        )
                    ]
                ]
            ),
        )
        await state.set_state(AdminStates.programando_mensagem)

    elif query_data == "admin_panel":
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="📝 Programar Mensagem",
                        callback_data="admin_programar_msg",
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="⚙️ Configurações", callback_data="admin_config"
                    )
                ],
            ]
        )
        await query.message.edit_text("Painel Administrativo:", reply_markup=keyboard)

    elif query_data == "admin_config":
        await query.message.edit_text(
            "Configurações (em desenvolvimento).",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="🔙 Voltar", callback_data="admin_panel"
                        )
                    ]
                ]
            ),
        )


@dp.message(AdminStates.programando_mensagem)
async def receber_mensagem_programar(message: types.Message, state: FSMContext):
    mensagem_para_programar = message.text
    await state.update_data(mensagem_programada=mensagem_para_programar)

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Enviar para todos os grupos gerenciados",
                    callback_data="programar_msg_todos_grupos",
                )
            ],
            [
                InlineKeyboardButton(
                    text="Escolher grupos específicos",
                    callback_data="programar_msg_escolher_grupos",
                )
            ],
            [InlineKeyboardButton(text="🔙 Voltar", callback_data="admin_panel")],
        ]
    )
    await message.reply(
        "Mensagem recebida. Agora, escolha onde enviar e quando:", reply_markup=keyboard
    )
    await state.set_state(
        AdminStates.configurando_grupo
    )  # Mudar para um estado mais apropriado, talvez para escolher horário e grupos


@dp.callback_query(AdminStates.configurando_grupo)
async def configurar_programacao_mensagem(
    query: types.CallbackQuery, state: FSMContext
):
    query_data = query.data
    await query.answer()

    if query_data == "programar_msg_todos_grupos":
        user_data = await state.get_data()
        mensagem = user_data.get("mensagem_programada")

        # Solicitar horário
        await query.message.edit_text(
            "Por favor, envie o horário (HH:MM) para a mensagem programada (ex: 10:30):"
        )
        await state.set_state(
            AdminStates.programando_mensagem_horario
        )  # Novo estado para receber o horário

    elif query_data == "programar_msg_escolher_grupos":
        grupos = obter_grupos_gerenciados()
        if not grupos:
            await query.message.edit_text(
                "Nenhum grupo gerenciado encontrado. Por favor, adicione grupos primeiro.",
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=[
                        [
                            InlineKeyboardButton(
                                text="🔙 Voltar", callback_data="admin_panel"
                            )
                        ]
                    ]
                ),
            )
            await state.clear()
            return

        keyboard_grupos = []
        for grupo in grupos:
            keyboard_grupos.append(
                [
                    InlineKeyboardButton(
                        text=grupo[2], callback_data=f"selecionar_grupo_{grupo[1]}"
                    )
                ]
            )  # grupo[2] é o nome, grupo[1] é o ID

        keyboard_grupos.append(
            [InlineKeyboardButton(text="🔙 Voltar", callback_data="admin_panel")]
        )

        await query.message.edit_text(
            "Selecione os grupos para enviar a mensagem:",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard_grupos),
        )
        await state.set_state(
            AdminStates.selecionando_grupos_para_mensagem
        )  # Novo estado para seleção de grupos

    elif query_data == "admin_panel":
        await state.clear()
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="📝 Programar Mensagem",
                        callback_data="admin_programar_msg",
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="⚙️ Configurações", callback_data="admin_config"
                    )
                ],
            ]
        )
        await query.message.edit_text("Painel Administrativo:", reply_markup=keyboard)


@dp.message(AdminStates.programando_mensagem_horario)
async def receber_horario_programar(message: types.Message, state: FSMContext):
    horario = message.text
    # Validação simples de formato HH:MM
    try:
        datetime.strptime(horario, "%H:%M")
    except ValueError:
        await message.reply(
            "Formato de horário inválido. Por favor, use HH:MM (ex: 10:30)."
        )
        return

    user_data = await state.get_data()
    mensagem = user_data.get("mensagem_programada")

    # Por enquanto, salva sem dias da semana ou grupo específico
    salvar_mensagem_programada(mensagem, horario)
    await message.reply(
        "Mensagem programada com sucesso para todos os grupos gerenciados neste horário!",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🔙 Voltar ao Painel Admin", callback_data="admin_panel"
                    )
                ]
            ]
        ),
    )
    await state.clear()


@dp.callback_query(AdminStates.selecionando_grupos_para_mensagem)
async def selecionar_grupos_para_mensagem(
    query: types.CallbackQuery, state: FSMContext
):
    query_data = query.data
    await query.answer()

    if query_data.startswith("selecionar_grupo_"):
        grupo_id_selecionado = query_data.split("_")[2]
        user_data = await state.get_data()

        # Adicionar o grupo selecionado à lista de grupos para a mensagem
        grupos_selecionados = user_data.get("grupos_selecionados_msg", [])
        if grupo_id_selecionado not in grupos_selecionados:
            grupos_selecionados.append(grupo_id_selecionado)
            await state.update_data(grupos_selecionados_msg=grupos_selecionados)
            await query.message.edit_text(
                f"Grupo {grupo_id_selecionado} adicionado. Selecione mais ou finalize:",
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=[
                        [
                            InlineKeyboardButton(
                                text="Finalizar seleção e programar",
                                callback_data="finalizar_selecao_grupos",
                            )
                        ],
                        [
                            InlineKeyboardButton(
                                text="🔙 Voltar", callback_data="admin_panel"
                            )
                        ],
                    ]
                ),
            )
        else:
            await query.message.edit_text(
                f"Grupo {grupo_id_selecionado} já selecionado. Selecione mais ou finalize:",
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=[
                        [
                            InlineKeyboardButton(
                                text="Finalizar seleção e programar",
                                callback_data="finalizar_selecao_grupos",
                            )
                        ],
                        [
                            InlineKeyboardButton(
                                text="🔙 Voltar", callback_data="admin_panel"
                            )
                        ],
                    ]
                ),
            )

    elif query_data == "finalizar_selecao_grupos":
        user_data = await state.get_data()
        grupos_selecionados = user_data.get("grupos_selecionados_msg", [])
        mensagem = user_data.get("mensagem_programada")

        if not grupos_selecionados:
            await query.message.edit_text(
                "Nenhum grupo selecionado. Por favor, selecione pelo menos um grupo.",
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=[
                        [
                            InlineKeyboardButton(
                                text="🔙 Voltar", callback_data="admin_panel"
                            )
                        ]
                    ]
                ),
            )
            return

        await query.message.edit_text(
            "Por favor, envie o horário (HH:MM) para a mensagem programada (ex: 10:30):"
        )
        await state.set_state(
            AdminStates.programando_mensagem_horario_grupos_especificos
        )  # Novo estado para receber o horário para grupos específicos

    elif query_data == "admin_panel":
        await state.clear()
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="📝 Programar Mensagem",
                        callback_data="admin_programar_msg",
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="⚙️ Configurações", callback_data="admin_config"
                    )
                ],
            ]
        )
        await query.message.edit_text("Painel Administrativo:", reply_markup=keyboard)


@dp.message(AdminStates.programando_mensagem_horario_grupos_especificos)
async def receber_horario_programar_grupos_especificos(
    message: types.Message, state: FSMContext
):
    horario = message.text
    try:
        datetime.strptime(horario, "%H:%M")
    except ValueError:
        await message.reply(
            "Formato de horário inválido. Por favor, use HH:MM (ex: 10:30)."
        )
        return

    user_data = await state.get_data()
    mensagem = user_data.get("mensagem_programada")
    grupos_selecionados = user_data.get("grupos_selecionados_msg", [])

    for grupo_id in grupos_selecionados:
        salvar_mensagem_programada(mensagem, horario, grupo_id=grupo_id)

    await message.reply(
        "Mensagem programada com sucesso para os grupos selecionados neste horário!",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🔙 Voltar ao Painel Admin", callback_data="admin_panel"
                    )
                ]
            ]
        ),
    )
    await state.clear()


# Função principal para iniciar o bot
async def main():
    init_db()
    # Iniciar o processamento de mensagens programadas em uma tarefa em segundo plano
    asyncio.create_task(processar_mensagens_programadas())
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.info("Bot iniciado!")
    asyncio.run(main())
