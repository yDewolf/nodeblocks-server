<!-- ![](https://github.com/yDewolf/NodeEditor/blob/main/repo/assets/nodeblocks.svg) -->

[NodeEditor](https://github.com/yDewolf/NodeEditor/) • [Nodeblocks::Server](https://github.com/yDewolf/node-editor-server-api) • [Documentação](https://github.com/yDewolf/NodeEditor/blob/server-docs/docs/server-docs.md) • [TODOs](TODO.md)

# Nodeblocks
Nodeblocks é um framework de sistemas baseados em nodes voltado para edição e em tempo real.

## Aviso:
Esse projeto está em constante desenvolvimento e está atualmente em estado de **beta**, ou seja, não há garantia alguma de que novas versões serão compatíveis com ``NodeScenes`` e ``TypeData`` de formatos anteriores.

## Aviso sobre esse Branch:
Esse branch busca atualizar a arquitetura do projeto para melhorar a escalabilidade, separando o projeto em 3 partes:
- `Protocols`: Definição dos protocolos de `NodeScene`, etc; (basicamente o atual `wrapper/`)
- `Engine`: implementação abstrata dos `Nodes` e coisas relacionadas ao runtime das cenas;
- `Server`: tudo que é relacionado à comunicação externa


## Esse repositório:
![GitHub repo size](https://img.shields.io/github/repo-size/yDewolf/node-editor-server-api)

Esse repositório é voltado para o backend do Nodeblocks. O frontend pode ser encontrado [aqui](https://github.com/yDewolf/NodeEditor).
> O Nodeblocks::Server é um framework para aplicações baseadas em NodeScenes que são interpretadas pelo servidor. Sua versão base oferece conexão com múltiplos Clients via Websocket. O framework é feito para ser modificado de acordo com as necessidades do seu projeto. [sobre o server](https://github.com/yDewolf/NodeEditor/blob/server-docs/docs/layers/server-api.md).

## Como Desenvolver:
O requisito mínimo é o [python 3.13](https://www.python.org/downloads/release/python-3130/).

````
# Como instalar usando pip:
pip install -e .
````

## Como instalar no seu projeto:
...
