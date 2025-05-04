import mysql.connector
from mysql.connector import errorcode
from faker import Faker
import time
import matplotlib.pyplot as plt

# 1) Garante existência do BD
root_cnx = mysql.connector.connect(host='localhost', user='root', password='root')
root_cur = root_cnx.cursor()
root_cur.execute("CREATE DATABASE IF NOT EXISTS indice_teste")
root_cur.close()
root_cnx.close()

# 2) Conecta ao BD
conn = mysql.connector.connect(
    host='localhost', user='root', password='root', database='indice_teste'
)
cursor = conn.cursor()
fake = Faker('pt_BR')

# 3) Cria schema limpo
def reset_schema():
    cursor.execute("DROP TABLE IF EXISTS orders")
    cursor.execute("DROP TABLE IF EXISTS customers")
    cursor.execute("""
    CREATE TABLE customers (
        id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(100),
        email VARCHAR(100),
        birth_date DATE,
        address TEXT
    ) ENGINE=InnoDB;
    """)
    cursor.execute("""
    CREATE TABLE orders (
        id INT AUTO_INCREMENT PRIMARY KEY,
        customer_id INT,
        total DECIMAL(10,2),
        description TEXT,
        order_date DATETIME,
        status VARCHAR(20),
        FOREIGN KEY (customer_id) REFERENCES customers(id)
    ) ENGINE=InnoDB;
    """)
    conn.commit()

# 4) Popula com dados fictícios
def populate(n_customers, n_orders):
    cursor.execute("DELETE FROM orders")
    cursor.execute("DELETE FROM customers")
    conn.commit()

    # Gera clientes em lotes menores
    batch_size = 1000
    for i in range(0, n_customers, batch_size):
        current_batch = min(batch_size, n_customers - i)
        custs = [(fake.name(), fake.unique.email(), fake.date_of_birth(), fake.address()) 
                 for _ in range(current_batch)]
        cursor.executemany("INSERT INTO customers (name,email,birth_date,address) VALUES (%s,%s,%s,%s)", custs)
        conn.commit()
        print(f"Inseridos {i + current_batch} de {n_customers} clientes")

    # Busca IDs
    cursor.execute("SELECT id FROM customers")
    ids = [r[0] for r in cursor.fetchall()]

    # Gera pedidos em lotes menores
    for i in range(0, n_orders, batch_size):
        current_batch = min(batch_size, n_orders - i)
        orders = [
            (
                fake.random_element(ids),
                round(fake.pydecimal(left_digits=4, right_digits=2, min_value=10, max_value=1000),2),
                fake.text(max_nb_chars=200),
                fake.date_time_this_year(),
                fake.random_element(['Pendente', 'Processando', 'Enviado', 'Entregue'])
            )
            for _ in range(current_batch)
        ]
        cursor.executemany(
            "INSERT INTO orders (customer_id,total,description,order_date,status) VALUES (%s,%s,%s,%s,%s)",
            orders
        )
        conn.commit()
        print(f"Inseridos {i + current_batch} de {n_orders} pedidos")

# 5) Mede performance: sem índice → cria índice → com índice → drop índice
def measure_performance(create_sql, drop_sql, query_sql, params=None):
    if params is None:
        params = ()
    
    # Sem índice
    t0 = time.time()
    cursor.execute(query_sql, params)
    cursor.fetchall()
    no_idx = time.time() - t0

    # Cria índice
    if create_sql:
        try:
            cursor.execute(create_sql)
            conn.commit()
        except mysql.connector.Error as err:
            print(f"Erro ao criar índice: {err}")
            return no_idx, no_idx

    # Com índice
    t1 = time.time()
    cursor.execute(query_sql, params)
    cursor.fetchall()
    with_idx = time.time() - t1

    # Drop
    if drop_sql:
        try:
            cursor.execute(drop_sql)
            conn.commit()
        except mysql.connector.Error as err:
            print(f"Erro ao remover índice: {err}")

    return no_idx, with_idx

# 6) Testa para vários tamanhos
sizes = [
    (10000, 50000),
    (20000, 100000),
    (50000, 250000),
    (100000, 500000),
]
results = {
    'idx_cust_email': [],
    'idx_ord_date': [],
    'idx_ord_status': [],
    'idx_ord_total': [],
    'idx_ord_desc': []
}

