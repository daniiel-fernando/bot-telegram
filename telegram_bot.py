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
    configurando_rifa = State()
    configurando_mensagem_rifa = State()
    aguardando_mensagem_programada = State()
    aguardando_horario_mensagem_programada = State()
    aguardando_dias_semana_mensagem_programada = State()
    selecionando_tipo_mensagem_programada = State()


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
            tipo TEXT DEFAULT 'text', -- 'text' ou 'photo'
            media_file_id TEXT, -- ID da foto/vídeo no Telegram
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

    # Nova tabela para configurações da rifa
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS rifa_configuracoes (
            chave TEXT PRIMARY KEY,
            valor TEXT NOT NULL
        )
    """
    )

    # Nova tabela para inscritos na rifa
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS rifa_inscritos (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
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
ADMIN_ID = os.getenv("ADMIN_ID", "1447551455,7575373579")  # Substitua pelo ID real


# Funções de utilidade para o banco de dados
def get_db_connection():
    return sqlite3.connect("bot_database.db")


def get_config(chave):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT valor FROM configuracoes WHERE chave = ?", (chave,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None


def set_config(chave, valor):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT OR REPLACE INTO configuracoes (chave, valor) VALUES (?, ?)",
        (chave, valor),
    )
    conn.commit()
    conn.close()


def get_rifa_config(chave):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT valor FROM rifa_configuracoes WHERE chave = ?", (chave,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None


def set_rifa_config(chave, valor):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT OR REPLACE INTO rifa_configuracoes (chave, valor) VALUES (?, ?)",
        (chave, valor),
    )
    conn.commit()
    conn.close()


def is_user_subscribed_to_rifa(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM rifa_inscritos WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result is not None


def subscribe_user_to_rifa(user_id, username):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT OR IGNORE INTO rifa_inscritos (user_id, username) VALUES (?, ?)",
        (user_id, username),
    )
    conn.commit()
    conn.close()


def unsubscribe_user_from_rifa(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM rifa_inscritos WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()


def get_all_rifa_subscribers():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM rifa_inscritos")
    subscribers = [row[0] for row in cursor.fetchall()]
    conn.close()
    return subscribers


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
def salvar_mensagem_programada(
    mensagem, horario, dias_semana=None, grupo_id=None, tipo="text", media_file_id=None
):
    conn = sqlite3.connect("bot_database.db")
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO mensagens_programadas (mensagem, horario, dias_semana, grupo_id, ativo, tipo, media_file_id)
        VALUES (?, ?, ?, ?, 1, ?, ?)
    """,
        (mensagem, horario, dias_semana, grupo_id, tipo, media_file_id),
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
async def enviar_mensagem_grupo(grupo_id, mensagem, tipo="text", media_file_id=None):
    try:
        if tipo == "photo" and media_file_id:
            await bot.send_photo(
                chat_id=grupo_id,
                photo=media_file_id,
                caption=mensagem,
                parse_mode="Markdown",
            )
        elif tipo == "video" and media_file_id:
            await bot.send_video(
                chat_id=grupo_id,
                video=media_file_id,
                caption=mensagem,
                parse_mode="Markdown",
            )
        else:
            await bot.send_message(grupo_id, mensagem, parse_mode="Markdown")
        logging.info(f"Mensagem enviada para grupo {grupo_id}")
        return True
    except Exception as e:
        logging.error(f"Erro ao enviar mensagem para grupo {grupo_id}: {e}")
        return False


# Função para processar mensagens programadas (removida para notification_manager.py)


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
            [InlineKeyboardButton(text="🎟️ Rifa", callback_data="rifa")],
            [InlineKeyboardButton(text="📞 Contato", callback_data="contato")],
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
        await bot.send_message(ADMIN_ID, mensagem, parse_mode="Markdown")
    except Exception as e:
        logging.error(f"Erro ao notificar vendedora: {e}")


