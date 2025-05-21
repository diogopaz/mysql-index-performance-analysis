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
###

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

## 🎯 Objetivo

O objetivo é estudar e comparar o desempenho dos diferentes tipos de índices disponíveis no MySQL, analisando:
- Tempo de execução das consultas com e sem índices
- Melhoria percentual de desempenho
- Comportamento com diferentes volumes de dados
- Planos de execução EXPLAIN

## 🔍 Tipos de Índices Analisados

1. **Índice UNIQUE (B-Tree)**
   - Aplicado em: `customers.email`
   - Uso: Garante unicidade e acelera buscas por email
   - ![image](https://github.com/user-attachments/assets/cb04f9c7-0d69-4372-8423-bd5b09abeed8)

2. **Índice B-Tree em Data**
   - Aplicado em: `orders.order_date`
   - Uso: Otimiza consultas por período
  
   - ![image](https://github.com/user-attachments/assets/cb3f2c2a-427e-43c4-bb17-6d5d8707b655)

3. **Índice B-Tree em Status**
   - Aplicado em: `orders.status`
   - Uso: Melhora filtros por status do pedido
  
   - ![image](https://github.com/user-attachments/assets/a0151a4a-d122-4175-aa07-870c2a1e301a)

4. **Índice B-Tree em Valor**
   - Aplicado em: `orders.total`
   - Uso: Acelera consultas com ranges de valores
  
   - ![image](https://github.com/user-attachments/assets/19e23c27-da14-408c-a08c-f46b4a085ebb)

5. **Índice FULLTEXT**
   - Aplicado em: `orders.description`
   - Uso: Otimiza buscas textuais
  
   - ![image](https://github.com/user-attachments/assets/a95b6e75-ea8e-4195-9b4b-163381dcf78a)

6. **Índice COMPOSTO (B-Tree)**
   - Aplicado em: `orders(status, order_date)`
   - Uso: Otimiza consultas que filtram por status e período simultaneamente
  
   - ![image](https://github.com/user-attachments/assets/c1a45b51-f92d-4c55-bf94-87691661b337)

7. **Índice HASH**
   - Aplicado em: Tabela MEMORY com chave primária usando HASH
   - Uso: Demonstra a eficiência para operações de igualdade exata
  
   - ![image](https://github.com/user-attachments/assets/824adae8-b300-45de-8a67-9c46fff382df)

## 📊 Estrutura do Projeto

- `graficos/`: Gráficos de tempos de execução e melhorias percentuais
- `explain_plans/`: Planos de execução EXPLAIN do MySQL
- `tempos/`: Arquivos CSV com os tempos de execução

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

## 🚀 Como Executar

### Pré-requisitos
- Python 3.x
- MySQL Server
- Bibliotecas necessárias: `pip install -r requirements.txt`

### Configuração
1. Certifique-se que o MySQL está rodando
2. Crie um arquivo `.env` na raiz do projeto:
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

## 📈 Volumes de Dados Testados

- Pequeno: 10.000 clientes e 50.000 pedidos
- Médio: 20.000 clientes e 100.000 pedidos
- Grande: 50.000 clientes e 250.000 pedidos
- Muito Grande: 100.000 clientes e 500.000 pedidos

## 📊 Resultados e Análises

### Índice UNIQUE (B-Tree)
- Melhoria significativa em buscas exatas
- Overhead na inserção devido à verificação de unicidade

- ![image](https://github.com/user-attachments/assets/8d8491c2-b054-4bab-b7e9-2b2cfe849074)
- ![image](https://github.com/user-attachments/assets/63bb88c0-846a-4341-96d9-78b7ced35ab1)

### Índice B-Tree (order_date)
- Eficiente para ranges de datas
- Ideal para relatórios por período

- ![image](https://github.com/user-attachments/assets/475c574d-1300-4f24-9e3b-9e55d2c7590c)
- ![image](https://github.com/user-attachments/assets/5e79d184-b37e-4596-91b4-5436bb311155)

### Índice B-Tree (status)
- Útil para valores categóricos
- Menor impacto devido à baixa cardinalidade (poucos valores distintos)

- ![image](https://github.com/user-attachments/assets/5b2e564d-cd47-49b2-8898-9f5a8d8f7ab8)
- ![image](https://github.com/user-attachments/assets/7cff507a-1530-4382-ab57-5237c266c777)

### Índice B-Tree (total)
- Eficaz para ranges numéricos
- Bom para relatórios financeiros e filtros por faixa de preço

- ![image](https://github.com/user-attachments/assets/783013c0-4f79-4e60-9652-b463cafb870a)
- ![image](https://github.com/user-attachments/assets/5519d17a-5bb9-4c35-b5b0-06a2afe90982)

### Índice FULLTEXT (description)
- Otimiza buscas textuais
- Maior overhead de armazenamento

- ![image](https://github.com/user-attachments/assets/e3f6a33d-50ca-400a-aeda-4168ab7de25a)
- ![image](https://github.com/user-attachments/assets/80188333-f867-4f1c-bfee-899e6ba049fa)

### Índice COMPOSTO (status, order_date)
- Melhoria dramática para consultas com múltiplos filtros
- Demonstra a importância da ordem das colunas no índice

- ![image](https://github.com/user-attachments/assets/71f1617a-76d4-4975-90f3-502a3e605233)
- ![image](https://github.com/user-attachments/assets/aeb74198-3e8f-44e4-986c-8ca61313007f)

### Índice HASH (id)
- Extremamente eficiente para buscas por igualdade exata
- Limitado a operações de igualdade (não suporta ranges)

- ![image](https://github.com/user-attachments/assets/9b7d1ab3-fe72-44a4-b4c3-08954c00f3aa)
- ![image](https://github.com/user-attachments/assets/facd898e-917e-4387-ace4-a60191a7ff20)

## 📝 Conclusões

1. Índices melhoram significativamente o desempenho das consultas
2. O ganho de performance aumenta com o volume de dados
3. Cada tipo de índice tem seu caso de uso ideal
4. É importante balancear o uso de índices com o overhead de manutenção
5. Índices compostos são essenciais para consultas com múltiplos filtros
6. Índices HASH são extremamente eficientes para buscas por chave exata
