"""
models.py — camada MODEL do padrão MVC.

Um único arquivo com TODAS as entidades de domínio do FoodGo (dados +
as pequenas regras de negócio que pertencem só a elas, como uma
CartLine saber calcular seu próprio total) e os dados fictícios de
restaurantes usados no app.

Estas classes NÃO desenham nada na tela (isso é papel de `views.py`) e
NÃO sabem ler/gravar arquivos ou SharedPreferences (isso é papel de
`controller.py`) — essa separação de responsabilidades é a ideia
central do MVC.

"""
# Digitar a partir deste ponto (1ª digitação)


# 🍕🧄🍔🥓🍟🍣🍜🍤🥗🥣🥤🍰🍫🍨