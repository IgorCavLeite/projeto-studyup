from backend.recuperacao_senha import atualizar_senha
from backend.services.auth import autenticar_usuario

# Restaurar senhas para 1234
print("Restaurando senhas para '1234'...")
resultado_igor = atualizar_senha('Igor', '1234')
print(f'Igor: {resultado_igor}')

resultado_gabriel = atualizar_senha('Gabriel', '1234')
print(f'Gabriel: {resultado_gabriel}')

# Testar login com a senha restaurada
print("\nTestando login após restaurar senhas...")
print(f'Igor: {autenticar_usuario("Igor", "1234")}')
print(f'Gabriel: {autenticar_usuario("Gabriel", "1234")}')
