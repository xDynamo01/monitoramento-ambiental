# Sistema Integrado de Monitoramento Ambiental

Rede em malha, torres autônomas, base de campo tripulada e aeronaves de patrulha para apoio à defesa ambiental.

> Documento técnico oficial do projeto. O arquivo DOCX original permanece preservado no repositório.

Rede em malha, torres autônomas, base de campo tripulada e aeronaves de patrulha para apoio à defesa ambiental

Visão conceitual da infraestrutura distribuída em ambiente florestal brasileiro.

Prevenção de incêndios • fiscalização ambiental • busca e localização • monitoramento territorial

## 1. Resumo executivo

## 2. Contexto e finalidade pública

## 3. Objetivos operacionais

## 4. Arquitetura do sistema

## 5. Rede em malha e comunicação

## 6. Infraestrutura de campo

## 7. Aeronave HARP-01

## 8. Operação e resposta a eventos

## 9. Arquitetura elétrica e energia

## 10. Componentes eletrônicos e subsistemas

## 11. Segurança, confiabilidade e manutenção

## 12. Estratégia de implantação e validação

## 13. Interfaces regulatórias no Brasil

## 14. Indicadores de desempenho e impacto

## 15. Conclusão

Referências técnicas e normativas

Glossário

## 1. Resumo executivo

O Sistema Integrado de Monitoramento Ambiental foi concebido para ampliar a presença operacional de órgãos de defesa ambiental em áreas florestais extensas, de difícil acesso e com cobertura limitada de telecomunicações. A arquitetura combina torres distribuídas, comunicação em rede em malha, aeronaves não tripuladas de patrulha, geração local de energia e um centro de operações responsável por consolidar dados e apoiar decisões.

O sistema prioriza a detecção antecipada de incêndios florestais, mas foi estruturado para atender também fiscalização territorial, monitoramento de áreas protegidas, identificação de alterações ambientais, apoio à busca de pessoas e levantamento de informações em locais onde o deslocamento de equipes terrestres é lento ou arriscado.

A comunicação de campo não depende da disponibilidade de internet comercial. As torres formam uma rede própria, capaz de encaminhar dados por rotas alternativas. A internet, a fibra, a rede móvel ou o enlace por satélite podem ser utilizados como meios complementares de conexão do sistema com estruturas externas.

## 2. Contexto e finalidade pública

Incêndios florestais, atividades extrativistas ilegais e ocorrências de busca em áreas remotas compartilham um problema operacional: o tempo entre o primeiro indício e a confirmação em campo. Em territórios extensos, a presença humana contínua é inviável, e a ausência de conectividade dificulta a transmissão de imagens, telemetria e alertas.

A proposta responde a esse problema por meio de infraestrutura permanente de observação e comunicação associada a aeronaves de patrulha. As torres mantêm a rede ativa e fornecem energia, abrigo e pontos de apoio; os drones realizam rondas programadas e investigações direcionadas; a torre central tripulada concentra manutenção e apoio logístico; o centro de operações consolida as informações e coordena as ações institucionais.

Redução do tempo entre detecção e confirmação de um foco de incêndio ou outra anomalia.

Cobertura de setores remotos sem exigir equipes permanentes em cada ponto da rede.

Capacidade de manter comunicação local mesmo diante de indisponibilidade de internet pública.

Formação de histórico georreferenciado para planejamento, fiscalização e análise posterior.

Apoio a decisões de deslocamento de equipes, priorização de recursos e resposta emergencial.

## 3. Objetivos operacionais

3.1 Objetivo primário

Detectar, localizar e acompanhar indícios de incêndio florestal com maior antecedência, fornecendo imagens, telemetria e contexto operacional ao órgão responsável antes do deslocamento de recursos de combate.

3.2 Objetivos complementares

Patrulhar áreas delimitadas por setor e comparar condições observadas ao longo do tempo.

Apoiar a detecção de fumaça, calor anômalo, abertura de clareiras, movimentações incomuns e alterações do território.

Executar inspeção aérea direcionada após alerta gerado por sensor fixo, operador ou sistema de análise.

Apoiar busca e localização de pessoas por câmeras visual e térmica, quando tecnicamente aplicável.

Fornecer dados ambientais e meteorológicos de apoio à interpretação dos eventos observados.

3.3 Limites operacionais

O sistema não substitui equipes de combate, fiscalização ou salvamento. Sua função é ampliar consciência situacional, reduzir incerteza e direcionar recursos. Operações aéreas devem ser suspensas quando vento, chuva, descargas atmosféricas, visibilidade ou outras condições excederem o envelope aprovado para a aeronave.

## 4. Arquitetura do sistema

Figura 1 — Formação da rede em malha: torre central tripulada, torres autônomas distribuídas e enlaces redundantes sobre a área florestal.