# Comando /start
@dp.message(Command("start"))
async def send_welcome(message: types.Message, state: FSMContext):
    await state.clear()  # Limpar qualquer estado anterior

    # Verificar se o comando foi enviado em um grupo
    if message.chat.type in ["group", "supergroup"]:
        if str(message.from_user.id) == ADMIN_ID:
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
    if str(message.from_user.id) != ADMIN_ID:
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
            ],
            [
                InlineKeyboardButton(
                    text="🎟️ Configurar Rifa", callback_data="admin_config_rifa"
                )
            ],
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

    elif query_data.startswith("data_"):
        data_selecionada = query_data.split("_")[1]
        servico_selecionado = (await state.get_data()).get("servico_selecionado")
        await state.update_data(data_selecionada=data_selecionada)
        await query.message.edit_text(
            f"Data selecionada: {data_selecionada}\nSelecione o horário:",
            reply_markup=get_horarios_keyboard(data_selecionada, servico_selecionado),
        )

    elif query_data.startswith("cal_"):
        _, year, month = query_data.split("_")
        await query.message.edit_text(
            "Selecione a data desejada:",
            reply_markup=get_calendar_keyboard(int(year), int(month)),
        )

    elif query_data.startswith("confirmar_"):
        _, data, horario, servico = query_data.split("_")
        user_id = query.from_user.id
        username = query.from_user.username or query.from_user.first_name

        # Aqui você integraria com o Mercado Pago ou outro sistema de pagamento
        # Por enquanto, vamos simular um agendamento
        mensagem_confirmacao = (
            f"✅ Agendamento Confirmado!\n\n"
            f"Serviço: {servico}\n"
            f"Data: {data}\n"
            f"Horário: {horario}\n\n"
            f"Em breve entrarei em contato para finalizar os detalhes."
        )
        await query.message.edit_text(mensagem_confirmacao)

        # Notificar a vendedora
        await notificar_vendedora(
            f"Novo agendamento de {username} ({user_id}): {servico} em {data} às {horario}"
        )

    elif query_data == "grupo_previas":
        await query.message.edit_text(
            "Acesse nosso grupo de prévias aqui:(https://t.me/seu_grupo_de_previas)"
        )

    elif query_data == "contato":
        await query.message.edit_text(
            f"Entre em contato via WhatsApp: [Clique aqui](https://wa.me/{WHATSAPP_NUMBER})"
        )

    elif query_data == "rifa":
        rifa_link = get_rifa_config("link_rifa")
        if rifa_link:
            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="Acessar Rifa", url=rifa_link)],
                    [
                        InlineKeyboardButton(
                            text="Inscrever-me para Notificações",
                            callback_data="rifa_inscrever",
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            text="Cancelar Notificações", callback_data="rifa_cancelar"
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            text="🔙 Voltar", callback_data="voltar_menu"
                        )
                    ],
                ]
            )
            await query.message.edit_text(
                "🎉 Participe da nossa rifa!", reply_markup=keyboard
            )
        else:
            await query.message.edit_text(
                "Desculpe, o link da rifa ainda não foi configurado.",
                reply_markup=get_main_menu(),
            )

    elif query_data == "rifa_inscrever":
        if not is_user_subscribed_to_rifa(user_id):
            subscribe_user_to_rifa(user_id, username)
            await query.message.edit_text(
                "✅ Você foi inscrito(a) para receber notificações da rifa!",
                reply_markup=get_main_menu(),
            )
        else:
            await query.message.edit_text(
                "Você já está inscrito(a) para receber notificações da rifa.",
                reply_markup=get_main_menu(),
            )

    elif query_data == "rifa_cancelar":
        if is_user_subscribed_to_rifa(user_id):
            unsubscribe_user_from_rifa(user_id)
            await query.message.edit_text(
                "❌ Você cancelou as notificações da rifa.",
                reply_markup=get_main_menu(),
            )
        else:
            await query.message.edit_text(
                "Você não está inscrito(a) para receber notificações da rifa.",
                reply_markup=get_main_menu(),
            )

    elif query_data == "admin_config_rifa":
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🔗 Definir Link da Rifa",
                        callback_data="admin_set_rifa_link",
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="📝 Definir Mensagem da Rifa",
                        callback_data="admin_set_rifa_message",
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🔙 Voltar ao Admin", callback_data="admin_panel"
                    )
                ],
            ]
        )
        await query.message.edit_text("Configurações da Rifa:", reply_markup=keyboard)

    elif query_data == "admin_set_rifa_link":
        await state.set_state(AdminStates.configurando_rifa)
        await query.message.edit_text("Por favor, envie o novo link da rifa:")

    elif query_data == "admin_set_rifa_message":
        await state.set_state(AdminStates.configurando_mensagem_rifa)
        await query.message.edit_text(
            "Por favor, envie a nova mensagem para a rifa (pode incluir foto/vídeo):"
        )

    elif query_data == "admin_programar_msg":
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="Para Usuários",
                        callback_data="admin_programar_msg_usuarios",
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="Para Grupos", callback_data="admin_programar_msg_grupos"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🔙 Voltar ao Admin", callback_data="admin_panel"
                    )
                ],
            ]
        )
        await query.message.edit_text("Programar Mensagem:", reply_markup=keyboard)

    elif query_data == "admin_config":
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="Gerenciar Grupos", callback_data="admin_gerenciar_grupos"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🔙 Voltar ao Admin", callback_data="admin_panel"
                    )
                ],
            ]
        )
        await query.message.edit_text("Configurações Gerais:", reply_markup=keyboard)

    elif query_data == "admin_programar_msg_usuarios":
        await state.set_state(AdminStates.aguardando_mensagem_programada)
        await state.update_data(target_type="users")
        await query.message.edit_text(
            "Por favor, envie a mensagem que deseja programar para os usuários (pode incluir foto/vídeo):"
        )

    elif query_data == "admin_programar_msg_grupos":
        grupos = obter_grupos_gerenciados()
        if not grupos:
            await query.message.edit_text(
                "Nenhum grupo gerenciado encontrado. Por favor, adicione o bot a um grupo e use /start nele para que ele seja registrado.",
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=[
                        [
                            InlineKeyboardButton(
                                text="🔙 Voltar ao Admin", callback_data="admin_panel"
                            )
                        ]
                    ]
                ),
            )
            return

        keyboard_buttons = []
        for grupo in grupos:
            keyboard_buttons.append(
                [
                    InlineKeyboardButton(
                        text=grupo[2], callback_data=f"select_group_{grupo[1]}"
                    )
                ]
            )
        keyboard_buttons.append(
            [
                InlineKeyboardButton(
                    text="🔙 Voltar", callback_data="admin_programar_msg"
                )
            ]
        )
        keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
        await query.message.edit_text(
            "Selecione o(s) grupo(s) para esta mensagem:", reply_markup=keyboard
        )

    elif query_data.startswith("select_group_"):
        group_id = query.data.split("_")[2]
        current_data = await state.get_data()
        selected_groups = current_data.get("selected_groups", [])
        if group_id not in selected_groups:
            selected_groups.append(group_id)
            await state.update_data(selected_groups=selected_groups)
            await query.message.edit_text(
                f"Grupo {group_id} selecionado. Envie a mensagem ou selecione mais grupos."
            )
        else:
            await query.message.edit_text(
                f"Grupo {group_id} já selecionado. Envie a mensagem ou selecione mais grupos."
            )
        await state.set_state(AdminStates.aguardando_mensagem_programada)
        await state.update_data(target_type="groups")

    elif query_data == "admin_gerenciar_grupos":
        grupos = obter_grupos_gerenciados()
        if not grupos:
            await query.message.edit_text(
                "Nenhum grupo gerenciado encontrado.",
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=[
                        [
                            InlineKeyboardButton(
                                text="🔙 Voltar ao Admin", callback_data="admin_panel"
                            )
                        ]
                    ]
                ),
            )
            return

        keyboard_buttons = []
        for grupo in grupos:
            status = "Ativo" if grupo[4] else "Inativo"
            keyboard_buttons.append(
                [
                    InlineKeyboardButton(
                        text=f"{grupo[2]} ({status})",
                        callback_data=f"manage_group_{grupo[1]}",
                    )
                ]
            )
        keyboard_buttons.append(
            [
                InlineKeyboardButton(
                    text="🔙 Voltar ao Admin", callback_data="admin_panel"
                )
            ]
        )
        keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
        await query.message.edit_text("Gerenciar Grupos:", reply_markup=keyboard)

    elif query_data.startswith("manage_group_"):
        group_id = query.data.split("_")[2]
        # Aqui você pode adicionar opções para ativar/desativar o grupo, remover, etc.
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="Ativar/Desativar",
                        callback_data=f"toggle_group_status_{group_id}",
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="Remover Grupo", callback_data=f"remove_group_{group_id}"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🔙 Voltar", callback_data="admin_gerenciar_grupos"
                    )
                ],
            ]
        )
        await query.message.edit_text(
            f"Opções para o grupo {group_id}:", reply_markup=keyboard
        )

    elif query_data.startswith("toggle_group_status_"):
        group_id = query.data.split("_")[2]
        # Lógica para alternar o status do grupo no banco de dados
        await query.message.edit_text(
            f"Status do grupo {group_id} alternado.",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="🔙 Voltar", callback_data="admin_gerenciar_grupos"
                        )
                    ]
                ]
            ),
        )

    elif query_data.startswith("remove_group_"):
        group_id = query.data.split("_")[2]
        # Lógica para remover o grupo do banco de dados
        await query.message.edit_text(
            f"Grupo {group_id} removido.",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="🔙 Voltar", callback_data="admin_gerenciar_grupos"
                        )
                    ]
                ]
            ),
        )

    elif query_data == "voltar_menu":
        await query.message.edit_text(
            "Selecione uma opção abaixo para começar:", reply_markup=get_main_menu()
        )


