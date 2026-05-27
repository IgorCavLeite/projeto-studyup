# 🏗️ Documentação Técnica - Sistema de Cronograma

## 📂 Estrutura de Arquivos

```
StudyUp/
├── backend/
│   ├── database/
│   │   ├── __init__.py
│   │   └── connection.py                    # BD e funções de cronograma
│   └── services/
│       ├── cronograma.py        ✨ NOVO - Lógica de cronograma
│       ├── ai_mentor.py
│       ├── analytics.py
│       ├── auth.py
│       └── pomodoro.py
├── frontend/
│   ├── app.py                   ✏️ MODIFICADO - Importações
│   ├── components/
│   │   ├── cronograma_ui.py     ✨ NOVO - Componentes UI
│   │   ├── auth_ui.py
│   │   └── login.py
│   └── assets/
│       └── style.css
├── CRONOGRAMA_FEATURES.md       ✨ NOVO - Documentação de features
├── CRONOGRAMA_GUIA_USO.md       ✨ NOVO - Guia de uso
└── CRONOGRAMA_TECNICO.md        ✨ NOVO - Este arquivo
```

---

## 🔧 Componentes Técnicos

### 1. Backend: `backend/services/cronograma.py`

**Arquivo Principal**: Lógica de negócio completa

#### Classes/Constantes:
```python
DIAS_SEMANA = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"]

CORES_PADRAO = {
    'verde': '#4CAF50',
    'azul': '#2196F3',
    'laranja': '#FF9800',
    'rosa': '#E91E63',
    'roxo': '#9C27B0',
    'vermelho': '#F44336',
}
```

#### Principais Funções:

**Validação:**
- `validar_dia_semana(dia)` - Valida se dia está entre 0-6
- `validar_horario(horario)` - Valida formato HH:MM
- `validar_duracao(duracao)` - Valida se é entre 1-480 min
- `validar_conflito_horario()` - Detecta sobreposição

**Gerenciamento de Disciplinas:**
- `adicionar_disciplina_cronograma()` - Adiciona com validação completa
  ```python
  sucesso, mensagem, cronograma_id = adicionar_disciplina_cronograma(
      disciplina_id=1,
      dia_semana=0,      # 0=Segunda, 6=Domingo
      start_time="14:00",
      duration=60,
      color="#4CAF50",
      usuario_id=None
  )
  ```
- `remover_disciplina_cronograma()` - Remove com retorno de feedback

**Consultas:**
- `obter_cronograma_completo()` - Retorna dict organizado por dia
- `calcular_progresso_dia()` - Retorna dict com progresso
- `calcular_carga_horaria_semanal()` - Retorna horas totais

**Compromissos Extras:**
- `adicionar_compromisso()` - Adiciona com validação
- `remover_compromisso()` - Remove compromisso

**Sugestões:**
- `obter_sugestoes_cronograma()` - Gera cronograma automático

---

### 2. Frontend: `frontend/components/cronograma_ui.py`

**Arquivo Principal**: Componentes Streamlit reutilizáveis

#### Componentes de Visualização:

1. **`exibir_cronograma_semanal(usuario_id=None)`**
   - Renderiza grid 7x7 ou coluna única
   - Modo semanal/diário
   - Destaque para hoje
   - Botões de ação

2. **`renderizar_cartao_disciplina()`**
   - Card HTML customizado
   - Ícones de status (✅, ⏳, 📌)
   - Cores personalizáveis

3. **`exibir_resumo_semanal()`**
   - Métricas de carga horária
   - Barras de progresso por dia
   - Totais e médias

#### Formulários:

1. **`form_adicionar_disciplina_cronograma()`**
   - Seleção de disciplina, dia, horário, duração, cor
   - Validação de conflito in-page
   - Feedback visual

2. **`form_gerenciar_disciplinas()`**
   - Lista com botões de remoção
   - Atualização em tempo real

3. **`form_adicionar_compromisso()`**
   - Campos de entrada para compromisso
   - Validação de nome obrigatório

4. **`form_gerenciar_compromissos()`**
   - Lista com botões de remoção

5. **`sugerir_cronograma_automatico()`**
   - Multiselect de disciplinas
   - Input de horas por dia
   - Preview de sugestões
   - Aceitar/rejeitar

---

### 3. Database: `backend/database/connection.py`

**Tabelas Utilizadas:**

