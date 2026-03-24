import json
import sqlglot
from sqlglot import expressions as exp

def analyze_sql(sql_text):
    if not sql_text or not sql_text.strip() or sql_text == "[Binary/Non-Text Content Hidden]":
        return {"tables": [], "selected_columns": []}

    try:
        tree = sqlglot.parse_one(sql_text, read="mysql", error_level=sqlglot.ErrorLevel.IGNORE)
        if not tree:
            return {"tables": [], "selected_columns": []}

        # --- Base Metadata ---
        alias_map = {t.alias_or_name: t.name for t in tree.find_all(exp.Table)}
        tables_list = [{"table_name": t.name, "alias": t.alias_or_name} for t in tree.find_all(exp.Table)]

        def resolve_table(node):
            if hasattr(node, 'table') and node.table:
                return alias_map.get(node.table, node.table)
            sel = node.find_ancestor(exp.Select)
            if sel:
                tbls = [t.name for t in sel.find_all(exp.Table) if t.find_ancestor(exp.Select) is sel]
                if len(tbls) == 1:
                    return tbls[0]
            return list(alias_map.values())[0] if len(alias_map) == 1 else "unknown"

        # --- Selected Columns & Aliases ---
        columns_output = []
        select_node = tree.find(exp.Select)
        # We need the ordered list of select expressions to resolve "ORDER BY 1"
        select_expressions = list(select_node.expressions) if select_node else []

        for expr in select_expressions:
            # Handle Aliased columns (e.g., first_name AS fname)
            if isinstance(expr, exp.Alias):
                col = expr.find(exp.Column)
                col_obj = {
                    "table": resolve_table(col) if col else "unknown",
                    "column": col.name if col else expr.this.sql(),
                    "alias": expr.alias
                }
            # Handle standard columns
            elif isinstance(expr, exp.Column):
                col_obj = {"table": resolve_table(expr), "column": expr.name}
            else:
                continue
            
            if col_obj not in columns_output:
                columns_output.append(col_obj)

        # --- Order By Resolution (The 1, 3 scene) ---
        order_by_output = []
        order_node = tree.find(exp.Order)
        if order_node:
            for ordered_item in order_node.expressions:
                col_node = ordered_item.this
                direction = "DESC" if ordered_item.args.get("desc") else "ASC"

                # Check if it's a positional integer (e.g., ORDER BY 1)
                if isinstance(col_node, exp.Literal) and col_node.is_int:
                    idx = int(col_node.name) - 1
                    if 0 <= idx < len(columns_output):
                        resolved_col = columns_output[idx]["column"]
                        resolved_tbl = columns_output[idx]["table"]
                    else:
                        resolved_col = col_node.sql()
                        resolved_tbl = "unknown"
                else:
                    resolved_col = col_node.name if isinstance(col_node, exp.Column) else col_node.sql()
                    resolved_tbl = resolve_table(col_node) if isinstance(col_node, exp.Column) else "unknown"

                order_by_output.append({
                    "table": resolved_tbl,
                    "column": resolved_col,
                    "direction": direction
                })

        # --- Filters, Joins, Aggs (Keep your existing logic) ---
        filters_output = []
        for where in tree.find_all(exp.Where):
            for column in where.find_all(exp.Column):
                filt_obj = {"table": resolve_table(column), "column": column.name}
                if filt_obj not in filters_output: filters_output.append(filt_obj)

        subqueries_output = []
        all_selects = list(tree.find_all(exp.Select))
        if len(all_selects) > 1:
            for sub in all_selects[1:]:
                subqueries_output.append(sub.sql())

        # --- Final Result ---
        result = {
            "tables": tables_list,
            "selected_columns": columns_output,
        }
        if order_by_output: result["order_by"] = order_by_output
        if filters_output: result["filters"] = filters_output
        if subqueries_output: result["subqueries"] = subqueries_output

        return result

    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    query = "select * from employees e order by 1 asc, 2 desc;"
    print(json.dumps(analyze_sql(query), indent=2))