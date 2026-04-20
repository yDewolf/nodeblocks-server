FIX PARAMETER PARSING

[X] Maybe use UIDs instead of numbers for: nodes, slots, connections;
    That way I can always check if the target on Client is actually the same as the one on Server
[ ] Recursive Save State:
    ter uma função save_state em cada node que recebe o caminho de onde o ServerInstance está salvando o próprio estado. Quando o ServerInstance faz save_state e chama save_state em cada um dos nodes, que devem retornar um dict, ou algum outro valor para representar o que aquele node vai salvar.
    Por exemplo, se eu tiver que salvar muita coisa do node, por exemplo os pesos do torch, eu posso salvar com base no caminho do save do ServerInstance, e retornar na função save_state um dict com o caminho dos pesos. Aí quando eu fosse dar load_state no ServerInstance, cada node também chama load_state só que recebendo o valor que ele tinha retornado no save_state (nesse caso o caminho do arquivo dos pesos)
[ ] Send Errors to client so it can know what it messed up
    or at least send it on debug console