```sql
CREATE TABLE cronograma (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    disciplina_id INTEGER NOT NULL,
    dia_semana INTEGER NOT NULL,          -- 0=Seg, 6=Dom
    usuario_id INTEGER,                    -- NULL = compartilhado
    start_time TEXT,                       -- "HH:MM"
    duration INTEGER DEFAULT 60,           -- minutos
    color TEXT DEFAULT '#4CAF50',          -- hex color
    FOREIGN KEY (disciplina_id) REFERENCES disciplinas (id),
    FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
);

CREATE TABLE compromissos_extras (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    dia_semana INTEGER NOT NULL,
    usuario_id INTEGER,
    start_time TEXT,
    duration INTEGER DEFAULT 60,
    color TEXT DEFAULT '#FF9800',
    FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
);
```

**Funções Disponíveis:**
- `salvar_cronograma()` - INSERT OR REPLACE
- `buscar_cronograma_usuario()` - SELECT com JOIN
- `obter_disciplinas_por_dia()` - SELECT com filtro
- `remover_cronograma()` - DELETE
- `salvar_compromisso_extra()` - INSERT
- `buscar_compromissos_extras_usuario()` - SELECT
- `remover_compromisso_extra()` - DELETE
- `foi_estudada_hoje()` - SELECT com JOIN temporal

---

### 4. Frontend: `frontend/app.py`

**Modificações:**

1. **Importações Adicionadas:**
```python
from frontend.components.cronograma_ui import (
    exibir_cronograma_semanal,
    form_adicionar_disciplina_cronograma,
    form_gerenciar_disciplinas,
    form_adicionar_compromisso,
    form_gerenciar_compromissos,
    exibir_resumo_semanal,
    sugerir_cronograma_automatico,
)
```

2. **Bug Corrigido:**
   - Arquivo: `frontend/app.py` linha ~635
   - Problema: Faltava `if st.button()` na remoção
   - Solução: Adicionado botão com callback correto

3. **Página Cronograma:**
   - Renderiza usando `exibir_cronograma_semanal()`
   - Modo semanal/diário
   - Seção de gerenciamento

---

## 🔄 Fluxos de Dados

### Fluxo: Adicionar Disciplina

```
Frontend (form_adicionar_disciplina_cronograma)
    ↓ (input validação)
Backend (cronograma.adicionar_disciplina_cronograma)
    ↓ (validações)
Database (salvar_cronograma)
    ↓ (INSERT)
Streamlit (st.rerun)
    ↓ (atualizar)
Frontend (exibir_cronograma_semanal)
    ↓ (renderizar nova disciplina)
```

### Fluxo: Obter Cronograma

```
Frontend (exibir_cronograma_semanal)
    ↓ (chama)
Backend (obter_cronograma_completo)
    ↓ (organiza por dia)
Database (buscar_cronograma_usuario + buscar_compromissos_extras_usuario)
    ↓ (SELECT com JOINs)
Backend (retorna dict {dia: {disciplinas: [], compromissos: []}})
    ↓
Frontend (renderiza grid/cards)
```

---

## 📊 Estrutura de Dados

### Retorno de `obter_cronograma_completo()`:

```python
{
    0: {  # Segunda
        'disciplinas': [
            {
                'id': 1,
                'disciplina_id': 5,
                'nome': 'Python',
                'dia': 0,
                'horario': '14:00',
                'duracao': 60,
                'cor': '#4CAF50',
                'tipo': 'disciplina'
            },
            ...
        ],
        'compromissos': [
            {
                'id': 1,
                'nome': 'Academia',
                'dia': 0,
                'horario': '18:00',
                'duracao': 60,
                'cor': '#FF9800',
                'tipo': 'compromisso'
            },
            ...
        ]
    },
    1: { ... },  # Terça
    ...
}
```

### Retorno de `calcular_progresso_dia()`:

```python
{
    'total': 3,           # Total de disciplinas
    'estudadas': 2,       # Quantas foram estudadas
    'percentual': 66.7    # Percentual de conclusão
}
```

---

## ⚠️ Validações Implementadas

### Nível Frontend:
- ✅ Campo obrigatório (nome do compromisso)
- ✅ Feedback visual de erro/sucesso

### Nível Backend (cronograma.py):
- ✅ Dia semana entre 0-6
- ✅ Horário formato HH:MM e range 00:00-23:59
- ✅ Duração entre 1-480 minutos (8h)
- ✅ Cor formato hexadecimal 7 chars

### Nível Database:
- ✅ Chave estrangeira (disciplina_id, usuario_id)
- ✅ NOT NULL para campos obrigatórios
- ✅ DEFAULT para valores padrão

---

## 🎯 Casos de Uso

