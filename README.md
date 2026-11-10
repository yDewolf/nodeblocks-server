<!-- ![](https://github.com/yDewolf/NodeEditor/blob/main/repo/assets/nodeblocks.svg) -->

[NodeEditor](https://github.com/yDewolf/NodeEditor/) • [Nodeblocks::Server](https://github.com/yDewolf/node-editor-server-api) • [Documentação](https://github.com/yDewolf/NodeEditor/blob/server-docs/docs/server-docs.md) • [TODOs](TODO.md)

## Nodeblocks
Nodeblocks é um framework de nodes voltado para edição e processamento em tempo real.

## Aviso:
Esse projeto está em constante desenvolvimento e está atualmente em **beta**, ou seja, espere encontrar os seguintes problemas ao transitar entre commits:
- Incompatibilidade com determinados plugins;
- Incompatibilidade com protocolos de comunicação antigos;
- Bugs inesperados ([reportar aqui](https://github.com/yDewolf/nodeblocks-server/issues/))

## Esse repositório:
![GitHub repo size](https://img.shields.io/github/repo-size/yDewolf/node-editor-server-api)

Esse repositório é voltado para o backend do Nodeblocks. O frontend pode ser encontrado [aqui](https://github.com/yDewolf/NodeEditor).
> Nodeblocks::Server oferece tudo que é necessário para carregar plugins, interpretar grafos e editá-los através de um endpoint websocket (preferencialmente usando um [client](https://github.com/yDewolf/NodeEditor)). 

## Como Desenvolver:
O requisito mínimo é o [python 3.13](https://www.python.org/downloads/release/python-3130/).

````
# Como instalar usando pip:
pip install -e .[dev]
````
Depois compile os arquivos .proto:
````
nodeblocks build:protos
````

## Como rodar o servidor:
1. Instale o projeto usando `pip install -e .`
2. Compile os protobuffers com: `nodeblocks build:protos`
3. Rode o servidor base com: `nodeblocks run --plugins {caminho/dos/plugins} --extraction {caminho/para/plugins/extraidos} --scenes {caminho/para/guardar/cenas}`
   - `--plugins` é `./plugins` por padrão;
   - `--extraction` é `./plugins` por padrão;
   - `--scenes` é `./scenes` por padrão.

## Como criar plugins:
1. Certifique-se de que o projeto foi instalado com `pip install -e .`
2. Use o comando `nodeblocks create:plugin <path>` para criar a estrutura base do plugin.
Em `path` coloque o caminho da sua pasta de plugins (crie uma se não tiver) da seguinte forma: `pasta/de/plugins/id_do_seu_plugin`.
3. Vá até o diretório criado pelo comando e edite o arquivo `plugin.py`
  - Esse arquivo apenas define informações do seu plugin e NÃO DEVE IMPORTAR NADA que não seja do próprio `nodeblocks`;
  - Você pode atualizar as `python_dependencies` de acordo com o que você vai usar. **Nota:** a dependência `core` em `dependencies` define `datatypes` para os tipos padrão do python como `str`, `int`, `float`, `list`, etc;
4. Rode o servidor e verifique se seu plugin foi carregado corretamente;
5. Comece a implementar os seus `nodes` e `datatypes`.
  - Todo node deve estar anotado com `@plugin_node(id='id_do_seu_node')` e deve herdar `BaseNode`;
  - Todo datatype deve estar anotado com `@plugin_datatype(id='id_do_seu_datatype', base_id=DefaultDataTypes.TIPO_DE_DADO, base_id=DefaultRenderers.TIPO_DE_RENDERER)` e deve herdar `PluginDatatype`;
6. Mais informações sobre a criação de nodes em breve...

## Comandos CLI:
- `nodeblocks run` -> executa o servidor base.
  - `--plugins {caminho/dos/plugins}`: `./plugins` por padrão;
  - `--extraction {caminho/para/plugins/extraidos}`: `./plugins` por padrão;
  - `--scenes {caminho/para/guardar/cenas}`: `./scenes` por padrão;
- `nodeblocks build:protos` -> compila os arquivos .proto usados para a definição de protobuffers
- `nodeblocks create:plugin <path>` -> cria a estrutura de pastas de um plugin.
  - `path`: Caminho da pasta onde o plugin deve ser criado. O caminho final seria: `path/package_id/plugin.py`
  - `--id`: define o `package_id` do plugin. Caso não seja definido, o id do plugin será o nome da pasta do `path` e o caminho final será: `path/plugin.py`
- `nodeblocks pack:plugin <path>` -> compacta um plugin no formato `.nbplugin` (.zip)
  - `path`: Caminho da pasta do plugin que deve ser compactado. É `.` por padrão;
  - `-o`/`--output`: Pasta onde o arquivo compactado deve ser gerado.
  - `--zip`: Se verdadeiro -> adiciona .zip ao sufixo do arquivo (o arquivo final fica como: `nbplugin.zip`). Útil para fazer upload no Github Releases.

## Sobre a arquitetura do projeto:
O projeto usa uma "arquitetura hexagonal" bem adaptada dividida nas seguintes camadas:
- `protocols`: Definição dos protocolos de utilizados em múltiplas camadas como: `ManifestPackage`, `NodeTypeSpec`, etc;
- `engine`: implementação abstrata dos nodes lógicos (`BaseNode`), definição da API de plugins e coisas relacionadas ao processamento dos grafos;
- `server`: tudo que tem a ver com comunicação externa como: routers HTTP, websocket, etc.
Essa é a divisão principal da estrutura do projeto que fica dividida em três pastas com os mesmos nomes das camadas. Cada uma dessas camadas tem seus próprios protocolos internos.
