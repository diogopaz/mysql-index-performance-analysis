# Análise de Desempenho de Índices MySQL

Este projeto demonstra e analisa o impacto do uso de diferentes tipos de índices no desempenho de consultas em um banco de dados MySQL. O estudo utiliza um cenário de e-commerce com clientes e pedidos para realizar testes práticos.

## 🎯 Objetivo

O objetivo principal é estudar e compreender o funcionamento dos diferentes tipos de índices disponíveis no MySQL, analisando:
- Tempo de execução das consultas com e sem índices
- Melhoria percentual de desempenho
- Comportamento com diferentes volumes de dados

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

1. **Índice UNIQUE**
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
  pip install mysql-connector-python faker matplotlib
  ```

### Configuração
1. Certifique-se que o MySQL está rodando
2. Ajuste as credenciais de conexão no arquivo `bda.py`:
   ```python
   host='localhost'
   user='root'
   password='root'
   ```

### Execução
```bash
python bda.py
```

## 📊 Resultados

O script gera cinco gráficos diferentes, um para cada tipo de índice:
- `resultados_idx_cust_email.png`
- `resultados_idx_ord_date.png`
- `resultados_idx_ord_status.png`
- `resultados_idx_ord_total.png`
- `resultados_idx_ord_desc.png`

Cada gráfico mostra:
1. Tempo de execução (com e sem índice)
2. Melhoria percentual de desempenho

## 🔍 Análise dos Resultados

### Índice UNIQUE (email)
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

## 📝 Conclusões

1. Índices melhoram significativamente o desempenho das consultas
2. O ganho de performance aumenta com o volume de dados
3. Cada tipo de índice tem seu caso de uso ideal
4. É importante balancear o uso de índices com o overhead de manutenção

## 👥 Contribuições

Contribuições são bem-vindas! Sinta-se à vontade para:
- Reportar bugs
- Sugerir melhorias
- Adicionar novos tipos de índices
- Melhorar a documentação

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para mais detalhes. 