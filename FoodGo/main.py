# FoodGo — exercício de clone de app de delivery (estilo Keeta/iFood/UberEats)
#
# Sem usar nome, logo ou marca de nenhum app real: só a experiência (telas,
# fluxo de pedido, carrinho, checkout) recriada com dados fictícios.
#
# --------------------------------------------------------------------------
# ARQUITETURA: MVC (Model - View - Controller), versão enxuta
# --------------------------------------------------------------------------
#   models.py      -> MODEL: MenuItem, Restaurant, CartLine, Order (dados +
#                     regrinhas próprias) e a lista fictícia de restaurantes.
#   controller.py   -> CONTROLLER: a classe `AppController`, que guarda o
#                     estado do app (carrinho, pedidos) e faz TODA a regra
#                     de negócio — é o que as Views chamam para ler/mudar dados.
#   views.py        -> VIEW: uma classe por tela (todas herdando de
#                     `BaseView`) — só desenham a interface e reagem a
#                     toques, sem nenhuma regra de negócio própria.
#
# Este arquivo (`main.py`) é o "ponto de entrada": cria o AppController,
# conecta a persistência local e liga o roteamento entre as telas.
#



# Digitar a partir deste ponto (3ª digitação)