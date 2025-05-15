import mysql.connector
from mysql.connector import errorcode
from faker import Faker
import time
import matplotlib.pyplot as plt
import os
from dotenv import load_dotenv
import csv

# Carrega variáveis de ambiente
load_dotenv()

DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_USER = os.getenv('DB_USER', 'root')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'root')
DB_NAME = os.getenv('DB_NAME', 'indice_teste')
N_RUNS = int(os.getenv('N_RUNS', 5))  # Número de execuções por teste

# Diretórios para resultados
EXPLAIN_DIR = "explain_plans"
CHARTS_DIR = "graficos"
TIMES_DIR = "tempos"

# Cria diretórios se não existirem
os.makedirs(EXPLAIN_DIR, exist_ok=True)
os.makedirs(CHARTS_DIR, exist_ok=True)
os.makedirs(TIMES_DIR, exist_ok=True)

def create_database():
    """Cria o banco de dados caso não exista."""
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

def get_connection():
    """Retorna conexão com o banco de dados."""
    return mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME
    )

def reset_schema(conn, cursor):
    """Cria esquema limpo com as tabelas customers e orders."""
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

def populate(conn, cursor, n_customers, n_orders):
    """Popula as tabelas com dados fictícios usando Faker."""
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

def get_explain_plan(cursor, query, params=()):
    """Retorna o plano EXPLAIN da query executada."""
    try:
        cursor.execute("EXPLAIN " + query, params)
        plan = cursor.fetchall()
        return plan, cursor.description
    except mysql.connector.Error as err:
        print(f"Erro ao obter plano EXPLAIN: {err}")
        return None, None

def save_explain_plan(plan_data, filename):
    """Salva o plano EXPLAIN em arquivo CSV para análise."""
    if plan_data is None:
        return
    
    plan, description = plan_data
    if plan is None:
        return

    filepath = os.path.join(EXPLAIN_DIR, filename)
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        # Obtém os cabeçalhos da descrição do cursor
        if description:
            headers = [desc[0] for desc in description]
            writer.writerow(headers)
        # Escreve as linhas do plano
        writer.writerows(plan)

