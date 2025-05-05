import mysql.connector
from mysql.connector import errorcode
from faker import Faker
import time
import matplotlib.pyplot as plt
import os
from dotenv import load_dotenv

# Carrega variáveis de ambiente
load_dotenv()

# Configurações
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_USER = os.getenv('DB_USER', 'root')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'root')
DB_NAME = os.getenv('DB_NAME', 'indice_teste')
N_RUNS = int(os.getenv('N_RUNS', 5))  # Número de execuções por teste

# 1) Garante existência do BD
def create_database():
    try:
        root_cnx = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD
        )
        root_cur = root_cnx.cursor()
        root_cur.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME}")
        root_cur.close()
        root_cnx.close()
    except mysql.connector.Error as err:
        print(f"Erro ao criar banco de dados: {err}")
        raise

# 2) Conecta ao BD
def get_connection():
    return mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME
    )

# 3) Cria schema limpo
def reset_schema(conn, cursor):
    try:
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
    except mysql.connector.Error as err:
        print(f"Erro ao resetar schema: {err}")
        raise

# 4) Popula com dados fictícios
def populate(conn, cursor, n_customers, n_orders):
    try:
        cursor.execute("DELETE FROM orders")
        cursor.execute("DELETE FROM customers")
        conn.commit()

        fake = Faker('pt_BR')
        batch_size = 1000

        # Insere clientes
        for i in range(0, n_customers, batch_size):
            batch = min(batch_size, n_customers - i)
            custs = [
                (fake.name(), fake.unique.email(), fake.date_of_birth(), fake.address())
                for _ in range(batch)
            ]
            cursor.executemany(
                "INSERT INTO customers (name, email, birth_date, address) VALUES (%s, %s, %s, %s)",
                custs
            )
            conn.commit()
            print(f"Inseridos {i + batch} de {n_customers} clientes")

        # Busca IDs para pedidos
        cursor.execute("SELECT id FROM customers")
        ids = [r[0] for r in cursor.fetchall()]

        # Insere pedidos
        for i in range(0, n_orders, batch_size):
            batch = min(batch_size, n_orders - i)
            orders = [
                (
                    fake.random_element(ids),
                    round(fake.pydecimal(left_digits=4, right_digits=2, min_value=10, max_value=1000), 2),
                    fake.text(max_nb_chars=200),
                    fake.date_time_this_year(),
                    fake.random_element(['Pendente', 'Processando', 'Enviado', 'Entregue'])
                )
                for _ in range(batch)
            ]
            cursor.executemany(
                "INSERT INTO orders (customer_id, total, description, order_date, status) VALUES (%s, %s, %s, %s, %s)",
                orders
            )
            conn.commit()
            print(f"Inseridos {i + batch} de {n_orders} pedidos")
    except mysql.connector.Error as err:
        print(f"Erro ao popular banco: {err}")
        raise

# 5) Funções de medição
def measure_performance(conn, cursor, create_sql, drop_sql, query_sql, params=()):
    try:
        # Garante que o índice foi removido
        if drop_sql:
            try:
                cursor.execute(drop_sql)
                conn.commit()
            except mysql.connector.Error:
                pass

        # Sem índice: warm-up
        cursor.execute(query_sql, params)
        cursor.fetchall()

        # Medidas sem índice
        times = []
        for _ in range(N_RUNS):
            t0 = time.time()
            cursor.execute(query_sql, params)
            cursor.fetchall()
            times.append(time.time() - t0)
        no_idx_avg = sum(times[1:]) / (N_RUNS - 1)  # descarta primeira execução

        # Cria índice
        if create_sql:
            cursor.execute(create_sql)
            conn.commit()

        # Com índice: warm-up
        cursor.execute(query_sql, params)
        cursor.fetchall()

        # Medidas com índice
        times = []
        for _ in range(N_RUNS):
            t0 = time.time()
            cursor.execute(query_sql, params)
            cursor.fetchall()
            times.append(time.time() - t0)
        with_idx_avg = sum(times[1:]) / (N_RUNS - 1)

        # Remove índice
        if drop_sql:
            cursor.execute(drop_sql)
            conn.commit()

        return no_idx_avg, with_idx_avg
    except mysql.connector.Error as err:
        print(f"Erro ao medir performance: {err}")
        return None, None

def measure_fulltext(conn, cursor, idx_sql, drop_sql, query_with, params_with, query_without, params_without):
    try:
        # Garante que não há índice
        try:
            cursor.execute(drop_sql)
            conn.commit()
        except mysql.connector.Error:
            pass

        # Sem índice (LIKE): warm-up
        cursor.execute(query_without, params_without)
        cursor.fetchall()

        # Medidas sem índice
        times = []
        for _ in range(N_RUNS):
            t0 = time.time()
            cursor.execute(query_without, params_without)
            cursor.fetchall()
            times.append(time.time() - t0)
        no_idx_avg = sum(times[1:]) / (N_RUNS - 1)

        # Cria FULLTEXT
        cursor.execute(idx_sql)
        conn.commit()

        # Com índice (MATCH): warm-up
        cursor.execute(query_with, params_with)
        cursor.fetchall()

        # Medidas com índice
        times = []
        for _ in range(N_RUNS):
            t0 = time.time()
            cursor.execute(query_with, params_with)
            cursor.fetchall()
            times.append(time.time() - t0)
        with_idx_avg = sum(times[1:]) / (N_RUNS - 1)

        # Remove índice
        cursor.execute(drop_sql)
        conn.commit()

        return no_idx_avg, with_idx_avg
    except mysql.connector.Error as err:
        print(f"Erro ao medir FULLTEXT: {err}")
        return None, None

