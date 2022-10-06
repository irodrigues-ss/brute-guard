def count_from(conn, tb_name: str) -> int:
    cur = conn.execute(f"SELECT COUNT(*) FROM {tb_name}")
    return cur.fetchone()[0]