def measure_performance(conn, cursor, create_sql, drop_sql, query_sql, params=(), test_name="", size_label="", index_type="BTREE"):
    """
    Mede tempo de execução de consulta com e sem índice,
    executa planos EXPLAIN e salva resultados.
    """
    try:
        # Remove índice se existir
        if drop_sql:
            try:
                cursor.execute(drop_sql)
                conn.commit()
            except mysql.connector.Error:
                pass

        # Warm-up sem índice
        cursor.execute(query_sql, params)
        cursor.fetchall()

        no_idx_times = []
        for _ in range(N_RUNS):
            t0 = time.time()
            cursor.execute(query_sql, params)
            cursor.fetchall()
            no_idx_times.append(time.time() - t0)
        no_idx_avg = sum(no_idx_times[1:]) / (N_RUNS - 1)  # descarta warm-up

        # Salva plano explain sem índice
        explain_plan_no_idx = get_explain_plan(cursor, query_sql, params)
        save_explain_plan(explain_plan_no_idx, f'{index_type}_{test_name}_{size_label}_no_idx.csv')

        # Cria índice
        if create_sql:
            cursor.execute(create_sql)
            conn.commit()

        # Warm-up com índice
        cursor.execute(query_sql, params)
        cursor.fetchall()

        with_idx_times = []
        for _ in range(N_RUNS):
            t0 = time.time()
            cursor.execute(query_sql, params)
            cursor.fetchall()
            with_idx_times.append(time.time() - t0)
        with_idx_avg = sum(with_idx_times[1:]) / (N_RUNS - 1)

        # Salva plano explain com índice
        explain_plan_with_idx = get_explain_plan(cursor, query_sql, params)
        save_explain_plan(explain_plan_with_idx, f'{index_type}_{test_name}_{size_label}_with_idx.csv')

        # Remove índice para próxima rodada
        if drop_sql:
            cursor.execute(drop_sql)
            conn.commit()

        # Salvando tempos em CSV (append)
        filename = os.path.join(TIMES_DIR, f'times_{index_type}_{test_name}.csv')
        file_exists = os.path.isfile(filename)
        with open(filename, 'a', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            if not file_exists:
                writer.writerow(['Volume', 'Sem Índice (s)', 'Com Índice (s)', 'Melhoria (%)'])
            improvement = ((no_idx_avg - with_idx_avg) / no_idx_avg * 100) if no_idx_avg else 0
            writer.writerow([size_label, round(no_idx_avg, 4), round(with_idx_avg, 4), round(improvement, 2)])

        return no_idx_avg, with_idx_avg
    except mysql.connector.Error as err:
        print(f"Erro ao medir performance: {err}")
        return None, None

def measure_fulltext(conn, cursor, idx_sql, drop_sql, query_with, params_with, query_without, params_without, test_name="", size_label=""):
    """
    Mede desempenho específico para FULLTEXT index,
    comparando MATCH AGAINST e LIKE, incluindo planos EXPLAIN.
    """
    try:
        # Remove índice
        try:
            cursor.execute(drop_sql)
            conn.commit()
        except mysql.connector.Error:
            pass

        # Warm-up LIKE (sem índice)
        cursor.execute(query_without, params_without)
        cursor.fetchall()

        no_idx_times = []
        for _ in range(N_RUNS):
            t0 = time.time()
            cursor.execute(query_without, params_without)
            cursor.fetchall()
            no_idx_times.append(time.time() - t0)
        no_idx_avg = sum(no_idx_times[1:]) / (N_RUNS - 1)

        explain_no_idx = get_explain_plan(cursor, query_without, params_without)
        save_explain_plan(explain_no_idx, f'FULLTEXT_{test_name}_{size_label}_no_idx.csv')

        # Cria FULLTEXT index
        cursor.execute(idx_sql)
        conn.commit()

        # Warm-up MATCH AGAINST
        cursor.execute(query_with, params_with)
        cursor.fetchall()

        with_idx_times = []
        for _ in range(N_RUNS):
            t0 = time.time()
            cursor.execute(query_with, params_with)
            cursor.fetchall()
            with_idx_times.append(time.time() - t0)
        with_idx_avg = sum(with_idx_times[1:]) / (N_RUNS - 1)

        explain_with_idx = get_explain_plan(cursor, query_with, params_with)
        save_explain_plan(explain_with_idx, f'FULLTEXT_{test_name}_{size_label}_with_idx.csv')

        # Remove índice para próxima rodada
        cursor.execute(drop_sql)
        conn.commit()

        # Salvando tempos em CSV (append)
        filename = os.path.join(TIMES_DIR, f'times_FULLTEXT_{test_name}.csv')
        file_exists = os.path.isfile(filename)
        with open(filename, 'a', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            if not file_exists:
                writer.writerow(['Volume', 'Sem Índice (s)', 'Com Índice (s)', 'Melhoria (%)'])
            improvement = ((no_idx_avg - with_idx_avg) / no_idx_avg * 100) if no_idx_avg else 0
            writer.writerow([size_label, round(no_idx_avg, 4), round(with_idx_avg, 4), round(improvement, 2)])

        return no_idx_avg, with_idx_avg
    except mysql.connector.Error as err:
        print(f"Erro ao medir FULLTEXT: {err}")
        return None, None

def plot_results(results, sizes, test_name, index_type=""):
    """
    Gera gráficos de comparação de tempos e melhoria percentual,
    salva arquivos PNG.
    """
    x = list(range(len(sizes)))
    labels = [f"{no:,} pedidos" for _, no in sizes]

    no_times, wi_times = zip(*results)

    plt.figure(figsize=(10, 6))
    plt.plot(x, no_times, '--o', label='Sem índice')
    plt.plot(x, wi_times, '-o', label='Com índice')
    plt.xticks(x, labels, rotation=45)
    plt.xlabel("Número de pedidos")
    plt.ylabel("Tempo de Execução (s)")
    plt.title(f"{index_type} {test_name} — Execução sem vs com índice")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(os.path.join(CHARTS_DIR, f"{index_type}_{test_name}_exec_time.png"))
    plt.close()

    # Gráfico de melhoria percentual
    improvements = [((no - wi) / no * 100) if no else 0 for no, wi in results]
    plt.figure(figsize=(10, 6))
    plt.plot(x, improvements, '-o', color='green')
    plt.xticks(x, labels, rotation=45)
    plt.xlabel("Número de pedidos")
    plt.ylabel("Melhoria Percentual (%)")
    plt.title(f"{index_type} {test_name} — Melhoria percentual com índice")
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(os.path.join(CHARTS_DIR, f"{index_type}_{test_name}_improvement.png"))
    plt.close()

def run_tests():
    """Executa sequência completa de testes para todos os índices e volumes."""
    try:
        sizes = [
            # (10000, 50000),     # Pequeno
            # (20000, 100000),    # Médio
            # (50000, 250000),    # Grande
            # (100000, 500000),   # Muito Grande

            ## Escala menor para testes:
            (1000, 5000),      # Muito Pequeno
            (2000, 10000),     # Pequeno
            (5000, 25000),     # Médio
        ]
        
        results = {
            'idx_cust_email': [],
            'idx_ord_date': [],
            'idx_ord_status': [],
            'idx_ord_total': [],
            'idx_ord_desc': [],
            'idx_composto': [],
            'idx_hash': []
        }

        # Mapeia os nomes dos índices para seus tipos
        index_types = {
            'idx_cust_email': 'BTREE_UNIQUE',
            'idx_ord_date': 'BTREE',
            'idx_ord_status': 'BTREE',
            'idx_ord_total': 'BTREE',
            'idx_ord_desc': 'FULLTEXT',
            'idx_composto': 'BTREE_COMPOSTO',
            'idx_hash': 'HASH'
        }

        create_database()
        conn = get_connection()
        cursor = conn.cursor()

        reset_schema(conn, cursor)

        for nc, no in sizes:
            size_label = f"{no}"
            print(f"\nTestando com {nc} clientes e {no} pedidos...")
            populate(conn, cursor, nc, no)

            cursor.execute("SELECT email FROM customers LIMIT 1")
            sample_email = cursor.fetchone()[0]

            # UNIQUE customers.email
            ni, wi = measure_performance(
                conn, cursor,
                "CREATE UNIQUE INDEX idx_cust_email ON customers(email)",
                "DROP INDEX idx_cust_email ON customers",
                "SELECT * FROM customers WHERE email = %s",
                (sample_email,),
                test_name='idx_cust_email',
                size_label=size_label,
                index_type='BTREE_UNIQUE'
            )
            if ni is not None and wi is not None:
                results['idx_cust_email'].append((ni, wi))

            # B-Tree orders.order_date
            ni, wi = measure_performance(
                conn, cursor,
                "CREATE INDEX idx_ord_date ON orders(order_date)",
                "DROP INDEX idx_ord_date ON orders",
                "SELECT * FROM orders WHERE order_date BETWEEN %s AND %s",
                ('2023-01-01', '2023-12-31'),
                test_name='idx_ord_date',
                size_label=size_label,
                index_type='BTREE'
            )
            if ni is not None and wi is not None:
                results['idx_ord_date'].append((ni, wi))

            # B-Tree orders.status
            ni, wi = measure_performance(
                conn, cursor,
                "CREATE INDEX idx_ord_status ON orders(status)",
                "DROP INDEX idx_ord_status ON orders",
                "SELECT * FROM orders WHERE status = %s",
                ('Entregue',),
                test_name='idx_ord_status',
                size_label=size_label,
                index_type='BTREE'
            )
            if ni is not None and wi is not None:
                results['idx_ord_status'].append((ni, wi))

            # B-Tree orders.total
            ni, wi = measure_performance(
                conn, cursor,
                "CREATE INDEX idx_ord_total ON orders(total)",
                "DROP INDEX idx_ord_total ON orders",
                "SELECT * FROM orders WHERE total > %s",
                (500,),
                test_name='idx_ord_total',
                size_label=size_label,
                index_type='BTREE'
            )
            if ni is not None and wi is not None:
                results['idx_ord_total'].append((ni, wi))

            # FULLTEXT orders.description
            ni, wi = measure_fulltext(
                conn, cursor,
                "CREATE FULLTEXT INDEX idx_ord_desc ON orders(description)",
                "DROP INDEX idx_ord_desc ON orders",
                "SELECT * FROM orders WHERE MATCH(description) AGAINST(%s IN BOOLEAN MODE)",
                ('importante',),
                "SELECT * FROM orders WHERE description LIKE %s",
                ('%importante%',),
                test_name='idx_ord_desc',
                size_label=size_label
            )
            if ni is not None and wi is not None:
                results['idx_ord_desc'].append((ni, wi))
                
            # ÍNDICE COMPOSTO orders (status, order_date)
            try:
                # Removemos qualquer índice anterior primeiro para evitar erros
                try:
                    cursor.execute("DROP INDEX idx_composto ON orders")
                    conn.commit()
                except mysql.connector.Error:
                    pass  # Ignora erros se o índice não existir
                
                # Consulta sem índice composto
                cursor.execute("SELECT * FROM orders WHERE status = 'Entregue' AND order_date BETWEEN '2023-01-01' AND '2023-12-31' LIMIT 1")
                cursor.fetchall()  # Warm-up
                
                no_idx_times = []
                for _ in range(N_RUNS):
                    t0 = time.time()
                    cursor.execute("SELECT * FROM orders WHERE status = 'Entregue' AND order_date BETWEEN '2023-01-01' AND '2023-12-31'")
                    cursor.fetchall()
                    no_idx_times.append(time.time() - t0)
                no_idx_avg = sum(no_idx_times[1:]) / (N_RUNS - 1)
                
                # Salva plano explain sem índice
                explain_no_idx = get_explain_plan(cursor, "SELECT * FROM orders WHERE status = 'Entregue' AND order_date BETWEEN '2023-01-01' AND '2023-12-31'")
                save_explain_plan(explain_no_idx, f'BTREE_COMPOSTO_idx_composto_{size_label}_no_idx.csv')
                
                # Cria índice composto
                cursor.execute("CREATE INDEX idx_composto ON orders(status, order_date)")
                conn.commit()
                
                # Consulta com índice composto
                cursor.execute("SELECT * FROM orders WHERE status = 'Entregue' AND order_date BETWEEN '2023-01-01' AND '2023-12-31' LIMIT 1")
                cursor.fetchall()  # Warm-up
                
                with_idx_times = []
                for _ in range(N_RUNS):
                    t0 = time.time()
                    cursor.execute("SELECT * FROM orders WHERE status = 'Entregue' AND order_date BETWEEN '2023-01-01' AND '2023-12-31'")
                    cursor.fetchall()
                    with_idx_times.append(time.time() - t0)
                with_idx_avg = sum(with_idx_times[1:]) / (N_RUNS - 1)
                
                # Salva plano explain com índice
                explain_with_idx = get_explain_plan(cursor, "SELECT * FROM orders WHERE status = 'Entregue' AND order_date BETWEEN '2023-01-01' AND '2023-12-31'")
                save_explain_plan(explain_with_idx, f'BTREE_COMPOSTO_idx_composto_{size_label}_with_idx.csv')
                
                # Salva resultados
                filename = os.path.join(TIMES_DIR, f'times_BTREE_COMPOSTO_idx_composto.csv')
                file_exists = os.path.isfile(filename)
                with open(filename, 'a', newline='', encoding='utf-8') as csvfile:
                    writer = csv.writer(csvfile)
                    if not file_exists:
                        writer.writerow(['Volume', 'Sem Índice (s)', 'Com Índice (s)', 'Melhoria (%)'])
                    improvement = ((no_idx_avg - with_idx_avg) / no_idx_avg * 100) if no_idx_avg else 0
                    writer.writerow([size_label, round(no_idx_avg, 4), round(with_idx_avg, 4), round(improvement, 2)])
                
                results['idx_composto'].append((no_idx_avg, with_idx_avg))
                
                # Remove índice para próxima iteração
                cursor.execute("DROP INDEX idx_composto ON orders")
                conn.commit()
                
            except mysql.connector.Error as err:
                print(f"Erro ao testar índice composto: {err}")
                
            # ÍNDICE HASH (simulado via MEMORY ENGINE)
            try:
                # Remove tabela se existir
                cursor.execute("DROP TABLE IF EXISTS orders_memory")
                conn.commit()
                
                # Cria tabela com engine MEMORY
                cursor.execute("""
                CREATE TABLE orders_memory (
                    id INT,
                    customer_id INT,
                    total DECIMAL(10,2),
                    status VARCHAR(20),
                    PRIMARY KEY USING HASH (id)
                ) ENGINE=MEMORY
                """)
                conn.commit()
                
                # Insere dados de amostra
                cursor.execute("INSERT INTO orders_memory SELECT id, customer_id, total, status FROM orders LIMIT 1000")
                conn.commit()
                
                # Teste sem usar índice hash (consulta por coluna não indexada)
                cursor.execute("SELECT * FROM orders_memory WHERE total > 500 LIMIT 1")
                cursor.fetchall()  # Warm-up
                
                no_idx_times = []
                for _ in range(N_RUNS):
                    t0 = time.time()
                    cursor.execute("SELECT * FROM orders_memory WHERE total > 500")
                    cursor.fetchall()
                    no_idx_times.append(time.time() - t0)
                no_idx_avg = sum(no_idx_times[1:]) / (N_RUNS - 1)
                
                # Teste usando índice hash (consulta pela chave primária)
                cursor.execute("SELECT * FROM orders_memory WHERE id = 100 LIMIT 1")
                cursor.fetchall()  # Warm-up
                
                with_idx_times = []
                for _ in range(N_RUNS):
                    t0 = time.time()
                    cursor.execute("SELECT * FROM orders_memory WHERE id = 100")
                    cursor.fetchall()
                    with_idx_times.append(time.time() - t0)
                with_idx_avg = sum(with_idx_times[1:]) / (N_RUNS - 1)
                
                # Salva planos explain
                explain_no_idx = get_explain_plan(cursor, "SELECT * FROM orders_memory WHERE total > 500")
                save_explain_plan(explain_no_idx, f'HASH_idx_hash_{size_label}_no_idx.csv')
                
                explain_with_idx = get_explain_plan(cursor, "SELECT * FROM orders_memory WHERE id = 100")
                save_explain_plan(explain_with_idx, f'HASH_idx_hash_{size_label}_with_idx.csv')
                
                # Salvando tempos em CSV
                filename = os.path.join(TIMES_DIR, f'times_HASH_idx_hash.csv')
                file_exists = os.path.isfile(filename)
                with open(filename, 'a', newline='', encoding='utf-8') as csvfile:
                    writer = csv.writer(csvfile)
                    if not file_exists:
                        writer.writerow(['Volume', 'Sem Índice (s)', 'Com Índice (s)', 'Melhoria (%)'])
                    improvement = ((no_idx_avg - with_idx_avg) / no_idx_avg * 100) if no_idx_avg else 0
                    writer.writerow([size_label, round(no_idx_avg, 4), round(with_idx_avg, 4), round(improvement, 2)])
                
                results['idx_hash'].append((no_idx_avg, with_idx_avg))
                
                # Limpeza
                cursor.execute("DROP TABLE IF EXISTS orders_memory")
                conn.commit()
                
            except mysql.connector.Error as err:
                print(f"Erro ao testar índice HASH: {err}")

        # Gera gráficos para cada índice
        for idx_name, times in results.items():
            if times:
                plot_results(times, sizes, idx_name, index_types[idx_name])

        cursor.close()
        conn.close()

        print("\nTestes concluídos com sucesso.")
    except Exception as e:
        print(f"Erro durante a execução: {e}")
        raise

if __name__ == "__main__":
    run_tests()