# 6) Testes principais
def run_tests():
    try:
        # Escala maior para testes completos
        sizes = [
            (10000, 50000),     # Pequeno
            (20000, 100000),    # Médio
            (50000, 250000),    # Grande
            (100000, 500000),   # Muito Grande
        ]
        
        results = {
            'idx_cust_email': [],
            'idx_ord_date': [],
            'idx_ord_status': [],
            'idx_ord_total': [],
            'idx_ord_desc': []
        }

        # Cria banco e conecta
        create_database()
        conn = get_connection()
        cursor = conn.cursor()

        # Reseta schema
        reset_schema(conn, cursor)

        for nc, no in sizes:
            print(f"\nTestando com {nc} clientes e {no} pedidos...")
            populate(conn, cursor, nc, no)

            # Seleciona um email real para testar
            cursor.execute("SELECT email FROM customers LIMIT 1")
            sample_email = cursor.fetchone()[0]

            # 1) UNIQUE em customers.email
            ni, wi = measure_performance(
                conn, cursor,
                "CREATE UNIQUE INDEX idx_cust_email ON customers(email)",
                "DROP INDEX idx_cust_email ON customers",
                "SELECT * FROM customers WHERE email = %s",
                (sample_email,)
            )
            if ni is not None and wi is not None:
                results['idx_cust_email'].append((ni, wi))

            # 2) B-Tree em orders.order_date
            ni, wi = measure_performance(
                conn, cursor,
                "CREATE INDEX idx_ord_date ON orders(order_date)",
                "DROP INDEX idx_ord_date ON orders",
                "SELECT * FROM orders WHERE order_date BETWEEN %s AND %s",
                ('2023-01-01', '2023-12-31')
            )
            if ni is not None and wi is not None:
                results['idx_ord_date'].append((ni, wi))

            # 3) B-Tree em orders.status
            ni, wi = measure_performance(
                conn, cursor,
                "CREATE INDEX idx_ord_status ON orders(status)",
                "DROP INDEX idx_ord_status ON orders",
                "SELECT * FROM orders WHERE status = %s",
                ('Entregue',)
            )
            if ni is not None and wi is not None:
                results['idx_ord_status'].append((ni, wi))

            # 4) B-Tree em orders.total
            ni, wi = measure_performance(
                conn, cursor,
                "CREATE INDEX idx_ord_total ON orders(total)",
                "DROP INDEX idx_ord_total ON orders",
                "SELECT * FROM orders WHERE total > %s",
                (500,)
            )
            if ni is not None and wi is not None:
                results['idx_ord_total'].append((ni, wi))

            # 5) FULLTEXT em orders.description
            ni, wi = measure_fulltext(
                conn, cursor,
                "CREATE FULLTEXT INDEX idx_ord_desc ON orders(description)",
                "DROP INDEX idx_ord_desc ON orders",
                "SELECT * FROM orders WHERE MATCH(description) AGAINST(%s IN BOOLEAN MODE)",
                ('importante',),
                "SELECT * FROM orders WHERE description LIKE %s",
                ('%importante%',)
            )
            if ni is not None and wi is not None:
                results['idx_ord_desc'].append((ni, wi))

        # 7) Gera gráficos
        x = list(range(len(sizes)))
        labels = [f"{no:,} pedidos" for _, no in sizes]

        for idx_name, times in results.items():
            if not times:  # Pula se não houver resultados
                continue

            no_times, wi_times = zip(*times)

            # Gráfico de tempo de execução
            plt.figure(figsize=(10, 6))
            plt.plot(x, no_times, '--o', label='Sem índice')
            plt.plot(x, wi_times, '-o', label='Com índice')
            plt.xticks(x, labels, rotation=45)
            plt.xlabel("Número de pedidos")
            plt.ylabel("Tempo de Execução (s)")
            plt.title(f"{idx_name} — Execução sem vs com índice")
            plt.legend()
            plt.grid(True)
            plt.tight_layout()
            plt.savefig(f"{idx_name}_exec_time.png")
            plt.close()

            # Gráfico de melhoria percentual
            improvement = [
                ((no - wi) / no * 100) if no > 0 else 0
                for no, wi in zip(no_times, wi_times)
            ]
            plt.figure(figsize=(10, 6))
            plt.plot(x, improvement, '-o')
            plt.xticks(x, labels, rotation=45)
            plt.xlabel("Número de pedidos")
            plt.ylabel("Melhoria Percentual (%)")
            plt.title(f"{idx_name} — Melhoria Percentual")
            plt.grid(True)
            plt.tight_layout()
            plt.savefig(f"{idx_name}_improvement.png")
            plt.close()

        cursor.close()
        conn.close()

    except Exception as e:
        print(f"Erro durante a execução: {e}")
        raise

if __name__ == "__main__":
    run_tests()