A infraestrutura adota organização hierárquica na operação e distribuída na comunicação. A torre central tripulada concentra apoio humano e manutenção, enquanto as torres autônomas executam funções locais sem equipe permanente. Na camada de comunicação, todos os nós aptos podem participar do encaminhamento de dados, evitando dependência de uma única rota.

4.1 Camadas funcionais

## 5. Rede em malha e comunicação

A rede em malha (mesh) é a infraestrutura de transporte de dados do sistema. Em vez de exigir conexão direta de cada torre com a base, os nós podem encaminhar tráfego de outros nós. Essa característica permite que uma torre utilize diferentes vizinhos como caminho até a torre central ou até o ponto de saída para redes externas.

5.1 Papel do Raspberry Pi 4

O Raspberry Pi 4 é utilizado como computador de nó e computador de missão. Ele não substitui o rádio. A interface de radiofrequência é externa e será selecionada de acordo com frequência, potência autorizada, alcance, consumo, suporte a rede em malha e disponibilidade de drivers estáveis.

No drone, o Raspberry Pi 4 recebe dados de sensores e do controlador de voo, organiza registros, gerencia comunicação e executa serviços de missão. Na torre, o mesmo tipo de computador pode executar roteamento, supervisão, armazenamento temporário, monitoramento de energia e controle de docas.

5.2 Tecnologias candidatas

IEEE 802.11s para formação de enlaces em malha quando houver suporte adequado de hardware e driver.

Roteamento em camada 2 com BATMAN-adv como alternativa para gerenciamento de múltiplos enlaces.

Rádios de maior alcance ou Wi-Fi HaLow para cenários em que alcance e consumo justifiquem sua adoção.

Enlaces direcionais entre torres quando o relevo permitir visada definida e maior capacidade de transporte.

Canal de contingência em faixa sub-GHz para mensagens curtas de localização, estado e emergência.

5.3 Classes de tráfego

5.4 Segurança de comunicação

A rede deve utilizar autenticação de nós, criptografia dos enlaces, segmentação lógica entre tráfego de missão e manutenção, chaves rotacionáveis, registro de eventos e administração restrita. A perda de um nó não deve conceder acesso irrestrito ao restante da infraestrutura.

## 6. Infraestrutura de campo

6.1 Torre central tripulada (base de campo)

Figura 2 — Conceito da torre central tripulada em ambiente de Mata Atlântica: alojamento de curta permanência, oficina, área de operação e droneporto.

A torre central tripulada é a base técnica da malha em campo. Sua função vai além da repetição de sinal: ela recebe pessoal por períodos de permanência definidos pela escala operacional, concentra manutenção de equipamentos, mantém estoque de peças e serve como destino para drones encaminhados para inspeção ou reparo.

O conceito estrutural combina a lógica de torres de observação florestal, que mantêm pessoal em posição elevada por períodos prolongados, com a modularidade de plataformas industriais, nas quais funções técnicas, circulação, energia e manutenção são distribuídas em níveis.

Drones selecionados para manutenção deixam temporariamente o setor de origem e voam até a torre central. Enquanto a unidade estiver fora, a disponibilidade do setor é preservada pela rotação entre as demais aeronaves da torre autônoma correspondente.

6.2 Torre autônoma com hangar multidoca

Figura 3 — Torre autônoma: plataforma superior ampliada com docas independentes, painéis solares, comunicação e armazenamento distribuído de energia.

As torres autônomas operam sem equipe permanente. A plataforma superior é dimensionada como hangar multidoca, com acessos independentes distribuídos pelas faces da estrutura. Cada acesso atende uma aeronave, permitindo recolhimento, proteção contra intempéries, recarga e preparação para nova missão.

A configuração prevista comporta três a quatro HARP-01 por torre. A frota trabalha de forma intercalada: uma aeronave pode estar em patrulha, outra em recarga, outra disponível como reserva e uma quarta em inspeção ou aguardando janela operacional. Essa rotação reduz dependência de um único drone e evita interrupção do setor durante recarga ou manutenção.

6.3 Formação territorial da malha

As torres são distribuídas conforme relevo, cobertura vegetal, alcance medido dos rádios, risco ambiental e necessidade de acesso. O desenho da rede deve privilegiar sobreposição de conectividade entre nós, evitando cadeias lineares longas em que a perda de uma única torre interrompa o setor inteiro.

A torre central tripulada não precisa ocupar o centro geométrico da floresta. Sua posição deve equilibrar acesso logístico, cobertura da rede, segurança da equipe, disponibilidade de energia, proximidade de vias de apoio e tempo de voo dos drones encaminhados para manutenção.

## 7. Aeronave HARP-01

Figura 4 — Geometria de referência do HARP-01 em vista inferior. O terceiro propulsor VTOL está integrado à parte inferior traseira da fuselagem.