@dp.message(AdminStates.configurando_rifa)
async def process_set_rifa_link(message: types.Message, state: FSMContext):
    if str(message.from_user.id) != ADMIN_ID:
        await message.reply("❌ Você não tem permissão para realizar esta ação.")
        await state.clear()
        return

    rifa_link = message.text
    set_rifa_config("link_rifa", rifa_link)
    await message.reply(f"✅ Link da rifa atualizado para: {rifa_link}")
    await state.clear()
    await admin_panel(message, state)  # Voltar ao painel admin


@dp.message(AdminStates.configurando_mensagem_rifa)
async def process_set_rifa_message(message: types.Message, state: FSMContext):
    if str(message.from_user.id) != ADMIN_ID:
        await message.reply("❌ Você não tem permissão para realizar esta ação.")
        await state.clear()
        return

    mensagem = message.caption if message.caption else message.text
    media_file_id = None
    tipo = "text"

    if message.photo:
        media_file_id = message.photo[-1].file_id
        tipo = "photo"
    elif message.video:
        media_file_id = message.video.file_id
        tipo = "video"

    set_rifa_config("mensagem_rifa_texto", mensagem)
    set_rifa_config("mensagem_rifa_tipo", tipo)
    set_rifa_config("mensagem_rifa_media_id", media_file_id if media_file_id else "")

    await message.reply("✅ Mensagem da rifa atualizada com sucesso!")
    await state.clear()
    await admin_panel(message, state)  # Voltar ao painel admin


