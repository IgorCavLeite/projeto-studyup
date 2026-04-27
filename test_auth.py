# Simular o fluxo do Streamlit
from backend.recuperacao_senha import atualizar_senha
from backend.services.auth import autenticar_usuario, cadastrar_usuario

# Testar autenticação
print('=== TESTE 1: Autenticação ===')
resultado = autenticar_usuario('Igor', '1234')
print(f'Igor com 1234: {resultado}')

resultado = autenticar_usuario('Gabriel', '1234')
print(f'Gabriel com 1234: {resultado}')

# Testar com senhas erradas
print('\n=== TESTE 2: Senhas erradas ===')
resultado = autenticar_usuario('Igor', '12345')
print(f'Igor com 12345: {resultado}')

# Testar recuperação de senha
print('\n=== TESTE 3: Recuperação de senha ===')
resultado = atualizar_senha('Igor', 'nova_senha_123')
print(f'Atualizar senha Igor: {resultado}')

# Verificar se a senha foi atualizada
print('\n=== TESTE 4: Login após atualizar senha ===')
resultado = autenticar_usuario('Igor', 'nova_senha_123')
print(f'Igor com nova_senha_123: {resultado}')

resultado = autenticar_usuario('Igor', '1234')
print(f'Igor com 1234 (antiga): {resultado}')
