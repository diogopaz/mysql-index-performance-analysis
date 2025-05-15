# Análise de Desempenho de Índices MySQL

Este projeto realiza uma análise comparativa do desempenho de diferentes tipos de índices no MySQL, medindo o tempo de execução de consultas com e sem índices.

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

### Índice B-Tree (order_date)
- Eficiente para ranges de datas
- Ideal para relatórios por período

### Índice B-Tree (status)
- Útil para valores categóricos
- Menor impacto devido à baixa cardinalidade (poucos valores distintos)

### Índice B-Tree (total)
- Eficaz para ranges numéricos
- Bom para relatórios financeiros e filtros por faixa de preço

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

## 📚 Apêndice: Tipos de Índices no MySQL

### B-TREE (Padrão)
- Tipo de índice padrão para engines InnoDB e MyISAM
- Estrutura baseada em árvore balanceada
- Otimiza buscas por igualdade e intervalo

### Índices Compostos
- Combina duas ou mais colunas
- A ordem das colunas impacta a eficiência

### Índices Únicos
- Garante valores únicos nas colunas indexadas
- Também acelera consultas por essas colunas

### Índices HASH
- Usados principalmente na engine MEMORY
- Muito eficientes para buscas por igualdade exata
- Não suportam ordenações ou buscas por intervalo

### Índices FULLTEXT
- Especializados para busca em texto longo
- Permitem buscas por relevância, palavras-chave e frases
