def isIter(arg) -> bool:
    # allows program to handle tuples and lists
    return isinstance(arg, list) or isinstance(arg, tuple)

getTables = "SELECT name FROM sqlite_schema WHERE type='table' AND name NOT LIKE 'sqlite_%';"

_insertDict1 = {None: isIter}
_insertDict2 = {
            True: lambda wrap, values: f"VALUES{wrap(values)}",
            False: lambda wrap, values: wrap(values.keys()) + " VALUES" + wrap(values.values())
        }

def createTable(name: str, fields: dict):
    # https://www.sqlite.org/datatype3.html
    """Generate a CREATE TABLE sqlite query

    fields format example:
    {"ID": ["INT", "PRIMARY KEY"], "NAME": ["TEXT", "NOT NULL"]}
    or
    {"ID": "INT PRIMARY KEY", "NAME": "TEXT NOT NULL"}
    """

    query = f"CREATE TABLE {name}("

    for fName, fArgs in fields.items(): # fieldName, fieldArgs

        if isIter(fArgs): # convert to string if iter
            fArgs = " ".join(fArgs)

        query+= f"{fName} {fArgs}, "

    query = query[:-2] # remove trailing ", "
    query+= ");" # add ending

    return query


def addColumn(tableName: str, columnName: str, args: tuple | str):
    """Generate an sqlite query to add a column

    Example: addColumn("myTable", "myColumn", "INT DEFAULT 0")
    or
    Example: addColumn("myTable", "myColumn", ["INT", "DEFAULT 0"])
    """

    if isIter(args): args = " ".join(args)

    return f"ALTER TABLE {tableName} ADD COLUMN '{columnName}' {args};"


def getColumns(name: str):
    """Generate a PRAGMA TABLE_INFO sqlite query"""
    return f"PRAGMA TABLE_INFO({name});"


def insert(tableName: str, values: tuple | dict, columns=None):
    # This is a horribly written function. I, @pyes on Discord, take full responsibility
    """Generate an INSERT sqlite query"""
    wrap = lambda iterable: "(" + ", ".join(map(repr, iterable)) + ")"
    query = f"INSERT INTO {tableName} "

    try:
        query+= _insertDict2[(_insertDict1[columns](values))](wrap, values)

    except KeyError:
        query+= f"{wrap(columns)} VALUES{wrap(values)}"

    query+= ";"

    return query


def _generic(
    tableName: str, # name of the table
    mode: str, # "DELETE", "UPDATE" or "SELECT"
    conditions: dict = None, #
    orderBy: str = None,
    limit: int = None,
    offset: int = None,
    desc: bool = False,
    *,
    columns: tuple = None,
    values: dict = None
    ):
    """Create a generic query. Intended for internal use only.

tableName (str) - Name of the table
mode (str) - "DELETE", "UPDATE" or "SELECT"
conditions (dict) - Conditions to pass to the WHERE statement
orderBy (str) - Column to order matching entries by
limit (int) - Limit the amount of entries the action is performed on
offset (int) - Perform the action only on entries after the specified offset
desc (bool) - Reverses the order of the entries if True (descending)
columns (tuple) - Specifies which columns to retrieve if SELECT mode is used, ignored otherwise. By default all columns are retrieved.
values (dict) - Specifies which column (key in the dictionary) should get which value (value in the dictionary) if UPDATE mode is used, ignored otherwise
"""
    # [[[SELECT attributes] / DELETE FROM] / UPDATE] table [SET setList] WHERE whereList ORDER BY orderColumn LIMIT limitCount OFFSET offset

    attributes = (
        ",".join([f"{tableName}.'{column}'" for column in columns]) + " "
        if columns else ("* " if mode == "SELECT" else "")
        )

    fromKeyword = (
        "FROM "
        if mode in {"SELECT", "DELETE"} else ""
        )

    sets = (
        "SET " + ",".join((map("=".join, zip(values.keys(), map(str, values.values()))))) + " "
        if mode == "UPDATE" else ""
        )

    wheres = (
        "WHERE " + " AND ".join((map("=".join, zip(conditions.keys(), map(str, conditions.values()))))) + " "
        if conditions else ""
        )

    order = (
        f"ORDER BY {orderBy} "
        if orderBy else ""
        )

    desc = "DESC " if desc else ""

    limit = (
        f"LIMIT {limit} "
        if limit else ""
        )

    offset = (
        f"OFFSET {offset} "
        if offset else ""
        )

    query = f"{mode} {attributes}{fromKeyword}{tableName} {sets}{wheres}{order}{desc}{limit}{offset}"
    return query.rstrip() + ";"


def update( # shorthand for _generic
    tableName: str,
    values: dict,
    conditions: dict = None,
    orderBy: str = None,
    limit: int = None,
    offset: int = None,
    desc: bool = None):
    """Generate an UPDATE sqlite query

    Example: update("myTable", {"salary": 100, "department": "sales"}, {"employee_id": 23, "job_title": "Sales Manager"})
    For information about the orderBy, limit, offset, and desc values see https://www.sqlite.org/lang_update.html
    """

    return _generic(tableName, "UPDATE", conditions, orderBy, limit, offset, desc, values=values)


def select( # shorthand for _generic
    tableName: str,
    conditions: dict = None,
    columns: tuple = None,
    orderBy: str = None,
    limit: int = None,
    offset: int = None,
    desc: bool = None):
    """Generate a SELECT sqlite query

    Example: select("myTable", {"employee_id": 23, "job_title": "Sales Manager"}, ["salary", "department"])
    Note that either lists or tuples can be used for the "columns" argument
    If "columns" is left empty, it is defaulted to "*"
    """

    return _generic(tableName, "SELECT", conditions, orderBy, limit, offset, desc, columns=columns)


def delete( # shorthand for _generic
    tableName: str,
    conditions: dict = None,
    orderBy: str = None,
    limit: int = None,
    offset: int = None,
    desc: bool = None):
    """Generate a DELETE sqlite query

    Example: delete("myTable", {"employee_id": 23, "job_title": "Sales Manager"})
"""

    return _generic(tableName, "DELETE", conditions, orderBy, limit, offset, desc)
