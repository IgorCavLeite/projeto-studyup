# 📅 Funcionalidades de Cronograma - StudyUp

## 📋 Resumo

Implementei um sistema completo de cronograma semanal para o StudyUp que permite aos alunos:
- ✅ Criar cronogramas de estudos semanais com disciplinas cadastradas
- ✅ Gerenciar horários e durações de estudo
- ✅ Adicionar compromissos extras (academia, almoço, etc.)
- ✅ Visualizar cronograma em modo semanal ou diário
- ✅ Rastrear progresso de estudos por dia
- ✅ Validar conflitos de horário
- ✅ Sugerir cronogramas automáticos

---

## 🎯 Funcionalidades Implementadas

### 1. **Serviço de Cronograma** (`backend/services/cronograma.py`)

Um módulo com lógica de negócio completa para gerenciar cronogramas:

#### Funções Principais:
- `adicionar_disciplina_cronograma()` - Adiciona disciplina ao cronograma com validação
- `remover_disciplina_cronograma()` - Remove disciplina do cronograma
- `obter_cronograma_completo()` - Retorna cronograma organizado por dia
- `calcular_progresso_dia()` - Calcula percentual de conclusão do dia
- `calcular_carga_horaria_semanal()` - Calcula horas totais de estudo
- `adicionar_compromisso()` - Adiciona compromisso extra
- `remover_compromisso()` - Remove compromisso extra
- `validar_conflito_horario()` - Verifica sobreposição de horários
- `obter_sugestoes_cronograma()` - Gera sugestões automáticas

#### Validações Implementadas:
- ✅ Validação de dia da semana (0-6)
- ✅ Validação de formato de horário (HH:MM)
- ✅ Validação de duração (1-480 minutos)
- ✅ Validação de cores em formato hexadecimal
- ✅ Validação de conflitos de horário

---

### 2. **Componentes UI** (`frontend/components/cronograma_ui.py`)

Componentes reutilizáveis para construir a interface de cronograma:

#### Componentes Disponíveis:

1. **`exibir_cronograma_semanal()`** - Visualização completa da semana
   - Modo semanal (7 colunas) ou diário (1 coluna)
   - Destaque visual para o dia atual
   - Indicadores de disciplinas estudadas (✅) vs pendentes (📌)
   - Botões rápidos para iniciar Pomodoro

2. **`form_adicionar_disciplina_cronograma()`** - Formulário para adicionar disciplinas
   - Seleção de disciplina, dia, horário, duração e cor
   - Verificação de conflitos de horário
   - Feedback imediato de sucesso/erro

3. **`form_gerenciar_disciplinas()`** - Gerenciamento de disciplinas
   - Lista todas as disciplinas no cronograma
   - Botão para remover cada item
   - Atualização em tempo real

4. **`form_adicionar_compromisso()`** - Adicionar compromissos extras
   - Campos: nome, dia, horário, duração, cor
   - Validação de entrada

5. **`form_gerenciar_compromissos()`** - Gerenciar compromissos
   - Lista e remove compromissos

6. **`exibir_resumo_semanal()`** - Dashboard de carga horária
   - Total semanal em horas
   - Média diária
   - Carga horária por dia com barras de progresso

7. **`sugerir_cronograma_automatico()`** - Gerador automático
   - Seleciona disciplinas a estudar
   - Define horas por dia
   - Gera e aceita sugestões automáticas

---

### 3. **Banco de Dados** (Estrutura existente em `backend/database/connection.py`)

Tabelas utilizadas:

```sql
-- Cronograma de Disciplinas
CREATE TABLE cronograma (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    disciplina_id INTEGER NOT NULL,
    dia_semana INTEGER NOT NULL,
    usuario_id INTEGER,
    start_time TEXT,
    duration INTEGER DEFAULT 60,
    color TEXT DEFAULT '#4CAF50',
    FOREIGN KEY (disciplina_id) REFERENCES disciplinas (id),
    FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
);

-- Compromissos Extras
CREATE TABLE compromissos_extras (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    dia_semana INTEGER NOT NULL,
    start_time TEXT,
    duration INTEGER DEFAULT 60,
    color TEXT DEFAULT '#FF9800',
    usuario_id INTEGER,
    FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
);
```

