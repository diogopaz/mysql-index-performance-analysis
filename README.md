# Análise de Desempenho de Índices MySQL

Este projeto realiza uma análise comparativa do desempenho de diferentes tipos de índices no MySQL, medindo o tempo de execução de consultas com e sem índices.

# Introdução: A Importância dos Índices em Bancos de Dados (MySQL)

Em sistemas de banco de dados relacionais como o **MySQL**, os **índices** são estruturas essenciais para melhorar a performance das consultas. Eles funcionam como mecanismos que permitem encontrar registros rapidamente sem precisar varrer toda a tabela, algo que se torna cada vez mais importante à medida que os dados crescem.

Sem índices, consultas com filtros (`WHERE`), ordenações (`ORDER BY`) ou junções (`JOIN`) podem se tornar lentas e ineficientes, comprometendo a escalabilidade da aplicação.

---

## 🔍 Tipos de Índices Suportados pelo MySQL

Abaixo estão os principais tipos de índices que o MySQL suporta, com exemplos e suas características:

---

### Índices B-TREE (Padrão)

- Tipo de índice padrão para as engines **InnoDB** e **MyISAM**.
- Estrutura baseada em **árvore balanceada**.
- Otimizam buscas por igualdade e intervalo.
- Muito úteis com `WHERE`, `ORDER BY`, `LIKE 'abc%'`, `BETWEEN`, etc.

#### Exemplo:
```sql
CREATE INDEX idx_nome ON clientes(nome);
```

### Índices Compostos
- Envolvem duas ou mais colunas.
- Melhoram consultas que usam as colunas em conjunto na cláusula WHERE, ORDER BY, etc.
- A ordem das colunas importa na utilização do índice.

#### Exemplo:
```sql
CREATE INDEX idx_cliente_data ON pedidos(cliente_id, data_pedido);
```
Este índice melhora consultas como:
```sql
SELECT * FROM pedidos
WHERE cliente_id = 5 AND data_pedido >= '2024-01-01';
```

### Índices Únicos
- Garantem que os valores em uma ou mais colunas não se repitam.
- Também aceleram buscas, além de impor restrições de integridade.

#### Exemplo:
```sql
CREATE UNIQUE INDEX idx_email ON usuarios(email);
```
Garante que nenhum outro usuário possa ser cadastrado com o mesmo e-mail.

### Índices HASH
- Usados principalmente com a engine MEMORY.
- Muito eficientes para buscas por igualdade (=), mas não suportam ordenações ou buscas por intervalo.

#### Exemplo:
```sql
CREATE TABLE cache (
  chave VARCHAR(100),
  valor TEXT,
  INDEX USING HASH (chave)
) ENGINE=MEMORY;
```

### Índices Full-Text
- Especializado para busca eficiente em colunas de texto longo, como TEXT, VARCHAR ou CHAR.
- Permite buscas por palavras-chave, frases e operadores booleanos, acelerando consultas que utilizam busca textual.
- Ideal para sistemas de busca, blogs e portais de conteúdo.

#### Exemplo:
```sql
CREATE FULLTEXT INDEX idx_texto ON artigos(conteudo);
```
Consulta otimizada:
```sql
SELECT * FROM artigos
WHERE MATCH(conteudo) AGAINST('palavra-chave');
```
## Configuração

1. Instale as dependências:
```bash
pip install -r requirements.txt
```

2. Configure as variáveis de ambiente:
```bash
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=root
DB_NAME=indice_teste
N_RUNS=5
```

## Execução

Execute o script principal:
```bash
python bda.py
```

## Estrutura do Projeto

- `graficos/`: Contém os gráficos gerados para cada tipo de índice
- `explain_plans/`: Contém os planos de execução EXPLAIN do MySQL
- `tempos/`: Contém os arquivos CSV com os tempos de execução

## Resultados

O script gera dois tipos de gráficos para cada índice:

1. **Gráfico de Tempo de Execução**
   - Compara tempo com e sem índice
   - Mostra a evolução com diferentes volumes de dados

2. **Gráfico de Melhoria Percentual**
   - Mostra o ganho percentual de performance
   - Calcula a diferença relativa entre tempos

Todos os resultados são organizados por tipo de índice, facilitando a análise.

## Escala de Testes

Os testes são realizados com os seguintes volumes de dados:
- Pequeno: 10.000 clientes e 50.000 pedidos
- Médio: 20.000 clientes e 100.000 pedidos
- Grande: 50.000 clientes e 250.000 pedidos
- Muito Grande: 100.000 clientes e 500.000 pedidos

## Observações

- Cada teste é executado 5 vezes (configurável via N_RUNS)
- A primeira execução é descartada (warm-up)
- Os planos de execução EXPLAIN são salvos para análise
- O banco é recriado a cada execução

## 🎯 Objetivo