HARP-01 é a designação da aeronave do sistema. A configuração consolidada adota asa fixa, duas unidades propulsivas basculantes nas asas e um terceiro propulsor vertical integrado à região inferior traseira da fuselagem. O objetivo é combinar eficiência de cruzeiro com decolagem e pouso vertical em plataformas compactas.

7.1 Perfil de missão

## 1.  Partida da doca e verificação automática dos sistemas de voo, energia, comunicação e ambiente.

## 2.  Decolagem vertical a partir da plataforma da torre.

## 3.  Transição controlada para voo de asa fixa.

## 4.  Execução da rota de patrulha do setor com coleta de dados.

## 5.  Desvio para inspeção direcionada quando houver alerta ou comando do operador.

## 6.  Retorno à torre, transição para voo vertical, pouso, recolhimento e recarga.

7.2 Controle de voo e computador de missão

O controlador de voo e o Raspberry Pi 4 são sistemas distintos. O controlador de voo executa estabilização, navegação, controle dos atuadores, retorno automático e rotinas de segurança. O Raspberry Pi 4 executa funções de missão, comunicação, organização de sensores, registro e interface com a rede.

A arquitetura evita que uma falha do sistema operacional do computador de missão derrube o controle primário da aeronave. O HARP-01 deve continuar capaz de manter atitude e executar procedimento de contingência mesmo se o Raspberry Pi reiniciar ou ficar indisponível.

7.3 Sensoriamento

Câmera RGB para inspeção visual, fumaça, alterações do terreno e apoio à navegação contextual.

Câmera térmica para detecção de contrastes térmicos, operação noturna e busca, sem utilizar temperatura absoluta como único critério de incêndio.

GNSS para posicionamento e navegação.

Sensor de velocidade do ar para controle de voo de asa fixa.

Sensores de corrente, tensão e temperatura para gestão do estado energético e detecção de degradação.

7.4 Processamento e inteligência artificial

A arquitetura inicial não exige modelo de inteligência artificial de grande porte executando a bordo. O drone coleta, comprime e transmite dados; o processamento mais pesado pode permanecer no centro de operações ou em servidores associados à rede. Essa escolha reduz massa, consumo e complexidade térmica da aeronave.

Análises automáticas podem gerar indicação de evento, mas a confirmação de ocorrências críticas permanece sob supervisão humana. Em caso de alerta, um operador pode redirecionar a missão para observação detalhada, mantendo o controlador de voo responsável pela estabilidade e pelos limites de segurança.

## 8. Operação e resposta a eventos

8.1 Patrulha regular

Cada torre autônoma é associada a um setor operacional. As aeronaves alternam missões para preservar cobertura sem exigir que todas permaneçam em voo. Rotas, frequência de patrulha e prioridade são ajustadas conforme risco de incêndio, época do ano, meteorologia, histórico de ocorrências e determinações do órgão operador.

8.2 Detecção de anomalia

## 1.  Sensor embarcado, sensor fixo ou sistema de análise identifica condição fora do padrão esperado.

## 2.  O evento é georreferenciado e transmitido pela rede em malha.

## 3.  A central correlaciona imagem, temperatura, meteorologia e dados históricos.

## 4.  O operador avalia o alerta e, quando necessário, ordena inspeção aproximada.

## 5.  A aeronave coleta evidência adicional e mantém posição segura de observação.

## 6.  A equipe responsável decide mobilização de recursos terrestres ou aéreos.

8.3 Operação em clima adverso

Quando as condições superarem os limites aprovados, os drones permanecem recolhidos. A rede fixa e os sensores das torres continuam ativos. A decisão de voo deve considerar vento, precipitação, descargas atmosféricas, visibilidade, temperatura, estado das baterias e condições da plataforma de pouso.

8.4 Manutenção

A manutenção é dividida em dois níveis. Intervenções simples e automatizadas são realizadas na própria torre autônoma por diagnóstico, reinicialização e substituição de uma aeronave pela reserva. Falhas que exijam inspeção física direcionam o drone à torre central tripulada, onde existe oficina, equipe e estoque de componentes.

## 9. Arquitetura elétrica e energia

9.1 HARP-01

A aeronave utiliza dois domínios elétricos independentes. O banco de propulsão alimenta os motores e atuadores de maior potência. A bateria de aviônica alimenta controlador de voo, Raspberry Pi, rádios, navegação e sensores essenciais. A separação assegura que a perda da capacidade de propulsão não elimine imediatamente a capacidade de localizar e recuperar a aeronave.

Os módulos de propulsão são posicionados preferencialmente próximos às raízes das asas para manter massa próxima ao centro de gravidade. A capacidade final será determinada a partir do consumo medido em VTOL, transição e cruzeiro, e não por estimativa nominal isolada.

9.2 Torres