---

### 4. **Integração no Frontend** (`frontend/app.py`)

Página de Cronograma completamente funcional com:

#### Página "Cronograma" (`st.session_state['pagina'] == "Cronograma"`):
- Visualização do cronograma da semana
- Modo semanal ou diário
- Metas diárias
- Progresso de estudo do dia
- Grid visual com cores personalizadas
- Seção de gerenciamento (adicionar/remover disciplinas e compromissos)

#### Página "Configurar Cronograma" (`st.session_state['pagina'] == "Configurar Cronograma"`):
- Configuração inicial de cronograma
- Redireciona para a página principal quando concluído

---

## 🎨 Cores Padrão

```python
CORES_PADRAO = {
    'verde': '#4CAF50',      # Padrão para disciplinas
    'azul': '#2196F3',
    'laranja': '#FF9800',    # Padrão para compromissos
    'rosa': '#E91E63',
    'roxo': '#9C27B0',
    'vermelho': '#F44336',
}
```

---

## 🐛 Bugs Corrigidos

1. **Bug na remoção de disciplinas** - Faltava `if st.button()` na condição
   - Correção: Adicionado `if st.button("🗑️", key=f"remove_disc_{cron_id}")`

---

## ✨ Melhorias Implementadas

1. **Validação robusta** - Todas as entradas são validadas
2. **Detecção de conflitos** - Previne sobreposição de horários
3. **Componentes reutilizáveis** - Código limpo e modular
4. **Sugestões automáticas** - Gera cronogramas inteligentemente
5. **Indicadores visuais** - ✅ (estudada), ⏳ (hoje), 📌 (pendente)
6. **Feedback ao usuário** - Mensagens de sucesso/erro claras
7. **Integração com Pomodoro** - Botões rápidos para iniciar estudos

---

## 📊 Visualizações

### Modo Semanal
- 7 colunas com dias da semana
- Destaque para dia atual
- Disciplinas organizadas por horário

### Modo Diário
- Visão focada em um dia
- Metas do dia
- Todos os compromissos e disciplinas

### Resumo Semanal
- Total de horas de estudo
- Média diária
- Carga horária por dia

---

## 🚀 Como Usar

### Adicionar Disciplina ao Cronograma

```python
from backend.services.cronograma import adicionar_disciplina_cronograma

sucesso, mensagem, _ = adicionar_disciplina_cronograma(
    disciplina_id=1,
    dia_semana=0,  # Segunda
    start_time="14:00",
    duration=60,   # 1 hora
    color="#4CAF50",
    usuario_id=None
)
```

### Obter Cronograma Completo

```python
from backend.services.cronograma import obter_cronograma_completo

cronograma = obter_cronograma_completo(usuario_id=None)
# Retorna: {0: {'disciplinas': [...], 'compromissos': [...]}, ...}
```

### Calcular Progresso do Dia

```python
from backend.services.cronograma import calcular_progresso_dia

progresso = calcular_progresso_dia(dia_semana=0)
# Retorna: {'total': 3, 'estudadas': 2, 'percentual': 66.7}
```

---

## 📝 Notas Técnicas

- **Frontend**: Streamlit com componentes customizados
- **Backend**: Python puro com SQLite
- **Validação**: Feita no serviço com tratamento de erros
- **Estado**: Gerenciado por `st.session_state`
- **Performance**: Queries otimizadas com índices no banco

---

## ✅ Próximas Melhorias Sugeridas

1. Importar/exportar cronogramas em PDF ou iCal
2. Sincronização com Google Calendar
3. Notificações de horários (desktop/mobile)
4. Estatísticas de consistência de estudos
5. Recomendações baseadas em IA para melhor cronograma
6. Cronograma compartilhado entre grupos de estudo
7. Histórico de cronogramas anteriores

---

**Status**: ✅ Implementado e Testado
**Data**: 26 de Maio de 2026
**Versão**: 1.0.0