O objetivo principal é estudar e compreender o funcionamento dos diferentes tipos de índices disponíveis no MySQL, analisando:
- Tempo de execução das consultas com e sem índices
- Melhoria percentual de desempenho
- Comportamento com diferentes volumes de dados
- Planos de execução EXPLAIN

## 🗄️ Estrutura do Banco de Dados

### Tabela `customers`
```sql
CREATE TABLE customers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100),
    email VARCHAR(100),
    birth_date DATE,
    address TEXT
);
```

### Tabela `orders`
```sql
CREATE TABLE orders (
    id INT AUTO_INCREMENT PRIMARY KEY,
    customer_id INT,
    total DECIMAL(10,2),
    description TEXT,
    order_date DATETIME,
    status VARCHAR(20),
    FOREIGN KEY (customer_id) REFERENCES customers(id)
);
```

## 📊 Tipos de Índices Analisados

1. **Índice UNIQUE (B-Tree)**
   - Aplicado em: `customers.email`
   - Uso: Garante unicidade e acelera buscas por email

2. **Índice B-Tree em Data**
   - Aplicado em: `orders.order_date`
   - Uso: Otimiza consultas por período

3. **Índice B-Tree em Status**
   - Aplicado em: `orders.status`
   - Uso: Melhora filtros por status do pedido

4. **Índice B-Tree em Valor**
   - Aplicado em: `orders.total`
   - Uso: Acelera consultas com ranges de valores

5. **Índice FULLTEXT**
   - Aplicado em: `orders.description`
   - Uso: Otimiza buscas textuais

6. **Índice COMPOSTO (B-Tree)**
   - Aplicado em: `orders(status, order_date)`
   - Uso: Otimiza consultas que filtram por status e período simultaneamente

7. **Índice HASH**
   - Aplicado em: Tabela MEMORY com chave primária usando HASH
   - Uso: Demonstra a eficiência para operações de igualdade exata

## 📈 Volumes de Dados Testados

- 10.000 clientes e 50.000 pedidos
- 20.000 clientes e 100.000 pedidos
- 50.000 clientes e 250.000 pedidos
- 100.000 clientes e 500.000 pedidos

## 🚀 Como Executar

### Pré-requisitos
- Python 3.x
- MySQL Server
- Bibliotecas Python (instale via pip):
  ```bash
  pip install -r requirements.txt
  ```

### Configuração
1. Certifique-se que o MySQL está rodando
2. Crie um arquivo `.env` na raiz do projeto com as variáveis de ambiente:
   ```
   DB_HOST=localhost
   DB_USER=root
   DB_PASSWORD=root
   DB_NAME=indice_teste
   N_RUNS=5
   ```

### Execução
```bash
python bda.py
```

## 📊 Resultados

Os resultados são organizados nas seguintes pastas:

1. **graficos/**
   - Contém gráficos de tempo de execução para cada tipo de índice
   - Contém gráficos de melhoria percentual para cada tipo de índice

2. **explain_plans/**
   - Contém os planos de execução EXPLAIN para cada consulta
   - Organizado por tipo de índice, volume de dados e com/sem índice

3. **tempos/**
   - Contém arquivos CSV com os tempos de execução
   - Cada arquivo mostra a comparação entre consultas com e sem índice

## 🔍 Análise dos Resultados

### Índice UNIQUE (B-Tree)
- Melhora significativa em buscas exatas
- Overhead na inserção devido à verificação de unicidade

### Índice B-Tree (order_date)
- Eficiente para ranges de datas
- Bom para relatórios por período

### Índice B-Tree (status)
- Útil para valores categóricos
- Menor impacto devido à baixa cardinalidade

### Índice B-Tree (total)
- Eficaz para ranges numéricos
- Bom para relatórios financeiros

### Índice FULLTEXT (description)
- Otimiza buscas textuais
- Maior overhead de armazenamento

### Índice COMPOSTO (status, order_date)
- Melhoria dramática para consultas com múltiplos filtros
- Demonstra a importância da ordem das colunas no índice

### Índice HASH (id)
- Extremamente eficiente para buscas por igualdade exata
- Limitado a operações de igualdade (não suporta ranges)

## 📝 Conclusões

1. Índices melhoram significativamente o desempenho das consultas
2. O ganho de performance aumenta com o volume de dados
3. Cada tipo de índice tem seu caso de uso ideal
4. É importante balancear o uso de índices com o overhead de manutenção
5. Índices compostos são essenciais para consultas com múltiplos filtros
6. Índices HASH são extremamente eficientes para buscas por chave exata

## 👥 Contribuições

Contribuições são bem-vindas! Sinta-se à vontade para:
- Reportar bugs
- Sugerir melhorias
- Adicionar novos tipos de índices
- Melhorar a documentação

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para mais detalhes. 
