## Tarefas para o Bot do Telegram

### Fase 1: Análise e estruturação do projeto
- [x] Detalhar as funcionalidades do bot.
- [x] Definir a arquitetura do bot (linguagem, frameworks, banco de dados).
- [x] Esboçar o fluxo de interação do usuário com o bot.
- [x] Pesquisar sobre a API do Telegram para bots.
- [x] Pesquisar sobre a API do Mercado Pago para pagamentos.
- [x] Pesquisar sobre bibliotecas Python para desenvolvimento de bots no Telegram.

### Fase 2: Configuração do ambiente e dependências
- [x] Instalar as dependências necessárias.
- [x] Configurar o ambiente de desenvolvimento.

### Fase 3: Desenvolvimento do bot principal
- [x] Criar a estrutura básica do bot.
- [x] Implementar o menu principal.
- [x] Implementar a exibição dos preços e opções de agendamento.

### Fase 4: Sistema de agendamento
- [x] Desenvolver a lógica de verificação de disponibilidade de horários.
- [x] Implementar a gravação dos agendamentos.
- [x] Implementar a notificação da vendedora sobre novos agendamentos.

### Fase 5: Integração com Mercado Pago
- [x] Obter as credenciais do Mercado Pago.
- [x] Implementar a criação de links de pagamento.
- [x] Configurar webhooks para confirmação de pagamento.

### Fase 6: Sistema de administração de grupo
- [x] Implementar a funcionalidade para o bot ser administrador do grupo.
- [x] Desenvolver a interface para a vendedora programar mensagens.

### Fase 7: Sistema de notificações e mensagens automáticas
- [x] Implementar o envio de mensagens diárias no grupo.
- [x] Implementar notificações para a vendedora.

### Fase 8: Documentação e instruções de uso
- [x] Criar um guia de uso para a vendedora.
- [x] Documentar o código do bot.

### Fase 9: Entrega do projeto completo
- [x] Empacotar o bot para entrega.
- [x] Fornecer instruções para deploy.




### Fluxo de Interação do Usuário:
1.  **Início do Bot:** O usuário inicia o bot e recebe uma mensagem de boas-vindas com o menu principal.
2.  **Menu Principal:**
    *   Opção para ver os serviços/preços.
    *   Opção para agendar um atendimento.
    *   Opção para ver o grupo de prévias.
    *   Opção para entrar em contato.
3.  **Serviços/Preços:**
    *   Ao selecionar esta opção, o bot exibe os preços:
        *   1 hora: R$ 250
        *   2 horas: R$ 500
        *   3 horas: R$ 750
        *   Pernoite: R$ 2000
    *   Cada opção de preço terá um botão para iniciar o processo de pagamento.
4.  **Agendamento:**
    *   Ao selecionar esta opção, o bot solicita a duração do atendimento (1h, 2h, 3h, pernoite).
    *   Em seguida, o bot solicita a data e o horário desejado.
    *   O bot verifica a disponibilidade do horário.
        *   Se disponível: O bot confirma o agendamento e, se for um agendamento pago, direciona para o pagamento.
        *   Se indisponível: O bot informa a indisponibilidade e sugere horários alternativos.
    *   Após a confirmação do agendamento (e pagamento, se aplicável), a vendedora é notificada.
5.  **Grupo de Prévias:**
    *   Ao selecionar esta opção, o bot fornece um link para o grupo de prévias.
6.  **Contato:**
    *   Ao selecionar esta opção, o bot fornece informações de contato (ex: Telegram da vendedora).

### Fluxo de Interação da Vendedora (Administração):
1.  **Programação de Mensagens:** A vendedora acessa uma interface (via bot ou outra ferramenta) para programar mensagens diárias para o grupo de prévias.
2.  **Notificações:** A vendedora recebe notificações sobre novos agendamentos e pagamentos confirmados.

### Tecnologias Propostas:
*   **Linguagem:** Python (devido à vasta quantidade de bibliotecas para Telegram e APIs).
*   **Framework para Bot:** `python-telegram-bot` ou `aiogram` (ambos são excelentes, vou pesquisar qual se encaixa melhor).
*   **Banco de Dados:** SQLite (para agendamentos e configurações do bot, simples e embutido) ou PostgreSQL (se a escala for maior no futuro).
*   **Pagamento:** API do Mercado Pago.




### Pesquisa sobre Integração com Mercado Pago

Com base na pesquisa realizada na documentação oficial do Mercado Pago, identifiquei as seguintes informações importantes para a integração:

#### Opções de Integração:

1. **Payment Links (Links de Pagamento)**: 
   - Forma mais simples de integração
   - Ideal para vendas via redes sociais (WhatsApp, Instagram, Facebook)
   - Não requer programação
   - Taxas: Cartão de crédito (3,99% a 4,98%), Pix (0,99%), Boleto (R$ 3,49)

2. **Checkout Pro**:
   - Experiência pré-desenhada do Mercado Pago
   - Cliente é redirecionado para ambiente do Mercado Pago
   - Mais controle sobre o processo de pagamento

3. **API de Preferences**:
   - Permite criar preferências de pagamento via API
   - Endpoint: POST https://api.mercadopago.com/checkout/preferences
   - Retorna URL de pagamento para redirecionamento

#### Credenciais Necessárias:
- **Access Token**: Para autenticação nas APIs
- **Public Key**: Para identificação da aplicação
- **Client ID** e **Client Secret**: Para OAuth (se necessário)

#### Fluxo Recomendado para o Bot:

1. **Criar Preferência de Pagamento**: Usar a API para criar uma preferência com os dados do serviço
2. **Obter URL de Pagamento**: A API retorna uma URL de checkout
3. **Redirecionar Cliente**: Enviar a URL via bot para o cliente
4. **Webhook de Confirmação**: Receber notificação quando o pagamento for aprovado
5. **Atualizar Status**: Confirmar o agendamento no sistema

#### Estrutura da API de Preferences:

```json
{
  "items": [
    {
      "id": "servico_id",
      "title": "Atendimento 1 hora",
      "description": "Atendimento personalizado de 1 hora",
      "quantity": 1,
      "currency_id": "BRL",
      "unit_price": 250.00
    }
  ],
  "payer": {
    "name": "Nome do Cliente",
    "email": "cliente@email.com"
  },
  "back_urls": {
    "success": "https://seu-site.com/success",
    "failure": "https://seu-site.com/failure",
    "pending": "https://seu-site.com/pending"
  },
  "notification_url": "https://seu-webhook.com/notifications"
}
```

#### Próximos Passos:
1. Implementar função para criar preferências de pagamento
2. Configurar webhook para receber notificações
3. Integrar com o sistema de agendamento do bot