reset_schema()
for nc, no in sizes:
    print(f"\nTestando com {nc} clientes e {no} pedidos...")
    populate(nc, no)

    # Índice UNIQUE em customers.email
    ni, wi = measure_performance(
        "CREATE UNIQUE INDEX idx_cust_email ON customers(email)",
        "DROP INDEX idx_cust_email ON customers",
        "SELECT * FROM customers WHERE email LIKE %s",
        ('%@gmail.com',)
    )
    results['idx_cust_email'].append((ni, wi))

    # Índice B-Tree em orders.order_date
    ni, wi = measure_performance(
        "CREATE INDEX idx_ord_date ON orders(order_date)",
        "DROP INDEX idx_ord_date ON orders",
        "SELECT * FROM orders WHERE order_date BETWEEN %s AND %s",
        ('2023-01-01', '2023-12-31')
    )
    results['idx_ord_date'].append((ni, wi))

    # Índice B-Tree em orders.status
    ni, wi = measure_performance(
        "CREATE INDEX idx_ord_status ON orders(status)",
        "DROP INDEX idx_ord_status ON orders",
        "SELECT * FROM orders WHERE status = %s",
        ('Entregue',)
    )
    results['idx_ord_status'].append((ni, wi))

    # Índice B-Tree em orders.total
    ni, wi = measure_performance(
        "CREATE INDEX idx_ord_total ON orders(total)",
        "DROP INDEX idx_ord_total ON orders",
        "SELECT * FROM orders WHERE total > %s",
        (500,)
    )
    results['idx_ord_total'].append((ni, wi))

    # Índice FULLTEXT em orders.description
    try:
        cursor.execute("CREATE FULLTEXT INDEX idx_ord_desc ON orders(description)")
        conn.commit()
        
        # Teste com índice
        t1 = time.time()
        cursor.execute(
            "SELECT * FROM orders WHERE MATCH(description) AGAINST(%s IN BOOLEAN MODE)",
            ('importante',)
        )
        cursor.fetchall()
        with_idx = time.time() - t1
        
        # Teste sem índice
        cursor.execute("DROP INDEX idx_ord_desc ON orders")
        conn.commit()
        t0 = time.time()
        cursor.execute(
            "SELECT * FROM orders WHERE description LIKE %s",
            ('%importante%',)
        )
        cursor.fetchall()
        no_idx = time.time() - t0
        
    except mysql.connector.Error as err:
        print(f"Erro com índice FULLTEXT: {err}")
        no_idx, with_idx = 0, 0
    
    results['idx_ord_desc'].append((no_idx, with_idx))

# 7) Gera gráficos individuais
x = list(range(len(sizes)))
labels = [f"{no:,} pedidos" for _, no in sizes]

for idx_name, times in results.items():
    plt.figure(figsize=(10, 6))
    no_times, wi_times = zip(*times)
    
    # Gráfico de tempo de execução
    plt.subplot(2, 1, 1)
    plt.plot(x, no_times, '--o', label='Sem índice')
    plt.plot(x, wi_times, '-o', label='Com índice')
    plt.xticks(x, labels, rotation=45)
    plt.xlabel("Número de registros")
    plt.ylabel("Tempo (s)")
    plt.title(f"Tempo de Execução - {idx_name}")
    plt.legend()
    plt.grid(True)
    
    # Gráfico de melhoria percentual
    plt.subplot(2, 1, 2)
    improvement = []
    for no, wi in zip(no_times, wi_times):
        if no > 0:
            improvement.append((no - wi) / no * 100)
        else:
            improvement.append(0)
    plt.plot(x, improvement, '-o', color='green')
    plt.xticks(x, labels, rotation=45)
    plt.xlabel("Número de registros")
    plt.ylabel("Melhoria (%)")
    plt.title(f"Melhoria Percentual - {idx_name}")
    plt.grid(True)
    
    plt.tight_layout()
    plt.savefig(f'resultados_{idx_name}.png')
    plt.close()

cursor.close()
conn.close()