@dp.message(AdminStates.aguardando_mensagem_programada)
async def process_programar_mensagem(message: types.Message, state: FSMContext):
    if str(message.from_user.id) != ADMIN_ID:
        await message.reply("❌ Você não tem permissão para realizar esta ação.")
        await state.clear()
        return

    mensagem_texto = message.caption if message.caption else message.text
    media_file_id = None
    tipo = "text"

    if message.photo:
        media_file_id = message.photo[-1].file_id
        tipo = "photo"
    elif message.video:
        media_file_id = message.video.file_id
        tipo = "video"

    await state.update_data(
        mensagem_texto=mensagem_texto, media_file_id=media_file_id, tipo_mensagem=tipo
    )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=f"{h}:00", callback_data=f"set_time_{h}")
                for h in range(8, 24, 2)
            ],
            [
                InlineKeyboardButton(
                    text="🔙 Voltar", callback_data="admin_programar_msg"
                )
            ],
        ]
    )
    await state.set_state(AdminStates.aguardando_horario_mensagem_programada)
    await message.reply(
        "Agora, selecione o horário para enviar a mensagem:", reply_markup=keyboard
    )


@dp.callback_query(lambda query: query.data.startswith("set_time_"))
async def process_set_time_programar_mensagem(
    query: types.CallbackQuery, state: FSMContext
):
    logging.info(f"Callback 'set_time_' received. Query data: {query.data}")
    await query.answer()
    horario = query.data.split("_")[1]
    await state.update_data(horario_programado=horario)

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Todos os Dias", callback_data="set_days_all")],
            [InlineKeyboardButton(text="Segunda", callback_data="set_days_1")],
            [InlineKeyboardButton(text="Terça", callback_data="set_days_2")],
            [InlineKeyboardButton(text="Quarta", callback_data="set_days_3")],
            [InlineKeyboardButton(text="Quinta", callback_data="set_days_4")],
            [InlineKeyboardButton(text="Sexta", callback_data="set_days_5")],
            [InlineKeyboardButton(text="Sábado", callback_data="set_days_6")],
            [InlineKeyboardButton(text="Domingo", callback_data="set_days_0")],
            [
                InlineKeyboardButton(
                    text="🔙 Voltar", callback_data="admin_programar_msg"
                )
            ],
        ]
    )
    await state.set_state(AdminStates.aguardando_dias_semana_mensagem_programada)
    await query.message.edit_text(
        "Selecione os dias da semana para a mensagem (ou 'Todos os Dias'):",
        reply_markup=keyboard,
    )