As torres devem operar prioritariamente de forma autônoma por geração fotovoltaica e armazenamento local. O dimensionamento considera consumo médio do nó, picos de recarga de drones, autonomia desejada sem geração, sazonalidade solar e margem para envelhecimento das baterias.

A distribuição física do armazenamento ao longo da torre reduz concentração de massa na plataforma superior e facilita segregação entre baterias, eletrônica de comunicação e áreas de circulação. Bancos instalados em diferentes níveis devem possuir proteção mecânica, ventilação adequada, monitoramento e acesso seguro para manutenção.

## 10. Componentes eletrônicos e subsistemas

10.1 HARP-01

10.2 Torre autônoma

10.3 Torre central tripulada

## 11. Segurança, confiabilidade e manutenção

11.1 Princípios de segurança funcional

Nenhuma função crítica de estabilização depende exclusivamente do Raspberry Pi.

Uma transição VTOL somente ocorre após confirmação dos estados mecânicos necessários.

Falhas de atuadores, energia ou comunicação devem gerar modo degradado previsível, e não correções ilimitadas pelo software.

A bateria de aviônica preserva telemetria mínima e localização após perda da propulsão.

Cada torre possui monitoramento de energia, temperatura e integridade dos compartimentos.

A malha deve manter caminhos alternativos sempre que a implantação territorial permitir.

11.2 Manutenção preventiva

O ambiente florestal impõe umidade, fungos, insetos, poeira, fuligem, corrosão e grandes variações térmicas. A manutenção preventiva deve incluir inspeção de conectores, antenas, superfícies dos painéis, vedação, drenos, ventilação, baterias, mecanismos de doca, cabos e estruturas metálicas. A torre central tripulada reduz o tempo de resposta para esses serviços e permite manutenção planejada por setores.

11.3 Recuperação de aeronave

Após pouso forçado, a aeronave entra em modo de sobrevivência energética: reduz vídeo e processamento não essencial, mantém GNSS e canal de comunicação de baixa taxa e transmite identificação, posição, causa provável da interrupção e estado da bateria de aviônica em intervalos definidos.

## 12. Estratégia de implantação e validação

A implantação operacional depende de validação progressiva. Cada etapa deve produzir critérios de aprovação mensuráveis antes do avanço para a seguinte.

## 13. Interfaces regulatórias no Brasil

A implantação depende de enquadramento regulatório específico para o perfil operacional, massa final, local de operação, tipo de operador e características do enlace. O projeto deve manter interlocução com os órgãos competentes desde a fase de ensaios externos.

## 14. Indicadores de desempenho e impacto

A avaliação do sistema deve ser baseada em resultados mensuráveis e comparáveis antes e depois da implantação. Os indicadores abaixo orientam ensaios e estudos de impacto, sem estabelecer metas numéricas antes da coleta de dados de campo.

## 15. Conclusão

O Sistema Integrado de Monitoramento Ambiental propõe uma infraestrutura territorial permanente que combina comunicação resiliente, geração distribuída de energia, aeronaves de patrulha e presença humana concentrada onde ela produz maior valor: manutenção, supervisão e decisão.

A adoção de torres autônomas com múltiplos drones reduz a necessidade de ocupação humana em todos os pontos da rede. A torre central tripulada mantém capacidade logística e técnica no campo. A rede em malha reduz dependência de comunicação pública. O HARP-01 amplia o alcance da observação sem exigir pistas ou deslocamentos terrestres para cada verificação.

A etapa seguinte é transformar as escolhas arquiteturais em parâmetros medidos: alcance de rádio, balanço energético, desempenho aerodinâmico, autonomia, estabilidade do sistema de docagem e confiabilidade da operação. Esses resultados determinarão espaçamento entre torres, quantidade de aeronaves, capacidade dos bancos de energia e custo de implantação por área monitorada.

Referências técnicas e normativas

## 1. ANAC — RBAC 100, Requisitos gerais para aeronaves não tripuladas de uso civil, aprovado pela Resolução nº 805, de 15 de junho de 2026. Fonte oficial

## 2. DECEA — Portal DRONE (UAS) e SARPAS, sistema para solicitação de acesso ao Espaço Aéreo Brasileiro por aeronaves não tripuladas. Fonte oficial

## 3. ANATEL — Certificação e homologação de equipamentos de telecomunicações e orientações para drones e rádios. Fonte oficial

## 4. Raspberry Pi — Raspberry Pi 4 Model B, especificações e documentação mecânica. Fonte oficial

## 5. OpenWrt — documentação de redes em malha IEEE 802.11s e BATMAN-adv. Fonte oficial

## 6. ArduPilot — documentação de computadores auxiliares, MAVLink e aeronaves VTOL/tilt-rotor. Fonte oficial

Referências eletrônicas consultadas em setembro de 2026.

Glossário