### Caso 1: Criar cronograma do zero
1. Aluno vai para página Cronograma
2. Cronograma vazio → botão "Configurar Cronograma"
3. Aluno seleciona disciplina, dia, horário
4. Sistema salva e mostra nova disciplina

### Caso 2: Adicionar disciplina existente
1. Aluno expande "Adicionar ou Remover Disciplinas"
2. Preenche formulário
3. Sistema valida conflito de horário
4. Se OK, salva; se conflito, mostra erro

### Caso 3: Gerar cronograma automático
1. Aluno clica "Sugerir Cronograma Automático"
2. Seleciona disciplinas e horas por dia
3. Sistema distribui disciplinas na semana
4. Mostra preview
5. Aluno confirma para aceitar

---

## 🐛 Tratamento de Erros

**Estratégia:**
- Validações retornam tuplas `(sucesso, mensagem, ...)`
- Frontend exibe `st.error()` ou `st.success()` conforme resultado
- Exceções são capturadas e convertidas em mensagens

**Exemplos:**
```python
sucesso, msg = adicionar_compromisso(...)
if sucesso:
    st.success(msg)  # "✅ Academia adicionada!"
else:
    st.error(msg)    # "❌ Erro: Nome não pode estar vazio"
```

---

## 🚀 Performance

**Otimizações:**
- Queries usam JOINs para reduzir chamadas ao BD
- Dados são organizados em memória (Python)
- Caching implícito do Streamlit com `st.cache_data`
- Sem N+1 queries

**Escalabilidade:**
- Estrutura preparada para multi-usuário
- Campo `usuario_id` permite isolamento de dados
- Índices no banco (via chaves estrangeiras)

---

## 🔐 Segurança

**Implementado:**
- ✅ Input validation em todo o backend
- ✅ Prepared statements (sqlite3 com ?)
- ✅ Isolamento por usuário (usuario_id)
- ✅ Sem SQL injection possível

**Futuro:**
- 🔜 Rate limiting nas operações
- 🔜 Auditoria de mudanças
- 🔜 Backup automático

---

## 📝 Padrões de Código

**Nomenclatura:**
- Funções: `verbo_substantivo()` - `adicionar_disciplina()`
- Variáveis: `snake_case` - `dia_semana`, `start_time`
- Constantes: `UPPER_CASE` - `DIAS_SEMANA`, `CORES_PADRAO`
- Componentes UI: `renderizar_*()`, `form_*()`, `exibir_*()`

**Estrutura de Funções:**
```python
def funcao(param1, param2, param3=None):
    """Docstring em português explicando o que faz."""
    # Validações
    if not validar(param1):
        return False, "Erro de validação"
    
    # Lógica
    resultado = fazer_algo(param1, param2)
    
    # Retorno
    return True, "Sucesso", resultado
```

**Imports:**
- Backend imports: Relativos ou absolutos com `backend.`
- Frontend imports: Relativos ou absolutos com `frontend.`
- Nunca imports circulares

---

## 🧪 Testes Realizados

✅ Adicionar disciplina ao cronograma (Funcionando)  
✅ Remover disciplina do cronograma (Funcionando - bug corrigido)  
✅ Visualizar cronograma semanal (Funcionando)  
✅ Visualizar cronograma diário (Implementado)  
✅ Validação de conflito de horário (Implementado)  
✅ Adicionar compromisso extra (Implementado)  
✅ Remover compromisso extra (Implementado)  
✅ Sugestão automática (Implementado)  

**Não testado em produção:**
- Performance com 1000+ cronogramas
- Sincronização multi-usuário em tempo real
- Backup e recovery do BD

---

## 🔄 Próximas Melhorias

**Curto Prazo (v1.1):**
- [ ] Editar horário/duração de disciplina existente
- [ ] Duplicar cronograma da semana anterior
- [ ] Exportar cronograma em PDF
- [ ] Undo/Redo de ações

**Médio Prazo (v1.2):**
- [ ] Sincronizar com Google Calendar
- [ ] Cronogramas compartilhados entre usuários
- [ ] Notificações 30min antes do horário
- [ ] Templates de cronogramas prontos

**Longo Prazo (v2.0):**
- [ ] App mobile com sincronização
- [ ] Recomendações de cronograma via IA
- [ ] Análise de produtividade
- [ ] Cronograma inteligente baseado em histórico

---

## 📞 Contato & Suporte

Para dúvidas técnicas ou contribuições:
- Revise este documento
- Consulte os arquivos `.md` de features e guia de uso
- Verifique os comentários no código

---

**Versão**: 1.0.0  
**Data**: 26 de Maio de 2026  
**Autor**: Assistente de IA  
**Status**: ✅ Documentação Completa