@dp.callback_query(lambda query: query.data.startswith("set_days_"))
async def process_set_days_programar_mensagem(
    query: types.CallbackQuery, state: FSMContext
):
    await query.answer()
    dias_semana_raw = query.data.split("_")[1]
    dias_semana = None
    if dias_semana_raw != "all":
        dias_semana = dias_semana_raw

    data = await state.get_data()
    mensagem_texto = data.get("mensagem_texto")
    horario_programado = data.get("horario_programado")
    tipo_mensagem = data.get("tipo_mensagem")
    media_file_id = data.get("media_file_id")
    target_type = data.get("target_type")
    selected_groups = data.get("selected_groups", [])

    if target_type == "users":
        salvar_mensagem_programada(
            mensagem_texto,
            horario_programado,
            dias_semana,
            None,
            tipo_mensagem,
            media_file_id,
        )
        await query.message.edit_text(
            "✅ Mensagem programada para usuários com sucesso!",
            reply_markup=get_main_menu(),
        )
    elif target_type == "groups":
        for group_id in selected_groups:
            salvar_mensagem_programada(
                mensagem_texto,
                horario_programado,
                dias_semana,
                group_id,
                tipo_mensagem,
                media_file_id,
            )
        await query.message.edit_text(
            "✅ Mensagem programada para os grupos selecionados com sucesso!",
            reply_markup=get_main_menu(),
        )

    await state.clear()


async def main():
    init_db()
    # Iniciar o bot
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
