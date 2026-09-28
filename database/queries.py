"""Functions that make SQL Queries for the database."""


def _select_column(columns : list = []):
    """Take list of column names and get SELECT string."""
    if columns == []:
        col_str = '*'
    else:
        col_str = ", ".join(columns)
    return f"SELECT {col_str}"


def _type_param(type_param : tuple = ()):
    """Take 3-tuples of event type, column name and column value and get AND string."""
    if len(type_param) == 3:
        t = str(type_param[0])
        n = str(type_param[1])
        v = str(type_param[2])
        return f"(type = {t} AND {n} = {v})"
    else:
        return ""


def _type_noparam(type_noparam : str = ""):
    """Take type name and return a WHERE ready string."""
    if type_noparam == "":
        return type_noparam
    else:
        return f"(type = {type_noparam})"


def _col_param(col_param : tuple = ()):
    """Take 2-tuples of column name and column value and return a WHERE ready string."""
    if len(col_param) == 2:
        n = str(col_param[0])
        v = str(col_param[1])
        return f"({n} = {v})"
    else:
        return ""

def player_match_query(player_id : float, match_id : int, columns : list = [], type_params : list = [], type_noparams : list = [], col_params : list = []):
    INIT_FROM = "FROM events"
    init_select = _col_param(columns = columns)

    main_query = init_select + ' ' + INIT_FROM + f" WHERE (player_id = {player_id}) AND (match_id = {match_id}) AND "

    or_clauses = []
    for type_param in type_params:
        add_query = _type_param(type_param=type_param)
        if add_query == "":
            continue
        else:
            or_clauses.append(add_query)


    for type_noparam in type_noparams:
        add_query = _type_noparam(type_noparam=type_noparam)
        if add_query == "":
            continue
        else:
            or_clauses.append(add_query)


    for col_param in col_params:
        add_query = _col_param(col_param=col_param)
        if add_query == "":
            continue
        else:
            or_clauses.append(add_query)

    if or_clauses:
        combined_or = " OR ".join(or_clauses)
        main_query = f"{main_query} AND ({combined_or})"

    return main_query + ';'